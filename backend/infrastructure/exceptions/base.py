"""
业务异常类体系
"""

from typing import Optional, Dict, Any

class BaseAPIException(Exception):
    """基础 API 异常"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "status_code": self.status_code
        }

class BusinessException(BaseAPIException):
    """业务逻辑异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, error_code="BUSINESS_ERROR", details=details)

class ValidationException(BaseAPIException):
    """输入验证异常"""
    def __init__(self, message: str, field: str = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if field:
            details["field"] = field
        super().__init__(message, status_code=422, error_code="VALIDATION_ERROR", details=details)

class ResourceNotFoundException(BaseAPIException):
    """资源未找到异常"""
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} 未找到"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, status_code=404, error_code="NOT_FOUND")

class RateLimitExceededException(BaseAPIException):
    """限流异常"""
    def __init__(self, limit: int, window: int):
        message = f"请求频率超过限制：{limit} 次/{window} 秒"
        super().__init__(message, status_code=429, error_code="RATE_LIMIT_EXCEEDED")

class ConflictException(BaseAPIException):
    """资源冲突异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=409, error_code="CONFLICT", details=details)
