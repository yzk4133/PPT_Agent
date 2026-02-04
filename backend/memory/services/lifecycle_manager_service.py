"""
生命周期管理服务 - Lifecycle Manager Service

实现数据生命周期管理：

1. 时间衰减重要性评分 - importance * 0.95^(days/30)
2. 分层归档策略 - 热/温/冷数据
3. 内容摘要 - LLM压缩大内容
4. 定期清理 - 自动清理过期数据

数据分类：
- 热数据 (0-30天): PG主库，快速访问
- 温数据 (30-180天): 只读副本，降级访问
- 冷数据 (180天+): S3归档，摘要+向量

使用示例：
```python
lifecycle = LifecycleManagerService(db_manager)

# 计算衰减后的重要性
decayed_importance = await lifecycle.calculate_decay_importance(
    original_importance=0.8,
    days_since_creation=60
)

# 归档冷数据
archived_count = await lifecycle.archive_cold_data()

# 恢复归档数据
data = await lifecycle.retrieve_archived_data(memory_id)
```
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# SQLAlchemy
from sqlalchemy import and_, or_, desc, func

# 尝试导入OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

# ============================================================================
# 枚举和配置
# ============================================================================

class DataTemperature(Enum):
    """数据温度分类"""
    HOT = "hot"       # 0-30天
    WARM = "warm"     # 30-180天
    COLD = "cold"     # 180天+

class LifecycleConfig:
    """生命周期管理配置"""

    # 时间衰减参数
    DECAY_RATE = 0.95           # 衰减率
    DECAY_PERIOD_DAYS = 30      # 衰减周期（天）
    MIN_IMPORTANCE = 0.1        # 最低重要性

    # 数据分类阈值
    HOT_DAYS = 30               # 热数据天数
    WARM_DAYS = 180             # 温数据天数
    COLD_DAYS = 180             # 冷数据天数

    # 摘要配置
    SUMMARY_MAX_LENGTH = 500    # 摘要最大长度
    SUMMARY_MIN_COMPRESSION = 0.3  # 最小压缩比

    # 清理配置
    CLEANUP_INTERVAL = 86400    # 清理间隔（秒，1天）
    MIN_ACCESS_COUNT = 1        # 最低访问次数

# ============================================================================
# 数据模型
# ============================================================================

@dataclass
class ArchivedMemory:
    """归档数据"""
    id: str
    original_key: str
    scope: str
    scope_id: str
    content_summary: str
    original_importance: float
    decayed_importance: float
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    archived_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "original_key": self.original_key,
            "scope": self.scope,
            "scope_id": self.scope_id,
            "content_summary": self.content_summary,
            "original_importance": self.original_importance,
            "decayed_importance": self.decayed_importance,
            "embedding": self.embedding,
            "metadata": self.metadata,
            "archived_at": self.archived_at.isoformat(),
        }

# ============================================================================
# 生命周期管理服务
# ============================================================================

class LifecycleManagerService:
    """
    生命周期管理服务

    负责数据的老化、衰减和归档。
    """

    def __init__(self, db_manager, config: Optional[LifecycleConfig] = None):
        """
        初始化服务

        Args:
            db_manager: 数据库管理器
            config: 配置
        """
        self.db = db_manager
        self.config = config or LifecycleConfig()

        # OpenAI客户端（用于摘要）
        if OPENAI_AVAILABLE:
            self.openai_client = openai.AsyncOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
            )
        else:
            self.openai_client = None
            logger.warning("OpenAI not available, summarization disabled")

        # 归档存储（内存实现，生产环境应使用S3）
        self._archive_storage: Dict[str, ArchivedMemory] = {}

        # 后台任务
        self._cleanup_task = None

        # 统计信息
        self.stats = {
            "archived_count": 0,
            "decayed_count": 0,
            "cleaned_count": 0,
            "summary_generated": 0,
        }

    def start_background_tasks(self):
        """启动后台任务"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._lifecycle_loop())

    async def stop_background_tasks(self):
        """停止后台任务"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _lifecycle_loop(self):
        """生命周期管理循环"""
        while True:
            try:
                await asyncio.sleep(self.config.CLEANUP_INTERVAL)
                await self.perform_lifecycle_tasks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in lifecycle loop: {e}")

    async def perform_lifecycle_tasks(self):
        """执行生命周期管理任务"""
        logger.info("Starting lifecycle management tasks")

        # 1. 更新衰减重要性
        decayed = await self.update_decay_importance()
        self.stats["decayed_count"] += decayed

        # 2. 归档冷数据
        archived = await self.archive_cold_data()
        self.stats["archived_count"] += archived

        # 3. 清理过期数据
        cleaned = await self.cleanup_expired_data()
        self.stats["cleaned_count"] += cleaned

        logger.info(
            f"Lifecycle tasks completed: "
            f"decayed={decayed}, archived={archived}, cleaned={cleaned}"
        )

    def calculate_decay_importance(
        self,
        original_importance: float,
        days_since_creation: int,
    ) -> float:
        """
        计算衰减后的重要性

        公式: decayed_importance = importance * decay_rate^(days/period)

        Args:
            original_importance: 原始重要性
            days_since_creation: 创建后的天数

        Returns:
            衰减后的重要性
        """
        # 计算衰减周期数
        decay_periods = days_since_creation / self.config.DECAY_PERIOD_DAYS

        # 计算衰减后的重要性
        decayed_importance = original_importance * (
            self.config.DECAY_RATE ** decay_periods
        )

        # 确保不低于最低值
        return max(self.config.MIN_IMPORTANCE, decayed_importance)

    def classify_data_temperature(self, days_since_access: int) -> DataTemperature:
        """
        分类数据温度

        Args:
            days_since_access: 距离上次访问的天数

        Returns:
            数据温度
        """
        if days_since_access < self.config.HOT_DAYS:
            return DataTemperature.HOT
        elif days_since_access < self.config.WARM_DAYS:
            return DataTemperature.WARM
        else:
            return DataTemperature.COLD

    async def update_decay_importance(self) -> int:
        """
        更新所有数据的衰减重要性

        Returns:
            更新的数量
        """
        try:
            with self.db.get_session() as session:
                # 获取需要更新的数据
                result = session.execute(
                    """
                    SELECT id, memory_key, importance, created_at
                    FROM longterm_memory
                    WHERE importance > :min_importance
                    """,
                    {"min_importance": self.config.MIN_IMPORTANCE},
                ).fetchall()

                updated_count = 0
                now = datetime.now()

                for memory_id, key, importance, created_at in result:
                    # 计算天数
                    days = (now - created_at).days

                    # 计算衰减重要性
                    decayed = self.calculate_decay_importance(importance, days)

                    # 更新数据库
                    if decayed < importance:
                        session.execute(
                            """
                            UPDATE longterm_memory
                            SET importance = :decayed,
                                updated_at = :now
                            WHERE id = :id
                            """,
                            {"decayed": decayed, "now": now, "id": memory_id},
                        )
                        updated_count += 1

                session.commit()
                logger.info(f"Updated decay importance for {updated_count} memories")
                return updated_count

        except Exception as e:
            logger.error(f"Failed to update decay importance: {e}")
            return 0

    async def archive_cold_data(
        self,
        min_access_count: Optional[int] = None,
    ) -> int:
        """
        归档冷数据

        Args:
            min_access_count: 最低访问次数

        Returns:
            归档数量
        """
        min_access_count = min_access_count or self.config.MIN_ACCESS_COUNT

        try:
            with self.db.get_session() as session:
                # 查找冷数据
                cold_threshold = datetime.now() - timedelta(days=self.config.COLD_DAYS)

                result = session.execute(
                    """
                    SELECT id, memory_key, scope, scope_id, content,
                           importance, created_at, access_count
                    FROM longterm_memory
                    WHERE last_accessed < :threshold
                    AND access_count < :min_access
                    AND importance < 0.5
                    ORDER BY last_accessed ASC
                    LIMIT 100
                    """,
                    {
                        "threshold": cold_threshold,
                        "min_access": min_access_count,
                    },
                ).fetchall()

                archived_count = 0

                for row in result:
                    memory_id, key, scope, scope_id, content, importance, created_at, access_count = row

                    # 生成摘要
                    summary = await self._generate_summary(content)

                    # 创建归档记录
                    archived = ArchivedMemory(
                        id=str(memory_id),
                        original_key=key,
                        scope=scope,
                        scope_id=scope_id,
                        content_summary=summary,
                        original_importance=importance,
                        decayed_importance=importance * 0.5,  # 冷数据衰减更多
                        metadata={
                            "created_at": created_at.isoformat(),
                            "access_count": access_count,
                        },
                    )

                    # 存储归档（生产环境应写入S3）
                    self._archive_storage[str(memory_id)] = archived

                    # 删除原记录（或标记为已归档）
                    session.execute(
                        """
                        DELETE FROM longterm_memory
                        WHERE id = :id
                        """,
                        {"id": memory_id},
                    )

                    archived_count += 1

                session.commit()
                logger.info(f"Archived {archived_count} cold memories")
                return archived_count

        except Exception as e:
            logger.error(f"Failed to archive cold data: {e}")
            return 0

    async def _generate_summary(self, content: Any) -> str:
        """
        使用LLM生成内容摘要

        Args:
            content: 原始内容

        Returns:
            摘要文本
        """
        if not self.openai_client:
            # 简单截断
            text = str(content)[:self.config.SUMMARY_MAX_LENGTH]
            return text + "..." if len(content) > self.config.SUMMARY_MAX_LENGTH else text

        try:
            # 构建提示
            prompt = f"""
