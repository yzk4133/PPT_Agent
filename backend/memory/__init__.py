"""
Memory System - 扁平化架构

统一的记忆系统，提供三层缓存架构和高层服务。

使用示例:
    from memory import HierarchicalMemoryManager, MemoryScope
    from memory.services import UserPreferenceService
    from memory.integration import AgentMemoryMixin
"""

# 核心管理器
from .manager import HierarchicalMemoryManager, get_global_memory_manager

# 核心模型
from .models import (
    MemoryLayer,
    MemoryScope,
    MemoryMetadata,
    PromotionReason,
    PromotionTracker,
)

# 提升引擎
from .promotion import PromotionEngine, PromotionConfig

__all__ = [
    # 管理器
    "HierarchicalMemoryManager",
    "get_global_memory_manager",
    # 模型
    "MemoryLayer",
    "MemoryScope",
    "MemoryMetadata",
    "PromotionReason",
    "PromotionTracker",
    # 提升引擎
    "PromotionEngine",
    "PromotionConfig",
]
