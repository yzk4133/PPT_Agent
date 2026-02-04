"""
HTTP 异常类

HTTP exceptions for API layer.
"""

from typing import Optional, Any, Dict

class HTTPException(Exception):
    """基础HTTP异常"""

    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str = None,
        details: Dict[str, Any] = None
    ):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status_code": self.status_code,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }

    def __str__(self) -> str:
        return self.message

class NotFoundError(HTTPException):
    """404 Not Found"""

    def __init__(self, resource: str = None, resource_id: str = None, message: str = "资源未找到"):
        if resource and resource_id:
            message = f"{resource}未找到: {resource_id}"
        elif resource:
            message = f"{resource}未找到"
        super().__init__(
            status_code=404,
            message=message,
            error_code="NOT_FOUND",
            details={"resource": resource, "resource_id": resource_id}
        )

class BadRequestError(HTTPException):
    """400 Bad Request"""

    def __init__(
        self,
        message: str = "请求参数无效",
        field: str = None,
        errors: list = None,
        details: Dict[str, Any] = None
    ):
        details = details or {}
        if field:
            details["field"] = field
        if errors:
            details["errors"] = errors

        super().__init__(
            status_code=400,
            message=message,
            error_code="BAD_REQUEST",
            details=details
        )

class UnauthorizedError(HTTPException):
    """401 Unauthorized"""

    def __init__(self, message: str = "未授权访问"):
        super().__init__(
            status_code=401,
            message=message,
            error_code="UNAUTHORIZED"
        )

class ForbiddenError(HTTPException):
    """403 Forbidden"""

    def __init__(self, message: str = "无权限访问"):
        super().__init__(
            status_code=403,
            message=message,
            error_code="FORBIDDEN"
        )

class ConflictError(HTTPException):
    """409 Conflict"""

    def __init__(self, message: str = "资源冲突", details: Dict[str, Any] = None):
        super().__init__(
            status_code=409,
            message=message,
            error_code="CONFLICT",
            details=details
        )

class UnprocessableEntityError(HTTPException):
    """422 Unprocessable Entity"""

    def __init__(self, message: str = "无法处理的实体", details: Dict[str, Any] = None):
        super().__init__(
            status_code=422,
            message=message,
            error_code="UNPROCESSABLE_ENTITY",
            details=details
        )

class TooManyRequestsError(HTTPException):
    """429 Too Many Requests"""

    def __init__(self, message: str = "请求过于频繁", retry_after: int = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            status_code=429,
            message=message,
            error_code="TOO_MANY_REQUESTS",
            details=details
        )

class InternalServerError(HTTPException):
    """500 Internal Server Error"""

    def __init__(self, message: str = "服务器内部错误", details: Dict[str, Any] = None):
        super().__init__(
            status_code=500,
            message=message,
            error_code="INTERNAL_SERVER_ERROR",
            details=details
        )

class ServiceUnavailableError(HTTPException):
    """503 Service Unavailable"""

    def __init__(self, message: str = "服务暂时不可用", details: Dict[str, Any] = None):
        super().__init__(
            status_code=503,
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            details=details
        )
