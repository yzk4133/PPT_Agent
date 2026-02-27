"""
Storage Layer - Database and Cache Management

v5.1 简化：
- ✅ 保留 BaseModel, UserProfile - 实际使用
- ❌ 删除其他6个未使用的模型
"""

# Models
from .models import Base, BaseModel, UserProfile

# Database
from .database import DatabaseManager, get_db, get_db_session

# Cache
from .redis_cache import RedisCache

__all__ = [
    # Models
    "Base",
    "BaseModel",
    "UserProfile",
    # Database
    "DatabaseManager",
    "get_db",
    "get_db_session",
    # Cache
    "RedisCache",
]
