"""
Services Module

业务服务层，负责业务编排
"""

from .presentation_service import (
    PresentationService,
    create_presentation_from_request
)
from .outline_service import (
    OutlineService,
    generate_outline_simple
)
from .task_service import (
    TaskService,
    get_task_service
)

__all__ = [
    "PresentationService",
    "create_presentation_from_request",
    "OutlineService",
    "generate_outline_simple",
    "TaskService",
    "get_task_service",
]
