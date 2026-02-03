"""
持久化记忆系统 - 三层内存架构

目录结构：
├── core/                    # 三层内存架构核心
│   ├── memory_layer_base.py      # 抽象基类
│   ├── l1_transient_layer.py     # L1瞬时内存
│   ├── l2_short_term_layer.py    # L2短期内存
│   ├── l3_longterm_layer.py      # L3长期内存
│   └── hierarchical_memory_manager.py  # 统一管理器
├── services/                # 业务服务层
│   ├── postgres_session_service.py    # 会话管理
│   ├── user_preference_service.py     # 用户偏好
│   ├── vector_memory_service.py       # 向量检索
│   ├── agent_decision_service.py      # Agent决策追踪
│   ├── tool_feedback_service.py       # 工具反馈
│   ├── shared_workspace_service.py    # 协作工作区
│   └── context_optimizer.py           # 上下文优化
├── demos/                   # 演示示例
├── migrations/              # 数据库迁移
├── database.py              # 数据库管理
├── models.py                # 数据模型
├── redis_cache.py           # Redis缓存
└── README.md                # 使用文档

核心架构：
L1 (瞬时内存): 纯内存存储，任务级生命周期 (seconds)
L2 (短期内存): Redis存储，会话级生命周期 (hours)
L3 (长期内存): PostgreSQL+pgvector，用户级永久存储
"""

# 基础设施
from .database import DatabaseManager, get_db
from .redis_cache import RedisCache
from .models import Base, Session, UserProfile

# 三层内存架构核心
from .core import (
    MemoryLayer,
    MemoryScope,
    MemoryMetadata,
    PromotionReason,
    BaseMemoryLayer,
    PromotionTracker,
    L1TransientLayer,
    L2ShortTermLayer,
    L3LongtermLayer,
    HierarchicalMemoryManager,
    get_global_memory_manager,
    init_global_memory_manager,
    shutdown_global_memory_manager,
)

# 业务服务
from .services import (
    PostgresSessionService,
    UserPreferenceService,
    VectorMemoryService,
    AgentDecisionService,
    ToolFeedbackService,
    SharedWorkspaceService,
    ContextWindowOptimizer,
)

__all__ = [
    # 基础设施
    "DatabaseManager",
    "get_db",
    "RedisCache",
    "Base",
    "Session",
    "UserProfile",
    # 三层内存架构
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
    # 业务服务
    "PostgresSessionService",
    "UserPreferenceService",
    "VectorMemoryService",
    "AgentDecisionService",
    "ToolFeedbackService",
    "SharedWorkspaceService",
    "ContextWindowOptimizer",
]
