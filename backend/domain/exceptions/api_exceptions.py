"""
[DEPRECATED] API Exceptions

⚠️ DEPRECATION NOTICE ⚠️

此文件已弃用！API异常已移至 api.exceptions 模块。

正确的导入方式:
    # 错误 (old):
    from domain.exceptions.api_exceptions import NotFoundError

    # 正确 (new):
    from api.exceptions import NotFoundError

此文件保留用于向后兼容，但将在未来版本中移除。

================================================================================

API Exceptions (Legacy)

API层异常，用于FastAPI错误处理
"""

import warnings
from typing import Optional, Dict, Any
from .base_exceptions import BaseApplicationError

# 发出弃用警告
warnings.warn(
    "domain.exceptions.api_exceptions is deprecated. "
    "Use 'api.exceptions' instead.",
    DeprecationWarning,
    stacklevel=2
)

# HTTP状态码映射
HTTP_STATUS_MAP = {
    "ValidationError": 422,
    "AuthenticationError": 401,
    "AuthorizationError": 403,
    "NotFoundError": 404,
    "ConflictError": 409,
    "RateLimitError": 429,
    "ServiceUnavailableError": 503,
}

class APIError(BaseApplicationError):
    """
    API异常基类

    所有API层异常的基类，自动映射到HTTP状态码
    """

    # 默认HTTP状态码（子类应覆盖）
    http_status_code: int = 500

    def __init__(
        self,
        message: str,
        http_status_code: Optional[int] = None,
        **kwargs
    ):
        if http_status_code:
            self.http_status_code = http_status_code
        super().__init__(message, **kwargs)

class ValidationError(APIError):
    """
    验证错误 (HTTP 422)

    请求参数验证失败
    """
    http_status_code = 422

    def __init__(
        self,
        message: str = "Validation failed",
        field: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if field:
            details["field"] = field
        super().__init__(message, details=details, **kwargs)

class AuthenticationError(APIError):
    """
    认证错误 (HTTP 401)

    用户未认证或认证失败
    """
    http_status_code = 401

    def __init__(
        self,
        message: str = "Authentication required",
        **kwargs
    ):
        super().__init__(message, **kwargs)

class AuthorizationError(APIError):
    """
    授权错误 (HTTP 403)

    用户无权限执行此操作
    """
    http_status_code = 403

    def __init__(
        self,
        message: str = "Permission denied",
        required_permission: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if required_permission:
            details["required_permission"] = required_permission
        super().__init__(message, details=details, **kwargs)

class NotFoundError(APIError):
    """
    资源未找到错误 (HTTP 404)

    请求的资源不存在
    """
    http_status_code = 404

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(message, details=details, **kwargs)

class ConflictError(APIError):
    """
    冲突错误 (HTTP 409)

    请求与当前状态冲突
    """
    http_status_code = 409

    def __init__(
        self,
        message: str = "Resource conflict",
        conflict_type: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if conflict_type:
            details["conflict_type"] = conflict_type
        super().__init__(message, details=details, **kwargs)

class RateLimitError(APIError):
    """
    速率限制错误 (HTTP 429)

    超过API调用速率限制
    """
    http_status_code = 429

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if retry_after is not None:
            details["retry_after_seconds"] = retry_after
        if limit is not None:
            details["limit"] = limit
        super().__init__(message, details=details, **kwargs)

class ServiceUnavailableError(APIError):
    """
    服务不可用错误 (HTTP 503)

    服务暂时不可用
    """
    http_status_code = 503

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        reason: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if reason:
            details["reason"] = reason
        super().__init__(message, details=details, **kwargs)

# ========================================================================
# 便捷函数
# ========================================================================

def exception_to_http_response(exception: BaseApplicationError) -> Dict[str, Any]:
    """
    将异常转换为HTTP响应格式

    Args:
        exception: 应用异常

    Returns:
        HTTP响应字典
    """
    status_code = 500

    if isinstance(exception, APIError):
        status_code = exception.http_status_code

    response_body = exception.to_dict()
    response_body["status_code"] = status_code

    return response_body

def get_http_status(exception: BaseApplicationError) -> int:
    """
    获取异常对应的HTTP状态码

    Args:
        exception: 应用异常

    Returns:
        HTTP状态码
    """
    if isinstance(exception, APIError):
        return exception.http_status_code

    # 从映射表查找
    code = HTTP_STATUS_MAP.get(exception.code)
    if code:
        return code

    # 默认500
    return 500
