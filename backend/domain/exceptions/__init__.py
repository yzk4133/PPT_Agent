"""
Domain Exceptions

Provides custom exceptions for domain-specific errors.
"""

from .domain_exceptions import (
    DomainError,
    ValidationError,
    InvalidStateTransitionError,
    InvalidTaskError,
    TaskNotFoundError,
)

__all__ = [
    "DomainError",
    "ValidationError",
    "InvalidStateTransitionError",
    "InvalidTaskError",
    "TaskNotFoundError",
]
