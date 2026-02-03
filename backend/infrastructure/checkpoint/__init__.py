"""
Checkpoint Infrastructure Module

Provides checkpoint management for two-phase PPT generation workflow.
"""

from .checkpoint_manager import CheckpointManager, get_checkpoint_manager, set_checkpoint_manager
from .database_backend import (
    ICheckpointBackend,
    InMemoryCheckpointBackend,
    DatabaseCheckpointBackend,
    get_checkpoint_backend,
    set_checkpoint_backend,
    DatabaseConfig
)

__all__ = [
    # Manager
    "CheckpointManager",
    "get_checkpoint_manager",
    "set_checkpoint_manager",

    # Backend
    "ICheckpointBackend",
    "InMemoryCheckpointBackend",
    "DatabaseCheckpointBackend",
    "get_checkpoint_backend",
    "set_checkpoint_backend",
    "DatabaseConfig",
]
