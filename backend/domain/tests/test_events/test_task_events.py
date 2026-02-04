"""
Task Events 测试

测试任务事件的创建、序列化和工厂函数
"""

import pytest
from datetime import datetime, timedelta
from domain.events.task_events import (
    TaskEvent,
    TaskEventType,
    create_task_created_event,
    create_requirement_parsed_event,
    create_framework_designed_event,
    create_checkpoint_saved_event,
    create_stage_started_event,
    create_stage_completed_event,
    create_stage_failed_event,
    create_task_failed_event,
    create_task_completed_event
)

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p0
class TestTaskEventCreation:
    """TaskEvent 创建测试"""

    def test_create_basic_event(self):
        """
        [TEST-EVT-001] 测试创建基本事件

        Given: 必要的事件数据
        When: 创建TaskEvent
        Then: 事件应该被正确创建
        """
        # Given
        event_type = TaskEventType.TASK_CREATED
        version = 1
        data = {"task_id": "task_001"}
        timestamp = datetime.now()

        # When
        event = TaskEvent(
            event_type=event_type,
            version=version,
            data=data,
            timestamp=timestamp
        )

        # Then
        assert event.event_type == event_type
        assert event.version == version
        assert event.data == data
        assert event.timestamp == timestamp
        assert event.metadata == {}  # 默认空字典

    def test_create_event_with_metadata(self):
        """
        [TEST-EVT-002] 测试创建带元数据的事件

        Given: 包含元数据的事件数据
        When: 创建TaskEvent
        Then: 元数据应该被正确存储
        """
        # Given
        metadata = {"source": "agent", "retry_count": 1}

        # When
        event = TaskEvent(
            event_type=TaskEventType.TASK_STARTED,
            version=1,
            data={"task_id": "task_001"},
            timestamp=datetime.now(),
            metadata=metadata
        )

        # Then
        assert event.metadata == metadata

    def test_create_event_with_correlation_id(self):
        """
        [TEST-EVT-003] 测试创建带关联ID的事件

        Given: 包含关联ID的事件数据
        When: 创建TaskEvent
        Then: 关联ID应该被正确存储
        """
        # Given
        correlation_id = "task_001"

        # When
        event = TaskEvent(
            event_type=TaskEventType.TASK_STARTED,
            version=1,
            data={"task_id": "task_001"},
            timestamp=datetime.now(),
            correlation_id=correlation_id
        )

        # Then
        assert event.correlation_id == correlation_id

    def test_event_metadata_defaults_to_empty_dict(self):
        """
        [TEST-EVT-004] 测试元数据默认为空字典

        Given: 不提供元数据
        When: 创建TaskEvent
        Then: 元数据应该被初始化为空字典
        """
        # When
        event = TaskEvent(
            event_type=TaskEventType.TASK_CREATED,
            version=1,
            data={},
            timestamp=datetime.now()
        )

        # Then
        assert event.metadata is not None
        assert event.metadata == {}

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p0
class TestTaskEventFactoryFunctions:
    """TaskEvent 工厂函数测试"""

    def test_create_task_created_event(self):
        """
        [TEST-EVT-005] 测试创建任务创建事件

        Given: 任务ID、输入和用户ID
        When: 调用create_task_created_event
        Then: 应该返回正确的TASK_CREATED事件
        """
        # Given
        version = 1
        task_id = "task_001"
        raw_input = "生成一份AI介绍PPT"
        user_id = "user_001"

        # When
        event = create_task_created_event(
            version=version,
            task_id=task_id,
            raw_input=raw_input,
            user_id=user_id
        )

        # Then
        assert event.event_type == TaskEventType.TASK_CREATED
        assert event.version == version
        assert event.data["task_id"] == task_id
        assert event.data["raw_user_input"] == raw_input
        assert event.data["user_id"] == user_id
        assert event.correlation_id == task_id

    def test_create_requirement_parsed_event(self):
        """
        [TEST-EVT-006] 测试创建需求解析完成事件

        Given: 任务ID和需求数据
        When: 调用create_requirement_parsed_event
        Then: 应该返回正确的REQUIREMENT_PARSED事件
        """
        # Given
        version = 1
        task_id = "task_001"
        requirement = {
            "ppt_topic": "AI介绍",
            "page_num": 10,
            "scene": "business_report"
        }

        # When
        event = create_requirement_parsed_event(
            version=version,
            task_id=task_id,
            requirement=requirement
        )

        # Then
        assert event.event_type == TaskEventType.REQUIREMENT_PARSED
        assert event.data["task_id"] == task_id
        assert event.data["requirement"] == requirement
        assert event.correlation_id == task_id

    def test_create_framework_designed_event(self):
        """
        [TEST-EVT-007] 测试创建框架设计完成事件

        Given: 任务ID和框架数据
        When: 调用create_framework_designed_event
        Then: 应该返回正确的FRAMEWORK_DESIGNED事件
        """
        # Given
        version = 1
        task_id = "task_001"
        framework = {
            "title": "AI技术介绍",
            "outline": ["封面", "目录", "内容"],
            "total_slides": 10
        }

        # When
        event = create_framework_designed_event(
            version=version,
            task_id=task_id,
            framework=framework
        )

        # Then
        assert event.event_type == TaskEventType.FRAMEWORK_DESIGNED
        assert event.data["task_id"] == task_id
        assert event.data["framework"] == framework
        assert event.correlation_id == task_id

    def test_create_checkpoint_saved_event(self):
        """
        [TEST-EVT-008] 测试创建检查点保存事件

        Given: 任务ID、阶段和检查点数据
        When: 调用create_checkpoint_saved_event
        Then: 应该返回正确的CHECKPOINT_SAVED事件
        """
        # Given
        version = 1
        task_id = "task_001"
        phase = 1
        checkpoint_data = {"stage": "requirement_parsing", "status": "completed"}

        # When
        event = create_checkpoint_saved_event(
            version=version,
            task_id=task_id,
            phase=phase,
            checkpoint_data=checkpoint_data
        )

        # Then
        assert event.event_type == TaskEventType.CHECKPOINT_SAVED
        assert event.data["task_id"] == task_id
        assert event.data["phase"] == phase
        assert event.data["checkpoint_data"] == checkpoint_data

    def test_create_stage_started_event(self):
        """
        [TEST-EVT-009] 测试创建阶段开始事件

        Given: 任务ID和阶段名称
        When: 调用create_stage_started_event
        Then: 应该返回TASK_STARTED类型事件
        """
        # Given
        version = 1
        task_id = "task_001"
        stage_name = "requirement_parsing"

        # When
        event = create_stage_started_event(
            version=version,
            task_id=task_id,
            stage_name=stage_name
        )

        # Then
        assert event.event_type == TaskEventType.TASK_STARTED
        assert event.data["task_id"] == task_id
        assert event.data["stage"] == stage_name
        assert event.data["status"] == "started"

    def test_create_stage_completed_event(self):
        """
        [TEST-EVT-010] 测试创建阶段完成事件

        Given: 任务ID、阶段名称和结果数据
        When: 调用create_stage_completed_event
        Then: 应该返回TASK_COMPLETED类型事件
        """
        # Given
        version = 1
        task_id = "task_001"
        stage_name = "requirement_parsing"
        result_data = {"output": "success"}

        # When
        event = create_stage_completed_event(
            version=version,
            task_id=task_id,
            stage_name=stage_name,
            result_data=result_data
        )

        # Then
        assert event.event_type == TaskEventType.TASK_COMPLETED
        assert event.data["task_id"] == task_id
        assert event.data["stage"] == stage_name
        assert event.data["status"] == "completed"
        assert event.data["result"] == result_data

    def test_create_stage_completed_event_without_result(self):
        """
        [TEST-EVT-011] 测试创建无结果的阶段完成事件

        Given: 任务ID和阶段名称（无结果数据）
        When: 调用create_stage_completed_event
        Then: 结果应该为空字典
        """
        # Given
        version = 1
        task_id = "task_001"
        stage_name = "requirement_parsing"

        # When
        event = create_stage_completed_event(
            version=version,
            task_id=task_id,
            stage_name=stage_name
        )

        # Then
        assert event.data["result"] == {}

    def test_create_stage_failed_event(self):
        """
        [TEST-EVT-012] 测试创建阶段失败事件

        Given: 任务ID、阶段名称和错误信息
        When: 调用create_stage_failed_event
        Then: 应该返回TASK_FAILED类型事件
        """
        # Given
        version = 1
        task_id = "task_001"
        stage_name = "requirement_parsing"
        error = "LLM调用超时"

        # When
        event = create_stage_failed_event(
            version=version,
            task_id=task_id,
            stage_name=stage_name,
            error=error
        )

        # Then
        assert event.event_type == TaskEventType.TASK_FAILED
        assert event.data["task_id"] == task_id
        assert event.data["stage"] == stage_name
        assert event.data["status"] == "failed"
        assert event.data["error"] == error

    def test_create_task_failed_event(self):
        """
        [TEST-EVT-013] 测试创建任务失败事件

        Given: 任务ID和错误信息
        When: 调用create_task_failed_event
        Then: 应该返回TASK_FAILED类型事件
        """
        # Given
        version = 1
        task_id = "task_001"
        error = "任务执行失败"

        # When
        event = create_task_failed_event(
            version=version,
            task_id=task_id,
            error=error
        )

        # Then
        assert event.event_type == TaskEventType.TASK_FAILED
        assert event.data["task_id"] == task_id
        assert event.data["status"] == "failed"
        assert event.data["error"] == error

    def test_create_task_completed_event(self):
        """
        [TEST-EVT-014] 测试创建任务完成事件

        Given: 任务ID
        When: 调用create_task_completed_event
        Then: 应该返回TASK_COMPLETED类型事件
        """
        # Given
        version = 1
        task_id = "task_001"

        # When
        event = create_task_completed_event(
            version=version,
            task_id=task_id
        )

        # Then
        assert event.event_type == TaskEventType.TASK_COMPLETED
        assert event.data["task_id"] == task_id
        assert event.data["status"] == "completed"

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p0
class TestTaskEventSerialization:
    """TaskEvent 序列化测试"""

    def test_to_dict_converts_all_fields(self):
        """
        [TEST-EVT-015] 测试to_dict转换所有字段

        Given: 一个完整的TaskEvent
        When: 调用to_dict
        Then: 所有字段都应该被正确转换
        """
        # Given
        event = TaskEvent(
            event_type=TaskEventType.TASK_CREATED,
            version=1,
            data={"task_id": "task_001"},
            timestamp=datetime.now(),
            correlation_id="corr_001",
            metadata={"key": "value"}
        )

        # When
        data = event.to_dict()

        # Then
        assert data["event_type"] == "TASK_CREATED"
        assert data["version"] == 1
        assert data["data"] == {"task_id": "task_001"}
        assert "timestamp" in data
        assert data["correlation_id"] == "corr_001"
        assert data["metadata"] == {"key": "value"}

    def test_to_dict_timestamp_format(self):
        """
        [TEST-EVT-016] 测试to_dict时间戳格式

        Given: 一个带时间戳的事件
        When: 调用to_dict
        Then: 时间戳应该被转换为ISO格式字符串
        """
        # Given
        timestamp = datetime(2025, 2, 4, 12, 30, 45)
        event = TaskEvent(
            event_type=TaskEventType.TASK_CREATED,
            version=1,
            data={},
            timestamp=timestamp
        )

        # When
        data = event.to_dict()

        # Then
        assert data["timestamp"] == "2025-02-04T12:30:45"

    def test_from_dict_creates_event(self):
        """
        [TEST-EVT-017] 测试from_dict创建事件

        Given: 一个事件字典
        When: 调用from_dict
        Then: 应该创建正确的TaskEvent
        """
        # Given
        data = {
            "event_type": "TASK_CREATED",
            "version": 1,
            "data": {"task_id": "task_001"},
            "timestamp": "2025-02-04T12:30:45",
            "correlation_id": "corr_001",
            "metadata": {"key": "value"}
        }

        # When
        event = TaskEvent.from_dict(data)

        # Then
        assert event.event_type == TaskEventType.TASK_CREATED
        assert event.version == 1
        assert event.data == {"task_id": "task_001"}
        assert event.correlation_id == "corr_001"
        assert event.metadata == {"key": "value"}

    def test_from_dict_handles_missing_timestamp(self):
        """
        [TEST-EVT-018] 测试from_dict处理缺失时间戳

        Given: 没有时间戳的事件字典
        When: 调用from_dict
        Then: 应该使用当前时间
        """
        # Given
        data = {
            "event_type": "TASK_CREATED",
            "version": 1,
            "data": {"task_id": "task_001"}
        }

        # When
        before = datetime.now()
        event = TaskEvent.from_dict(data)
        after = datetime.now()

        # Then
        assert before <= event.timestamp <= after

    def test_from_dict_handles_missing_optional_fields(self):
        """
        [TEST-EVT-019] 测试from_dict处理缺失的可选字段

        Given: 缺少可选字段的事件字典
        When: 调用from_dict
        Then: 可选字段应该被设置为默认值
        """
        # Given
        data = {
            "event_type": "TASK_CREATED",
            "version": 1,
            "data": {"task_id": "task_001"},
            "timestamp": "2025-02-04T12:30:45"
        }

        # When
        event = TaskEvent.from_dict(data)

        # Then
        assert event.correlation_id is None
        assert event.metadata == {}

    def test_round_trip_preserves_data(self):
        """
        [TEST-EVT-020] 测试往返转换保持数据一致性

        Given: 一个TaskEvent
        When: 转换为字典再还原
        Then: 数据应该完全一致
        """
        # Given
        original = TaskEvent(
            event_type=TaskEventType.TASK_CREATED,
            version=1,
            data={"task_id": "task_001", "user_id": "user_001"},
            timestamp=datetime.now(),
            correlation_id="task_001",
            metadata={"source": "api"}
        )

        # When
        data = original.to_dict()
        restored = TaskEvent.from_dict(data)

        # Then
        assert restored.event_type == original.event_type
        assert restored.version == original.version
        assert restored.data == original.data
        assert restored.correlation_id == original.correlation_id
        assert restored.metadata == original.metadata
        # 时间戳应该相同或非常接近
        assert abs((restored.timestamp - original.timestamp).total_seconds()) < 1

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p1
class TestTaskEventTimestamps:
    """TaskEvent 时间戳测试"""

    def test_events_have_different_timestamps(self):
        """
        [TEST-EVT-021] 测试不同事件有不同的时间戳

        Given: 连续创建多个事件
        When: 检查它们的时间戳
        Then: 时间戳应该是递增的
        """
        # When
        event1 = create_task_created_event(1, "task_001", "测试")
        # 添加小延迟确保时间戳不同
        import time
        time.sleep(0.01)
        event2 = create_task_completed_event(1, "task_001")

        # Then
        assert event2.timestamp > event1.timestamp

    def test_event_timestamp_is_datetime(self):
        """
        [TEST-EVT-022] 测试事件时间戳是datetime类型

        Given: 使用工厂函数创建事件
        When: 检查时间戳类型
        Then: 应该是datetime实例
        """
        # When
        event = create_task_created_event(1, "task_001", "测试")

        # Then
        assert isinstance(event.timestamp, datetime)

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p2
class TestTaskEventTypes:
    """TaskEvent 事件类型测试"""

    def test_all_event_types_exist(self):
        """
        [TEST-EVT-023] 测试所有事件类型都存在

        Given: TaskEventType枚举
        When: 检查所有定义的类型
        Then: 应该包含所有必要的事件类型
        """
        # Then - 验证关键事件类型存在
        assert TaskEventType.TASK_CREATED
        assert TaskEventType.TASK_STARTED
        assert TaskEventType.TASK_COMPLETED
        assert TaskEventType.TASK_FAILED
        assert TaskEventType.REQUIREMENT_PARSED
        assert TaskEventType.FRAMEWORK_DESIGNED
        assert TaskEventType.CHECKPOINT_SAVED

    def test_event_type_values_are_strings(self):
        """
        [TEST-EVT-024] 测试事件类型值是字符串

        Given: TaskEventType枚举
        When: 检查类型值
        Then: 所有值应该是字符串
        """
        # Then
        for event_type in TaskEventType:
            assert isinstance(event_type.value, str)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
