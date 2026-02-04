#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
向量记忆服务 - 使用pgvector进行语义检索
"""
import os
import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy import and_, desc, func, text
from sqlalchemy.dialects.postgresql import insert

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("openai package not installed, vector memory will be disabled")

from ..storage.database import get_db
from ..storage.models import VectorMemory
from ..storage.redis_cache import RedisCache

logger = logging.getLogger(__name__)

class VectorMemoryService:
    """向量记忆服务 - 语义搜索和缓存"""

    # 相似度阈值
    SIMILARITY_THRESHOLD = 0.85  # 余弦相似度 > 0.85 认为命中

    # 命名空间
    NS_RESEARCH = "research_findings"
    NS_OUTLINES = "outlines"
    NS_TEMPLATES = "slide_templates"

    def __init__(self, enable_cache: bool = True):
        """
        初始化向量记忆服务

        Args:
            enable_cache: 是否启用Redis缓存
        """
        self.db = get_db()
        self.cache = RedisCache() if enable_cache else None

        # 配置OpenAI API
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                openai.api_key = api_key
                self.embedding_model = "text-embedding-3-small"
                self.embedding_dim = 1536
                logger.info("VectorMemoryService initialized with OpenAI embeddings")
            else:
                logger.warning("OPENAI_API_KEY not set, vector memory disabled")
                self.embedding_model = None
        else:
            self.embedding_model = None

    def is_available(self) -> bool:
        """检查向量服务是否可用"""
        return self.embedding_model is not None and OPENAI_AVAILABLE

    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """
        生成文本的向量表示

        Args:
            text: 输入文本

        Returns:
            向量列表（1536维）
        """
        if not self.is_available():
            return None

        try:
            # 使用OpenAI API生成embedding
            response = await openai.embeddings.create(
                model=self.embedding_model, input=text[:8000]  # 限制长度避免超限
            )

            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding (dim={len(embedding)})")
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    def _compute_query_hash(self, query: str, namespace: str, k: int) -> str:
        """计算查询哈希（用于缓存key）"""
        content = f"{query}|{namespace}|{k}"
        return hashlib.md5(content.encode()).hexdigest()

    async def search(
        self,
        query: str,
        namespace: str,
        k: int = 5,
        user_id: Optional[str] = None,
        similarity_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        语义搜索

        Args:
            query: 查询文本
            namespace: 命名空间
            k: 返回TopK结果
            user_id: 用户ID（可选，用于过滤用户特定记忆）
            similarity_threshold: 相似度阈值（默认0.85）

        Returns:
            搜索结果列表，每项包含：
            - id: 记录ID
            - content: 内容
            - metadata: 元数据
            - similarity: 相似度分数 (0-1)
        """
        if not self.is_available():
            logger.warning("Vector memory not available, returning empty results")
            return []

        similarity_threshold = similarity_threshold or self.SIMILARITY_THRESHOLD

        # 1. 检查缓存
        query_hash = self._compute_query_hash(query, namespace, k)
        if self.cache:
            cached = await self.cache.get_vector_results(query_hash)
            if cached:
                logger.info(f"Vector search cache hit: {query[:50]}...")
                return cached["results"]

        # 2. 生成查询向量
        query_embedding = await self._get_embedding(query)
        if not query_embedding:
            return []

        # 3. 在数据库中执行向量搜索
        try:
            with self.db.get_session() as db_session:
                # 构建查询条件
                conditions = [VectorMemory.namespace == namespace]
                if user_id:
                    conditions.append(
                        (VectorMemory.user_id == user_id)
                        | (VectorMemory.user_id.is_(None))
                    )

                # 使用pgvector的余弦相似度搜索
                # 1 - cosine_distance = cosine_similarity
                query_obj = (
                    db_session.query(
                        VectorMemory,
                        (
                            1 - VectorMemory.embedding.cosine_distance(query_embedding)
                        ).label("similarity"),
                    )
                    .filter(and_(*conditions))
                    .order_by(desc("similarity"))
                    .limit(k * 2)
                )  # 先取2倍数量，再过滤

                results = []
                for record, similarity in query_obj.all():
                    # 过滤低于阈值的结果
                    if similarity < similarity_threshold:
                        continue

                    results.append(
                        {
                            "id": str(record.id),
                            "content": record.content,
                            "metadata": record.metadata,
                            "similarity": float(similarity),
                            "created_at": record.created_at.isoformat(),
                            "access_count": record.access_count,
                        }
                    )

                    # 更新访问统计
                    record.access_count += 1
                    record.last_accessed_at = datetime.utcnow()

                    if len(results) >= k:
                        break

                db_session.commit()

                logger.info(
                    f"Vector search: query='{query[:50]}...', "
                    f"namespace={namespace}, found={len(results)}"
                )

                # 4. 写入缓存
                if self.cache and results:
                    await self.cache.set_vector_results(
                        query_hash, {"query": query, "results": results}
                    )

                return results

        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []

    async def store(
        self,
        content: str,
        namespace: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        embedding: Optional[List[float]] = None,
    ) -> Optional[str]:
        """
        存储向量记忆

        Args:
            content: 内容文本
            namespace: 命名空间
            metadata: 元数据
            user_id: 用户ID（可选）
            embedding: 预计算的向量（可选，不提供则自动生成）

        Returns:
            记录ID，失败返回None
        """
        if not self.is_available():
            logger.warning("Vector memory not available")
            return None

        # 生成向量
        if embedding is None:
            embedding = await self._get_embedding(content)
            if not embedding:
                return None

        try:
            with self.db.get_session() as db_session:
                record = VectorMemory(
                    namespace=namespace,
                    content=content,
                    metadata=metadata or {},
                    embedding=embedding,
                    user_id=user_id,
                    access_count=0,
                )

                db_session.add(record)
                db_session.commit()
                db_session.refresh(record)

                logger.info(
                    f"Stored vector memory: namespace={namespace}, "
                    f"content_length={len(content)}, id={record.id}"
                )

                return str(record.id)

        except Exception as e:
            logger.error(f"Failed to store vector memory: {e}")
            return None

    async def batch_store(
        self,
        items: List[Tuple[str, Dict[str, Any]]],
        namespace: str,
        user_id: Optional[str] = None,
    ) -> List[str]:
        """
        批量存储向量记忆

        Args:
            items: (content, metadata) 元组列表
            namespace: 命名空间
            user_id: 用户ID（可选）

        Returns:
            成功存储的记录ID列表
        """
        if not self.is_available() or not items:
            return []

        # 批量生成embeddings
        contents = [item[0] for item in items]

        try:
            # 使用OpenAI批量API（更高效）
            response = await openai.embeddings.create(
                model=self.embedding_model, input=contents
            )

            embeddings = [data.embedding for data in response.data]

            # 批量插入数据库
            with self.db.get_session() as db_session:
                records = []
                for (content, metadata), embedding in zip(items, embeddings):
                    record = VectorMemory(
                        namespace=namespace,
                        content=content,
                        metadata=metadata,
                        embedding=embedding,
                        user_id=user_id,
                        access_count=0,
                    )
                    records.append(record)

                db_session.bulk_save_objects(records, return_defaults=True)
                db_session.commit()

                record_ids = [str(r.id) for r in records]
                logger.info(f"Batch stored {len(record_ids)} vector memories")

                return record_ids

        except Exception as e:
            logger.error(f"Batch store error: {e}")
            return []

    async def delete(self, record_id: str) -> bool:
        """删除向量记忆"""
        try:
            with self.db.get_session() as db_session:
                deleted = (
                    db_session.query(VectorMemory)
                    .filter(VectorMemory.id == record_id)
                    .delete()
                )

                db_session.commit()
                return deleted > 0

        except Exception as e:
            logger.error(f"Failed to delete vector memory: {e}")
            return False

    async def clear_namespace(
        self, namespace: str, user_id: Optional[str] = None
    ) -> int:
        """
        清空命名空间

        Args:
            namespace: 命名空间
            user_id: 用户ID（可选，仅清空该用户的记忆）

        Returns:
            删除的记录数
        """
        try:
            with self.db.get_session() as db_session:
                query = db_session.query(VectorMemory).filter(
                    VectorMemory.namespace == namespace
                )

                if user_id:
                    query = query.filter(VectorMemory.user_id == user_id)

                deleted = query.delete()
                db_session.commit()

                logger.info(f"Cleared {deleted} records from namespace: {namespace}")
                return deleted

        except Exception as e:
            logger.error(f"Failed to clear namespace: {e}")
            return 0
