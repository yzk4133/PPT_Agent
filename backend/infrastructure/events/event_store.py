"""
Event Sourcing for State Management

Provides event sourcing pattern for managing agent execution state.
Supports event replay, rollback, and audit trails.
"""

import json
import logging
import threading
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    """Event types for agent execution"""

    # Requirement events
    REQUIREMENT_PARSED = "requirement_parsed"
    REQUIREMENT_UPDATED = "requirement_updated"

    # Framework events
    FRAMEWORK_DESIGNED = "framework_designed"
    FRAMEWORK_UPDATED = "framework_updated"
    FRAMEWORK_PAGE_ADDED = "framework_page_added"
    FRAMEWORK_PAGE_REMOVED = "framework_page_removed"

    # Research events
    RESEARCH_STARTED = "research_started"
    RESEARCH_COMPLETED = "research_completed"
    RESEARCH_FAILED = "research_failed"

    # Content events
    CONTENT_GENERATED = "content_generated"
    CONTENT_UPDATED = "content_updated"

    # Rendering events
    RENDERING_STARTED = "rendering_started"
    RENDERING_COMPLETED = "rendering_completed"
    RENDERING_FAILED = "rendering_failed"

    # Task events
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_REVISION_REQUESTED = "task_revision_requested"

    # State events
    STATE_SNAPSHOT = "state_snapshot"
    STATE_RESTORED = "state_restored"

