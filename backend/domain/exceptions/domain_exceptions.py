"""
Domain Exception Classes

Custom exceptions for domain-specific errors.
"""

from typing import Optional, List, Dict, Any
from .base_exceptions import BaseApplicationError
import logging

logger = logging.getLogger(__name__)

class DomainError(BaseApplicationError):
    """
    Base domain exception

    All domain-specific exceptions should inherit from this class.
    """
    pass

class TaskNotFoundException(DomainError):
    """
    Task not found exception

    Raised when a requested task does not exist.
    """

    def __init__(self, task_id: str, **kwargs):
        # 合并details，允许扩展
        details = kwargs.pop("details", {})
        details["task_id"] = task_id

        super().__init__(
            message=f"Task not found: {task_id}",
            details=details,
            **kwargs
        )
        self.task_id = task_id

class TaskValidationError(DomainError):
    """
    Task validation failed

    Raised when task data validation fails.
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        errors: Optional[List[str]] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if field:
            details["field"] = field
        if errors:
            details["errors"] = errors
        super().__init__(message, details=details, **kwargs)
        self.field = field
        self.errors = errors or []

class InvalidTaskStateError(DomainError):
    """
    Invalid task state

    Raised when a task is in an invalid state for the requested operation.
    """

    def __init__(
        self,
        message: str,
        task_id: Optional[str] = None,
        current_status: Optional[str] = None,
        expected_status: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if task_id:
            details["task_id"] = task_id
        if current_status:
            details["current_status"] = current_status
        if expected_status:
            details["expected_status"] = expected_status
        super().__init__(message, details=details, **kwargs)

class TaskTransitionError(DomainError):
    """
    Invalid task state transition

    Raised when an invalid state transition is attempted.
    """

    def __init__(
        self,
        message: str,
        current_state: Optional[str] = None,
        target_state: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if current_state:
            details["current_state"] = current_state
        if target_state:
            details["target_state"] = target_state
        super().__init__(message, details=details, **kwargs)

# ========================================================================
# Agent 相关异常
# ========================================================================

class AgentNotFoundException(DomainError):
    """Agent not found"""

    def __init__(self, agent_name: str, **kwargs):
        super().__init__(
            message=f"Agent not found: {agent_name}",
            details={"agent_name": agent_name},
            **kwargs
        )
        self.agent_name = agent_name

class AgentExecutionError(DomainError):
    """Agent execution failed"""

    def __init__(
        self,
        message: str,
        agent_name: Optional[str] = None,
        stage: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if agent_name:
            details["agent_name"] = agent_name
        if stage:
            details["stage"] = stage
        super().__init__(message, details=details, **kwargs)

class AgentTimeoutError(DomainError):
    """Agent execution timeout"""

    def __init__(
        self,
        message: str = "Agent execution timeout",
        agent_name: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if agent_name:
            details["agent_name"] = agent_name
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        super().__init__(message, details=details, **kwargs)

# ========================================================================
# Presentation 相关异常
# ========================================================================

class PresentationNotFoundException(DomainError):
    """Presentation not found"""

    def __init__(self, presentation_id: str, **kwargs):
        super().__init__(
            message=f"Presentation not found: {presentation_id}",
            details={"presentation_id": presentation_id},
            **kwargs
        )
        self.presentation_id = presentation_id

class PresentationGenerationError(DomainError):
    """Presentation generation failed"""

    def __init__(
        self,
        message: str,
        stage: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if stage:
            details["stage"] = stage
        super().__init__(message, details=details, **kwargs)

# ========================================================================
# 内存相关异常
# ========================================================================

class MemoryQuotaExceededError(DomainError):
    """Memory quota exceeded"""

    def __init__(
        self,
        message: str = "Memory quota exceeded",
        quota: Optional[int] = None,
        current_usage: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if quota:
            details["quota"] = quota
        if current_usage:
            details["current_usage"] = current_usage
        super().__init__(message, details=details, **kwargs)

class MemoryOperationError(DomainError):
    """Memory operation failed"""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if operation:
            details["operation"] = operation
        super().__init__(message, details=details, **kwargs)

# ========================================================================
# 向后兼容的别名
# ========================================================================

class ValidationError(TaskValidationError):
    """向后兼容的验证错误别名"""
    pass

class InvalidStateTransitionError(TaskTransitionError):
    """向后兼容的状态转换错误别名"""
    pass

class InvalidTaskError(InvalidTaskStateError):
    """向后兼容的任务错误别名"""
    pass

class TaskNotFoundError(TaskNotFoundException):
    """向后兼容的任务未找到错误别名"""
    pass

class RequirementValidationError(ValidationError):
    """Requirement validation failed"""
    pass

class FrameworkValidationError(ValidationError):
    """Framework validation failed"""
    pass

class ResearchValidationError(ValidationError):
    """Research result validation failed"""
    pass

# ========================================================================
# PPT 生成相关业务异常
# ========================================================================

class PPTGenerationError(DomainError):
    """
    PPT generation failed

    Raised when PPT generation encounters a business logic error.
    """

    def __init__(
        self,
        message: str,
        stage: Optional[str] = None,
        task_id: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if stage:
            details["stage"] = stage
        if task_id:
            details["task_id"] = task_id
        super().__init__(message, details=details, **kwargs)

class OutlineGenerationError(PPTGenerationError):
    """Outline generation failed"""

    def __init__(self, message: str = "大纲生成失败", task_id: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        details["phase"] = "outline"
        if task_id:
            details["task_id"] = task_id
        super().__init__(message, stage="outline", details=details, **kwargs)

class SlideGenerationError(PPTGenerationError):
    """Slide generation failed"""

    def __init__(self, message: str = "幻灯片生成失败", task_id: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        details["phase"] = "slides"
        if task_id:
            details["task_id"] = task_id
        super().__init__(message, stage="slides", details=details, **kwargs)

class TaskExpiredError(DomainError):
    """
    Task has expired

    Raised when attempting to operate on an expired task.
    """

    def __init__(self, task_id: Optional[str] = None, **kwargs):
        message = "任务已过期"
        details = kwargs.pop("details", {})
        if task_id:
            message += f": {task_id}"
            details["task_id"] = task_id
        super().__init__(message, details=details, **kwargs)
        self.task_id = task_id

