"""
Domain Module

Domain-Driven Design structure with entities, value objects, services,
events, exceptions, and communication models.

This module provides backward compatibility by re-exporting from models/
while transitioning to the new DDD structure.
"""

# ============================================================================
# Backward Compatibility: Import everything from models
# ============================================================================
from .models import *
from .interfaces import *

# ============================================================================
# New DDD Structure (gradually rolling out)
# ============================================================================

# Base classes
from .entities.base import Entity, ValueObject, Serializable, AggregateRoot

# Domain services
from .services import (
    TaskProgressService,
    TaskValidationService,
    StageTransitionService,
    task_progress_service,
    task_validation_service,
    stage_transition_service,
)

# Domain configuration
from .config import (
    TaskProgressWeights,
    TaskConfig,
    default_task_config,
)

# Domain exceptions
from .exceptions import (
    DomainError,
    ValidationError,
    InvalidStateTransitionError,
    InvalidTaskError,
    TaskNotFoundError,
)

# Events
from .events.task_events import (
    TaskEvent,
    TaskEventType,
    create_task_created_event,
    create_requirement_parsed_event,
    create_framework_designed_event,
    create_checkpoint_saved_event,
    create_stage_started_event,
    create_stage_completed_event,
    create_stage_failed_event,
    create_task_failed_event,
    create_task_completed_event,
)

# Interfaces
from .interfaces.agent import (
    IAgent,
    IAgentConfig,
    IAgentContext,
    IAgentResult,
    ITopicSplitterAgent,
    IResearchAgent,
    IContentGeneratorAgent,
    ISlideWriterAgent,
    IQualityCheckerAgent,
    IAgentFactory,
)

__all__ = [
    # Base classes
    "Entity",
    "ValueObject",
    "Serializable",
    "AggregateRoot",
    # Services
    "TaskProgressService",
    "task_progress_service",
    "TaskValidationService",
    "task_validation_service",
    "StageTransitionService",
    "stage_transition_service",
    # Configuration
    "TaskProgressWeights",
    "TaskConfig",
    "default_task_config",
    # Exceptions
    "DomainError",
    "ValidationError",
    "InvalidStateTransitionError",
    "InvalidTaskError",
    "TaskNotFoundError",
    # Events
    "TaskEvent",
    "TaskEventType",
    "create_task_created_event",
    "create_requirement_parsed_event",
    "create_framework_designed_event",
    "create_checkpoint_saved_event",
    "create_stage_started_event",
    "create_stage_completed_event",
    "create_stage_failed_event",
    "create_task_failed_event",
    "create_task_completed_event",
    # Interfaces
    "IAgent",
    "IAgentConfig",
    "IAgentContext",
    "IAgentResult",
    "ITopicSplitterAgent",
    "IResearchAgent",
    "IContentGeneratorAgent",
    "ISlideWriterAgent",
    "IQualityCheckerAgent",
    "IAgentFactory",
]

# Also export everything from models for backward compatibility
__all__.extend([name for name in dir() if not name.startswith('_')])
