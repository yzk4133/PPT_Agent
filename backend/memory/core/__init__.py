"""
Memory Core Module

提供记忆系统的核心配置和初始化功能。
"""

# 系统初始化相关
try:
    from .memory_system import (
        MemorySystem,
        get_global_memory_system,
        initialize_memory_system,
        shutdown_memory_system
    )
    from .config import (
        MemoryConfig,
        load_config_from_env,
        validate_config,
        get_global_config,
        set_global_config
    )

    _SYSTEM_AVAILABLE = True
except ImportError:
    _SYSTEM_AVAILABLE = False

__all__ = []

# 如果系统模块可用，导出系统相关的
if _SYSTEM_AVAILABLE:
    __all__.extend([
        # System
        "MemorySystem",
        "get_global_memory_system",
        "initialize_memory_system",
        "shutdown_memory_system",
        # Config
        "MemoryConfig",
        "load_config_from_env",
        "validate_config",
        "get_global_config",
        "set_global_config"
    ])
