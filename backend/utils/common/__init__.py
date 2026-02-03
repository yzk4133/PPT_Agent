"""
⚠️ DEPRECATED: utils.common 已迁移到 infrastructure

此模块仅为向后兼容保留，将在未来版本移除。

迁移路径对照表：
- from utils.common import get_config → from infrastructure.config import get_config
- from utils.common.model_factory import ... → from infrastructure.llm import ...
- from utils.common.tool_manager import ... → from infrastructure.tools import ...
- from utils.common.context_compressor import ... → from infrastructure.utils import ...
- from utils.common.retry_decorator import ... → from infrastructure.llm import ...
- from utils.common.fallback import ... → from infrastructure.llm.fallback import ...

请更新您的导入路径。
"""

import warnings
import sys

# 发出弃用警告
warnings.warn(
    "utils.common is deprecated. Use 'infrastructure' module instead. "
    "See module docstring for migration paths.",
    DeprecationWarning,
    stacklevel=2
)

__version__ = "2.0.0-deprecated"

# 重新导出以确保向后兼容
# 从 infrastructure 层导入并重新导出
from infrastructure.config.common_config import AppConfig, AgentConfig, get_config
from infrastructure.llm.common_model_factory import (
    create_model_with_fallback,
    create_model_with_fallback_simple,
    ModelType,
)
from infrastructure.utils.context_compressor import ContextCompressor
from infrastructure.llm.retry_decorator import (
    retry_with_exponential_backoff,
    async_retry_with_fallback,
    RetryableError,
)
from infrastructure.llm.fallback import JSONFallbackParser, PartialSuccessHandler, FallbackChain

# tool_manager 暂时注释，存在 AgentTool 导入问题
# from infrastructure.tools.tool_manager import UnifiedToolManager, get_tool_manager
UnifiedToolManager = None
get_tool_manager = None

__all__ = [
    "AppConfig",
    "AgentConfig",
    "get_config",
    "create_model_with_fallback",
    "create_model_with_fallback_simple",
    "ModelType",
    # "UnifiedToolManager",  # Commented due to AgentTool import issues
    # "get_tool_manager",  # Commented due to AgentTool import issues
    "ContextCompressor",
    "retry_with_exponential_backoff",
    "async_retry_with_fallback",
    "RetryableError",
    "JSONFallbackParser",
    "PartialSuccessHandler",
    "FallbackChain",
]