@dataclass
class Event:
    """
    Base event class.

    Attributes:
        event_id: Unique event identifier
        event_type: Type of event
        aggregate_id: ID of the aggregate (e.g., task_id)
        aggregate_type: Type of aggregate (e.g., "task", "presentation")
        version: Event version number
        data: Event data payload
        metadata: Additional metadata
        timestamp: Event creation time
        correlation_id: Optional correlation ID for related events
        causation_id: Optional causation ID (what caused this event)
    """
    event_id: str
    event_type: EventType
    aggregate_id: str
    aggregate_type: str
    version: int
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "version": self.version,
            "data": self.data,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create Event from dictionary"""
        return cls(
            event_id=data["event_id"],
            event_type=EventType(data["event_type"]),
            aggregate_id=data["aggregate_id"],
            aggregate_type=data["aggregate_type"],
            version=data["version"],
            data=data["data"],
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(),
            correlation_id=data.get("correlation_id"),
            causation_id=data.get("causation_id")
        )

class EventStore(ABC):
    """
    Abstract base class for event storage.

    Implementations can store events in memory, database, files, etc.
    """

    @abstractmethod
    def append(self, event: Event) -> None:
        """Append a new event"""
        pass

    @abstractmethod
    def get_events(
        self,
        aggregate_id: str,
        from_version: Optional[int] = None,
        to_version: Optional[int] = None
    ) -> List[Event]:
        """Get events for an aggregate"""
        pass

    @abstractmethod
    def get_event(self, event_id: str) -> Optional[Event]:
        """Get a specific event by ID"""
        pass

    @abstractmethod
    def get_latest_version(self, aggregate_id: str) -> int:
        """Get the latest version number for an aggregate"""
        pass

class InMemoryEventStore(EventStore):
    """
    In-memory event store implementation.

    Suitable for development and testing.
    For production, use a database-backed implementation.
    """

    def __init__(self):
        """Initialize the in-memory store"""
        self._events: Dict[str, List[Event]] = {}
        self._event_index: Dict[str, Event] = {}
        self._version_index: Dict[str, int] = {}
        self._lock = threading.RLock()

    def append(self, event: Event) -> None:
        """Append a new event"""
        with self._lock:
            # Initialize list if needed
            if event.aggregate_id not in self._events:
                self._events[event.aggregate_id] = []

            # Check version
            current_version = self._version_index.get(event.aggregate_id, 0)
            if event.version != current_version + 1:
                raise ValueError(
                    f"Version mismatch for {event.aggregate_id}: "
                    f"expected {current_version + 1}, got {event.version}"
                )

            # Store event
            self._events[event.aggregate_id].append(event)
            self._event_index[event.event_id] = event
            self._version_index[event.aggregate_id] = event.version

            logger.debug(
                f"Appended event {event.event_type} "
                f"to {event.aggregate_id} v{event.version}"
            )

    def get_events(
        self,
        aggregate_id: str,
        from_version: Optional[int] = None,
        to_version: Optional[int] = None
    ) -> List[Event]:
        """Get events for an aggregate"""
        with self._lock:
            events = self._events.get(aggregate_id, [])

            if from_version is not None:
                events = [e for e in events if e.version >= from_version]
            if to_version is not None:
                events = [e for e in events if e.version <= to_version]

            return events.copy()

    def get_event(self, event_id: str) -> Optional[Event]:
        """Get a specific event by ID"""
        with self._lock:
            return self._event_index.get(event_id)

    def get_latest_version(self, aggregate_id: str) -> int:
        """Get the latest version number for an aggregate"""
        with self._lock:
            return self._version_index.get(aggregate_id, 0)

    def get_all_aggregates(self) -> List[str]:
        """Get all aggregate IDs"""
        with self._lock:
            return list(self._events.keys())

    def clear(self) -> None:
        """Clear all events"""
        with self._lock:
            self._events.clear()
            self._event_index.clear()
            self._version_index.clear()

class EventSourcedState:
    """
    Event-sourced state manager.

    Manages state through events, supporting replay and rollback.
    """

    def __init__(
        self,
        event_store: Optional[EventStore] = None,
        aggregate_id: Optional[str] = None,
        aggregate_type: str = "state"
    ):
        """
        Initialize the event-sourced state.

        Args:
            event_store: Event store to use (creates InMemoryEventStore if None)
            aggregate_id: ID of this aggregate
            aggregate_type: Type of this aggregate
        """
        self._event_store = event_store or InMemoryEventStore()
        self._aggregate_id = aggregate_id or self._generate_id()
        self._aggregate_type = aggregate_type
        self._state: Dict[str, Any] = {}
        self._version = 0
        self._pending_events: List[Event] = []
        self._lock = threading.RLock()

        # Event handlers
        self._handlers: Dict[EventType, List[Callable]] = {}

    def _generate_id(self) -> str:
        """Generate a unique ID"""
        import uuid
        return f"{self._aggregate_type}_{uuid.uuid4().hex[:16]}"

    @property
    def aggregate_id(self) -> str:
        """Get the aggregate ID"""
        return self._aggregate_id

    @property
    def version(self) -> int:
        """Get the current version"""
        return self._version

    @property
    def state(self) -> Dict[str, Any]:
        """Get the current state"""
        return self._state.copy()

    def register_handler(
        self,
        event_type: EventType,
        handler: Callable[[Event], None]
    ) -> None:
        """
        Register an event handler.

        Args:
            event_type: Type of event to handle
            handler: Function to call when event occurs
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def raise_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> Event:
        """
        Raise a new event.

        Args:
            event_type: Type of event
            data: Event data
            metadata: Optional metadata
            correlation_id: Optional correlation ID
            causation_id: Optional causation ID

        Returns:
            The created event
        """
        import uuid

        self._version += 1
        event = Event(
            event_id=f"evt_{uuid.uuid4().hex[:16]}",
            event_type=event_type,
            aggregate_id=self._aggregate_id,
            aggregate_type=self._aggregate_type,
            version=self._version,
            data=data,
            metadata=metadata or {},
            correlation_id=correlation_id,
            causation_id=causation_id
        )

        # Apply event to state
        self._apply_event(event)

        # Store as pending
        with self._lock:
            self._pending_events.append(event)

        return event

    def commit(self) -> None:
        """
        Commit pending events to the event store.

        Should be called after raising events to persist them.
        """
        with self._lock:
            for event in self._pending_events:
                self._event_store.append(event)
            self._pending_events.clear()

    def rollback(self) -> None:
        """
        Rollback pending events.

        Discards any uncommitted events.
        """
        with self._lock:
            self._pending_events.clear()

    def _apply_event(self, event: Event) -> None:
        """
        Apply an event to the current state.

        Args:
            event: Event to apply
        """
        # Default behavior: merge data into state
        self._state.update(event.data.get("state_changes", {}))

        # Call registered handlers
        if event.event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")

    def replay(self, to_version: Optional[int] = None) -> None:
        """
        Replay events from the event store.

        Args:
            to_version: Replay up to this version (None for all)
        """
        events = self._event_store.get_events(
            self._aggregate_id,
            to_version=to_version
        )

        # Clear current state and version
        self._state.clear()
        self._version = 0

        # Replay events
        for event in events:
            self._version = event.version
            self._apply_event(event)

        logger.info(
            f"Replayed {len(events)} events "
            f"for {self._aggregate_id} to version {self._version}"
        )

    def get_events(
        self,
        from_version: Optional[int] = None,
        to_version: Optional[int] = None
    ) -> List[Event]:
        """
        Get events from the event store.

        Args:
            from_version: Start version
            to_version: End version

        Returns:
            List of events
        """
        return self._event_store.get_events(
            self._aggregate_id,
            from_version=from_version,
            to_version=to_version
        )

    def snapshot(self) -> Dict[str, Any]:
        """
        Create a snapshot of the current state.

        Returns:
            Snapshot dictionary
        """
        return {
            "aggregate_id": self._aggregate_id,
            "aggregate_type": self._aggregate_type,
            "version": self._version,
            "state": self._state.copy(),
            "timestamp": datetime.now().isoformat()
        }

    def restore_from_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """
        Restore state from a snapshot.

        Args:
            snapshot: Snapshot dictionary
        """
        if snapshot["aggregate_id"] != self._aggregate_id:
            raise ValueError("Snapshot does not match this aggregate")

        self._state = snapshot["state"].copy()
        self._version = snapshot["version"]

        # Replay any events after the snapshot
        self.replay(from_version=self._version + 1)

        logger.info(f"Restored {self._aggregate_id} from snapshot to version {self._version}")

