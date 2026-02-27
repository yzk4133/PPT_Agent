"""
Database Models for Memory System
兼容 MySQL 和 PostgreSQL

v5.1 简化：
- ✅ 保留 BaseModel - 模型基类
- ✅ 保留 UserProfile - 用户配置（被UserPreferenceService使用）
- ❌ 删除 Session - 未使用
- ❌ 删除 ConversationHistory - 未使用
- ❌ 删除 AgentDecision - 未使用
- ❌ 删除 ToolExecutionFeedback - 未使用
- ❌ 删除 VectorMemory - 未使用
- ❌ 删除 SharedWorkspaceMemory - 未使用
"""
from .base import Base, BaseModel
from .user_profile import UserProfile

__all__ = [
    "Base",
    "BaseModel",
    "UserProfile",
]
