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
    AgentConfig,
    AgentContext,
    AgentResult
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
    "AgentConfig",
    "AgentContext",
    "AgentResult",

    # Repository Interfaces
    "IRepository",
    "IPresentationRepository",
    "IUserPreferenceRepository",
    "ICacheRepository",
    "IVectorRepository",
    "ISessionRepository",
]
