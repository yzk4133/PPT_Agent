"""
Database Connection Manager 测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
from sqlalchemy import text

from infrastructure.database.connection_manager import (
    DatabaseManager,
    get_db_manager,
    init_database,
    close_database,
    get_postgres_session,
    get_redis_client,
    _global_db_manager,
)
from infrastructure.config.common_config import DatabaseConfig

@pytest.mark.unit
@pytest.mark.asyncio
async def test_initialization(mock_db_manager):
    """测试数据库管理器初始化"""
    db_manager, mock_engine, mock_session_factory = mock_db_manager

    await db_manager.initialize()

    assert db_manager.is_initialized
    assert db_manager._postgres_engine is not None
    assert db_manager._postgres_session_factory is not None

@pytest.mark.unit
@pytest.mark.asyncio
async def test_double_initialization_protection():
    """测试重复初始化防护"""
    with patch('infrastructure.database.connection_manager.create_async_engine') as mock_engine, \
         patch('infrastructure.database.connection_manager.async_sessionmaker') as mock_sessionmaker, \
         patch('infrastructure.database.connection_manager.ConnectionPool.from_url') as mock_redis:

        mock_engine.return_value = MagicMock()
        mock_sessionmaker.return_value = MagicMock()
        mock_redis.return_value = MagicMock()

        db_manager = DatabaseManager()
        await db_manager.initialize()

        # 第二次初始化应该被忽略
        await db_manager.initialize()

        # 验证引擎和会话工厂只创建一次
        assert mock_engine.call_count == 1
        assert mock_sessionmaker.call_count == 1

@pytest.mark.unit
@pytest.mark.asyncio
async def test_postgres_session_creation():
    """测试 PostgreSQL 会话创建"""
    with patch('infrastructure.database.connection_manager.create_async_engine') as mock_create_engine, \
         patch('infrastructure.database.connection_manager.async_sessionmaker') as mock_sessionmaker, \
         patch('infrastructure.database.connection_manager.ConnectionPool.from_url'):

        # Mock engine
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        # Mock session factory
        mock_session = AsyncMock()
        mock_session_factory = MagicMock(return_value=mock_session)
        mock_sessionmaker.return_value = mock_session_factory

        db_manager = DatabaseManager()
        await db_manager.initialize()

        # 获取会话
        session = db_manager.get_postgres_session()
        assert session is not None
        mock_session_factory.assert_called_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_redis_client_creation():
    """测试 Redis 客户端创建"""
    with patch('infrastructure.database.connection_manager.create_async_engine'), \
         patch('infrastructure.database.connection_manager.async_sessionmaker'), \
         patch('infrastructure.database.connection_manager.ConnectionPool.from_url') as mock_redis_pool:

        mock_pool = MagicMock()
        mock_pool.aclose = AsyncMock()
        mock_redis_pool.return_value = mock_pool

        db_manager = DatabaseManager()
        await db_manager.initialize()

        # 获取 Redis 客户端
        redis_client = db_manager.get_redis_client()
        assert redis_client is not None

@pytest.mark.unit
@pytest.mark.asyncio
async def test_postgres_context_manager():
    """测试 PostgreSQL 上下文管理器"""
    with patch('infrastructure.database.connection_manager.create_async_engine'), \
         patch('infrastructure.database.connection_manager.async_sessionmaker') as mock_sessionmaker, \
         patch('infrastructure.database.connection_manager.ConnectionPool.from_url'):

        # Mock session
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        async def mock_session_factory():
            return mock_session

        mock_sessionmaker.return_value = mock_session_factory

        db_manager = DatabaseManager()
        await db_manager.initialize()

        # 使用上下文管理器
        async with db_manager.postgres_session() as session:
            assert session is not None

        # 验证提交被调用
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_session_rollback_on_error():
    """测试异常时回滚"""
    with patch('infrastructure.database.connection_manager.create_async_engine'), \
         patch('infrastructure.database.connection_manager.async_sessionmaker') as mock_sessionmaker, \
         patch('infrastructure.database.connection_manager.ConnectionPool.from_url'):

        # Mock session
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.execute.side_effect = Exception("DB Error")

        async def mock_session_factory():
            return mock_session

        mock_sessionmaker.return_value = mock_session_factory

        db_manager = DatabaseManager()
        await db_manager.initialize()

        # 使用上下文管理器并抛出异常
        with pytest.raises(Exception, match="DB Error"):
            async with db_manager.postgres_session() as session:
                await session.execute(text("SELECT 1"))

        # 验证回滚被调用，提交未被调用
        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_redis_context_manager():
    """测试 Redis 上下文管理器"""
    with patch('infrastructure.database.connection_manager.create_async_engine'), \
         patch('infrastructure.database.connection_manager.async_sessionmaker'), \
         patch('infrastructure.database.connection_manager.ConnectionPool.from_url') as mock_redis_pool:

        mock_pool = MagicMock()
        mock_pool.aclose = AsyncMock()
        mock_redis_pool.return_value = mock_pool

        db_manager = DatabaseManager()
        await db_manager.initialize()

        # 使用上下文管理器
        async with db_manager.redis_client() as redis:
            assert redis is not None

@pytest.mark.unit
@pytest.mark.asyncio
async def test_uninitialized_access():
    """测试未初始化时访问的异常"""
    db_manager = DatabaseManager()

    # 不初始化直接访问应该抛出异常
    with pytest.raises(RuntimeError, match="not initialized"):
        db_manager.get_postgres_session()

    with pytest.raises(RuntimeError, match="not initialized"):
        db_manager.get_redis_client()

    async def test_context_manager():
        with pytest.raises(RuntimeError, match="not initialized"):
            async with db_manager.postgres_session():
                pass

    await test_context_manager()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_postgres_health_check_success():
    """测试 PostgreSQL 健康检查成功"""
    with patch('infrastructure.database.connection_manager.create_async_engine'), \
         patch('infrastructure.database.connection_manager.async_sessionmaker') as mock_sessionmaker, \
         patch('infrastructure.database.connection_manager.ConnectionPool.from_url'):

        # Mock session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        async def mock_session_factory():
            return mock_session

        mock_sessionmaker.return_value = mock_session_factory

        db_manager = DatabaseManager()
        await db_manager.initialize()

        # 健康检查
        health = await db_manager.check_postgres_health()

        assert health["status"] == "healthy"
        assert "PostgreSQL connection OK" in health["message"]
        assert "timestamp" in health

@pytest.mark.integration
@pytest.mark.asyncio
async def test_postgres_health_check_failure():
    """测试 PostgreSQL 健康检查失败"""
    with patch('infrastructure.database.connection_manager.create_async_engine'), \
         patch('infrastructure.database.connection_manager.async_sessionmaker') as mock_sessionmaker, \
         patch('infrastructure.database.connection_manager.ConnectionPool.from_url'):

        # Mock session
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Connection failed"))
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        async def mock_session_factory():
            return mock_session

        mock_sessionmaker.return_value = mock_session_factory

        db_manager = DatabaseManager()
        await db_manager.initialize()

        # 健康检查
        health = await db_manager.check_postgres_health()

        assert health["status"] == "unhealthy"
        assert "PostgreSQL connection failed" in health["message"]

@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_health_check_success():
    """测试 Redis 健康检查成功"""
    with patch('infrastructure.database.connection_manager.create_async_engine'), \
         patch('infrastructure.database.connection_manager.async_sessionmaker'), \
         patch('infrastructure.database.connection_manager.ConnectionPool.from_url') as mock_redis_pool:

        # Mock Redis pool
        mock_pool = MagicMock()
        mock_pool.aclose = AsyncMock()
        mock_redis_pool.return_value = mock_pool

        # Mock Redis client with ping
        mock_redis = MagicMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.__aenter__ = AsyncMock(return_value=mock_redis)
        mock_redis.__aexit__ = AsyncMock()

        db_manager = DatabaseManager()
        await db_manager.initialize()

        with patch.object(db_manager, 'redis_client', return_value=mock_redis):
            health = await db_manager.check_redis_health()

            assert health["status"] == "healthy"
            assert "Redis connection OK" in health["message"]

@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_health_check_failure():
    """测试 Redis 健康检查失败"""
    with patch('infrastructure.database.connection_manager.create_async_engine'), \
         patch('infrastructure.database.connection_manager.async_sessionmaker'), \
         patch('infrastructure.database.connection_manager.ConnectionPool.from_url') as mock_redis_pool:

        mock_pool = MagicMock()
        mock_pool.aclose = AsyncMock()
        mock_redis_pool.return_value = mock_pool

        db_manager = DatabaseManager()
        await db_manager.initialize()

        # Mock Redis client with ping failure
        mock_redis = MagicMock()
        mock_redis.ping = AsyncMock(side_effect=Exception("Connection failed"))
        mock_redis.__aenter__ = AsyncMock(return_value=mock_redis)
        mock_redis.__aexit__ = AsyncMock()

        with patch.object(db_manager, 'redis_client', return_value=mock_redis):
            health = await db_manager.check_redis_health()

            assert health["status"] == "unhealthy"
            assert "Redis connection failed" in health["message"]

@pytest.mark.integration
@pytest.mark.asyncio
async def test_overall_health_check():
    """测试整体健康检查"""
    with patch('infrastructure.database.connection_manager.create_async_engine'), \
         patch('infrastructure.database.connection_manager.async_sessionmaker') as mock_sessionmaker, \
         patch('infrastructure.database.connection_manager.ConnectionPool.from_url'):

        # Mock session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        async def mock_session_factory():
            return mock_session

        mock_sessionmaker.return_value = mock_session_factory

        db_manager = DatabaseManager()
        await db_manager.initialize()

        # Mock Redis
        mock_redis = MagicMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.__aenter__ = AsyncMock(return_value=mock_redis)
        mock_redis.__aexit__ = AsyncMock()

        with patch.object(db_manager, 'redis_client', return_value=mock_redis):
            health = await db_manager.check_health()

            assert health["status"] == "healthy"
            assert health["postgres"]["status"] == "healthy"
            assert health["redis"]["status"] == "healthy"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_pool_stats():
    """测试连接池统计"""
    with patch('infrastructure.database.connection_manager.create_async_engine') as mock_create_engine, \
         patch('infrastructure.database.connection_manager.async_sessionmaker'), \
         patch('infrastructure.database.connection_manager.ConnectionPool.from_url') as mock_redis_pool:

        # Mock engine with pool
        mock_engine = MagicMock()
        mock_pool = MagicMock()
        mock_pool.size = MagicMock(return_value=5)
        mock_pool.checkedout = MagicMock(return_value=2)
        mock_pool.overflow = MagicMock(return_value=0)
        mock_engine.pool = mock_pool
        mock_create_engine.return_value = mock_engine

        # Mock Redis pool
        mock_redis_pool_instance = MagicMock()
        mock_redis_pool_instance.max_connections = 50
        mock_redis_pool_instance.connection_kwargs = {"max_connections": 50}
        mock_redis_pool.return_value = mock_redis_pool_instance

        db_manager = DatabaseManager()
        await db_manager.initialize()

        stats = await db_manager.get_pool_stats()

        assert "postgres" in stats
        assert "redis" in stats
        assert "timestamp" in stats
        assert stats["postgres"]["pool_size"] == db_manager.config.pool_size
        assert stats["redis"]["max_connections"] == 50

@pytest.mark.unit
@pytest.mark.asyncio
async def test_close_all_connections():
    """测试关闭所有连接"""
    with patch('infrastructure.database.connection_manager.create_async_engine') as mock_create_engine, \
         patch('infrastructure.database.connection_manager.async_sessionmaker'), \
         patch('infrastructure.database.connection_manager.ConnectionPool.from_url') as mock_redis_pool:

        # Mock engine
        mock_engine = MagicMock()
        mock_engine.dispose = AsyncMock()
        mock_create_engine.return_value = mock_engine

        # Mock Redis pool
        mock_redis_pool_instance = MagicMock()
        mock_redis_pool_instance.aclose = AsyncMock()
        mock_redis_pool.return_value = mock_redis_pool_instance

        db_manager = DatabaseManager()
        await db_manager.initialize()
        assert db_manager.is_initialized

        # 关闭所有连接
        await db_manager.close_all()

        assert not db_manager.is_initialized
        mock_engine.dispose.assert_called_once()
        mock_redis_pool_instance.aclose.assert_called_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_close_without_initialization():
    """测试未初始化时关闭不应该报错"""
    db_manager = DatabaseManager()

    # 未初始化时关闭应该正常返回
    await db_manager.close_all()

    assert not db_manager.is_initialized

@pytest.mark.unit
def test_global_db_manager_singleton():
    """测试全局数据库管理器单例"""
    # 重置全局变量
    import infrastructure.database.connection_manager as conn_module
    conn_module._global_db_manager = None

    # 获取两个实例应该是同一个
    manager1 = get_db_manager()
    manager2 = get_db_manager()

    assert manager1 is manager2

@pytest.mark.unit
@pytest.mark.asyncio
async def test_init_database_convenience_function():
    """测试 init_database 便捷函数"""
    import infrastructure.database.connection_manager as conn_module

    with patch('infrastructure.database.connection_manager.create_async_engine'), \
         patch('infrastructure.database.connection_manager.async_sessionmaker'), \
         patch('infrastructure.database.connection_manager.ConnectionPool.from_url'):

        # 重置全局变量
        conn_module._global_db_manager = None

        await init_database()

        assert conn_module._global_db_manager is not None
        assert conn_module._global_db_manager.is_initialized

@pytest.mark.unit
@pytest.mark.asyncio
async def test_close_database_convenience_function():
    """测试 close_database 便捷函数"""
    import infrastructure.database.connection_manager as conn_module

    with patch('infrastructure.database.connection_manager.create_async_engine'), \
         patch('infrastructure.database.connection_manager.async_sessionmaker'), \
         patch('infrastructure.database.connection_manager.ConnectionPool.from_url'):

        # 重置全局变量
        conn_module._global_db_manager = None

        await init_database()
        await close_database()

        assert conn_module._global_db_manager is not None
        assert not conn_module._global_db_manager.is_initialized

@pytest.mark.unit
def test_custom_config():
    """测试自定义配置"""
    custom_config = DatabaseConfig(
        database_url="postgresql://user:pass@localhost/custom_db",
        redis_url="redis://localhost:6380/2",
        pool_size=20,
        max_overflow=10,
    )

    db_manager = DatabaseManager(config=custom_config)

    assert db_manager.config == custom_config
    assert db_manager.config.database_url == custom_config.database_url
