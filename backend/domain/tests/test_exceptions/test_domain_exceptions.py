"""
Domain Exceptions 测试

测试领域异常类的创建和属性
"""

import pytest
from domain.exceptions import (
    DomainError,
    TaskNotFoundException,
    TaskValidationError,
    InvalidTaskStateError,
    TaskTransitionError,
    ValidationError,
    InvalidStateTransitionError
)

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p0
class TestDomainError:
    """DomainError 基础测试"""

    def test_create_domain_error(self):
        """
        [TEST-EXC-001] 测试创建DomainError

        Given: 错误消息
        When: 创建DomainError
        Then: 异常应该被正确创建
        """
        # Given
        message = "测试领域错误"

        # When
        error = DomainError(message=message)

        # Then
        assert str(error) == message
        assert error.message == message

    def test_domain_error_with_details(self):
        """
        [TEST-EXC-002] 测试创建带详情的DomainError

        Given: 错误消息和详情
        When: 创建DomainError
        Then: 详情应该被正确存储
        """
        # Given
        message = "测试错误"
        details = {"key": "value", "code": 500}

        # When
        error = DomainError(message=message, details=details)

        # Then
        assert error.details == details
        assert error.details["key"] == "value"
        assert error.details["code"] == 500

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p0
class TestTaskNotFoundException:
    """TaskNotFoundException 测试"""

    def test_create_task_not_found_exception(self):
        """
        [TEST-EXC-003] 测试创建TaskNotFoundException

        Given: 任务ID
        When: 创建TaskNotFoundException
        Then: 异常消息和属性应该正确
        """
        # Given
        task_id = "task_001"

        # When
        error = TaskNotFoundException(task_id=task_id)

        # Then
        assert "task_001" in str(error)
        assert error.task_id == task_id
        assert error.details["task_id"] == task_id

    def test_task_not_found_message_format(self):
        """
        [TEST-EXC-004] 测试TaskNotFoundException消息格式

        Given: 不同的任务ID
        When: 创建异常
        Then: 消息应该遵循标准格式
        """
        # Given
        task_id = "missing_task_123"

        # When
        error = TaskNotFoundException(task_id=task_id)

        # Then
        assert "Task not found" in str(error)
        assert task_id in str(error)

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p0
class TestTaskValidationError:
    """TaskValidationError 测试"""

    def test_create_validation_error_with_message(self):
        """
        [TEST-EXC-005] 测试创建带消息的验证错误

        Given: 错误消息
        When: 创建TaskValidationError
        Then: 消息应该被正确设置
        """
        # Given
        message = "验证失败"

        # When
        error = TaskValidationError(message=message)

        # Then
        assert str(error) == message

    def test_create_validation_error_with_field(self):
        """
        [TEST-EXC-006] 测试创建带字段的验证错误

        Given: 错误消息和字段名
        When: 创建TaskValidationError
        Then: 字段信息应该被正确存储
        """
        # Given
        message = "字段验证失败"
        field = "page_num"

        # When
        error = TaskValidationError(message=message, field=field)

        # Then
        assert error.field == field
        assert error.details["field"] == field

    def test_create_validation_error_with_errors_list(self):
        """
        [TEST-EXC-007] 测试创建带错误列表的验证错误

        Given: 错误消息和错误列表
        When: 创建TaskValidationError
        Then: 错误列表应该被正确存储
        """
        # Given
        message = "多个字段验证失败"
        errors = [
            "页数必须大于0",
            "页数不能超过100",
            "主题不能为空"
        ]

        # When
        error = TaskValidationError(message=message, errors=errors)

        # Then
        assert error.errors == errors
        assert len(error.errors) == 3
        assert error.details["errors"] == errors

    def test_create_validation_error_with_all_parameters(self):
        """
        [TEST-EXC-008] 测试创建带所有参数的验证错误

        Given: 错误消息、字段、错误列表和额外详情
        When: 创建TaskValidationError
        Then: 所有参数都应该被正确存储
        """
        # Given
        message = "完整验证错误"
        field = "page_num"
        errors = ["页数无效"]
        extra_details = {"min": 1, "max": 100, "actual": 0}

        # When
        error = TaskValidationError(
            message=message,
            field=field,
            errors=errors,
            details=extra_details
        )

        # Then
        assert error.field == field
        assert error.errors == errors
        assert error.details["field"] == field
        assert error.details["errors"] == errors
        assert error.details["min"] == 1
        assert error.details["max"] == 100
        assert error.details["actual"] == 0

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p0
class TestInvalidTaskStateError:
    """InvalidTaskStateError 测试"""

    def test_create_invalid_state_error(self):
        """
        [TEST-EXC-009] 测试创建InvalidTaskStateError

        Given: 错误消息
        When: 创建InvalidTaskStateError
        Then: 消息应该被正确设置
        """
        # Given
        message = "任务状态无效"

        # When
        error = InvalidTaskStateError(message=message)

        # Then
        assert str(error) == message

    def test_create_with_task_id(self):
        """
        [TEST-EXC-010] 测试创建带任务ID的状态错误

        Given: 错误消息和任务ID
        When: 创建InvalidTaskStateError
        Then: 任务ID应该被存储在详情中
        """
        # Given
        message = "任务状态无效"
        task_id = "task_001"

        # When
        error = InvalidTaskStateError(message=message, task_id=task_id)

        # Then
        assert error.details["task_id"] == task_id

    def test_create_with_current_and_expected_status(self):
        """
        [TEST-EXC-011] 测试创建带当前和期望状态的错误

        Given: 错误消息和状态信息
        When: 创建InvalidTaskStateError
        Then: 状态信息应该被正确存储
        """
        # Given
        message = "状态不匹配"
        current_status = "pending"
        expected_status = "in_progress"

        # When
        error = InvalidTaskStateError(
            message=message,
            task_id="task_001",
            current_status=current_status,
            expected_status=expected_status
        )

        # Then
        assert error.details["current_status"] == current_status
        assert error.details["expected_status"] == expected_status
        assert error.details["task_id"] == "task_001"

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p0
class TestTaskTransitionError:
    """TaskTransitionError 测试"""

    def test_create_transition_error(self):
        """
        [TEST-EXC-012] 测试创建TaskTransitionError

        Given: 错误消息
        When: 创建TaskTransitionError
        Then: 消息应该被正确设置
        """
        # Given
        message = "无效的状态转换"

        # When
        error = TaskTransitionError(message=message)

        # Then
        assert str(error) == message

    def test_create_with_states(self):
        """
        [TEST-EXC-013] 测试创建带状态信息的转换错误

        Given: 当前状态和目标状态
        When: 创建TaskTransitionError
        Then: 状态信息应该被正确存储
        """
        # Given
        message = "不能从完成状态转换到待处理"
        current_state = "completed"
        target_state = "pending"

        # When
        error = TaskTransitionError(
            message=message,
            current_state=current_state,
            target_state=target_state
        )

        # Then
        assert error.details["current_state"] == current_state
        assert error.details["target_state"] == target_state

    def test_transition_error_message_contains_states(self):
        """
        [TEST-EXC-014] 测试转换错误消息包含状态信息

        Given: 当前状态和目标状态
        When: 创建TaskTransitionError
        Then: 消息应该描述转换
        """
        # Given
        current = "completed"
        target = "pending"

        # When
        error = TaskTransitionError(
            message=f"Invalid transition from {current} to {target}",
            current_state=current,
            target_state=target
        )

        # Then
        assert current in str(error)
        assert target in str(error)

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p1
class TestBackwardCompatibleAliases:
    """向后兼容别名测试"""

    def test_validation_error_is_task_validation_error(self):
        """
        [TEST-EXC-015] 测试ValidationError是TaskValidationError的别名

        Given: ValidationError类
        When: 检查继承关系
        Then: ValidationError应该是TaskValidationError的子类
        """
        # Then - ValidationError是TaskValidationError的子类（别名方式）
        # 注意：别名定义为子类，所以使用issubclass而不是==
        assert issubclass(ValidationError, TaskValidationError)
        assert issubclass(ValidationError, DomainError)

    def test_invalid_state_transition_error_is_task_transition_error(self):
        """
        [TEST-EXC-016] 测试InvalidStateTransitionError是TaskTransitionError的别名

        Given: InvalidStateTransitionError类
        When: 检查继承关系
        Then: InvalidStateTransitionError应该是TaskTransitionError的子类
        """
        # Then - InvalidStateTransitionError是TaskTransitionError的子类（别名方式）
        # 注意：别名定义为子类，所以使用issubclass而不是==
        assert issubclass(InvalidStateTransitionError, TaskTransitionError)
        assert issubclass(InvalidStateTransitionError, DomainError)

    def test_validation_error_has_same_attributes(self):
        """
        [TEST-EXC-017] 测试ValidationError具有相同属性

        Given: 使用ValidationError创建异常
        When: 访问属性
        Then: 应该与TaskValidationError相同
        """
        # Given
        field = "page_num"
        errors = ["错误1", "错误2"]

        # When
        error = ValidationError(
            message="验证失败",
            field=field,
            errors=errors
        )

        # Then
        assert error.field == field
        assert error.errors == errors
        assert isinstance(error, TaskValidationError)

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p1
class TestExceptionInheritance:
    """异常继承测试"""

    def test_all_exceptions_inherit_from_domain_error(self):
        """
        [TEST-EXC-018] 测试所有异常继承自DomainError

        Given: 所有领域异常类
        When: 检查继承关系
        Then: 所有都应该继承自DomainError
        """
        # Then
        assert issubclass(TaskNotFoundException, DomainError)
        assert issubclass(TaskValidationError, DomainError)
        assert issubclass(InvalidTaskStateError, DomainError)
        assert issubclass(TaskTransitionError, DomainError)

    def test_all_exceptions_are_exceptions(self):
        """
        [TEST-EXC-019] 测试所有异常都是Exception子类

        Given: 所有领域异常类
        When: 检查是否可以抛出
        Then: 所有都应该可以作为异常抛出
        """
        # Then - 验证可以抛出和捕获
        with pytest.raises(DomainError):
            raise TaskNotFoundException(task_id="test")

        with pytest.raises(DomainError):
            raise TaskValidationError(message="验证失败")

        with pytest.raises(DomainError):
            raise InvalidTaskStateError(message="状态错误")

        with pytest.raises(DomainError):
            raise TaskTransitionError(message="转换错误")

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p2
class TestExceptionDetails:
    """异常详情测试"""

    def test_error_details_can_be_extended(self):
        """
        [TEST-EXC-020] 测试异常详情可以扩展

        Given: 基础异常
        When: 添加额外详情
        Then: 详情应该被合并
        """
        # Given
        base_details = {"task_id": "task_001"}
        extra_details = {"retry_count": 3, "last_error": "timeout"}

        # When
        error = TaskNotFoundException(
            task_id="task_001",
            details=extra_details
        )

        # Then
        assert error.details["task_id"] == "task_001"
        assert error.details["retry_count"] == 3
        assert error.details["last_error"] == "timeout"

    def test_error_details_include_all_context(self):
        """
        [TEST-EXC-021] 测试错误详情包含所有上下文

        Given: 创建一个验证错误
        When: 包含多个上下文字段
        Then: 所有字段都应该在details中
        """
        # Given
        error = TaskValidationError(
            message="完整验证错误",
            field="page_num",
            errors=["错误1", "错误2"],
            details={"min": 1, "max": 100}
        )

        # Then
        assert "field" in error.details
        assert "errors" in error.details
        assert "min" in error.details
        assert "max" in error.details
        assert len(error.details) == 4  # field, errors, min, max

