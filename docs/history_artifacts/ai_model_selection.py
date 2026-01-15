"""AI模型选择策略模块

根据任务类型和成本考虑，智能选择最优的AI模型
"""

from enum import Enum
from typing import Optional, Dict, Any


class ModelProvider(Enum):
    """AI模型提供商枚举"""
    ANTHROPIC = "anthropic"  # Claude系列
    OPENAI = "openai"        # GPT系列
    MINIMIND = "minimind"    # 自研轻量模型


class TaskType(Enum):
    """任务类型枚举"""
    CONTENT_GENERATION = "content_generation"
    CODE_GENERATION = "code_generation"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    DESIGN_SUGGESTION = "design_suggestion"


class ModelSelector:
    """模型选择器 - 根据任务选择最优模型"""

    # 任务到模型的映射配置
    TASK_MODEL_MAP: Dict[TaskType, ModelProvider] = {
        TaskType.CONTENT_GENERATION: ModelProvider.ANTHROPIC,
        TaskType.CODE_GENERATION: ModelProvider.ANTHROPIC,
        TaskType.TRANSLATION: ModelProvider.MINIMIND,
        TaskType.SUMMARIZATION: ModelProvider.MINIMIND,
        TaskType.DESIGN_SUGGESTION: ModelProvider.ANTHROPIC,
    }

    @classmethod
    def select_for_task(cls, task_type: TaskType) -> ModelProvider:
        """根据任务类型选择最优模型

        Args:
            task_type: 任务类型

        Returns:
            推荐的模型提供商
        """
        return cls.TASK_MODEL_MAP.get(task_type, ModelProvider.ANTHROPIC)

    @classmethod
    def estimate_cost(cls, task_type: TaskType, tokens: int) -> float:
        """估算任务成本（美元）

        Args:
            task_type: 任务类型
            tokens: 预估token数量

        Returns:
            预估成本
        """
        model = cls.select_for_task(task_type)
        # 简化定价模型
        pricing = {
            ModelProvider.ANTHROPIC: 0.003,  # per 1k tokens
            ModelProvider.MINIMIND: 0.0001,
        }
        return (tokens / 1000) * pricing.get(model, 0.003)
