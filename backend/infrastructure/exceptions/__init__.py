"""
异常类模块

提供基础设施层的异常处理体系，包括：
- 基础异常类
- 认证技术异常（infrastructure内部使用）
- 验证技术异常（infrastructure内部使用）
- 技术异常

职责说明：
- 这些异常用于infrastructure层的内部模块之间通信
- 不包含业务逻辑（业务异常在 domain/exceptions/）
- 主要用于技术验证（Token格式、密码强度等）
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
    InvalidTokenException,
    InvalidCredentialsException,
    TokenExpiredException,
    PasswordFormatException,
    UserAlreadyExistsException,
    UserInactiveException,
    AuthorizationException,
)

from .validation import (
    PasswordValidationException,
    TokenValidationException,
    EmailValidationException,
    UsernameValidationException,
    MissingRequiredFieldException,
    InvalidDateFormatException,
    InvalidEnumException,
    FileValidationException,
    FileSizeException,
    FileFormatException,
)

from .technical import (
    BaseInfrastructureError,
    DatabaseConnectionError,
    LLMAPIError,
    CacheMissError,
    FileSystemError,
    MCPTimeoutError,
    MCPConnectionError,
    ConfigurationError,
    RetryExhaustedError
)

# Alias for backward compatibility
AuthenticationException = InvalidCredentialsException

__all__ = [
    # Base exceptions
    "BaseAPIException",
    "BusinessException",
    "ValidationException",
    "ResourceNotFoundException",
    "RateLimitExceededException",
    "ConflictException",

    # Auth technical exceptions (infrastructure internal)
    "InvalidTokenException",
    "InvalidCredentialsException",
    "TokenExpiredException",
    "PasswordFormatException",
    "UserAlreadyExistsException",
    "UserInactiveException",
    "AuthorizationException",

    # Validation technical exceptions (infrastructure internal)
    "PasswordValidationException",
    "TokenValidationException",
    "EmailValidationException",
    "UsernameValidationException",
    "MissingRequiredFieldException",
    "InvalidDateFormatException",
    "InvalidEnumException",
    "FileValidationException",
    "FileSizeException",
    "FileFormatException",

    # Technical exceptions (Infrastructure)
    "BaseInfrastructureError",
    "DatabaseConnectionError",
    "LLMAPIError",
    "CacheMissError",
    "FileSystemError",
    "MCPTimeoutError",
    "MCPConnectionError",
    "ConfigurationError",
    "RetryExhaustedError",

    # Alias
    "AuthenticationException",
]
