"""
Domain 层集成测试

测试Task、Requirement、Service和Event之间的协作
"""

import pytest
from datetime import datetime
from domain.entities.task import Task, TaskStatus, TaskStage
from domain.value_objects.requirement import Requirement, SceneType
from domain.services.task_validation_service import TaskValidationService
from domain.services.task_progress_service import TaskProgressService
from domain.exceptions import ValidationError, InvalidStateTransitionError

@pytest.mark.domain
@pytest.mark.integration
@pytest.mark.p0
class TestTaskFullLifecycle:
    """任务完整生命周期集成测试"""

    def test_complete_task_lifecycle(self):
        """
        [TEST-INT-001] 测试完整任务生命周期

        Given: 一个新任务
        When: 执行完整生命周期（创建→开始→完成各阶段→完成）
        Then: 任务应该正确转换状态，最终达到完成状态
        """
        # Given
        task = Task(id="test_001", raw_input="生成AI介绍PPT")

        # 验证初始状态
        assert task.status == TaskStatus.PENDING
        assert task.get_overall_progress() == 0

        # When - 执行完整生命周期
        events_collected = []

        # 阶段1: 需求解析
        task.start_stage(TaskStage.REQUIREMENT_PARSING)
        events_collected.extend(task.get_pending_events())
        task.update_stage_progress(TaskStage.REQUIREMENT_PARSING, 50)
        task.update_stage_progress(TaskStage.REQUIREMENT_PARSING, 100)
        task.complete_stage(TaskStage.REQUIREMENT_PARSING)
        events_collected.extend(task.get_pending_events())

        # 验证第一阶段完成
        assert task.stages[TaskStage.REQUIREMENT_PARSING].status == TaskStatus.COMPLETED
        assert 14 <= task.get_overall_progress() <= 16

        # 阶段2: 框架设计
        task.start_stage(TaskStage.FRAMEWORK_DESIGN)
        events_collected.extend(task.get_pending_events())
        task.complete_stage(TaskStage.FRAMEWORK_DESIGN)
        events_collected.extend(task.get_pending_events())

        # 验证第二阶段完成
        assert task.stages[TaskStage.FRAMEWORK_DESIGN].status == TaskStatus.COMPLETED
        assert 44 <= task.get_overall_progress() <= 46

        # 阶段3: 研究（可选）
        task.start_stage(TaskStage.RESEARCH)
        events_collected.extend(task.get_pending_events())
        task.complete_stage(TaskStage.RESEARCH)
        events_collected.extend(task.get_pending_events())

        # 阶段4: 内容生成
        task.start_stage(TaskStage.CONTENT_GENERATION)
        events_collected.extend(task.get_pending_events())
        task.complete_stage(TaskStage.CONTENT_GENERATION)
        events_collected.extend(task.get_pending_events())

        # 阶段5: 模板渲染
        task.start_stage(TaskStage.TEMPLATE_RENDERING)
        events_collected.extend(task.get_pending_events())
        task.complete_stage(TaskStage.TEMPLATE_RENDERING)
        events_collected.extend(task.get_pending_events())

        # 完成任务
        task.mark_completed()
        events_collected.extend(task.get_pending_events())

        # Then - 验证最终状态
        assert task.status == TaskStatus.COMPLETED
        assert task.get_overall_progress() == 100
        assert task.metadata.completed_at is not None
        assert task.metadata.total_duration > 0

        # 验证事件
        assert len(events_collected) > 0
        print(f"✓ 完整生命周期测试通过，触发了 {len(events_collected)} 个事件")

    def test_task_failure_and_recovery(self):
        """
        [TEST-INT-002] 测试任务失败和恢复

        Given: 一个正在执行的任务
        When: 某个阶段失败
        Then: 任务应该正确记录失败，可以重新开始
        """
        # Given
        task = Task(id="test_002", raw_input="测试")
        task.start_stage(TaskStage.REQUIREMENT_PARSING)

        # When - 阶段失败
        error_msg = "LLM服务超时"
        task.fail_stage(TaskStage.REQUIREMENT_PARSING, error_msg)

        # Then - 验证失败状态
        assert task.status == TaskStatus.FAILED
        assert task.stages[TaskStage.REQUIREMENT_PARSING].status == TaskStatus.FAILED
        assert task.error == error_msg

        # 验证失败事件
        events = task.get_pending_events()
        assert len(events) == 2  # 阶段失败 + 任务失败

        # 模拟恢复 - 创建新任务重试
        retry_task = Task(id="test_002_retry", raw_input="测试")
        retry_task.start_stage(TaskStage.REQUIREMENT_PARSING)
        retry_task.complete_stage(TaskStage.REQUIREMENT_PARSING)

        # 验证恢复成功
        assert retry_task.status != TaskStatus.FAILED
        assert retry_task.stages[TaskStage.REQUIREMENT_PARSING].status == TaskStatus.COMPLETED

    def test_task_with_requirement_integration(self):
        """
        [TEST-INT-003] 测试任务与需求集成

        Given: 一个任务和需求
        When: 将需求关联到任务
        Then: 任务应该正确存储需求
        """
        # Given
        task = Task(id="test_003", raw_input="生成AI介绍PPT")
        requirement = Requirement.with_defaults(
            ppt_topic="AI技术介绍",
            scene=SceneType.BUSINESS_REPORT,
            page_num=15
        )

        # When - 将需求保存到任务
        task.structured_requirements = requirement.to_dict()

        # Then - 验证需求被正确保存
        assert task.structured_requirements is not None
        assert task.structured_requirements["ppt_topic"] == "AI技术介绍"
        assert task.structured_requirements["page_num"] == 15

        # 验证可以还原需求
        restored_req = Requirement.from_dict(task.structured_requirements)
        assert restored_req.ppt_topic == requirement.ppt_topic
        assert restored_req.page_num == requirement.page_num

