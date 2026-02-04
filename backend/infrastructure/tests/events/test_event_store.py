"""
Event Store 测试
"""

import pytest
from infrastructure.events.event_store import (
    EventType,
    Event,
    EventStore,
    InMemoryEventStore,
    EventSourcedState,
    get_event_store,
    reset_event_store,
)

@pytest.mark.unit
class TestEvent:
    """测试 Event 类"""

    def test_event_creation(self):
        """测试事件创建"""
        from datetime import datetime

        event = Event(
            event_id="evt_123",
            event_type=EventType.TASK_CREATED,
            aggregate_id="task_001",
            aggregate_type="task",
            version=1,
            data={"status": "created"},
        )

        assert event.event_id == "evt_123"
        assert event.event_type == EventType.TASK_CREATED
        assert event.aggregate_id == "task_001"
        assert event.version == 1

    def test_event_to_dict(self):
        """测试事件转换为字典"""
        from datetime import datetime

        event = Event(
            event_id="evt_123",
            event_type=EventType.TASK_CREATED,
            aggregate_id="task_001",
            aggregate_type="task",
            version=1,
            data={"status": "created"},
        )

        result = event.to_dict()

        assert result["event_id"] == "evt_123"
        assert result["event_type"] == "task_created"
        assert result["aggregate_id"] == "task_001"

    def test_event_from_dict(self):
        """测试从字典创建事件"""
        data = {
            "event_id": "evt_123",
            "event_type": "task_created",
            "aggregate_id": "task_001",
            "aggregate_type": "task",
            "version": 1,
            "data": {"status": "created"},
            "metadata": {},
            "timestamp": "2024-01-01T00:00:00",
        }

        event = Event.from_dict(data)

        assert event.event_id == "evt_123"
        assert event.event_type == EventType.TASK_CREATED

@pytest.mark.unit
class TestInMemoryEventStore:
    """测试 InMemoryEventStore 类"""

    def test_append_event(self):
        """测试添加事件"""
        store = InMemoryEventStore()

        event = Event(
            event_id="evt_001",
            event_type=EventType.TASK_CREATED,
            aggregate_id="task_001",
            aggregate_type="task",
            version=1,
            data={},
        )

        store.append(event)

        assert store.get_latest_version("task_001") == 1

    def test_append_event_version_mismatch(self):
        """测试版本不匹配"""
        store = InMemoryEventStore()

        event1 = Event(
            event_id="evt_001",
            event_type=EventType.TASK_CREATED,
            aggregate_id="task_001",
            aggregate_type="task",
            version=1,
            data={},
        )

        event2 = Event(
            event_id="evt_002",
            event_type=EventType.TASK_STARTED,
            aggregate_id="task_001",
            aggregate_type="task",
            version=3,  # 跳过版本 2
            data={},
        )

        store.append(event1)

        with pytest.raises(ValueError, match="Version mismatch"):
            store.append(event2)

    def test_get_events(self):
        """测试获取事件"""
        store = InMemoryEventStore()

        for i in range(3):
            event = Event(
                event_id=f"evt_{i:03d}",
                event_type=EventType.TASK_CREATED,
                aggregate_id="task_001",
                aggregate_type="task",
                version=i + 1,
                data={"index": i},
            )
            store.append(event)

        events = store.get_events("task_001")

        assert len(events) == 3

    def test_get_events_with_version_range(self):
        """测试按版本范围获取事件"""
        store = InMemoryEventStore()

        for i in range(5):
            event = Event(
                event_id=f"evt_{i:03d}",
                event_type=EventType.TASK_CREATED,
                aggregate_id="task_001",
                aggregate_type="task",
                version=i + 1,
                data={},
            )
            store.append(event)

        events = store.get_events("task_001", from_version=2, to_version=4)

        assert len(events) == 3
        assert events[0].version == 2

    def test_get_event(self):
        """测试获取单个事件"""
        store = InMemoryEventStore()

        event = Event(
            event_id="evt_001",
            event_type=EventType.TASK_CREATED,
            aggregate_id="task_001",
            aggregate_type="task",
            version=1,
            data={},
        )

        store.append(event)

        result = store.get_event("evt_001")

        assert result is not None
        assert result.event_id == "evt_001"

    def test_clear(self):
        """测试清空事件存储"""
        store = InMemoryEventStore()

        event = Event(
            event_id="evt_001",
            event_type=EventType.TASK_CREATED,
            aggregate_id="task_001",
            aggregate_type="task",
            version=1,
            data={},
        )

        store.append(event)
        store.clear()

        assert len(store.get_events("task_001")) == 0

