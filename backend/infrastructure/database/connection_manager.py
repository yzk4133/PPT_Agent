"""
Database Connection Manager

统一的数据库连接管理，提供：
- PostgreSQL 异步会话管理
- Redis 连接池管理
- 连接健康检查
- 优雅关闭
"""

import asyncio
import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime

import redis.asyncio as aioredis
from redis.asyncio import Redis, ConnectionPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from ..config.common_config import get_config, DatabaseConfig

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    统一数据库连接管理器

    管理 PostgreSQL 和 Redis 连接，提供连接池、健康检查和优雅关闭功能。
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        初始化数据库管理器

        Args:
            config: 数据库配置（None 则使用全局配置）
        """
        self.config = config or get_config().database
        self._postgres_engine: Optional[AsyncEngine] = None
        self._postgres_session_factory: Optional[async_sessionmaker] = None
        self._redis_pool: Optional[ConnectionPool] = None
        self._initialized = False

    async def initialize(self):
        """
        初始化数据库连接

        创建 PostgreSQL 引擎和 Redis 连接池
        """
        if self._initialized:
            logger.warning("DatabaseManager already initialized")
            return

        logger.info("Initializing DatabaseManager...")

        # 初始化 PostgreSQL
        await self._init_postgres()

        # 初始化 Redis
        await self._init_redis()

        self._initialized = True
        logger.info("DatabaseManager initialized successfully")

    async def _init_postgres(self):
        """初始化 PostgreSQL 连接"""
        try:
            # 构建异步连接 URL
            database_url = self.config.database_url.replace(
                "postgresql://", "postgresql+asyncpg://"
            )

            # 创建引擎（增强连接池配置）
            self._postgres_engine = create_async_engine(
                database_url,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_pre_ping=True,         # 连接健康检查
                pool_recycle=3600,          # 1小时回收连接
                echo=False,                 # 生产环境关闭 SQL 日志
                pool_timeout=30,            # 连接池超时
                pool_use_lifo=True,         # 使用LIFO减少连接数
                connect_args={
                    "connect_timeout": 10,
                    "command_timeout": 30,
                    "server_settings": {"jit": "off"},  # 禁用JIT提高连接速度
                },
            )

            # 创建会话工厂
            self._postgres_session_factory = async_sessionmaker(
                bind=self._postgres_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

            logger.info(
                f"PostgreSQL engine created: "
                f"pool_size={self.config.pool_size}, "
                f"max_overflow={self.config.max_overflow}, "
                f"total_max={self.config.pool_size + self.config.max_overflow}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            raise

    async def _init_redis(self):
        """初始化 Redis 连接池"""
        try:
            self._redis_pool = ConnectionPool.from_url(
                self.config.redis_url,
                max_connections=50,          # 最大连接数
                socket_keepalive=True,       # 启用TCP keepalive
                socket_keepalive_options={},
                decode_responses=True,
                socket_connect_timeout=5,    # 连接超时
                socket_timeout=5,            # 读写超时
                retry_on_timeout=True,       # 超时重试
                health_check_interval=30,    # 健康检查间隔（秒）
            )

            # 测试连接
            async with Redis(connection_pool=self._redis_pool) as redis:
                await redis.ping()

            logger.info(
                f"Redis pool created: {self.config.redis_url} "
                f"(max_connections=50)"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise

    def get_postgres_session(self) -> AsyncSession:
        """
        获取 PostgreSQL 会话

        Returns:
            AsyncSession 实例

        Raises:
            RuntimeError: 如果未初始化
        """
        if not self._initialized or not self._postgres_session_factory:
            raise RuntimeError(
                "DatabaseManager not initialized. Call initialize() first."
            )

        return self._postgres_session_factory()

    def get_redis_client(self) -> Redis:
        """
        获取 Redis 客户端

        Returns:
            Redis 实例

        Raises:
            RuntimeError: 如果未初始化
        """
        if not self._initialized or not self._redis_pool:
            raise RuntimeError(
                "DatabaseManager not initialized. Call initialize() first."
            )

        return Redis(connection_pool=self._redis_pool)

    @asynccontextmanager
    async def postgres_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        PostgreSQL 会话上下文管理器

        自动处理提交和回滚

        Example:
            >>> async with db_manager.postgres_session() as session:
            ...     result = await session.execute(query)
        """
        if not self._initialized or not self._postgres_session_factory:
            raise RuntimeError(
                "DatabaseManager not initialized. Call initialize() first."
            )

        async with self._postgres_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    @asynccontextmanager
    async def redis_client(self) -> AsyncGenerator[Redis, None]:
        """
        Redis 客户端上下文管理器

        自动释放连接

        Example:
            >>> async with db_manager.redis_client() as redis:
            ...     await redis.set("key", "value")
        """
        if not self._initialized or not self._redis_pool:
            raise RuntimeError(
                "DatabaseManager not initialized. Call initialize() first."
            )

        async with Redis(connection_pool=self._redis_pool) as redis:
            yield redis

    async def check_postgres_health(self) -> dict:
        """
        检查 PostgreSQL 健康状态

        Returns:
            健康状态字典
        """
        try:
            async with self.postgres_session() as session:
                result = await session.execute(text("SELECT 1"))
                result.scalar()

            return {
                "status": "healthy",
                "message": "PostgreSQL connection OK",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"PostgreSQL connection failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def check_redis_health(self) -> dict:
        """
        检查 Redis 健康状态

        Returns:
            健康状态字典
        """
        try:
            async with self.redis_client() as redis:
                await redis.ping()

            return {
                "status": "healthy",
                "message": "Redis connection OK",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Redis connection failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def check_health(self) -> dict:
        """
        检查所有数据库健康状态

        Returns:
            健康状态字典
        """
        postgres_health = await self.check_postgres_health()
        redis_health = await self.check_redis_health()

        overall_status = (
            "healthy"
            if postgres_health["status"] == "healthy"
            and redis_health["status"] == "healthy"
            else "degraded"
        )

        return {
            "status": overall_status,
            "postgres": postgres_health,
            "redis": redis_health,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def close_all(self):
        """
        关闭所有数据库连接

        优雅关闭，等待所有操作完成
        """
        if not self._initialized:
            return

        logger.info("Closing all database connections...")

        # 关闭 PostgreSQL
        if self._postgres_engine:
            try:
                await self._postgres_engine.dispose()
                logger.info("PostgreSQL engine closed")
            except Exception as e:
                logger.error(f"Error closing PostgreSQL: {e}")

        # 关闭 Redis
        if self._redis_pool:
            try:
                await self._redis_pool.aclose()
                logger.info("Redis pool closed")
            except Exception as e:
                logger.error(f"Error closing Redis: {e}")

        self._initialized = False
        logger.info("All database connections closed")

    @property
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._initialized

    @property
    def postgres_engine(self) -> Optional[AsyncEngine]:
        """获取 PostgreSQL 引擎"""
        return self._postgres_engine

    @property
    def redis_pool(self) -> Optional[ConnectionPool]:
        """获取 Redis 连接池"""
        return self._redis_pool

    async def get_pool_stats(self) -> dict:
        """
        获取连接池统计信息

        Returns:
            连接池统计字典
        """
        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "postgres": {},
            "redis": {},
        }

        # PostgreSQL 连接池统计
        if self._postgres_engine:
            pool = self._postgres_engine.pool
            stats["postgres"] = {
                "pool_size": self.config.pool_size,
                "max_overflow": self.config.max_overflow,
                "total_max": self.config.pool_size + self.config.max_overflow,
                "current_connections": pool.size() if hasattr(pool, "size") else "N/A",
                "checked_out": pool.checkedout() if hasattr(pool, "checkedout") else "N/A",
                "overflow": pool.overflow() if hasattr(pool, "overflow") else "N/A",
            }

        # Redis 连接池统计
        if self._redis_pool:
            stats["redis"] = {
                "max_connections": self._redis_pool.max_connections,
                "available_connections": self._redis_pool.connection_kwargs.get("max_connections", "N/A"),
                "created_connections": getattr(self._redis_pool, "created_connections", "N/A"),
            }

        return stats

# 全局单例
_global_db_manager: Optional[DatabaseManager] = None

def get_db_manager() -> DatabaseManager:
    """
    获取全局数据库管理器实例

    Returns:
        DatabaseManager 实例
    """
    global _global_db_manager
    if _global_db_manager is None:
        _global_db_manager = DatabaseManager()
    return _global_db_manager

async def init_database():
    """
    初始化全局数据库管理器

    便捷函数，用于应用启动时初始化数据库
    """
    db_manager = get_db_manager()
    await db_manager.initialize()

async def close_database():
    """
    关闭全局数据库管理器

    便捷函数，用于应用关闭时清理数据库连接
    """
    db_manager = get_db_manager()
    await db_manager.close_all()

# 便捷函数
async def get_postgres_session() -> AsyncSession:
    """
    获取 PostgreSQL 会话（便捷函数）

    Returns:
        AsyncSession 实例
    """
    return get_db_manager().get_postgres_session()

async def get_redis_client() -> Redis:
    """
    获取 Redis 客户端（便捷函数）

    Returns:
        Redis 实例
    """
    return get_db_manager().get_redis_client()

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 测试数据库连接管理器
    async def test_db_manager():
        logger.info("Testing DatabaseManager")
        logger.info("=" * 60)

        # 初始化
        logger.info("1. Initializing...")
        db_manager = DatabaseManager()
        try:
            await db_manager.initialize()
            logger.info("   Initialized successfully")
        except Exception as e:
            logger.error(f"   Initialization failed: {e}")
            logger.info("   (This is expected if PostgreSQL/Redis are not running)")
            return

        # 健康检查
        logger.info("2. Health check...")
        health = await db_manager.check_health()
        logger.info(f"   Overall: {health['status']}")
        logger.info(f"   PostgreSQL: {health['postgres']['status']}")
        logger.info(f"   Redis: {health['redis']['status']}")

        # 连接池统计
        logger.info("2.5. Pool stats...")
        stats = await db_manager.get_pool_stats()
        logger.info(f"   PostgreSQL pool: {stats['postgres']}")
        logger.info(f"   Redis pool: {stats['redis']}")

        # 使用 PostgreSQL
        logger.info("3. Using PostgreSQL...")
        try:
            async with db_manager.postgres_session() as session:
                result = await session.execute(text("SELECT version()"))
                version = result.scalar()
                logger.info(f"   PostgreSQL version: {version[:50]}...")
        except Exception as e:
            logger.error(f"   Error: {e}")

        # 使用 Redis
        logger.info("4. Using Redis...")
        try:
            async with db_manager.redis_client() as redis:
                await redis.set("test_key", "test_value")
                value = await redis.get("test_key")
                logger.info(f"   Redis set/get: {value}")
                await redis.delete("test_key")
        except Exception as e:
            logger.error(f"   Error: {e}")

        # 关闭
        logger.info("5. Closing...")
        await db_manager.close_all()
        logger.info("   Closed successfully")

        logger.info("=" * 60)
        logger.info("Test completed!")

    asyncio.run(test_db_manager())
