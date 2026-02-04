"""
Domain Exceptions

Provides custom exceptions for domain-specific errors.

注意：Domain层只包含业务逻辑异常，不包含基础设施或API异常。
- 技术异常请使用: infrastructure.exceptions
- HTTP异常请使用: api.exceptions
"""

from .base_exceptions import (
    BaseApplicationError,
    RecoverableError,
    CriticalError,
)

from .domain_exceptions import (
    # Base
    DomainError,

    # Task相关
    TaskNotFoundException,
    TaskValidationError,
    InvalidTaskStateError,
    TaskTransitionError,

    # Agent相关
    AgentNotFoundException,
    AgentExecutionError,
    AgentTimeoutError,

    # Presentation相关
    PresentationNotFoundException,
    PresentationGenerationError,

    # 内存相关
    MemoryQuotaExceededError,
    MemoryOperationError,

    # PPT生成相关
    PPTGenerationError,
    OutlineGenerationError,
    SlideGenerationError,
    TaskExpiredError,

    # 向后兼容的别名
    ValidationError,
    InvalidStateTransitionError,
    InvalidTaskError,
    TaskNotFoundError,
    RequirementValidationError,
    FrameworkValidationError,
    ResearchValidationError,
)

__all__ = [
    # Base
    "BaseApplicationError",
    "RecoverableError",
    "CriticalError",
    "DomainError",

    # Task
    "TaskNotFoundException",
    "TaskValidationError",
    "InvalidTaskStateError",
    "TaskTransitionError",
    "TaskExpiredError",

    # Agent
    "AgentNotFoundException",
    "AgentExecutionError",
    "AgentTimeoutError",

    # Presentation
    "PresentationNotFoundException",
    "PresentationGenerationError",

    # Memory
    "MemoryQuotaExceededError",
    "MemoryOperationError",

    # PPT Generation
    "PPTGenerationError",
    "OutlineGenerationError",
    "SlideGenerationError",

    # 向后兼容
    "ValidationError",
    "InvalidStateTransitionError",
    "InvalidTaskError",
    "TaskNotFoundError",
    "RequirementValidationError",
    "FrameworkValidationError",
    "ResearchValidationError",
]

