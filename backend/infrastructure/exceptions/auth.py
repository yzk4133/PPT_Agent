"""
认证相关异常
"""

from .base import BaseAPIException


class AuthenticationException(BaseAPIException):
    """认证失败异常"""
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, status_code=401, error_code="AUTHENTICATION_FAILED")


class InvalidTokenException(AuthenticationException):
    """无效 Token 异常"""
    def __init__(self, reason: str = "Token 无效或已过期"):
        super().__init__(f"无效的访问令牌: {reason}")


class InvalidCredentialsException(AuthenticationException):
    """无效凭证异常"""
    def __init__(self):
        super().__init__("用户名或密码错误")


class TokenExpiredException(AuthenticationException):
    """Token 过期异常"""
    def __init__(self):
        super().__init__("访问令牌已过期，请重新登录")


class AuthorizationException(BaseAPIException):
    """授权失败异常"""
    def __init__(self, required_permission: str = None):
        message = "权限不足"
        if required_permission:
            message += f"，需要权限: {required_permission}"
        super().__init__(message, status_code=403, error_code="AUTHORIZATION_FAILED")


class UserAlreadyExistsException(BaseAPIException):
    """用户已存在异常"""
    def __init__(self, email: str = None):
        message = "用户已存在"
        if email:
            message += f": {email}"
        super().__init__(message, status_code=409, error_code="USER_ALREADY_EXISTS")


class UserInactiveException(AuthenticationException):
    """用户未激活异常"""
    def __init__(self):
        super().__init__("用户账户已被禁用")


class UserNotFoundException(BaseAPIException):
    """用户不存在异常"""
    def __init__(self, identifier: str = None):
        message = "用户不存在"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, status_code=404, error_code="USER_NOT_FOUND")
