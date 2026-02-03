"""
Infrastructure Events Module

Provides event sourcing pattern for state management.
Supports event replay, rollback, and audit trails.
"""

from .event_store import (
    EventType,
    Event,
    EventStore,
    InMemoryEventStore,
    EventSourcedState,
    get_event_store,
    reset_event_store
)

__all__ = [
    "EventType",
    "Event",
    "EventStore",
    "InMemoryEventStore",
    "EventSourcedState",
    "get_event_store",
    "reset_event_store",
]
