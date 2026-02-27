"""
模型模块 - 包含状态和领域模型
"""

from .state import (
    PPTGenerationState,
    InputState,
    RequirementState,
    FrameworkState,
    ResearchState,
    ContentState,
    OutputState,
)
from .framework import (
    PageType,
    ContentType,
    PageDefinition,
    PPTFramework,
)

__all__ = [
    # 状态模型
    "PPTGenerationState",
    "InputState",
    "RequirementState",
    "FrameworkState",
    "ResearchState",
    "ContentState",
    "OutputState",
    # 框架模型
    "PageType",
    "ContentType",
    "PageDefinition",
    "PPTFramework",
]
