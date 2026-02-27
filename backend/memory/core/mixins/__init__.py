"""
Memory Agent Mixins

将 MemoryAwareAgent 的功能按职责拆分为多个 Mixin 类：
- UserPreferenceMixin: 用户偏好管理
"""

from .user_preference_mixin import UserPreferenceMixin

__all__ = [
    "UserPreferenceMixin",
]
