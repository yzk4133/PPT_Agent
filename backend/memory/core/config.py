"""
Memory System Configuration
"""
import os
import logging
from typing import Any, Dict, Optional

# Pydantic v2 compatibility
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, field_validator, model_validator
except ImportError:
    from pydantic import BaseSettings, Field, validator as field_validator, model_validator

logger = logging.getLogger(__name__)


class MemoryConfig(BaseSettings):
    """
    记忆系统配置

    管理记忆系统的所有配置参数
    """

    # === 数据库配置 ===
    database_url: str = Field(
        default="mysql+pymysql://root:postgres@localhost:3306/multiagent_ppt",
        description="数据库连接URL"
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis连接URL"
    )

    # === 性能配置 ===
    l1_cache_size: int = Field(default=1000, ge=1, le=100000, description="L1缓存最大条目数")
    l2_ttl_seconds: int = Field(default=3600, ge=1, description="L2缓存默认TTL（秒）")
    connection_pool_size: int = Field(default=10, ge=1, le=1000, description="数据库连接池大小")
    max_overflow: int = Field(default=20, ge=0, le=500, description="连接池最大溢出")

    # === 功能开关 ===
    enable_user_preferences: bool = Field(default=True, description="启用用户偏好")
    enable_decision_tracking: bool = Field(default=True, description="启用决策追踪")
    enable_workspace: bool = Field(default=True, description="启用工作空间")
    enable_vector_search: bool = Field(default=False, description="启用向量搜索")
    enable_cache: bool = Field(default=True, description="启用Redis缓存")

    # === TTL配置 ===
    session_ttl: int = Field(default=3600, ge=1, description="会话缓存TTL（秒）")
    user_pref_ttl: int = Field(default=86400, ge=1, description="用户偏好缓存TTL（秒）")
    vector_ttl: int = Field(default=7200, ge=1, description="向量检索结果缓存TTL（秒）")
    workspace_default_ttl: int = Field(default=3600, ge=1, description="工作空间数据默认TTL（秒）")

    # === 日志配置 ===
    log_level: str = Field(default="INFO", description="日志级别")
    log_memory_operations: bool = Field(default=True, description="记录记忆操作日志")
    log_sql: bool = Field(default=False, description="记录SQL语句")

    # === 向量配置 ===
    vector_dimension: int = Field(default=1536, ge=1, description="OpenAI text-embedding-3-small 维度")
    embedding_model: str = Field(default="text-embedding-3-small", description="默认嵌入模型")

    class Config:
        env_prefix = "MEMORY_"
        case_sensitive = False
        extra = "ignore"

    @model_validator(mode='after')
    def setup_logging(self):
        """设置日志级别（替代 __post_init__）"""
        if self.log_level:
            logging.getLogger("backend.memory").setLevel(self.log_level)
        return self

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（向后兼容）"""
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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryConfig":
        """从字典创建实例（向后兼容）"""
        return cls(**data)


def load_config_from_env() -> MemoryConfig:
    """
    从环境变量加载配置

    Returns:
        MemoryConfig实例
    """
    # Pydantic BaseSettings 会自动从环境变量加载
    config = MemoryConfig()
    logger.info("[MemoryConfig] Loaded configuration from environment")
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

    # 检查数值范围（Pydantic 已自动验证）
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
