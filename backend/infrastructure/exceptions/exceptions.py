"""
统一的异常定义

只保留实际使用的异常，遵循 YAGNI 原则。
"""

from typing import Optional, Dict, Any


class BaseAPIException(Exception):
    """
    基础 API 异常

    所有自定义 API 异常的基类，提供统一的错误响应格式。
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "status_code": self.status_code,
        }


class RateLimitExceededException(BaseAPIException):
    """
    限流异常

    当API请求频率超过限制时抛出。
    """

    def __init__(self, limit: int | str = None, window: int = None):
        if isinstance(limit, str) and window is None:
            message = limit
        elif limit is not None and window is not None:
            message = f"请求频率超过限制：{limit} 次/{window} 秒"
        else:
            message = "请求频率超过限制"
        super().__init__(message, status_code=429, error_code="RATE_LIMIT_EXCEEDED")
