"""
Domain Events Module

Provides event types for task lifecycle and state transitions.
"""

from .task_events import (
    TaskEventType,
    TaskEvent,
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

__all__ = [
    # Event Types
    "TaskEventType",

    # Event Class
    "TaskEvent",

    # Factory Functions
    "create_task_created_event",
    "create_requirement_parsed_event",
    "create_framework_designed_event",
    "create_checkpoint_saved_event",
    "create_stage_started_event",
    "create_stage_completed_event",
    "create_stage_failed_event",
    "create_task_failed_event",
    "create_task_completed_event",
]
