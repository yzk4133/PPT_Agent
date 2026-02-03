"""
异常类模块

提供统一的异常处理体系，包括：
- 基础异常类
- 认证相关异常
- 业务异常
- 验证异常
"""

from .base import (
    BaseAPIException,
    BusinessException,
    ValidationException,
    ResourceNotFoundException,
    RateLimitExceededException,
    ConflictException
)

from .auth import (
    AuthenticationException,
    InvalidTokenException,
    InvalidCredentialsException,
    TokenExpiredException,
    AuthorizationException,
    UserAlreadyExistsException,
    UserInactiveException,
    UserNotFoundException
)

from .business import (
    PPTGenerationException,
    OutlineGenerationException,
    SlideGenerationException,
    TaskNotFoundException,
    TaskExpiredException,
    InvalidParameterException,
    ExternalServiceException,
    LLMServiceException,
    DatabaseException,
    CacheException
)

from .validation import (
    EmailValidationException,
    PasswordValidationException,
    UsernameValidationException,
    MissingRequiredFieldException,
    InvalidDateFormatException,
    InvalidEnumException,
    FileValidationException,
    FileSizeException,
    FileFormatException
)


__all__ = [
    # Base exceptions
    "BaseAPIException",
    "BusinessException",
    "ValidationException",
    "ResourceNotFoundException",
    "RateLimitExceededException",
    "ConflictException",

    # Auth exceptions
    "AuthenticationException",
    "InvalidTokenException",
    "InvalidCredentialsException",
    "TokenExpiredException",
    "AuthorizationException",
    "UserAlreadyExistsException",
    "UserInactiveException",
    "UserNotFoundException",

    # Business exceptions
    "PPTGenerationException",
    "OutlineGenerationException",
    "SlideGenerationException",
    "TaskNotFoundException",
    "TaskExpiredException",
    "InvalidParameterException",
    "ExternalServiceException",
    "LLMServiceException",
    "DatabaseException",
    "CacheException",

    # Validation exceptions
    "EmailValidationException",
    "PasswordValidationException",
    "UsernameValidationException",
    "MissingRequiredFieldException",
    "InvalidDateFormatException",
    "InvalidEnumException",
    "FileValidationException",
    "FileSizeException",
    "FileFormatException",
]
