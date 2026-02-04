"""
Domain Configuration

Export domain configuration classes.
"""

from .task_config import TaskProgressWeights, TaskConfig, default_task_config

__all__ = [
    "TaskProgressWeights",
    "TaskConfig",
    "default_task_config",
]
