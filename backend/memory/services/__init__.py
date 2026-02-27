"""
Memory Services (简化版 v5.1)

提供记忆系统的业务逻辑层：
- UserPreferenceService: 用户偏好管理

v5.1 简化：
- ❌ 删除 BaseService - 只有一个子类，继承价值不大
- ✅ UserPreferenceService 独立存在，不再继承BaseService
"""

from .user_preference_service import UserPreferenceService

__all__ = [
    "UserPreferenceService",
]
