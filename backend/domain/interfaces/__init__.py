"""
Core Interfaces Module

导出所有接口定义
"""

from .agent import (
    IAgent,
    ITopicSplitterAgent,
    IResearchAgent,
    IContentGeneratorAgent,
    ISlideWriterAgent,
    IQualityCheckerAgent,
    IAgentFactory,
    IAgentConfig,
    IAgentContext,
    IAgentResult
)
from .repository import (
    IRepository,
    IPresentationRepository,
    IUserPreferenceRepository,
    ICacheRepository,
    IVectorRepository,
    ISessionRepository
)

__all__ = [
    # Agent Interfaces
    "IAgent",
    "ITopicSplitterAgent",
    "IResearchAgent",
    "IContentGeneratorAgent",
    "ISlideWriterAgent",
    "IQualityCheckerAgent",
    "IAgentFactory",

    # Agent Data Classes
    "IAgentConfig",
    "IAgentContext",
    "IAgentResult",

    # Repository Interfaces
    "IRepository",
    "IPresentationRepository",
    "IUserPreferenceRepository",
    "ICacheRepository",
    "IVectorRepository",
    "ISessionRepository",
]
