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
"""

# Config
from .config.common_config import (
    AppConfig,
    AgentConfig,
    DatabaseConfig,
    FeatureFlags,
    ModelProvider,
    Environment,
    get_config,
)

# LLM
from .llm.common_model_factory import (
    create_model_with_fallback,
    create_model_with_fallback_simple,
    get_model_factory,
    ModelFactory,
    ModelType,
)

from .llm.retry_decorator import (
    retry_with_exponential_backoff,
    async_retry_with_fallback,
    RetryableError,
)

from .llm.fallback import (
    JSONFallbackParser,
    PartialSuccessHandler,
    FallbackChain,
)

# Database
from .database import (
    DatabaseManager,
    get_db_manager,
    init_database,
    close_database,
)

# Logging
from .logging import (
    setup_logger,
    get_logger,
    set_request_id,
    get_request_id,
    LoggerContext,
    log_function_call,
    get_app_logger,
    get_api_logger,
    get_agent_logger,
    get_infrastructure_logger,
)

# Health
from .health import (
    HealthStatus,
    HealthCheckResult,
    SystemHealthReport,
    HealthChecker,
    get_health_checker,
    setup_default_checks,
    check_system_health,
    check_component_health,
)

# Metrics
from .metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricsCollector,
    get_metrics_collector,
    count_exceptions,
    measure_time,
)

# Cache
from .cache import (
    AgentCache,
    CacheEntry,
    CacheStats,
    get_agent_cache,
    reset_agent_cache,
    cached,
)

# Events
from .events import (
    EventType,
    Event,
    EventStore,
    InMemoryEventStore,
    EventSourcedState,
    get_event_store,
    reset_event_store,
)

# Checkpoint
from .checkpoint import (
    CheckpointManager,
    get_checkpoint_manager,
    set_checkpoint_manager,
    ICheckpointBackend,
    InMemoryCheckpointBackend,
    DatabaseCheckpointBackend,
    PostgresCheckpointBackend,
)

# MCP
from .mcp.mcp_loader import (
    load_mcp_config_from_file,
    load_mcp_tools,
    load_mcp_tools_from_config,
    MCPManager,
    get_mcp_manager
)

# Security
from .security import (
    JWTHandler,
    PasswordHandler,
)

# Middleware
from .middleware import (
    get_current_user,
    RateLimiter,
    setup_exception_handlers,
)

# Exceptions
from .exceptions import (
    BaseAPIException,
    AuthenticationException,
    BusinessException,
    ValidationException,
    DatabaseException,
    CacheException,
)

# Dependency Injection
from .di import (
    Container,
    create_container,
    get_global_container as get_container,
)

__all__ = [
    # Config
    "AppConfig",
    "AgentConfig",
    "DatabaseConfig",
    "FeatureFlags",
    "ModelProvider",
    "Environment",
    "get_config",
    "get_agent_config",  # Convenience function defined below

    # LLM
    "create_model_with_fallback",
    "create_model_with_fallback_simple",
    "get_model_factory",
    "ModelFactory",
    "ModelType",

    # LLM Utils
    "retry_with_exponential_backoff",
    "async_retry_with_fallback",
    "RetryableError",
    "JSONFallbackParser",
    "PartialSuccessHandler",
    "FallbackChain",

    # Database
    "DatabaseManager",
    "get_db_manager",
    "init_database",
    "close_database",

    # Logging
    "setup_logger",
    "get_logger",
    "set_request_id",
    "get_request_id",
    "LoggerContext",
    "log_function_call",
    "get_app_logger",
    "get_api_logger",
    "get_agent_logger",
    "get_infrastructure_logger",

    # Health
    "HealthStatus",
    "HealthCheckResult",
    "SystemHealthReport",
    "HealthChecker",
    "get_health_checker",
    "setup_default_checks",
    "check_system_health",
    "check_component_health",

    # Metrics
    "Counter",
    "Gauge",
    "Histogram",
    "MetricsCollector",
    "get_metrics_collector",
    "count_exceptions",
    "measure_time",

    # Cache
    "AgentCache",
    "CacheEntry",
    "CacheStats",
    "get_agent_cache",
    "reset_agent_cache",
    "cached",

    # Events
    "EventType",
    "Event",
    "EventStore",
    "InMemoryEventStore",
    "EventSourcedState",
    "get_event_store",
    "reset_event_store",

    # Checkpoint
    "CheckpointManager",
    "get_checkpoint_manager",
    "set_checkpoint_manager",
    "ICheckpointBackend",
    "InMemoryCheckpointBackend",
    "DatabaseCheckpointBackend",
    "PostgresCheckpointBackend",

    # MCP
    "load_mcp_config_from_file",
    "load_mcp_tools",
    "load_mcp_tools_from_config",
    "MCPManager",
    "get_mcp_manager",

    # Security
    "JWTHandler",
    "PasswordHandler",

    # Middleware
    "get_current_user",
    "RateLimiter",
    "setup_exception_handlers",

    # Exceptions
    "BaseAPIException",
    "AuthenticationException",
    "BusinessException",
    "ValidationException",
    "DatabaseException",
    "CacheException",

    # Dependency Injection
    "Container",
    "create_container",
    "get_container",
]


# Convenience function for getting agent config
def get_agent_config(agent_name: str) -> AgentConfig:
    """
    Get agent configuration by name

    Args:
        agent_name: Name of the agent (split_topic, research, ppt_writer, etc.)

    Returns:
        AgentConfig instance for the specified agent
    """
    config = get_config()
    return config.get_agent_config(agent_name)