请将以下内容压缩成简洁的摘要（最多{self.config.SUMMARY_MAX_LENGTH}字）：

{content}

摘要：
"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的摘要生成器，擅长提取关键信息并简洁表达。"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
                temperature=0.3,
            )

            summary = response.choices[0].message.content.strip()
            self.stats["summary_generated"] += 1

            return summary

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            # 降级到简单截断
            text = str(content)[:self.config.SUMMARY_MAX_LENGTH]
            return text + "..." if len(content) > self.config.SUMMARY_MAX_LENGTH else text

    async def retrieve_archived_data(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        检索归档数据

        Args:
            memory_id: 记忆ID

        Returns:
            归档数据字典
        """
        archived = self._archive_storage.get(memory_id)
        if archived:
            return archived.to_dict()

        # 从持久化存储检索（生产环境应从S3读取）
        return None

    async def cleanup_expired_data(self) -> int:
        """
        清理过期数据

        Returns:
            清理数量
        """
        try:
            with self.db.get_session() as session:
                # 删除重要性极低且长期未访问的数据
                threshold = datetime.now() - timedelta(days=365)  # 1年

                result = session.execute(
                    """
                    DELETE FROM longterm_memory
                    WHERE importance < 0.2
                    AND last_accessed < :threshold
                    AND access_count < 2
                    """,
                    {"threshold": threshold},
                )

                cleaned_count = result.rowcount
                session.commit()

                logger.info(f"Cleaned up {cleaned_count} expired memories")
                return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup expired data: {e}")
            return 0

    async def get_lifecycle_stats(self) -> Dict[str, Any]:
        """获取生命周期统计信息"""
        try:
            with self.db.get_session() as session:
                # 数据温度统计
                now = datetime.now()
                hot_threshold = now - timedelta(days=self.config.HOT_DAYS)
                warm_threshold = now - timedelta(days=self.config.WARM_DAYS)

                result = session.execute(
                    """
                    SELECT
                        COUNT(*) FILTER (
                            WHERE last_accessed >= :hot_threshold
                        ) as hot_count,
                        COUNT(*) FILTER (
                            WHERE last_accessed >= :warm_threshold
                            AND last_accessed < :hot_threshold
                        ) as warm_count,
                        COUNT(*) FILTER (
                            WHERE last_accessed < :warm_threshold
                        ) as cold_count,
                        COUNT(*) as total_count,
                        AVG(importance) as avg_importance
                    FROM longterm_memory
                    """,
                    {
                        "hot_threshold": hot_threshold,
                        "warm_threshold": warm_threshold,
                    },
                ).fetchone()

                hot_count, warm_count, cold_count, total_count, avg_importance = result

                return {
                    "data_temperature": {
                        "hot": hot_count or 0,
                        "warm": warm_count or 0,
                        "cold": cold_count or 0,
                        "total": total_count or 0,
                    },
                    "avg_importance": float(avg_importance or 0),
                    "archived_count": len(self._archive_storage),
                    "stats": self.stats,
                }

        except Exception as e:
            logger.error(f"Failed to get lifecycle stats: {e}")
            return {"error": str(e)}

    async def promote_data(self, memory_id: str) -> bool:
        """
        提升数据（从归档恢复）

        Args:
            memory_id: 记忆ID

        Returns:
            是否成功
        """
        archived = self._archive_storage.get(memory_id)
        if not archived:
            return False

        try:
            with self.db.get_session() as session:
                # 恢复到主库
                session.execute(
                    """
                    INSERT INTO longterm_memory
                    (id, memory_key, scope, scope_id, content, content_text,
                     importance, access_count, created_at, last_accessed, updated_at)
                    VALUES
                    (:id, :key, :scope, :scope_id, :content, :content_text,
                     :importance, :access_count, :created_at, :now, :now)
                    """,
                    {
                        "id": memory_id,
                        "key": archived.original_key,
                        "scope": archived.scope,
                        "scope_id": archived.scope_id,
                        "content": archived.content_summary,  # 使用摘要
                        "content_text": archived.content_summary,
                        "importance": archived.decayed_importance * 1.2,  # 提升后增加重要性
                        "access_count": archived.metadata.get("access_count", 0),
                        "created_at": datetime.fromisoformat(archived.metadata["created_at"]),
                        "now": datetime.now(),
                    },
                )

                session.commit()

                # 从归档存储删除
                del self._archive_storage[memory_id]

                logger.info(f"Promoted archived memory: {memory_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to promote memory {memory_id}: {e}")
            return False

# ============================================================================
# 全局实例
# ============================================================================

_global_lifecycle_manager: Optional[LifecycleManagerService] = None

def get_lifecycle_manager(db_manager) -> LifecycleManagerService:
    """获取全局生命周期管理器实例"""
    global _global_lifecycle_manager
    if _global_lifecycle_manager is None:
        _global_lifecycle_manager = LifecycleManagerService(db_manager)
    return _global_lifecycle_manager
