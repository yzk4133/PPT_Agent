"""
Skills 系统

提供可复用的工作流程 Skills

注意：
- Python Skills 现在通过 tool_registry.py 统一管理
- 所有 Skills（Python + MD）都注册到 SKILL 类别中
"""

from .base_skill import BaseSkill, CompositeSkill, SkillExecutionError
from .markdown_skill import MarkdownSkill, create_md_skill_tool

__all__ = [
    # 基类
    "BaseSkill",
    "CompositeSkill",
    "SkillExecutionError",

    # MD Skill
    "MarkdownSkill",
    "create_md_skill_tool",
]

# 导出具体的 Skill 类（可选）
try:
    from .python_skills.research_workflow import (
        ResearchWorkflowSkill,
        ResearchKeywordSkill,
        ResearchSynthesisSkill
    )
    __all__.extend([
        "ResearchWorkflowSkill",
        "ResearchKeywordSkill",
        "ResearchSynthesisSkill"
    ])
except ImportError:
    pass

try:
    from .python_skills.content_generation import (
        ContentGenerationSkill,
        ContentOptimizationSkill,
        ContentQualityCheckSkill
    )
    __all__.extend([
        "ContentGenerationSkill",
        "ContentOptimizationSkill",
        "ContentQualityCheckSkill"
    ])
except ImportError:
    pass

try:
    from .python_skills.content_quality_check import ContentQualityCheckSkill, QuickQualityCheckSkill
    from .python_skills.content_optimization import ContentOptimizationSkill, IterativeOptimizationSkill
    __all__.extend([
        "ContentQualityCheckSkill",
        "QuickQualityCheckSkill",
        "ContentOptimizationSkill",
        "IterativeOptimizationSkill"
    ])
except ImportError:
    pass

try:
    from .python_skills.framework_design import (
        FrameworkDesignSkill,
        TopicDecompositionSkill,
        SectionPlanningSkill
    )
    __all__.extend([
        "FrameworkDesignSkill",
        "TopicDecompositionSkill",
        "SectionPlanningSkill"
    ])
except ImportError:
    pass

try:
    from .python_skills.topic_decomposition import TopicDecompositionSkill
    from .python_skills.section_planning import SectionPlanningSkill, PageDistributionSkill
    __all__.extend([
        "TopicDecompositionSkill",
        "SectionPlanningSkill",
        "PageDistributionSkill"
    ])
except ImportError:
    pass

try:
    from .python_skills.layout_selection import LayoutSelectionSkill, LayoutRecommendationSkill
    __all__.extend([
        "LayoutSelectionSkill",
        "LayoutRecommendationSkill"
    ])
except ImportError:
    pass
