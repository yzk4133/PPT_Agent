"""
Memory System Configuration
"""
import os
import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MemoryConfig:
    """
    记忆系统配置

    管理记忆系统的所有配置参数
    """

    # === 数据库配置 ===
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/multiagent_ppt"
        )
    )
    redis_url: str = field(
        default_factory=lambda: os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/0"
        )
    )

    # === 性能配置 ===
    l1_cache_size: int = 1000  # L1缓存最大条目数
    l2_ttl_seconds: int = 3600  # L2缓存默认TTL（秒）
    connection_pool_size: int = 10  # 数据库连接池大小
    max_overflow: int = 20  # 连接池最大溢出

    # === 功能开关 ===
    enable_user_preferences: bool = True  # 启用用户偏好
    enable_decision_tracking: bool = True  # 启用决策追踪
    enable_workspace: bool = True  # 启用工作空间
    enable_vector_search: bool = False  # 启用向量搜索
    enable_cache: bool = True  # 启用Redis缓存

    # === TTL配置 ===
    session_ttl: int = 3600  # 会话缓存TTL（秒）
    user_pref_ttl: int = 86400  # 用户偏好缓存TTL（秒）
    vector_ttl: int = 7200  # 向量检索结果缓存TTL（秒）
    workspace_default_ttl: int = 3600  # 工作空间数据默认TTL（秒）

    # === 日志配置 ===
    log_level: str = "INFO"
    log_memory_operations: bool = True  # 记录记忆操作日志
    log_sql: bool = False  # 记录SQL语句

    # === 向量配置 ===
    vector_dimension: int = 1536  # OpenAI text-embedding-3-small 维度
    embedding_model: str = "text-embedding-3-small"  # 默认嵌入模型

    def __post_init__(self):
        """初始化后处理"""
        # 设置日志级别
        if self.log_level:
            logging.getLogger("backend.memory").setLevel(self.log_level)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "database_url": self._mask_password(self.database_url),
            "redis_url": self._mask_password(self.redis_url),
            "l1_cache_size": self.l1_cache_size,
            "l2_ttl_seconds": self.l2_ttl_seconds,
            "connection_pool_size": self.connection_pool_size,
            "max_overflow": self.max_overflow,
            "enable_user_preferences": self.enable_user_preferences,
            "enable_decision_tracking": self.enable_decision_tracking,
            "enable_workspace": self.enable_workspace,
            "enable_vector_search": self.enable_vector_search,
            "enable_cache": self.enable_cache,
            "session_ttl": self.session_ttl,
            "user_pref_ttl": self.user_pref_ttl,
            "vector_ttl": self.vector_ttl,
            "workspace_default_ttl": self.workspace_default_ttl,
            "log_level": self.log_level,
            "log_memory_operations": self.log_memory_operations,
            "log_sql": self.log_sql,
            "vector_dimension": self.vector_dimension,
            "embedding_model": self.embedding_model,
        }

    @staticmethod
    def _mask_password(url: str) -> str:
        """隐藏URL中的密码"""
        if "@" in url and ":" in url:
            parts = url.split("@")
            if ":" in parts[0]:
                user_pass = parts[0].rsplit(":", 1)
                return f"{user_pass[0].split('//')[0]}//****:****@{parts[1]}"
        return url


def load_config_from_env() -> MemoryConfig:
    """
    从环境变量加载配置

    Returns:
        MemoryConfig实例
    """
    config = MemoryConfig()

    # 覆盖布尔值配置
    config.enable_user_preferences = os.getenv(
        "MEMORY_ENABLE_USER_PREFERENCES",
        str(config.enable_user_preferences)
    ).lower() == "true"

    config.enable_decision_tracking = os.getenv(
        "MEMORY_ENABLE_DECISION_TRACKING",
        str(config.enable_decision_tracking)
    ).lower() == "true"

    config.enable_workspace = os.getenv(
        "MEMORY_ENABLE_WORKSPACE",
        str(config.enable_workspace)
    ).lower() == "true"

    config.enable_vector_search = os.getenv(
        "MEMORY_ENABLE_VECTOR_SEARCH",
        str(config.enable_vector_search)
    ).lower() == "true"

    config.enable_cache = os.getenv(
        "MEMORY_ENABLE_CACHE",
        str(config.enable_cache)
    ).lower() == "true"

    # 覆盖数值配置
    if os.getenv("MEMORY_L1_CACHE_SIZE"):
        config.l1_cache_size = int(os.getenv("MEMORY_L1_CACHE_SIZE"))

    if os.getenv("MEMORY_L2_TTL_SECONDS"):
        config.l2_ttl_seconds = int(os.getenv("MEMORY_L2_TTL_SECONDS"))

    if os.getenv("MEMORY_CONNECTION_POOL_SIZE"):
        config.connection_pool_size = int(os.getenv("MEMORY_CONNECTION_POOL_SIZE"))

    # 覆盖日志配置
    if os.getenv("MEMORY_LOG_LEVEL"):
        config.log_level = os.getenv("MEMORY_LOG_LEVEL")

    config.log_memory_operations = os.getenv(
        "MEMORY_LOG_OPERATIONS",
        str(config.log_memory_operations)
    ).lower() == "true"

    config.log_sql = os.getenv(
        "MEMORY_LOG_SQL",
        str(config.log_sql)
    ).lower() == "true"

    logger.info(f"[MemoryConfig] Loaded configuration from environment")
    return config


def validate_config(config: MemoryConfig) -> bool:
    """
    验证配置有效性

    Args:
        config: MemoryConfig实例

    Returns:
        是否有效
    """
    is_valid = True

    # 检查必需的URL
    if not config.database_url:
        logger.error("[MemoryConfig] database_url is required")
        is_valid = False

    # 检查数值范围
    if config.l1_cache_size <= 0:
        logger.error("[MemoryConfig] l1_cache_size must be positive")
        is_valid = False

    if config.l2_ttl_seconds <= 0:
        logger.error("[MemoryConfig] l2_ttl_seconds must be positive")
        is_valid = False

    if config.connection_pool_size <= 0:
        logger.error("[MemoryConfig] connection_pool_size must be positive")
        is_valid = False

    # 检查向量配置
    if config.enable_vector_search and config.vector_dimension <= 0:
        logger.error("[MemoryConfig] vector_dimension must be positive when vector_search is enabled")
        is_valid = False

    if is_valid:
        logger.info("[MemoryConfig] Configuration is valid")
    else:
        logger.error("[MemoryConfig] Configuration validation failed")

    return is_valid


# 全局配置实例
_global_config: Optional[MemoryConfig] = None


def get_global_config() -> MemoryConfig:
    """
    获取全局配置实例

    Returns:
        MemoryConfig实例
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config_from_env()
    return _global_config


def set_global_config(config: MemoryConfig) -> None:
    """
    设置全局配置

    Args:
        config: MemoryConfig实例
    """
    global _global_config
    _global_config = config
    logger.info("[MemoryConfig] Global configuration updated")