@pytest.mark.domain
@pytest.mark.integration
@pytest.mark.p0
class TestValidationServiceIntegration:
    """验证服务集成测试"""

    def test_validate_requirement_before_use(self):
        """
        [TEST-INT-004] 测试在使用需求前验证

        Given: 一个需求对象
        When: 使用验证服务验证
        Then: 有效需求应该通过，无效需求应该失败
        """
        # Given
        service = TaskValidationService()
        valid_req = Requirement(ppt_topic="测试", page_num=10)

        # When - 验证有效需求
        service.validate_requirement(valid_req)  # 不应该抛出异常

        # Given - 无效需求
        class InvalidReq:
            ppt_topic = ""
            page_num = 0

        # When & Then - 验证无效需求应该失败
        with pytest.raises(ValidationError):
            service.validate_requirement(InvalidReq())

    def test_validate_state_transitions(self):
        """
        [TEST-INT-005] 测试状态转换验证集成

        Given: 一个任务和验证服务
        When: 尝试各种状态转换
        Then: 有效转换应该成功，无效转换应该失败
        """
        # Given
        task = Task(id="test_004", raw_input="测试")
        service = TaskValidationService()

        # When - 有效的转换
        task.start_stage(TaskStage.REQUIREMENT_PARSING)
        current_status = task.status.value

        # 验证下一步转换
        service.validate_task_transition(current_status, "designing_framework")

        # When & Then - 无效的转换
        with pytest.raises(InvalidStateTransitionError):
            service.validate_task_transition("completed", "parsing_requirements")

@pytest.mark.domain
@pytest.mark.integration
@pytest.mark.p1
class TestProgressServiceIntegration:
    """进度服务集成测试"""

    def test_progress_calculates_across_stages(self):
        """
        [TEST-INT-006] 测试进度计算跨阶段

        Given: 一个任务和进度服务
        When: 完成多个阶段
        Then: 进度应该正确累加
        """
        # Given
        task = Task(id="test_005", raw_input="测试")
        service = TaskProgressService()

        # When - 逐步完成阶段
        task.start_stage(TaskStage.REQUIREMENT_PARSING)
        task.complete_stage(TaskStage.REQUIREMENT_PARSING)
        progress1 = service.calculate_overall_progress(task.stages)

        task.start_stage(TaskStage.FRAMEWORK_DESIGN)
        task.complete_stage(TaskStage.FRAMEWORK_DESIGN)
        progress2 = service.calculate_overall_progress(task.stages)

        # Then - 验证进度递增
        assert progress2 > progress1
        assert 14 <= progress1 <= 16
        assert 44 <= progress2 <= 46

    def test_progress_with_research_skipped(self):
        """
        [TEST-INT-007] 测试跳过研究阶段时的进度

        Given: 一个不需要研究的任务
        When: 完成所有阶段
        Then: 进度应该正确计算（跳过研究阶段）
        """
        # Given
        task = Task(id="test_006", raw_input="测试")
        task.structured_requirements = {"need_research": False}
        service = TaskProgressService()

        # When - 完成所有阶段
        for stage in TaskStage:
            task.start_stage(stage)
            task.complete_stage(stage)

        # Then - 注意：服务层计算不处理跳过逻辑，只根据stages计算
        # 跳过逻辑在Task实体的get_overall_progress方法中
        progress = service.calculate_overall_progress(task.stages)
        # 由于Task实体的get_overall_progress会处理跳过，这里直接使用task的方法
        task_progress = task.get_overall_progress()
        assert task_progress == 100

