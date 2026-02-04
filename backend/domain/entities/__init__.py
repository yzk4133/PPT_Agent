"""
Domain Entities

Export all entity models from the entities folder.
"""

from .base import Entity, ValueObject, Serializable, AggregateRoot

# Import Task with fixed imports
try:
    from .task import Task, TaskStatus, TaskStage, StageProgress, TaskMetadata
    _task_imports = ["Task", "TaskStatus", "TaskStage", "StageProgress", "TaskMetadata"]
except ImportError:
    _task_imports = []

# State models
try:
    from .state import *
except ImportError:
    pass

__all__ = [
    # Base classes
    "Entity",
    "ValueObject",
    "Serializable",
    "AggregateRoot",
]

# Add task imports if available
if _task_imports:
    __all__.extend(_task_imports)
