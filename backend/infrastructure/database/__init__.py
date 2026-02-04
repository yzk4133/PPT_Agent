"""
Infrastructure database module

Provides unified database connection management for:
- PostgreSQL (Async)
- Redis
- Connection health checks
- Graceful shutdown
"""

from .connection_manager import (
    DatabaseManager,
    get_db_manager,
    init_database,
    close_database,
    get_postgres_session,
    get_redis_client,
)

__all__ = [
    "DatabaseManager",
    "get_db_manager",
    "init_database",
    "close_database",
    "get_postgres_session",
    "get_redis_client",
]
