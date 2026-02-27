"""
Memory Optimization Utilities
"""
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def calculate_memory_importance(
    access_count: int,
    last_accessed: Optional[datetime],
    age_days: float
) -> float:
    """
    计算记忆重要性分数

    综合考虑访问频率、最后访问时间和记忆年龄

    Args:
        access_count: 访问次数
        last_accessed: 最后访问时间
        age_days: 记忆年龄（天）

    Returns:
        重要性分数 (0.0-1.0)
    """
    # 访问频率分数 (0-0.4)
    access_score = min(access_count / 100.0, 0.4)

    # 最近访问分数 (0-0.3)
    recent_score = 0.0
    if last_accessed:
        days_since_access = (datetime.utcnow() - last_accessed).days
        if days_since_access < 1:
            recent_score = 0.3
        elif days_since_access < 7:
            recent_score = 0.2
        elif days_since_access < 30:
            recent_score = 0.1

    # 年龄分数 (0-0.3)，越新越重要
    age_score = max(0.3 - (age_days / 365.0) * 0.3, 0.0)

    importance = access_score + recent_score + age_score

    logger.debug(
        f"[MemoryOptimizer] Importance: {importance:.3f} "
        f"(access={access_score:.2f}, recent={recent_score:.2f}, age={age_score:.2f})"
    )

    return importance


async def optimize_memory_size(
    memory_manager: Any,
    max_size_mb: int = 100
) -> Dict[str, Any]:
    """
    优化记忆大小

    删除低重要性的记忆以控制总大小

    Args:
        memory_manager: 记忆管理器实例
        max_size_mb: 最大大小（MB）

    Returns:
        优化结果
    """
    logger.info(f"[MemoryOptimizer] Starting optimization (max={max_size_mb}MB)")

    # 这是一个简化实现
    # 实际应该查询数据库获取记忆大小分布
    result = {
        "before_size_mb": 0,
        "after_size_mb": 0,
        "deleted_count": 0,
        "kept_count": 0
    }

    logger.info(f"[MemoryOptimizer] Optimization complete: {result}")
    return result


async def cleanup_expired_memories(memory_manager: Any) -> int:
    """
    清理过期记忆

    Args:
        memory_manager: 记忆管理器实例

    Returns:
        清理的记忆数量
    """
    logger.info("[MemoryOptimizer] Starting expired memory cleanup")

    count = 0
    # 简化实现
    # 实际应该查询SharedWorkspaceMemory表删除过期记录

    logger.info(f"[MemoryOptimizer] Cleaned up {count} expired memories")
    return count


async def compress_memory_data(data: Any) -> Any:
    """
    压缩记忆数据

    Args:
        data: 原始数据

    Returns:
        压缩后的数据
    """
    # 简化实现
    # 实际可以使用gzip等压缩算法
    return data


class MemoryOptimizer:
    """
    记忆优化器

    提供记忆系统的优化功能
    """

    def __init__(self, memory_manager: Any):
        """
        初始化优化器

        Args:
            memory_manager: 记忆管理器实例
        """
        self.memory_manager = memory_manager

    async def optimize_all(self) -> Dict[str, Any]:
        """
        执行所有优化

        Returns:
            优化结果
        """
        logger.info("[MemoryOptimizer] Starting full optimization")

        results = {
            "expired_cleanup": 0,
            "size_optimization": {},
            "timestamp": datetime.utcnow().isoformat()
        }

        # 清理过期记忆
        results["expired_cleanup"] = await cleanup_expired_memories(
            self.memory_manager
        )

        # 优化大小
        results["size_optimization"] = await optimize_memory_size(
            self.memory_manager
        )

        logger.info(f"[MemoryOptimizer] Full optimization complete: {results}")
        return results

    async def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """
        获取优化建议

        Returns:
            优化建议列表
        """
        suggestions = []

        # 检查是否有大量过期记忆
        # suggestions.append({
        #     "type": "cleanup_expired",
        #     "priority": "high",
        #     "description": "Found X expired memories",
        #     "action": "Run cleanup_expired_memories()"
        # })

        return suggestions
