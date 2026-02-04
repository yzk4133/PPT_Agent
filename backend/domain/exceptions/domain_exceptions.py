"""
Domain Exception Classes

Custom exceptions for domain-specific errors.
"""

from typing import Optional, List


class DomainError(Exception):
    """
    Base domain exception

    All domain-specific exceptions should inherit from this class.
    """

    def __init__(self, message: str, details: Optional[dict] = None):
        """
        Initialize domain error

        Args:
            message: Error message
            details: Additional error details (optional)
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class ValidationError(DomainError):
    """
    Validation failed

    Raised when domain model validation fails.
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        errors: Optional[List[str]] = None
    ):
        """
        Initialize validation error

        Args:
            message: Error message
            field: Field that failed validation (optional)
            errors: List of specific error messages (optional)
        """
        details = {}
        if field:
            details["field"] = field
        if errors:
            details["errors"] = errors

        super().__init__(message, details)
        self.field = field
        self.errors = errors or []


class InvalidStateTransitionError(DomainError):
    """
    Invalid state transition

    Raised when an invalid state transition is attempted.
    """

    def __init__(
        self,
        message: str,
        current_state: Optional[str] = None,
        target_state: Optional[str] = None
    ):
        """
        Initialize invalid state transition error

        Args:
            message: Error message
            current_state: Current state (optional)
            target_state: Target state that was attempted (optional)
        """
        details = {}
        if current_state:
            details["current_state"] = current_state
        if target_state:
            details["target_state"] = target_state

        super().__init__(message, details)
        self.current_state = current_state
        self.target_state = target_state


class InvalidTaskError(DomainError):
    """
    Invalid task state

    Raised when a task is in an invalid state for the requested operation.
    """

    def __init__(
        self,
        message: str,
        task_id: Optional[str] = None,
        current_status: Optional[str] = None
    ):
        """
        Initialize invalid task error

        Args:
            message: Error message
            task_id: Task ID (optional)
            current_status: Current task status (optional)
        """
        details = {}
        if task_id:
            details["task_id"] = task_id
        if current_status:
            details["current_status"] = current_status

        super().__init__(message, details)
        self.task_id = task_id
        self.current_status = current_status


class TaskNotFoundError(DomainError):
    """
    Task not found

    Raised when a requested task does not exist.
    """

    def __init__(self, task_id: str):
        """
        Initialize task not found error

        Args:
            task_id: Task ID that was not found
        """
        super().__init__(f"Task not found: {task_id}", {"task_id": task_id})
        self.task_id = task_id


class RequirementValidationError(ValidationError):
    """
    Requirement validation failed

    Raised when requirement data is invalid.
    """

    pass


class FrameworkValidationError(ValidationError):
    """
    Framework validation failed

    Raised when framework data is invalid.
    """

    pass


class ResearchValidationError(ValidationError):
    """
    Research result validation failed

    Raised when research result data is invalid.
    """

    pass
