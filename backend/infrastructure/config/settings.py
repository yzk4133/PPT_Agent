"""
Infrastructure Configuration Module

统一配置管理
"""

from .common_config import (
    AppConfig,
    AgentConfig,
    DatabaseConfig,
    FeatureFlags,
    ModelProvider,
    Environment,
    get_config,
    get_agent_config,
)

__all__ = [
    "AppConfig",
    "AgentConfig",
    "DatabaseConfig",
    "FeatureFlags",
    "ModelProvider",
    "Environment",
    "get_config",
    "get_agent_config",
]


def get_model_config(provider: str, model: str) -> dict:
    """
    获取模型配置

    Args:
        provider: 提供商名称
        model: 模型名称

    Returns:
        模型配置字典
    """
    config = get_config()
    return {
        "provider": provider,
        "model": model,
        "api_key": config.get_api_key(ModelProvider(provider)),
        "temperature": 0.7,
        "max_tokens": 4096
    }


if __name__ == "__main__":
    # 测试配置加载
    config = get_config()
    print(f"Environment: {config.environment}")
    print(f"Use Flat Architecture: {config.features.use_flat_architecture}")

    # 测试Agent配置
    split_config = get_agent_config("split_topic")
    print(f"Split Topic Agent Model: {split_config.model}")
