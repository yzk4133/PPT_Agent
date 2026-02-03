"""
Infrastructure LLM Module

统一LLM模型工厂，为Agent提供模型创建功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from infrastructure.llm.common_model_factory import (
    ModelFactory,
    create_model_with_fallback,
    get_model_factory,
)

__all__ = [
    "ModelFactory",
    "create_model_with_fallback",
    "get_model_factory",
    "create_agent_model",
]


# 便捷函数
def create_agent_model(agent_name: str, config=None):
    """
    为Agent创建模型实例

    Args:
        agent_name: Agent名称
        config: 可选的配置对象

    Returns:
        模型实例或模型名称
    """
    from infrastructure import get_agent_config

    agent_config = config or get_agent_config(agent_name)
    return create_model_with_fallback(
        model=agent_config.model,
        provider=agent_config.provider.value
    )


if __name__ == "__main__":
    # 测试模型创建
    model = create_agent_model("split_topic")
    print(f"Created model: {model}")
