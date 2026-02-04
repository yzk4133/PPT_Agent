"""
Infrastructure Layer - 统一技术基础设施

此层提供技术基础设施和服务，包括：
- 配置管理（环境变量、Feature Flags）
- LLM模型工厂（创建、降级、熔断）
- 工具管理器（注册、健康检查）
- 数据库连接、ORM配置
- 日志系统配置
- MCP工具加载器
- 外部服务集成

设计原则：
- 与业务逻辑无关的技术组件
- 提供可配置的技术能力
- 可替换的实现（如LLM提供商、数据库）

便捷导入:
    # 配置
    from infrastructure import get_config, AppConfig

    # LLM
    from infrastructure import ModelFactory, create_model_with_fallback

    # 数据库
    from infrastructure import DatabaseManager, get_db_manager

    # 日志
    from infrastructure import setup_logger, get_logger

    # 安全
    from infrastructure import PasswordHandler, JWTHandler

    # 中间件
    from infrastructure import setup_exception_handlers
"""

# Exceptions (这些不依赖其他模块，可以安全导入)
from .exceptions import (
    BaseAPIException,
    AuthenticationException,
    BusinessException,
    ValidationException,
)

# 延迟导入函数（避免循环导入）
def __getattr__(name: str):
    """延迟导入模块，避免循环依赖"""
    import importlib

    lazy_imports = {
        # Config
        "get_config": ("infrastructure.config.common_config", "get_config"),
        "AppConfig": ("infrastructure.config.common_config", "AppConfig"),
        "ModelProvider": ("infrastructure.config.common_config", "ModelProvider"),
        "Environment": ("infrastructure.config.common_config", "Environment"),

        # LLM
        "ModelFactory": ("infrastructure.llm.common_model_factory", "ModelFactory"),
        "create_model_with_fallback": ("infrastructure.llm.common_model_factory", "create_model_with_fallback"),
        "retry_with_exponential_backoff": ("infrastructure.llm.retry_decorator", "retry_with_exponential_backoff"),
        "JSONFallbackParser": ("infrastructure.llm.fallback", "JSONFallbackParser"),

        # Database
        "DatabaseManager": ("infrastructure.database.connection_manager", "DatabaseManager"),
        "get_db_manager": ("infrastructure.database.connection_manager", "get_db_manager"),

        # Logging
        "setup_logger": ("infrastructure.logger_config.logger_config", "setup_logger"),
        "get_logger": ("infrastructure.logger_config.logger_config", "get_logger"),

        # Security
        "PasswordHandler": ("infrastructure.security.password_handler", "PasswordHandler"),
        "JWTHandler": ("infrastructure.security.jwt_handler", "JWTHandler"),

        # Middleware
        "setup_exception_handlers": ("infrastructure.middleware.error_handler", "setup_exception_handlers"),

        # Checkpoint
        "CheckpointManager": ("infrastructure.checkpoint.checkpoint_manager", "CheckpointManager"),
        "get_checkpoint_manager": ("infrastructure.checkpoint.checkpoint_manager", "get_checkpoint_manager"),
    }

    if name in lazy_imports:
        module_path, attr_name = lazy_imports[name]
        module = importlib.import_module(module_path)
        return getattr(module, attr_name)

    raise AttributeError(f"module 'infrastructure' has no attribute '{name}'")

__all__ = [
    # Exceptions
    "BaseAPIException",
    "AuthenticationException",
    "BusinessException",
    "ValidationException",

    # Config
    "get_config", "AppConfig", "ModelProvider", "Environment",

    # LLM
    "ModelFactory", "create_model_with_fallback",
    "retry_with_exponential_backoff", "JSONFallbackParser",

    # Database
    "DatabaseManager", "get_db_manager",

    # Logging
    "setup_logger", "get_logger",

    # Security
    "PasswordHandler", "JWTHandler",

    # Middleware
    "setup_exception_handlers",

    # Checkpoint
    "CheckpointManager", "get_checkpoint_manager",
]

# 注意：以下导入已注释以避免循环导入问题
# 请直接从子模块导入：
#
# Config:
#   from infrastructure.config import AppConfig, get_config, ModelProvider, Environment
#
# LLM:
#   from infrastructure.llm.common_model_factory import ModelFactory, create_model_with_fallback
#   from infrastructure.llm.retry_decorator import retry_with_exponential_backoff
#
# Database:
#   from infrastructure.database import DatabaseManager, get_db_manager
#
# Logging:
#   from infrastructure.logger_config import setup_logger, get_logger
#
# Health:
#   from infrastructure.health import HealthChecker, check_system_health
#
# Metrics:
#   from infrastructure.metrics import MetricsCollector, get_metrics_collector
#
# Cache:
#   from infrastructure.cache import AgentCache, get_agent_cache
#
# Events:
#   from infrastructure.events import EventStore, get_event_store
#
# Checkpoint:
#   from infrastructure.checkpoint import CheckpointManager, get_checkpoint_manager
#
# MCP:
#   from infrastructure.mcp.mcp_loader import MCPManager, load_mcp_tools
#
# Security:
#   from infrastructure.security import JWTHandler, PasswordHandler
#
# Middleware:
#   from infrastructure.middleware import get_current_user, RateLimiter
#
# DI:
#   from infrastructure.di import Container, create_container
