"""
Memory System - Unified Entry Point (简化版 v5.0)
"""
import logging
from typing import Any, Dict, Optional

from .config import MemoryConfig, load_config_from_env, validate_config
from ..services import (
    UserPreferenceService,
)
from ..storage.database import DatabaseManager
from ..storage.redis_cache import RedisCache

logger = logging.getLogger(__name__)


class MemorySystem:
    """
    记忆系统统一管理类（简化版）

    提供记忆系统的统一入口，管理服务和资源

    v5.0 简化：
    - ❌ 删除 DecisionService - 过度设计，实际未使用
    - ❌ 删除 WorkspaceService - 功能与LangGraph State重复
    - ✅ 只保留 UserPreferenceService - 用户偏好管理
    """

    def __init__(self, config: Optional[MemoryConfig] = None):
        """
        初始化记忆系统

        Args:
            config: 记忆系统配置（None则使用默认配置）
        """
        self.config = config or load_config_from_env()

        # 验证配置
        if not validate_config(self.config):
            raise ValueError("Invalid memory system configuration")

        # 数据库和缓存
        self._db: Optional[DatabaseManager] = None
        self._cache: Optional[RedisCache] = None

        # 服务实例（延迟初始化）
        self._user_preference_service: Optional[UserPreferenceService] = None

        # 初始化状态
        self._initialized = False

        logger.info(
            f"[MemorySystem] Created with config: "
            f"db={self.config.database_url[:20]}..., "
            f"cache={self.config.enable_cache}"
        )

    async def initialize(self) -> bool:
        """
        初始化记忆系统

        建立数据库连接、初始化缓存、创建服务实例

        Returns:
            是否成功
        """
        if self._initialized:
            logger.warning("[MemorySystem] Already initialized")
            return True

        try:
            # 初始化数据库
            self._db = DatabaseManager()
            if not self._db.health_check():
                logger.warning("[MemorySystem] Database health check failed")

            # 初始化缓存
            if self.config.enable_cache:
                self._cache = RedisCache()
                if not self._cache.is_available():
                    logger.warning("[MemorySystem] Redis cache unavailable")
                    self._cache = None

            # 初始化用户偏好服务
            if self.config.enable_user_preferences:
                self._user_preference_service = UserPreferenceService(
                    db_session=self._db.SessionLocal(),
                    cache_client=self._cache,
                    enable_cache=self.config.enable_cache
                )
                logger.info("[MemorySystem] UserPreferenceService initialized")

            self._initialized = True
            logger.info("[MemorySystem] Initialized successfully")
            return True

        except Exception as e:
            logger.error(f"[MemorySystem] Initialization failed: {e}")
            return False

    async def shutdown(self) -> None:
        """
        关闭记忆系统

        清理资源、关闭连接
        """
        if not self._initialized:
            return

        try:
            # 关闭服务
            if self._user_preference_service:
                # UserPreferenceService没有shutdown方法，直接置空
                self._user_preference_service = None

            # 清空实例
            self._db = None
            self._cache = None

            self._initialized = False
            logger.info("[MemorySystem] Shutdown complete")

        except Exception as e:
            logger.error(f"[MemorySystem] Shutdown error: {e}")

    # === 服务访问 ===

    @property
    def user_preference_service(self) -> Optional[UserPreferenceService]:
        """获取用户偏好服务"""
        return self._user_preference_service

    @property
    def database(self) -> Optional[DatabaseManager]:
        """获取数据库管理器"""
        return self._db

    @property
    def cache(self) -> Optional[RedisCache]:
        """获取缓存客户端"""
        return self._cache

    # === 健康检查 ===

    async def health_check(self) -> Dict[str, bool]:
        """
        健康检查

        Returns:
            各组件健康状态
        """
        status = {
            "database": False,
            "cache": False,
            "user_preference_service": False,
        }

        # 数据库健康检查
        if self._db:
            status["database"] = self._db.health_check()

        # 缓存健康检查
        if self._cache:
            status["cache"] = self._cache.is_available()

        # 服务健康检查
        status["user_preference_service"] = self._user_preference_service is not None

        return status

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return {
            "initialized": self._initialized,
            "config": self.config.to_dict(),
            "services": {
                "user_preferences": self._user_preference_service is not None,
            },
            "storage": {
                "database": self._db is not None,
                "cache": self._cache is not None,
            }
        }


# 全局记忆系统实例
_global_memory_system: Optional[MemorySystem] = None


def get_global_memory_system() -> Optional[MemorySystem]:
    """
    获取全局记忆系统实例

    Returns:
        MemorySystem实例或None
    """
    return _global_memory_system


async def initialize_memory_system(
    config: Optional[MemoryConfig] = None
) -> Optional[MemorySystem]:
    """
    初始化全局记忆系统

    Args:
        config: 记忆系统配置（None则使用默认配置）

    Returns:
        MemorySystem实例或None（失败时）
    """
    global _global_memory_system

    if _global_memory_system is not None:
        logger.warning("[MemorySystem] Global system already initialized")
        return _global_memory_system

    system = MemorySystem(config)
    success = await system.initialize()

    if success:
        _global_memory_system = system
        return system
    else:
        return None


async def shutdown_memory_system() -> None:
    """
    关闭全局记忆系统
    """
    global _global_memory_system

    if _global_memory_system:
        await _global_memory_system.shutdown()
        _global_memory_system = None
