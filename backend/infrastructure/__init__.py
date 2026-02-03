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

from .config.common_config import (
    AppConfig,
    AgentConfig,
    DatabaseConfig,
    FeatureFlags,
    ModelProvider,
    Environment,
    get_config,
)

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

from .utils.context_compressor import ContextCompressor

# Tool manager has AgentTool import issue, comment out for now
# from .tools.tool_manager import UnifiedToolManager, get_tool_manager
UnifiedToolManager = None
get_tool_manager = None

from .mcp.mcp_loader import (
    load_mcp_config_from_file,
    load_mcp_tools,
    load_mcp_tools_from_config,
    MCPManager,
    get_mcp_manager
)

from .cache import (
    AgentCache,
    CacheEntry,
    CacheStats,
    get_agent_cache,
    reset_agent_cache,
    cached
)

from .tracing import (
    AgentTracer,
    Span,
    Trace,
    get_tracer,
    reset_tracer,
    trace_span
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
    "ContextCompressor",

    # Tools
    "UnifiedToolManager",
    "get_tool_manager",

    # MCP
    "load_mcp_config_from_file",
    "load_mcp_tools",
    "load_mcp_tools_from_config",
    "MCPManager",
    "get_mcp_manager",

    # Cache
    "AgentCache",
    "CacheEntry",
    "CacheStats",
    "get_agent_cache",
    "reset_agent_cache",
    "cached",

    # Tracing
    "AgentTracer",
    "Span",
    "Trace",
    "get_tracer",
    "reset_tracer",
    "trace_span",
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
