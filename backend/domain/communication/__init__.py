"""
Domain Communication Models

Export agent communication models for type-safe agent interaction.
"""

from .agent_context import (
    AgentContext,
    Requirement as AgentRequirement,
    PPTFramework as AgentPPTFramework,
    ResearchResult as AgentResearchResult,
    SlideContent,
    ExecutionMode as AgentExecutionMode,
    AgentStage,
)
from .agent_result import (
    AgentResult,
    ResultStatus,
    ValidationResult,
    ProgressEvent,
)

__all__ = [
    # Agent Context
    "AgentContext",
    "AgentRequirement",
    "AgentPPTFramework",
    "AgentResearchResult",
    "SlideContent",
    "AgentExecutionMode",
    "AgentStage",
    # Agent Result
    "AgentResult",
    "ResultStatus",
    "ValidationResult",
    "ProgressEvent",
]