@pytest.mark.unit
class TestEventSourcedState:
    """测试 EventSourcedState 类"""

    def test_initialization(self):
        """测试初始化"""
        state = EventSourcedState()

        assert state.aggregate_id is not None
        assert state.version == 0
        assert state.state == {}

    def test_raise_event(self):
        """测试触发事件"""
        state = EventSourcedState()

        event = state.raise_event(
            EventType.TASK_CREATED,
            data={"status": "created"},
        )

        assert event is not None
        assert event.event_type == EventType.TASK_CREATED
        assert state.version == 1

    def test_commit(self):
        """测试提交事件"""
        state = EventSourcedState()

        state.raise_event(EventType.TASK_CREATED, data={"status": "created"})
        state.commit()

        # 事件应该已提交到事件存储
        events = state.get_events()
        assert len(events) == 1

    def test_rollback(self):
        """测试回滚事件"""
        state = EventSourcedState()

        state.raise_event(EventType.TASK_CREATED, data={"status": "created"})
        state.raise_event(EventType.TASK_STARTED, data={"status": "started"})

        state.rollback()

        # 待处理事件应该被清除
        assert len(state._pending_events) == 0

    def test_replay(self):
        """测试重放事件"""
        store = InMemoryEventStore()
        state = EventSourcedState(event_store=store, aggregate_id="task_001")

        # 触发并提交一些事件
        state.raise_event(EventType.TASK_CREATED, data={"status": "created"})
        state.commit()

        # 创建新的状态实例并重放
        new_state = EventSourcedState(event_store=store, aggregate_id="task_001")
        new_state.replay()

        assert new_state.version == 1

    def test_register_handler(self):
        """测试注册事件处理器"""
        state = EventSourcedState()

        handler_called = []

        def handler(event):
            handler_called.append(event)

        state.register_handler(EventType.TASK_CREATED, handler)
        state.raise_event(EventType.TASK_CREATED, data={})

        # 处理器应该被调用（在 _apply_event 中）
        # 注意：这需要实际的事件处理逻辑
        assert EventType.TASK_CREATED in state._handlers

    def test_snapshot(self):
        """测试快照"""
        state = EventSourcedState()

        state.raise_event(EventType.TASK_CREATED, data={"status": "created"})
        state.raise_event(EventType.TASK_STARTED, data={"status": "started"})

        snapshot = state.snapshot()

        assert snapshot["aggregate_id"] == state.aggregate_id
        assert snapshot["version"] == 2
        assert "state" in snapshot

@pytest.mark.unit
class TestGlobalEventStore:
    """测试全局事件存储"""

    def test_get_event_store_singleton(self):
        """测试全局事件存储单例"""
        store1 = get_event_store()
        store2 = get_event_store()

        assert store1 is store2

    def test_reset_event_store(self):
        """测试重置全局事件存储"""
        store1 = get_event_store()

        # 添加一些事件
        event = Event(
            event_id="evt_001",
            event_type=EventType.TASK_CREATED,
            aggregate_id="task_001",
            aggregate_type="task",
            version=1,
            data={},
        )
        store1.append(event)

        # 重置
        store2 = reset_event_store()

        assert store2 is not store1
        assert len(store2.get_all_aggregates()) == 0
