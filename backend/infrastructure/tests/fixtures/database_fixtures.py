"""
数据库测试 Fixtures
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
def mock_engine():
    """Mock 数据库引擎"""
    engine = MagicMock()
    engine.connect = AsyncMock()
    engine.dispose = AsyncMock()
    engine.pool = MagicMock()
    engine.pool.size = lambda: 10
    engine.pool.checkedout = lambda: 2
    return engine

@pytest.fixture
def mock_session_factory(mock_postgres_session):
    """Mock 会话工厂"""
    factory = MagicMock()
    factory.__call__ = MagicMock(return_value=mock_postgres_session)
    return factory

@pytest.fixture
async def mock_db_manager():
    """Mock 数据库管理器"""
    with patch('infrastructure.database.connection_manager.create_async_engine') as mock_create_engine, \
         patch('infrastructure.database.connection_manager.async_sessionmaker') as mock_sessionmaker, \
         patch('infrastructure.database.connection_manager.ConnectionPool.from_url') as mock_redis_pool_create, \
         patch('infrastructure.database.connection_manager.Redis') as mock_redis_class:

        # Mock engine
        mock_engine = MagicMock()
        mock_engine.connect = AsyncMock()
        mock_engine.dispose = AsyncMock()
        mock_create_engine.return_value = mock_engine

        # Mock session factory
        mock_session_factory = MagicMock()
        mock_session_factory.__call__ = MagicMock()
        mock_sessionmaker.return_value = mock_session_factory

        # Mock Redis pool
        mock_redis_pool = MagicMock()
        mock_redis_pool_create.return_value = mock_redis_pool

        # Mock Redis client (for ping)
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock(return_value=True)
        mock_redis_class.__aenter__ = AsyncMock(return_value=mock_redis_instance)
        mock_redis_class.__aexit__ = AsyncMock()
        mock_redis_class.return_value = mock_redis_instance

        from infrastructure.database.connection_manager import DatabaseManager
        db_manager = DatabaseManager()

        yield db_manager, mock_engine, mock_session_factory

@pytest.fixture
def mock_pool_stats():
    """Mock 连接池统计信息"""
    stats = MagicMock()
    stats.pool_size = 10
    stats.checked_out_connections = 2
    stats.available_connections = 8
    stats.overflow = 0
    stats.checked_in = 100
    stats.checked_out = 98
    stats.errors = 0
    return stats

@pytest.fixture
def mock_redis_pool():
    """Mock Redis 连接池"""
    pool = AsyncMock()
    pool.get = AsyncMock()
    pool.release = AsyncMock()
    pool.size = lambda: 50
    pool.available_connections = lambda: 48
    return pool
