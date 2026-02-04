"""
Core Models Module

导出所有领域模型

DEPRECATED: This module is maintained for backward compatibility.
New code should import from the new DDD structure:
- domain.entities for entities (Task, Presentation, Checkpoint)
- domain.value_objects for value objects (Requirement, Framework, Research, Slide, Topic)
- domain.services for domain services
- domain.communication for agent communication models (AgentContext, AgentResult)
- domain.exceptions for domain exceptions
- domain.events for domain events
"""

from .topic import Topic, TopicList, create_topic_from_json
from .research import ResearchResult, ResearchResults, ResearchStatus, Reference
from .slide import Slide, SlideList, Image, SlideLayout, SlideComponentType
from .presentation import (
    Presentation,
    PresentationRequest,
    PresentationMetadata,
    PresentationStatus,
)
from .task import Task, TaskStatus, TaskStage, StageProgress, TaskMetadata
from .requirement import Requirement, RequirementAnalysis, SceneType, TemplateType
from .framework import (
    PPTFramework,
    PageDefinition,
    PageType,
    ContentType,
    FrameworkValidation,
)
from .execution_mode import ExecutionMode
from .checkpoint import Checkpoint, CheckpointSummary
from .page_state import (
    PageStatus,
    PageState,
    PageStateManager,
    PagePipelineConfig,
    PagePipelineResult,
)

# Agent 通信模型 - 从 communication/ 重新导出以保持向后兼容
from ..communication.agent_context import (
    AgentContext,
    Requirement as AgentRequirement,
    PPTFramework as AgentPPTFramework,
    ResearchResult as AgentResearchResult,
    SlideContent,
    ExecutionMode as AgentExecutionMode,
    AgentStage,
)
from ..communication.agent_result import (
    AgentResult,
    ResultStatus,
    ValidationResult,
    ProgressEvent,
)

__all__ = [
    # Topic
    "Topic",
    "TopicList",
    "create_topic_from_json",
    # Research
    "ResearchResult",
    "ResearchResults",
    "ResearchStatus",
    "Reference",
    # Slide
    "Slide",
    "SlideList",
    "Image",
    "SlideLayout",
    "SlideComponentType",
    # Presentation
    "Presentation",
    "PresentationRequest",
    "PresentationMetadata",
    "PresentationStatus",
    # Task
    "Task",
    "TaskStatus",
    "TaskStage",
    "StageProgress",
    "TaskMetadata",
    # Requirement
    "Requirement",
    "RequirementAnalysis",
    "SceneType",
    "TemplateType",
    # Framework
    "PPTFramework",
    "PageDefinition",
    "PageType",
    "ContentType",
    "FrameworkValidation",
    # Execution
    "ExecutionMode",
    "Checkpoint",
    "CheckpointSummary",
    # Page State
    "PageStatus",
    "PageState",
    "PageStateManager",
    "PagePipelineConfig",
    "PagePipelineResult",
    # Agent Context (新增)
    "AgentContext",
    "AgentRequirement",
    "AgentPPTFramework",
    "AgentResearchResult",
    "SlideContent",
    "AgentExecutionMode",
    "AgentStage",
    # Agent Result (新增)
    "AgentResult",
    "ResultStatus",
    "ValidationResult",
    "ProgressEvent",
]