@pytest.mark.domain
@pytest.mark.integration
@pytest.mark.p1
class TestEventPropagation:
    """事件传播集成测试"""

    def test_events_across_task_lifecycle(self):
        """
        [TEST-INT-008] 测试事件在整个生命周期中传播

        Given: 一个任务
        When: 执行完整生命周期
        Then: 应该触发一系列事件
        """
        # Given
        task = Task(id="test_007", raw_input="测试")

        # When - 执行生命周期并收集事件
        all_events = []

        for stage in [TaskStage.REQUIREMENT_PARSING, TaskStage.FRAMEWORK_DESIGN]:
            task.start_stage(stage)
            all_events.extend(task.get_pending_events())

            task.complete_stage(stage)
            all_events.extend(task.get_pending_events())

        task.mark_completed()
        all_events.extend(task.get_pending_events())

        # Then - 验证事件
        assert len(all_events) > 0

        # 应该有开始事件
        start_events = [e for e in all_events if e.data.get("status") == "started"]
        assert len(start_events) == 2

        # 应该有完成事件
        complete_events = [e for e in all_events if e.data.get("status") == "completed"]
        assert len(complete_events) >= 2

        print(f"✓ 收集到 {len(all_events)} 个事件")

    def test_events_contain_correlation_id(self):
        """
        [TEST-INT-009] 测试事件包含关联ID

        Given: 一个任务
        When: 触发多个事件
        Then: 所有事件应该有相同的关联ID（任务ID）
        """
        # Given
        task_id = "test_008"
        task = Task(id=task_id, raw_input="测试")

        # When - 触发事件
        task.start_stage(TaskStage.REQUIREMENT_PARSING)
        events1 = task.get_pending_events()

        task.complete_stage(TaskStage.REQUIREMENT_PARSING)
        events2 = task.get_pending_events()

        # Then - 验证关联ID
        all_events = events1 + events2
        for event in all_events:
            assert event.correlation_id == task_id

@pytest.mark.domain
@pytest.mark.integration
@pytest.mark.p2
class TestErrorScenarios:
    """错误场景集成测试"""

    def test_multiple_validation_errors(self):
        """
        [TEST-INT-010] 测试多个验证错误

        Given: 有多个问题的需求
        When: 验证需求
        Then: 应该收集所有错误
        """
        # Given
        service = TaskValidationService()

        class InvalidReq:
            ppt_topic = ""
            page_num = 0
            scene = "invalid"

        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            service.validate_requirement(InvalidReq())

        errors = exc_info.value.errors
        assert len(errors) >= 2
        print(f"✓ 正确捕获了 {len(errors)} 个验证错误")

    def test_task_retry_mechanism(self):
        """
        [TEST-INT-011] 测试任务重试机制

        Given: 一个失败的任务
        When: 增加重试次数
        Then: 重试计数应该正确递增
        """
        # Given
        task = Task(id="test_009", raw_input="测试")
        task.start_stage(TaskStage.REQUIREMENT_PARSING)

        # When - 多次重试
        for i in range(1, 4):
            count = task.increment_retry(TaskStage.REQUIREMENT_PARSING)
            assert count == i

        # Then
        assert task.stages[TaskStage.REQUIREMENT_PARSING].retry_count == 3

@pytest.mark.domain
@pytest.mark.integration
@pytest.mark.p1
class TestSerializationIntegration:
    """序列化集成测试"""

    def test_task_serialization_preserves_state(self):
        """
        [TEST-INT-012] 测试任务序列化保持状态

        Given: 一个复杂的任务
        When: 序列化和反序列化
        Then: 任务状态应该完全恢复
        """
        # Given
        task = Task(id="test_010", raw_input="测试")
        task.start_stage(TaskStage.REQUIREMENT_PARSING)
        task.complete_stage(TaskStage.REQUIREMENT_PARSING)
        task.start_stage(TaskStage.FRAMEWORK_DESIGN)

        # 添加需求
        requirement = Requirement.with_defaults(ppt_topic="AI介绍")
        task.structured_requirements = requirement.to_dict()

        # 记录进度
        progress_before = task.get_overall_progress()

        # When - 序列化
        data = task.to_dict()

        # 反序列化
        restored_task = Task.from_dict(data)

        # Then - 验证状态恢复
        assert restored_task.id == task.id
        assert restored_task.status == task.status
        assert restored_task.get_overall_progress() == progress_before
        assert restored_task.structured_requirements == task.structured_requirements

        # 验证阶段状态
        assert restored_task.stages[TaskStage.REQUIREMENT_PARSING].status == TaskStatus.COMPLETED
        assert restored_task.stages[TaskStage.FRAMEWORK_DESIGN].status == TaskStatus.DESIGNING_FRAMEWORK

        print("✓ 任务序列化和反序列化测试通过")

    def test_requirement_serialization_round_trip(self):
        """
        [TEST-INT-013] 测试需求序列化往返

        Given: 一个复杂的需求
        When: 序列化和反序列化
        Then: 需求应该完全恢复
        """
        # Given
        requirement = Requirement.with_defaults(
            ppt_topic="AI技术在医疗领域的应用",
            scene=SceneType.BUSINESS_REPORT,
            page_num=20,
            industry="医疗",
            audience="医生"
        )

        # When
        data = requirement.to_dict()
        restored = Requirement.from_dict(data)

        # Then
        assert restored.ppt_topic == requirement.ppt_topic
        assert restored.page_num == requirement.page_num
        assert restored.scene == requirement.scene
        assert restored.industry == requirement.industry
        assert restored.audience == requirement.audience

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
