"""
Infrastructure Layer - 统一技术基础设施

此层提供技术基础设施和服务，包括：
- 配置管理（环境变量、Feature Flags）
- 检查点管理（任务状态持久化）
- 异常定义（API 异常基类）
- 中间件（错误处理、速率限制）

设计原则：
- 与业务逻辑无关的技术组件
- 提供可配置的技术能力
- 可替换的实现

便捷导入:
    # 配置
    from infrastructure import get_config, AppConfig

    # 中间件
    from infrastructure import setup_exception_handlers

    # 检查点
    from infrastructure import CheckpointManager, get_checkpoint_manager
"""

# Exceptions (这些不依赖其他模块，可以安全导入)
from .exceptions import (
    BaseAPIException,
    RateLimitExceededException,
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
        "get_llm_config": ("infrastructure.config.common_config", "get_llm_config"),
        "LLMConfig": ("infrastructure.config.common_config", "LLMConfig"),

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
    "RateLimitExceededException",

    # Config
    "get_config", "AppConfig", "ModelProvider", "Environment",
    "get_llm_config", "LLMConfig",

    # Middleware
    "setup_exception_handlers",

    # Checkpoint
    "CheckpointManager", "get_checkpoint_manager",
]