# Global event store
_global_event_store: Optional[EventStore] = None
_store_lock = threading.Lock()

def get_event_store() -> EventStore:
    """Get the global event store instance"""
    global _global_event_store
    with _store_lock:
        if _global_event_store is None:
            _global_event_store = InMemoryEventStore()
        return _global_event_store

def reset_event_store() -> EventStore:
    """Reset the global event store with a new instance"""
    global _global_event_store
    with _store_lock:
        _global_event_store = InMemoryEventStore()
        return _global_event_store

if __name__ == "__main__":
    # Test event sourcing
    logging.basicConfig(level=logging.DEBUG)

    # Create event store and state
    store = InMemoryEventStore()
    state = EventSourcedState(
        event_store=store,
        aggregate_id="task_001",
        aggregate_type="task"
    )

    # Register handler
    def on_requirement_parsed(event: Event):
        print(f"Handler: Requirement parsed with data: {event.data}")

    state.register_handler(EventType.REQUIREMENT_PARSED, on_requirement_parsed)

    # Raise events
    print("=== Raising Events ===")
    state.raise_event(
        EventType.TASK_CREATED,
        data={"state_changes": {"status": "created", "raw_input": "Make a PPT about AI"}}
    )

    state.raise_event(
        EventType.REQUIREMENT_PARSED,
        data={
            "state_changes": {
                "ppt_topic": "AI Introduction",
                "page_num": 10,
                "template_type": "business_template"
            },
            "parsed_by": "RequirementParserAgent"
        }
    )

    state.raise_event(
        EventType.FRAMEWORK_DESIGNED,
        data={"state_changes": {"total_page": 10, "has_framework": True}}
    )

    # Commit events
    print("\n=== Committing Events ===")
    state.commit()

    # Check state
    print("\n=== Current State ===")
    print(json.dumps(state.state, indent=2, ensure_ascii=False))
    print(f"Version: {state.version}")

    # Create new state instance and replay
    print("\n=== Replaying Events ===")
    new_state = EventSourcedState(
        event_store=store,
        aggregate_id="task_001",
        aggregate_type="task"
    )
    new_state.replay()
    print(f"Replayed state: {json.dumps(new_state.state, indent=2, ensure_ascii=False)}")
    print(f"Replayed version: {new_state.version}")

    # Test snapshot
    print("\n=== Snapshot ===")
    snapshot = new_state.snapshot()
    print(json.dumps(snapshot, indent=2, ensure_ascii=False))

    # Test rollback
    print("\n=== Rollback Test ===")
    state.raise_event(
        EventType.CONTENT_GENERATED,
        data={"state_changes": {"has_content": True}}
    )
    print(f"Version before rollback: {state.version}")
    print(f"Pending events: {len(state._pending_events)}")

    state.rollback()
    print(f"Version after rollback: {state.version}")
    print(f"Pending events: {len(state._pending_events)}")
