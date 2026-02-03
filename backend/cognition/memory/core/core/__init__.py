"""
三层内存架构核心模块
"""

from .memory_layer_base import (
    MemoryLayer,
    MemoryScope,
    MemoryMetadata,
    PromotionReason,
    BaseMemoryLayer,
    PromotionTracker,
)
from .l1_transient_layer import L1TransientLayer
from .l2_short_term_layer import L2ShortTermLayer
from .l3_longterm_layer import L3LongtermLayer
from .hierarchical_memory_manager import (
    HierarchicalMemoryManager,
    get_global_memory_manager,
    init_global_memory_manager,
    shutdown_global_memory_manager,
)

__all__ = [
    "MemoryLayer",
    "MemoryScope",
    "MemoryMetadata",
    "PromotionReason",
    "BaseMemoryLayer",
    "PromotionTracker",
    "L1TransientLayer",
    "L2ShortTermLayer",
    "L3LongtermLayer",
    "HierarchicalMemoryManager",
    "get_global_memory_manager",
    "init_global_memory_manager",
    "shutdown_global_memory_manager",
]