@pytest.mark.domain
@pytest.mark.unit
@pytest.mark.p1
class TestExceptionMessaging:
    """异常消息测试"""

    def test_exception_message_is_clear(self):
        """
        [TEST-EXC-022] 测试异常消息清晰

        Given: 不同类型的异常
        When: 获取消息字符串
        Then: 消息应该描述问题
        """
        # Then
        not_found = TaskNotFoundException(task_id="missing_task")
        assert "not found" in str(not_found).lower()
        assert "missing_task" in str(not_found)

        validation = TaskValidationError(
            message="验证失败",
            field="page_num",
            errors=["页数无效"]
        )
        assert "验证失败" in str(validation)

        transition = TaskTransitionError(
            message="无效转换",
            current_state="completed",
            target_state="pending"
        )
        assert "无效转换" in str(transition)

    def test_exception_can_be_raised_and_caught(self):
        """
        [TEST-EXC-023] 测试异常可以抛出和捕获

        Given: 各种领域异常
        When: 抛出并捕获
        Then: 应该正确处理
        """
        # Then - 测试每种异常类型
        exceptions_to_test = [
            TaskNotFoundException(task_id="test"),
            TaskValidationError(message="验证失败"),
            InvalidTaskStateError(message="状态错误"),
            TaskTransitionError(message="转换错误")
        ]

        for exc in exceptions_to_test:
            with pytest.raises(DomainError):
                raise exc

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
