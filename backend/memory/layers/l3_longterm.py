"""
L3 长期内存层 (Long-term Memory Layer)

特性：
- PostgreSQL + pgvector存储，永久保存
- 用户级生命周期 (permanent)
- 向量语义检索能力
- 跨会话数据持久化
- 支持复杂查询和分析
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import and_, or_, desc
import uuid

from ..storage.database import DatabaseManager
from ..models import BaseMemoryLayer, MemoryLayer, MemoryScope, MemoryMetadata

try:
    from pgvector.sqlalchemy import Vector

    VECTOR_AVAILABLE = True
except ImportError:
    Vector = None
    VECTOR_AVAILABLE = False

logger = logging.getLogger(__name__)

class LongtermMemoryModel:
    """长期内存数据库模型（不使用Base，独立定义）"""

    __tablename__ = "longterm_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 内存键和作用域
    memory_key = Column(String(500), nullable=False, index=True)
    scope = Column(String(50), nullable=False, index=True)  # user/agent/workspace
    scope_id = Column(String(255), nullable=False, index=True)  # user_id/agent_id等

    # 数据内容
    content = Column(JSONB, nullable=False)  # 实际数据值
    content_text = Column(Text)  # 文本摘要，用于全文检索

    # 向量嵌入（用于语义检索）
    embedding = Column(Vector(1536)) if VECTOR_AVAILABLE else Column(Text)

    # 元数据
    importance = Column(Float, default=0.5)
    access_count = Column(Integer, default=0)
    session_count = Column(Integer, default=0)  # 被多少个session访问过
    tags = Column(JSONB, default=list)  # 标签列表

    # 提升信息
    promoted_from_layer = Column(String(20))  # l1/l2
    promotion_reason = Column(String(50))  # 提升原因
    promotion_timestamp = Column(DateTime)

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 索引定义
    __table_args__ = (
        Index("idx_memory_scope", "scope", "scope_id"),
        Index("idx_memory_key_scope", "memory_key", "scope", "scope_id", unique=True),
        Index("idx_importance", "importance"),
        Index("idx_last_accessed", "last_accessed"),
    )

class L3LongtermLayer(BaseMemoryLayer):
    """L3 长期内存层"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        super().__init__(MemoryLayer.L3_LONG_TERM)
        self.db = db_manager or DatabaseManager()
        self._ensure_table_exists()

        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "semantic_searches": 0,
        }

    def _ensure_table_exists(self):
        """确保长期内存表存在"""
        try:
            with self.db.get_session() as session:
                # 检查表是否存在
                from sqlalchemy import inspect

                inspector = inspect(session.bind)

                if "longterm_memory" not in inspector.get_table_names():
                    # 创建表
                    from sqlalchemy import Table, MetaData

                    metadata = MetaData()

                    table = Table(
                        "longterm_memory",
                        metadata,
                        Column(
                            "id",
                            UUID(as_uuid=True),
                            primary_key=True,
                            default=uuid.uuid4,
                        ),
                        Column("memory_key", String(500), nullable=False, index=True),
                        Column("scope", String(50), nullable=False, index=True),
                        Column("scope_id", String(255), nullable=False, index=True),
                        Column("content", JSONB, nullable=False),
                        Column("content_text", Text),
                        Column("embedding", Vector(1536) if VECTOR_AVAILABLE else Text),
                        Column("importance", Float, default=0.5),
                        Column("access_count", Integer, default=0),
                        Column("session_count", Integer, default=0),
                        Column("tags", JSONB, default=list),
                        Column("promoted_from_layer", String(20)),
                        Column("promotion_reason", String(50)),
                        Column("promotion_timestamp", DateTime),
                        Column(
                            "created_at",
                            DateTime,
                            nullable=False,
                            default=datetime.utcnow,
                        ),
                        Column(
                            "last_accessed",
                            DateTime,
                            nullable=False,
                            default=datetime.utcnow,
                        ),
                        Column(
                            "updated_at",
                            DateTime,
                            nullable=False,
                            default=datetime.utcnow,
                        ),
                        Index("idx_memory_scope", "scope", "scope_id"),
                        Index(
                            "idx_memory_key_scope",
                            "memory_key",
                            "scope",
                            "scope_id",
                            unique=True,
                        ),
                        Index("idx_importance", "importance"),
                        Index("idx_last_accessed", "last_accessed"),
                    )

                    metadata.create_all(session.bind)
                    logger.info("Created longterm_memory table")

        except Exception as e:
            logger.warning(f"Failed to ensure table exists: {e}")

    def _build_db_key(self, key: str, scope: MemoryScope, scope_id: str) -> str:
        """构建数据库存储键"""
        return f"{scope.value}:{scope_id}:{key}"

    async def get(
        self, key: str, scope: MemoryScope, scope_id: str
    ) -> Optional[Tuple[Any, MemoryMetadata]]:
        """获取数据"""
        try:
            with self.db.get_session() as session:
                db_key = self._build_db_key(key, scope, scope_id)

                result = session.execute(
                    f"""
                    SELECT content, importance, access_count, session_count, 
                           tags, created_at, last_accessed, promoted_from_layer,
                           promotion_reason
                    FROM longterm_memory
                    WHERE memory_key = :key AND scope = :scope AND scope_id = :scope_id
                    """,
                    {"key": db_key, "scope": scope.value, "scope_id": scope_id},
                ).fetchone()

                if result is None:
                    self.stats["misses"] += 1
                    return None

                # 解析结果
                (
                    content,
                    importance,
                    access_count,
                    session_count,
                    tags,
                    created_at,
                    last_accessed,
                    promoted_from,
                    promotion_reason,
                ) = result

                # 构建元数据
                metadata = MemoryMetadata(
                    key=key,
                    layer=MemoryLayer.L3_LONG_TERM,
                    scope=scope,
                    created_at=created_at,
                    importance=importance,
                    access_count=access_count,
                    last_accessed=last_accessed,
                    tags=tags or [],
                )

                # 更新访问统计（异步，不阻塞）
                session.execute(
                    """
                    UPDATE longterm_memory
                    SET access_count = access_count + 1,
                        last_accessed = :now
                    WHERE memory_key = :key AND scope = :scope AND scope_id = :scope_id
                    """,
                    {
                        "now": datetime.utcnow(),
                        "key": db_key,
                        "scope": scope.value,
                        "scope_id": scope_id,
                    },
                )
                session.commit()

                self.stats["hits"] += 1
                return content, metadata

        except Exception as e:
            logger.error(f"L3 get error: {e}")
            self.stats["misses"] += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        scope: MemoryScope,
        scope_id: str,
        metadata: Optional[MemoryMetadata] = None,
        ttl_seconds: Optional[int] = None,  # L3不使用TTL，永久存储
    ) -> bool:
        """设置数据"""
        try:
            with self.db.get_session() as session:
                db_key = self._build_db_key(key, scope, scope_id)

                # 准备数据
                if metadata is None:
                    metadata = MemoryMetadata(
                        key=key, layer=MemoryLayer.L3_LONG_TERM, scope=scope
                    )

                # 提取文本内容用于全文检索
                content_text = self._extract_text_content(value)

                # 检查是否已存在
                existing = session.execute(
                    "SELECT id FROM longterm_memory WHERE memory_key = :key AND scope = :scope AND scope_id = :scope_id",
                    {"key": db_key, "scope": scope.value, "scope_id": scope_id},
                ).fetchone()

                now = datetime.utcnow()

                if existing:
                    # 更新现有记录
                    session.execute(
                        """
                        UPDATE longterm_memory
                        SET content = :content,
                            content_text = :content_text,
                            importance = :importance,
                            tags = :tags,
                            updated_at = :now
                        WHERE memory_key = :key AND scope = :scope AND scope_id = :scope_id
                        """,
                        {
                            "content": value,
                            "content_text": content_text,
                            "importance": metadata.importance,
                            "tags": metadata.tags,
                            "now": now,
                            "key": db_key,
                            "scope": scope.value,
                            "scope_id": scope_id,
                        },
                    )
                else:
                    # 插入新记录
                    session.execute(
                        """
                        INSERT INTO longterm_memory 
                        (id, memory_key, scope, scope_id, content, content_text, 
                         importance, access_count, session_count, tags, 
                         created_at, last_accessed, updated_at)
                        VALUES 
                        (:id, :key, :scope, :scope_id, :content, :content_text,
                         :importance, :access_count, :session_count, :tags,
                         :now, :now, :now)
                        """,
                        {
                            "id": uuid.uuid4(),
                            "key": db_key,
                            "scope": scope.value,
                            "scope_id": scope_id,
                            "content": value,
                            "content_text": content_text,
                            "importance": metadata.importance,
                            "access_count": metadata.access_count,
                            "session_count": len(metadata.session_ids),
                            "tags": metadata.tags,
                            "now": now,
                        },
                    )

                session.commit()
                self.stats["sets"] += 1
                return True

        except Exception as e:
            logger.error(f"L3 set error: {e}")
            return False

    def _extract_text_content(self, value: Any) -> str:
        """从数据中提取文本内容"""
        if isinstance(value, str):
            return value
        elif isinstance(value, dict):
            # 提取所有字符串值
            texts = []
            for v in value.values():
                if isinstance(v, str):
                    texts.append(v)
                elif isinstance(v, (list, dict)):
                    texts.append(str(v))
            return " ".join(texts)
        elif isinstance(value, list):
            return " ".join(str(item) for item in value)
        else:
            return str(value)

    async def delete(self, key: str, scope: MemoryScope, scope_id: str) -> bool:
        """删除数据"""
        try:
            with self.db.get_session() as session:
                db_key = self._build_db_key(key, scope, scope_id)

                result = session.execute(
                    """
                    DELETE FROM longterm_memory
                    WHERE memory_key = :key AND scope = :scope AND scope_id = :scope_id
                    """,
                    {"key": db_key, "scope": scope.value, "scope_id": scope_id},
                )

                session.commit()

                if result.rowcount > 0:
                    self.stats["deletes"] += 1
                    return True
                return False

        except Exception as e:
            logger.error(f"L3 delete error: {e}")
            return False

    async def exists(self, key: str, scope: MemoryScope, scope_id: str) -> bool:
        """检查数据是否存在"""
        try:
            with self.db.get_session() as session:
                db_key = self._build_db_key(key, scope, scope_id)

                result = session.execute(
                    """
                    SELECT 1 FROM longterm_memory
                    WHERE memory_key = :key AND scope = :scope AND scope_id = :scope_id
                    LIMIT 1
                    """,
                    {"key": db_key, "scope": scope.value, "scope_id": scope_id},
                ).fetchone()

                return result is not None

        except Exception as e:
            logger.error(f"L3 exists error: {e}")
            return False

    async def list_keys(
        self, scope: MemoryScope, scope_id: str, pattern: Optional[str] = None
    ) -> List[str]:
        """列出符合条件的所有键"""
        try:
            with self.db.get_session() as session:
                if pattern:
                    # 使用LIKE模式匹配
                    db_pattern = f"{scope.value}:{scope_id}:{pattern}"
                    result = session.execute(
                        """
                        SELECT memory_key FROM longterm_memory
                        WHERE scope = :scope AND scope_id = :scope_id
                        AND memory_key LIKE :pattern
                        """,
                        {
                            "scope": scope.value,
                            "scope_id": scope_id,
                            "pattern": db_pattern.replace("*", "%"),
                        },
                    )
                else:
                    result = session.execute(
                        """
                        SELECT memory_key FROM longterm_memory
                        WHERE scope = :scope AND scope_id = :scope_id
                        """,
                        {"scope": scope.value, "scope_id": scope_id},
                    )

                # 提取原始键名
                prefix = f"{scope.value}:{scope_id}:"
                keys = []
                for row in result:
                    full_key = row[0]
                    if full_key.startswith(prefix):
                        keys.append(full_key[len(prefix) :])

                return keys

        except Exception as e:
            logger.error(f"L3 list_keys error: {e}")
            return []

    async def get_metadata(
        self, key: str, scope: MemoryScope, scope_id: str
    ) -> Optional[MemoryMetadata]:
        """获取数据的元信息"""
        try:
            with self.db.get_session() as session:
                db_key = self._build_db_key(key, scope, scope_id)

                result = session.execute(
                    """
                    SELECT importance, access_count, session_count, tags, 
                           created_at, last_accessed
                    FROM longterm_memory
                    WHERE memory_key = :key AND scope = :scope AND scope_id = :scope_id
                    """,
                    {"key": db_key, "scope": scope.value, "scope_id": scope_id},
                ).fetchone()

                if result is None:
                    return None

                (
                    importance,
                    access_count,
                    session_count,
                    tags,
                    created_at,
                    last_accessed,
                ) = result

                return MemoryMetadata(
                    key=key,
                    layer=MemoryLayer.L3_LONG_TERM,
                    scope=scope,
                    created_at=created_at,
                    importance=importance,
                    access_count=access_count,
                    last_accessed=last_accessed,
                    tags=tags or [],
                )

        except Exception as e:
            logger.error(f"L3 get_metadata error: {e}")
            return None

    async def update_metadata(
        self, key: str, scope: MemoryScope, scope_id: str, metadata: MemoryMetadata
    ) -> bool:
        """更新数据的元信息"""
        try:
            with self.db.get_session() as session:
                db_key = self._build_db_key(key, scope, scope_id)

                result = session.execute(
                    """
                    UPDATE longterm_memory
                    SET importance = :importance,
                        tags = :tags,
                        updated_at = :now
                    WHERE memory_key = :key AND scope = :scope AND scope_id = :scope_id
                    """,
                    {
                        "importance": metadata.importance,
                        "tags": metadata.tags,
                        "now": datetime.utcnow(),
                        "key": db_key,
                        "scope": scope.value,
                        "scope_id": scope_id,
                    },
                )

                session.commit()
                return result.rowcount > 0

        except Exception as e:
            logger.error(f"L3 update_metadata error: {e}")
            return False

    async def clear_scope(self, scope: MemoryScope, scope_id: str) -> int:
        """清空指定作用域的所有数据"""
        try:
            with self.db.get_session() as session:
                result = session.execute(
                    """
                    DELETE FROM longterm_memory
                    WHERE scope = :scope AND scope_id = :scope_id
                    """,
                    {"scope": scope.value, "scope_id": scope_id},
                )

                session.commit()
                return result.rowcount

        except Exception as e:
            logger.error(f"L3 clear_scope error: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {"layer": self.layer_type.value, **self.stats}

        try:
            with self.db.get_session() as session:
                result = session.execute(
                    """
                    SELECT 
                        COUNT(*) as total_records,
                        AVG(importance) as avg_importance,
                        SUM(access_count) as total_accesses,
                        COUNT(DISTINCT scope_id) as unique_users
                    FROM longterm_memory
                    """
                ).fetchone()

                if result:
                    stats["total_records"] = result[0]
                    stats["avg_importance"] = float(result[1] or 0)
                    stats["total_accesses"] = result[2] or 0
                    stats["unique_users"] = result[3] or 0

        except Exception as e:
            logger.error(f"Failed to get L3 stats: {e}")

        hit_rate = 0.0
        total_requests = self.stats["hits"] + self.stats["misses"]
        if total_requests > 0:
            hit_rate = self.stats["hits"] / total_requests
        stats["hit_rate"] = hit_rate

        return stats

    async def semantic_search(
        self,
        query_embedding: List[float],
        scope: MemoryScope,
        scope_id: str,
        limit: int = 10,
        min_importance: float = 0.3,
    ) -> List[Tuple[str, Any, float]]:
        """
        语义相似度搜索

        Args:
            query_embedding: 查询向量
            scope: 作用域
            scope_id: 作用域ID
            limit: 返回数量
            min_importance: 最低重要性阈值

        Returns:
            [(key, content, similarity_score), ...]
        """
        if not VECTOR_AVAILABLE:
            logger.warning("pgvector not available, semantic search disabled")
            return []

        try:
            with self.db.get_session() as session:
                # 使用余弦相似度搜索
                result = session.execute(
                    """
                    SELECT memory_key, content, 
                           1 - (embedding <=> :query_vector) as similarity
                    FROM longterm_memory
                    WHERE scope = :scope AND scope_id = :scope_id
                    AND importance >= :min_importance
                    AND embedding IS NOT NULL
                    ORDER BY embedding <=> :query_vector
                    LIMIT :limit
                    """,
                    {
                        "query_vector": query_embedding,
                        "scope": scope.value,
                        "scope_id": scope_id,
                        "min_importance": min_importance,
                        "limit": limit,
                    },
                )

                # 提取结果
                results = []
                prefix = f"{scope.value}:{scope_id}:"
                for row in result:
                    full_key, content, similarity = row
                    if full_key.startswith(prefix):
                        key = full_key[len(prefix) :]
                        results.append((key, content, float(similarity)))

                self.stats["semantic_searches"] += 1
                return results

        except Exception as e:
            logger.error(f"L3 semantic_search error: {e}")
            return []
