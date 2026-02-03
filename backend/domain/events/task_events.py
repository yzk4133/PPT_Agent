"""
Task Events

Event types for task lifecycle and state transitions.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


class TaskEventType(str, Enum):
    """任务事件类型"""

    # Task lifecycle events
    TASK_CREATED = "TASK_CREATED"
    TASK_STARTED = "TASK_STARTED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"

    # Stage events
    REQUIREMENT_PARSED = "REQUIREMENT_PARSED"
    FRAMEWORK_DESIGNED = "FRAMEWORK_DESIGNED"
    RESEARCH_COMPLETED = "RESEARCH_COMPLETED"
    CONTENT_GENERATED = "CONTENT_GENERATED"
    PPT_RENDERED = "PPT_RENDERED"

    # Checkpoint events
    CHECKPOINT_SAVED = "CHECKPOINT_SAVED"
    CHECKPOINT_LOADED = "CHECKPOINT_LOADED"
    CHECKPOINT_UPDATED = "CHECKPOINT_UPDATED"

    # Revision events
    REQUIREMENT_MODIFIED = "REQUIREMENT_MODIFIED"  # 用户修改大纲
    FRAMEWORK_MODIFIED = "FRAMEWORK_MODIFIED"


@dataclass
class TaskEvent:
    """
    任务事件

    表示任务执行过程中的一个事件。

    Attributes:
        event_type: 事件类型
        version: 版本号
        data: 事件数据
        timestamp: 事件时间戳
        correlation_id: 关联ID（用于关联多个事件）
        metadata: 附加元数据
    """

    event_type: TaskEventType
    version: int
    data: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_type": self.event_type.value,
            "version": self.version,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskEvent":
        """从字典创建"""
        event_type = TaskEventType(data["event_type"])
        timestamp = datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now()

        return cls(
            event_type=event_type,
            version=data.get("version", 1),
            data=data.get("data", {}),
            timestamp=timestamp,
            correlation_id=data.get("correlation_id"),
            metadata=data.get("metadata", {})
        )


# Event factory functions for creating common task events

def create_task_created_event(
    version: int,
    task_id: str,
    raw_input: str,
    user_id: str = "anonymous"
) -> TaskEvent:
    """创建任务创建事件"""
    return TaskEvent(
        event_type=TaskEventType.TASK_CREATED,
        version=version,
        data={
            "task_id": task_id,
            "raw_user_input": raw_input,
            "user_id": user_id,
            "state_changes": {
                "task_id": task_id,
                "status": "created",
                "raw_user_input": raw_input
            }
        },
        timestamp=datetime.now(),
        correlation_id=task_id
    )


def create_requirement_parsed_event(
    version: int,
    task_id: str,
    requirement: Dict[str, Any]
) -> TaskEvent:
    """创建需求解析完成事件"""
    return TaskEvent(
        event_type=TaskEventType.REQUIREMENT_PARSED,
        version=version,
        data={
            "task_id": task_id,
            "requirement": requirement,
            "state_changes": {
                "structured_requirements": requirement
            }
        },
        timestamp=datetime.now(),
        correlation_id=task_id
    )


def create_framework_designed_event(
    version: int,
    task_id: str,
    framework: Dict[str, Any]
) -> TaskEvent:
    """创建框架设计完成事件"""
    return TaskEvent(
        event_type=TaskEventType.FRAMEWORK_DESIGNED,
        version=version,
        data={
            "task_id": task_id,
            "framework": framework,
            "state_changes": {
                "ppt_framework": framework
            }
        },
        timestamp=datetime.now(),
        correlation_id=task_id
    )


def create_checkpoint_saved_event(
    version: int,
    task_id: str,
    phase: int,
    checkpoint_data: Dict[str, Any]
) -> TaskEvent:
    """创建checkpoint保存事件"""
    return TaskEvent(
        event_type=TaskEventType.CHECKPOINT_SAVED,
        version=version,
        data={
            "task_id": task_id,
            "phase": phase,
            "checkpoint_data": checkpoint_data
        },
        timestamp=datetime.now(),
        correlation_id=task_id
    )


if __name__ == "__main__":
    # 测试代码
    print("Testing Task Events")

    event1 = create_task_created_event(
        version=1,
        task_id="task_001",
        raw_input="做一份AI介绍PPT",
        user_id="user_001"
    )
    print(f"Event 1: {event1.event_type.value}")
    print(f"Data: {event1.data}")

    event2 = create_requirement_parsed_event(
        version=2,
        task_id="task_001",
        requirement={"ppt_topic": "AI介绍", "page_num": 10}
    )
    print(f"\nEvent 2: {event2.event_type.value}")
    print(f"Data: {event2.data}")

    # Test serialization
    dict_data = event1.to_dict()
    restored = TaskEvent.from_dict(dict_data)
    print(f"\nRestored event type: {restored.event_type.value}")
