"""
认证技术异常类

用于infrastructure层内部的认证技术实现，如Token验证、凭证检查等。
注意：这些是infrastructure层的技术异常，不是HTTP响应异常。
"""

from .base import BaseAPIException

class InvalidTokenException(BaseAPIException):
    """Token验证失败（技术验证）"""
    def __init__(self, reason: str = "Token 无效或已过期"):
        super().__init__(
            f"无效的访问令牌: {reason}",
            status_code=401,
            error_code="INVALID_TOKEN"
        )

class InvalidCredentialsException(BaseAPIException):
    """凭证验证失败（技术验证）"""
    def __init__(self):
        super().__init__(
            "用户名或密码错误",
            status_code=401,
            error_code="INVALID_CREDENTIALS"
        )

class TokenExpiredException(BaseAPIException):
    """Token已过期（技术验证）"""
    def __init__(self):
        super().__init__(
            "访问令牌已过期，请重新登录",
            status_code=401,
            error_code="TOKEN_EXPIRED"
        )

class PasswordFormatException(BaseAPIException):
    """密码格式不符合要求（技术验证）"""
    def __init__(self, reason: str = "密码格式不符合要求"):
        super().__init__(
            reason,
            status_code=422,
            error_code="PASSWORD_FORMAT_INVALID"
        )

class UserAlreadyExistsException(BaseAPIException):
    """用户已存在（技术验证）"""
    def __init__(self, identifier: str = "用户已存在"):
        super().__init__(
            f"用户已存在: {identifier}",
            status_code=409,
            error_code="USER_ALREADY_EXISTS"
        )

class UserInactiveException(BaseAPIException):
    """用户未激活（技术验证）"""
    def __init__(self):
        super().__init__(
            "用户账户未激活",
            status_code=403,
            error_code="USER_INACTIVE"
        )

class AuthorizationException(BaseAPIException):
    """授权失败（技术验证）"""
    def __init__(self, reason: str = "权限不足"):
        super().__init__(
            f"授权失败: {reason}",
            status_code=403,
            error_code="AUTHORIZATION_FAILED"
        )
