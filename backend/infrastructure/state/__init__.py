"""
State Infrastructure Module

Provides event-sourced state management with domain models.
"""

from .event_sourced_state_manager import (
    AgentStateManager,
    get_state_manager,
    set_state_manager
)

__all__ = [
    "AgentStateManager",
    "get_state_manager",
    "set_state_manager",
]
