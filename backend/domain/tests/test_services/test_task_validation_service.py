"""
TaskValidationService 测试

测试任务验证服务的各项功能
"""

import pytest
from domain.services.task_validation_service import TaskValidationService
from domain.value_objects.requirement import Requirement, SceneType, TemplateType
from domain.exceptions import ValidationError, InvalidStateTransitionError

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p0
class TestTaskValidationServiceRequirement:
    """TaskValidationService 需求验证测试"""

    def test_validate_valid_requirement(self, sample_requirement):
        """
        [TEST-VAL-001] 测试验证有效需求

        Given: 一个有效的需求对象
        When: 调用validate_requirement
        Then: 不应该抛出异常
        """
        # Given
        service = TaskValidationService()
        req = sample_requirement

        # When & Then - 不应该抛出异常
        service.validate_requirement(req)

    def test_validate_empty_topic_fails(self):
        """
        [TEST-VAL-002] 测试空主题验证失败

        Given: 一个空主题的需求
        When: 调用validate_requirement
        Then: 应该抛出ValidationError
        """
        # Given
        service = TaskValidationService()

        # 创建一个空主题的需求（通过直接设置属性绕过验证）
        # 注意：由于Requirement是frozen，我们需要模拟这种情况
        # 这里我们用一个简化的方式
        class MockRequirement:
            ppt_topic = ""
            page_num = 10

        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            service.validate_requirement(MockRequirement())

        assert "PPT主题不能为空" in str(exc_info.value.errors)

    def test_validate_invalid_page_num_fails(self):
        """
        [TEST-VAL-003] 测试无效页数验证失败

        Given: 页数无效的需求
        When: 调用validate_requirement
        Then: 应该抛出ValidationError
        """
        # Given
        service = TaskValidationService()

        class MockRequirement:
            ppt_topic = "测试"
            page_num = 0

        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            service.validate_requirement(MockRequirement())

        assert "页数必须大于0" in str(exc_info.value.errors)

    def test_validate_page_num_exceeds_100_fails(self):
        """
        [TEST-VAL-004] 测试页数超过100验证失败

        Given: 页数为101的需求
        When: 调用validate_requirement
        Then: 应该抛出ValidationError
        """
        # Given
        service = TaskValidationService()

        class MockRequirement:
            ppt_topic = "测试"
            page_num = 101

        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            service.validate_requirement(MockRequirement())

        assert "页数不能超过100" in str(exc_info.value.errors)

    def test_validate_invalid_scene_fails(self):
        """
        [TEST-VAL-005] 测试无效场景验证失败

        Given: 场景类型无效的需求
        When: 调用validate_requirement
        Then: 应该抛出ValidationError
        """
        # Given
        service = TaskValidationService()

        class MockRequirement:
            ppt_topic = "测试"
            page_num = 10
            scene = "invalid_scene"

        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            service.validate_requirement(MockRequirement())

        assert "无效的场景类型" in str(exc_info.value.errors)

    def test_validate_invalid_template_fails(self):
        """
        [TEST-VAL-006] 测试无效模板验证失败

        Given: 模板类型无效的需求
        When: 调用validate_requirement
        Then: 应该抛出ValidationError
        """
        # Given
        service = TaskValidationService()

        class MockRequirement:
            ppt_topic = "测试"
            page_num = 10
            scene = SceneType.BUSINESS_REPORT
            template_type = "invalid_template"

        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            service.validate_requirement(MockRequirement())

        assert "无效的模板类型" in str(exc_info.value.errors)

    def test_validate_core_modules_exceeds_page_num(self):
        """
        [TEST-VAL-007] 测试核心模块数超过页数验证失败

        Given: 核心模块数大于页数的需求
        When: 调用validate_requirement
        Then: 应该抛出ValidationError
        """
        # Given
        service = TaskValidationService()

        class MockRequirement:
            ppt_topic = "测试"
            page_num = 5
            core_modules = ["模块1", "模块2", "模块3", "模块4", "模块5", "模块6"]

        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            service.validate_requirement(MockRequirement())

        assert "核心模块数量不能超过页数" in str(exc_info.value.errors)

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p1
class TestTaskValidationServiceFramework:
    """TaskValidationService 框架验证测试"""

    def test_validate_valid_framework(self, sample_framework):
        """
        [TEST-VAL-008] 测试验证有效框架

        Given: 一个有效的框架对象
        When: 调用validate_framework
        Then: 不应该抛出异常
        """
        # Given
        service = TaskValidationService()

        class MockFramework:
            title = "AI技术介绍"
            outline = [
                {"title": "封面", "content": "..."},
                {"title": "目录", "content": "..."}
            ]
            total_slides = 10

        # When & Then
        service.validate_framework(MockFramework())

    def test_validate_empty_title_fails(self):
        """
        [TEST-VAL-009] 测试空标题验证失败

        Given: 标题为空的框架
        When: 调用validate_framework
        Then: 应该抛出ValidationError
        """
        # Given
        service = TaskValidationService()

        class MockFramework:
            title = ""
            outline = [{"title": "封面", "content": "..."}]
            total_slides = 5

        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            service.validate_framework(MockFramework())

        assert "框架标题不能为空" in str(exc_info.value.errors)

    def test_validate_empty_outline_fails(self):
        """
        [TEST-VAL-010] 测试空大纲验证失败

        Given: 大纲为空的框架
        When: 调用validate_framework
        Then: 应该抛出ValidationError
        """
        # Given
        service = TaskValidationService()

        class MockFramework:
            title = "测试"
            outline = []
            total_slides = 5

        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            service.validate_framework(MockFramework())

        assert "大纲不能为空" in str(exc_info.value.errors)

    def test_validate_invalid_total_slides_fails(self):
        """
        [TEST-VAL-011] 测试无效幻灯片数验证失败

        Given: 幻灯片数小于1的框架
        When: 调用validate_framework
        Then: 应该抛出ValidationError
        """
        # Given
        service = TaskValidationService()

        class MockFramework:
            title = "测试"
            outline = [{"title": "封面", "content": "..."}]
            total_slides = 0

        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            service.validate_framework(MockFramework())

        assert "幻灯片总数必须大于0" in str(exc_info.value.errors)

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p0
class TestTaskValidationServiceStateTransition:
    """TaskValidationService 状态转换验证测试"""

    @pytest.mark.parametrize("current,next_target", [
        ("pending", "parsing_requirements"),
        ("pending", "failed"),
        ("parsing_requirements", "designing_framework"),
        ("parsing_requirements", "failed"),
        ("designing_framework", "researching"),
        ("designing_framework", "failed"),
        ("researching", "generating_content"),
        ("researching", "failed"),
        ("generating_content", "rendering"),
        ("generating_content", "failed"),
        ("rendering", "completed"),
        ("rendering", "failed"),
    ])
    def test_validate_valid_state_transitions(self, current, next_target):
        """
        [TEST-VAL-012] 测试有效的状态转换

        Given: 当前状态和有效的下一个状态
        When: 调用validate_task_transition
        Then: 不应该抛出异常
        """
        # Given
        service = TaskValidationService()

        # When & Then - 不应该抛出异常
        service.validate_task_transition(current, next_target)

    @pytest.mark.parametrize("current,next_target", [
        ("completed", "parsing_requirements"),  # 终态不能转换
        ("completed", "designing_framework"),
        ("pending", "completed"),  # 跳跃太多步骤
        ("parsing_requirements", "rendering"),  # 跳跃阶段
        ("researching", "parsing_requirements"),  # 倒退
    ])
    def test_validate_invalid_state_transitions(self, current, next_target):
        """
        [TEST-VAL-013] 测试无效的状态转换

        Given: 当前状态和无效的下一个状态
        When: 调用validate_task_transition
        Then: 应该抛出InvalidStateTransitionError
        """
        # Given
        service = TaskValidationService()

        # When & Then
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            service.validate_task_transition(current, next_target)

        assert exc_info.value.details["current_state"] == current
        assert exc_info.value.details["target_state"] == next_target

    def test_validate_transition_from_failed_state(self):
        """
        [TEST-VAL-014] 测试从失败状态的转换

        Given: 当前状态为失败
        When: 尝试转换到有效状态
        Then: 某些转换应该被允许
        """
        # Given
        service = TaskValidationService()

        # When & Then - 失败后可以重新开始或进入修订状态
        service.validate_task_transition("failed", "parsing_requirements")
        service.validate_task_transition("failed", "revision_pending")

        # 但不能直接跳到完成
        with pytest.raises(InvalidStateTransitionError):
            service.validate_task_transition("failed", "completed")

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p2
class TestTaskValidationServiceResearchResult:
    """TaskValidationService 研究结果验证测试"""

    def test_validate_valid_research_result(self):
        """
        [TEST-VAL-015] 测试验证有效研究结果

        Given: 一个有效的研究结果
        When: 调用validate_research_result
        Then: 不应该抛出异常
        """
        # Given
        service = TaskValidationService()

        class MockResearchResult:
            topic = "AI技术"
            content = "人工智能是计算机科学的一个分支..."
            confidence = 0.95

        # When & Then
        service.validate_research_result(MockResearchResult())

    def test_validate_empty_topic_fails(self):
        """
        [TEST-VAL-016] 测试空主题验证失败

        Given: 主题为空的研究结果
        When: 调用validate_research_result
        Then: 应该抛出ValidationError
        """
        # Given
        service = TaskValidationService()

        class MockResearchResult:
            topic = ""
            content = "内容"
            confidence = 0.9

        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            service.validate_research_result(MockResearchResult())

        assert "研究主题不能为空" in str(exc_info.value.errors)

    def test_validate_empty_content_fails(self):
        """
        [TEST-VAL-017] 测试空内容验证失败

        Given: 内容为空的研究结果
        When: 调用validate_research_result
        Then: 应该抛出ValidationError
        """
        # Given
        service = TaskValidationService()

        class MockResearchResult:
            topic = "AI技术"
            content = ""
            confidence = 0.9

        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            service.validate_research_result(MockResearchResult())

        assert "研究内容不能为空" in str(exc_info.value.errors)

    @pytest.mark.parametrize("confidence", [-0.1, -0.5, 1.1, 2.0])
    def test_validate_invalid_confidence(self, confidence):
        """
        [TEST-VAL-018] 测试无效置信度验证失败

        Given: 置信度不在[0, 1]范围内
        When: 调用validate_research_result
        Then: 应该抛出ValidationError
        """
        # Given
        service = TaskValidationService()

        class MockResearchResult:
            topic = "AI技术"
            content = "内容"
            confidence = confidence

        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            service.validate_research_result(MockResearchResult())

        assert "置信度必须在0-1之间" in str(exc_info.value.errors)

    @pytest.mark.parametrize("confidence", [0.0, 0.5, 1.0])
    def test_validate_valid_confidence(self, confidence):
        """
        [TEST-VAL-019] 测试有效置信度边界值

        Given: 置信度在[0, 1]边界
        When: 调用validate_research_result
        Then: 应该通过验证
        """
        # Given
        service = TaskValidationService()

        # 创建Mock对象，使用类型提示
        class MockResearchResult:
            def __init__(self, conf):
                self.topic = "AI技术"
                self.content = "内容"
                self.confidence = conf

        # When & Then - 不应该抛出异常
        service.validate_research_result(MockResearchResult(confidence))

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p1
class TestTaskValidationServiceMultipleErrors:
    """TaskValidationService 多错误验证测试"""

    def test_validate_requirement_with_multiple_errors(self):
        """
        [TEST-VAL-020] 测试多个验证错误

        Given: 有多个问题的需求
        When: 调用validate_requirement
        Then: 应该收集所有错误
        """
        # Given
        service = TaskValidationService()

        class MockRequirement:
            ppt_topic = ""  # 错误1
            page_num = 0    # 错误2
            scene = "invalid"  # 错误3

        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            service.validate_requirement(MockRequirement())

        errors = exc_info.value.errors
        assert len(errors) >= 2  # 至少有2个错误
        assert any("PPT主题不能为空" in e for e in errors)
        assert any("页数必须大于0" in e for e in errors)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
