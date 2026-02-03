"""
输入验证异常类
"""

from .base import ValidationException


class EmailValidationException(ValidationException):
    """邮箱验证异常"""
    def __init__(self, email: str = None):
        message = "邮箱格式不正确"
        if email:
            message += f": {email}"
        super().__init__(message, field="email")


class PasswordValidationException(ValidationException):
    """密码验证异常"""
    def __init__(self, reason: str = "密码格式不正确"):
        super().__init__(reason, field="password")


class UsernameValidationException(ValidationException):
    """用户名验证异常"""
    def __init__(self, username: str = None, reason: str = "用户名格式不正确"):
        message = reason
        if username:
            message = f"{reason}: {username}"
        super().__init__(message, field="username")


class MissingRequiredFieldException(ValidationException):
    """缺少必填字段异常"""
    def __init__(self, field: str):
        super().__init__(f"缺少必填字段: {field}", field=field)


class InvalidDateFormatException(ValidationException):
    """日期格式验证异常"""
    def __init__(self, field: str = None, format: str = None):
        message = "日期格式不正确"
        if format:
            message += f"，期望格式: {format}"
        super().__init__(message, field=field)


class InvalidEnumException(ValidationException):
    """枚举值验证异常"""
    def __init__(self, field: str, valid_values: list = None, actual_value: str = None):
        message = f"无效的枚举值"
        if actual_value:
            message += f": {actual_value}"
        if valid_values:
            message += f"，有效值: {', '.join(map(str, valid_values))}"
        super().__init__(message, field=field)


class FileValidationException(ValidationException):
    """文件验证异常"""
    def __init__(self, reason: str = "文件验证失败"):
        super().__init__(reason, field="file")


class FileSizeException(FileValidationException):
    """文件大小异常"""
    def __init__(self, max_size: str = None):
        message = "文件大小超过限制"
        if max_size:
            message += f" (最大: {max_size})"
        super().__init__(message)


class FileFormatException(FileValidationException):
    """文件格式异常"""
    def __init__(self, allowed_formats: list = None):
        message = "不支持的文件格式"
        if allowed_formats:
            message += f"，支持的格式: {', '.join(allowed_formats)}"
        super().__init__(message)
