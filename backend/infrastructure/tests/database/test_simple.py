"""Simple database test for debugging"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_db_manager_creation():
    """Test that DatabaseManager can be created"""
    # Mock everything at the module level
    with patch('infrastructure.database.connection_manager.create_async_engine') as mock_engine, \
         patch('infrastructure.database.connection_manager.async_sessionmaker') as mock_sessionmaker, \
         patch('infrastructure.database.connection_manager.ConnectionPool.from_url') as mock_redis, \
         patch('infrastructure.database.connection_manager.Redis') as mock_redis_class:

        # Setup mocks
        mock_engine.return_value = MagicMock()
        mock_sessionmaker.return_value = MagicMock()

        mock_redis_pool = MagicMock()
        mock_redis.return_value = mock_redis_pool

        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock(return_value=True)

        # Mock the async context manager
        async def mock_aenter():
            return mock_redis_instance
        async def mock_aexit(*args):
            pass

        mock_redis_class.return_value = mock_redis_instance
        mock_redis_class.__aenter__ = mock_aenter
        mock_redis_class.__aexit__ = mock_aexit

        # Import and create manager
        from infrastructure.database.connection_manager import DatabaseManager

        # Create a test config to avoid loading real config
        mock_config = MagicMock()
        mock_config.database_url = "postgresql+asyncpg://test:test@localhost/test"
        mock_config.redis_url = "redis://localhost:6379/1"
        mock_config.pool_size = 5
        mock_config.max_overflow = 10

        db_manager = DatabaseManager(config=mock_config)

        # Initialize
        await db_manager.initialize()

        assert db_manager.is_initialized
        print("Test passed!")
