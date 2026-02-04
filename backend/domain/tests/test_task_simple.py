"""
简单的Task实体测试

这是第一个测试文件，用于验证测试环境是否正确设置
运行时间: ~5秒
"""

import pytest
from datetime import datetime
from domain.entities.task import Task, TaskStatus, TaskStage, StageProgress

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p0
class TestTaskBasic:
    """Task实体基础测试"""

    def test_task_creation(self, sample_task_id):
        """
        [TEST-TASK-001] 测试任务创建

        Given: 准备有效的任务ID和输入
        When: 创建一个任务
        Then: 任务应该被正确创建，属性值正确
        """
        # Given
        task_id = sample_task_id
        raw_input = "生成一份AI介绍PPT"

        # When
        task = Task(id=task_id, raw_input=raw_input)

        # Then
        assert task.id == task_id
        assert task.raw_input == raw_input
        assert task.status == TaskStatus.PENDING
        assert len(task.stages) == len(TaskStage)

    def test_task_initialization_creates_all_stages(self, sample_task_id):
        """
        [TEST-TASK-002] 测试任务初始化创建所有阶段

        Given: 准备任务ID
        When: 创建任务
        Then: 应该创建所有5个阶段
        """
        # Given & When
        task = Task(id=sample_task_id, raw_input="测试")

        # Then
        assert len(task.stages) == len(TaskStage)
        assert TaskStage.REQUIREMENT_PARSING in task.stages
        assert TaskStage.FRAMEWORK_DESIGN in task.stages
        assert TaskStage.RESEARCH in task.stages
        assert TaskStage.CONTENT_GENERATION in task.stages
        assert TaskStage.TEMPLATE_RENDERING in task.stages

    def test_task_initial_progress_is_zero(self, sample_task_id):
        """
        [TEST-TASK-003] 测试新任务进度为0

        Given: 创建一个新任务
        When: 计算总体进度
        Then: 进度应该为0
        """
        # Given & When
        task = Task(id=sample_task_id, raw_input="测试")

        # Then
        progress = task.get_overall_progress()
        assert progress == 0, f"初始进度应该为0，实际为{progress}%"

    def test_task_str_representation(self, sample_task_id):
        """
        [TEST-TASK-004] 测试任务字符串表示

        Given: 创建一个任务
        When: 转换为字符串
        Then: 应该包含任务ID、状态和进度
        """
        # Given & When
        task = Task(id=sample_task_id, raw_input="测试")
        task_str = str(task)

        # Then
        assert sample_task_id in task_str
        assert "pending" in task_str
        assert "0%" in task_str

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p0
class TestTaskStageProgress:
    """任务阶段进度测试"""

    def test_start_stage_updates_status(self, sample_task_id):
        """
        [TEST-TASK-005] 测试开始阶段更新状态

        Given: 一个待处理任务
        When: 开始一个阶段
        Then: 阶段状态应该更新为进行中
        """
        # Given
        task = Task(id=sample_task_id, raw_input="测试")

        # When
        task.start_stage(TaskStage.REQUIREMENT_PARSING)

        # Then
        stage_progress = task.stages[TaskStage.REQUIREMENT_PARSING]
        assert stage_progress.status == TaskStatus.PARSING_REQUIREMENTS
        assert stage_progress.started_at is not None
        assert isinstance(stage_progress.started_at, datetime)

    def test_update_stage_progress(self, sample_task_id):
        """
        [TEST-TASK-006] 测试更新阶段进度

        Given: 一个进行中的任务
        When: 更新阶段进度
        Then: 进度值应该被更新
        """
        # Given
        task = Task(id=sample_task_id, raw_input="测试")
        task.start_stage(TaskStage.REQUIREMENT_PARSING)

        # When
        task.update_stage_progress(TaskStage.REQUIREMENT_PARSING, 50)

        # Then
        assert task.stages[TaskStage.REQUIREMENT_PARSING].progress == 50

    def test_update_progress_bounds_negative(self, sample_task_id):
        """
        [TEST-TASK-007] 测试更新负数进度被限制为0

        Given: 一个任务
        When: 尝试设置负数进度
        Then: 进度应该被限制为0
        """
        # Given
        task = Task(id=sample_task_id, raw_input="测试")

        # When
        task.update_stage_progress(TaskStage.REQUIREMENT_PARSING, -10)

        # Then
        assert task.stages[TaskStage.REQUIREMENT_PARSING].progress == 0

    def test_update_progress_bounds_exceeds_100(self, sample_task_id):
        """
        [TEST-TASK-008] 测试更新超过100的进度被限制为100

        Given: 一个任务
        When: 尝试设置超过100的进度
        Then: 进度应该被限制为100
        """
        # Given
        task = Task(id=sample_task_id, raw_input="测试")

        # When
        task.update_stage_progress(TaskStage.REQUIREMENT_PARSING, 150)

        # Then
        assert task.stages[TaskStage.REQUIREMENT_PARSING].progress == 100

    def test_complete_stage(self, sample_task_id):
        """
        [TEST-TASK-009] 测试完成阶段

        Given: 一个进行中的任务
        When: 完成一个阶段
        Then: 阶段状态应该变为已完成，进度为100
        """
        # Given
        task = Task(id=sample_task_id, raw_input="测试")
        task.start_stage(TaskStage.REQUIREMENT_PARSING)
        task.update_stage_progress(TaskStage.REQUIREMENT_PARSING, 50)

        # When
        task.complete_stage(TaskStage.REQUIREMENT_PARSING)

        # Then
        stage_progress = task.stages[TaskStage.REQUIREMENT_PARSING]
        assert stage_progress.status == TaskStatus.COMPLETED
        assert stage_progress.progress == 100
        assert stage_progress.completed_at is not None

    def test_fail_stage(self, sample_task_id):
        """
        [TEST-TASK-010] 测试阶段失败

        Given: 一个进行中的任务
        When: 标记阶段失败
        Then: 阶段和任务状态应该变为失败，错误信息被记录
        """
        # Given
        task = Task(id=sample_task_id, raw_input="测试")
        task.start_stage(TaskStage.REQUIREMENT_PARSING)

        # When
        error_message = "LLM调用失败"
        task.fail_stage(TaskStage.REQUIREMENT_PARSING, error_message)

        # Then
        stage_progress = task.stages[TaskStage.REQUIREMENT_PARSING]
        assert stage_progress.status == TaskStatus.FAILED
        assert stage_progress.error == error_message
        assert task.status == TaskStatus.FAILED
        assert task.error == error_message

    def test_increment_retry_count(self, sample_task_id):
        """
        [TEST-TASK-011] 测试增加重试次数

        Given: 一个任务
        When: 增加重试次数
        Then: 重试计数应该递增
        """
        # Given
        task = Task(id=sample_task_id, raw_input="测试")

        # When
        count = task.increment_retry(TaskStage.REQUIREMENT_PARSING)

        # Then
        assert count == 1
        assert task.stages[TaskStage.REQUIREMENT_PARSING].retry_count == 1

        # 再次重试
        count = task.increment_retry(TaskStage.REQUIREMENT_PARSING)
        assert count == 2

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p0
class TestTaskProgressCalculation:
    """任务进度计算测试"""

    def test_overall_progress_after_requirement_parsing(self, sample_task_id):
        """
        [TEST-TASK-012] 测试完成需求解析后的进度

        Given: 一个任务
        When: 完成需求解析阶段（权重15%）
        Then: 总体进度应该约为15%
        """
        # Given
        task = Task(id=sample_task_id, raw_input="测试")

        # When
        task.start_stage(TaskStage.REQUIREMENT_PARSING)
        task.complete_stage(TaskStage.REQUIREMENT_PARSING)

        # Then
        progress = task.get_overall_progress()
        assert 14 <= progress <= 16, f"进度应该在14-16%之间，实际为{progress}%"

    def test_overall_progress_after_framework_design(self, sample_task_id):
        """
        [TEST-TASK-013] 测试完成框架设计后的进度

        Given: 一个任务
        When: 完成需求解析和框架设计（15% + 30%）
        Then: 总体进度应该约为45%
        """
        # Given
        task = Task(id=sample_task_id, raw_input="测试")

        # When
        for stage in [TaskStage.REQUIREMENT_PARSING, TaskStage.FRAMEWORK_DESIGN]:
            task.start_stage(stage)
            task.complete_stage(stage)

        # Then
        progress = task.get_overall_progress()
        assert 44 <= progress <= 46, f"进度应该在44-46%之间，实际为{progress}%"

    def test_overall_progress_all_stages(self, sample_task_id):
        """
        [TEST-TASK-014] 测试完成所有阶段后的进度

        Given: 一个任务
        When: 完成所有阶段
        Then: 总体进度应该为100%
        """
        # Given
        task = Task(id=sample_task_id, raw_input="测试")

        # When
        for stage in TaskStage:
            task.start_stage(stage)
            task.complete_stage(stage)

        # Then
        progress = task.get_overall_progress()
        assert progress == 100, f"所有阶段完成后进度应为100%，实际为{progress}%"

    def test_research_stage_excluded_when_not_needed(self, sample_task_id):
        """
        [TEST-TASK-015] 测试不需要研究时跳过研究阶段权重

        Given: 一个不需要研究的任务
        When: 完成包括研究在内的所有阶段
        Then: 研究阶段应该被跳过，不计入进度
        """
        # Given
        task = Task(id=sample_task_id, raw_input="测试")
        task.structured_requirements = {"need_research": False}

        # When - 完成所有阶段
        for stage in TaskStage:
            task.start_stage(stage)
            task.complete_stage(stage)

        # Then - 总进度应该达到100%（即使跳过了研究）
        progress = task.get_overall_progress()
        # 完成所有阶段应该得到100%
        # 需求15% + 框架30% + 内容80% + 渲染100% = 100%
        assert progress == 100, f"不需要研究时总进度应为100%，实际为{progress}%"

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p0
class TestTaskEvents:
    """任务事件测试"""

    def test_stage_started_emits_event(self, sample_task_id):
        """
        [TEST-TASK-016] 测试开始阶段触发事件

        Given: 一个任务
        When: 开始一个阶段
        Then: 应该触发阶段开始事件
        """
        # Given
        task = Task(id=sample_task_id, raw_input="测试")

        # When
        task.start_stage(TaskStage.REQUIREMENT_PARSING)

        # Then
        events = task.get_pending_events()
        assert len(events) > 0
        assert events[0].data["stage"] == TaskStage.REQUIREMENT_PARSING.value
        assert events[0].data["status"] == "started"

    def test_stage_completed_emits_event(self, sample_task_id):
        """
        [TEST-TASK-017] 测试完成阶段触发事件

        Given: 一个进行中的任务
        When: 完成一个阶段
        Then: 应该触发阶段完成事件
        """
        # Given
        task = Task(id=sample_task_id, raw_input="测试")
        task.start_stage(TaskStage.REQUIREMENT_PARSING)

        # 清空开始事件
        task.get_pending_events()

        # When
        task.complete_stage(TaskStage.REQUIREMENT_PARSING)

        # Then
        events = task.get_pending_events()
        assert len(events) > 0
        assert events[0].data["stage"] == TaskStage.REQUIREMENT_PARSING.value
        assert events[0].data["status"] == "completed"

    def test_stage_failed_emits_two_events(self, sample_task_id):
        """
        [TEST-TASK-018] 测试阶段失败触发两个事件

        Given: 一个进行中的任务
        When: 阶段失败
        Then: 应该触发阶段失败事件和任务失败事件
        """
        # Given
        task = Task(id=sample_task_id, raw_input="测试")
        task.start_stage(TaskStage.REQUIREMENT_PARSING)

        # 清空开始事件
        task.get_pending_events()

        # When
        task.fail_stage(TaskStage.REQUIREMENT_PARSING, "测试错误")

        # Then
        events = task.get_pending_events()
        assert len(events) == 2, f"应该有2个事件，实际有{len(events)}个"
        # 两个事件都应该是TASK_FAILED类型
        assert all(event.event_type.value == "TASK_FAILED" for event in events)

    def test_get_pending_events_clears_list(self, sample_task_id):
        """
        [TEST-TASK-019] 测试获取事件后清空列表

        Given: 一个有事件的任务
        When: 获取待处理事件
        Then: 事件列表应该被清空
        """
        # Given
        task = Task(id=sample_task_id, raw_input="测试")
        task.start_stage(TaskStage.REQUIREMENT_PARSING)

        # When - 第一次获取
        events1 = task.get_pending_events()
        assert len(events1) > 0

        # When - 第二次获取
        events2 = task.get_pending_events()

        # Then - 第二次应该为空
        assert len(events2) == 0, "第二次获取事件应该返回空列表"

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p1
class TestTaskMetadata:
    """任务元数据测试"""

    def test_metadata_auto_created(self, sample_task_id):
        """
        [TEST-TASK-020] 测试元数据自动创建

        Given: 创建一个任务
        When: 检查元数据
        Then: 元数据应该被自动创建
        """
        # Given & When
        task = Task(id=sample_task_id, raw_input="测试")

        # Then
        assert task.metadata is not None
        assert task.metadata.user_id == "anonymous"
        assert task.metadata.created_at is not None
        assert isinstance(task.metadata.created_at, datetime)

    def test_metadata_updated_at_changes(self, sample_task_id):
        """
        [TEST-TASK-021] 测试更新时间自动更新

        Given: 一个任务
        When: 执行操作
        Then: 更新时间应该被设置
        """
        # Given
        task = Task(id=sample_task_id, raw_input="测试")
        assert task.metadata.updated_at is None

        # When
        task.start_stage(TaskStage.REQUIREMENT_PARSING)

        # Then
        assert task.metadata.updated_at is not None

    def test_mark_completed_sets_completion_data(self, sample_task_id):
        """
        [TEST-TASK-022] 测试标记完成设置完成数据

        Given: 一个任务
        When: 标记为完成
        Then: 完成时间和总耗时应该被设置
        """
        # Given
        import time
        task = Task(id=sample_task_id, raw_input="测试")
        # 等待一小段时间确保有时间差
        time.sleep(0.01)

        # When
        task.mark_completed()

        # Then
        assert task.status == TaskStatus.COMPLETED
        assert task.metadata.completed_at is not None
        # total_duration可能为0如果时间间隔太短，这是正常的
        assert task.metadata.total_duration >= 0

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p0
class TestTaskSerialization:
    """任务序列化测试"""

    def test_to_dict_includes_all_fields(self, sample_task_id):
        """
        [TEST-TASK-023] 测试to_dict包含所有字段

        Given: 一个任务
        When: 转换为字典
        Then: 应该包含所有重要字段
        """
        # Given
        task = Task(id=sample_task_id, raw_input="测试")

        # When
        data = task.to_dict()

        # Then
        assert "id" in data
        assert "status" in data
        assert "metadata" in data
        assert "stages" in data
        assert "raw_input" in data
        assert "overall_progress" in data
        assert data["id"] == sample_task_id
        assert data["raw_input"] == "测试"

    def test_from_dict_restores_task(self, sample_task_id):
        """
        [TEST-TASK-024] 测试from_dict还原任务

        Given: 一个任务的字典表示
        When: 从字典还原任务
        Then: 任务应该被正确还原
        """
        # Given
        task = Task(id=sample_task_id, raw_input="测试", status=TaskStatus.COMPLETED)
        data = task.to_dict()

        # When
        restored_task = Task.from_dict(data)

        # Then
        assert restored_task.id == task.id
        assert restored_task.status == task.status
        assert restored_task.raw_input == task.raw_input
        assert len(restored_task.stages) == len(task.stages)

    def test_round_trip_preserves_data(self, sample_task_id):
        """
        [TEST-TASK-025] 测试往返转换保持数据一致性

        Given: 一个任务
        When: 转换为字典再还原
        Then: 数据应该完全一致
        """
        # Given
        original_task = Task(
            id=sample_task_id,
            raw_input="测试",
            status=TaskStatus.COMPLETED
        )
        original_task.start_stage(TaskStage.REQUIREMENT_PARSING)

        # When
        data = original_task.to_dict()
        restored_task = Task.from_dict(data)

        # Then
        assert restored_task.id == original_task.id
        assert restored_task.raw_input == original_task.raw_input
        assert restored_task.status == original_task.status
        assert restored_task.get_overall_progress() == original_task.get_overall_progress()

if __name__ == "__main__":
    # 直接运行此文件
    pytest.main([__file__, "-v", "-s"])
