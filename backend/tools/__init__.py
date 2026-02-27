"""
工具系统模块（LangChain Native 架构）

提供两层架构的工具系统：
- 领域层：工具的核心实现
- 应用层/接口层：工具注册表和对外服务

功能特性：
- LangChain 原生工具
- 性能监控装饰器
- 简化的工具注册表
- 按类别管理工具
"""

# 基础设施层
from .core.monitoring import (
    monitor_tool,
    get_tool_metrics,
    get_all_metrics,
    reset_metrics,
    log_metrics_summary,
)

from .core.exceptions import (
    ToolException,
)

# 应用层/接口层
from .application.tool_registry import (
    NativeToolRegistry,
    get_native_registry,
    reset_global_registry,
)

__all__ = [
    # ===== 基础设施层 =====
    # 监控
    "monitor_tool",
    "get_tool_metrics",
    "get_all_metrics",
    "reset_metrics",
    "log_metrics_summary",
    # 异常
    "ToolException",

    # ===== 应用层/接口层 =====
    "NativeToolRegistry",
    "get_native_registry",
    "reset_global_registry",
]

