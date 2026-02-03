"""
业务异常类
"""

from .base import BaseAPIException, ValidationException


class PPTGenerationException(BaseAPIException):
    """PPT 生成异常"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=400, error_code="PPT_GENERATION_ERROR", details=details)


class OutlineGenerationException(PPTGenerationException):
    """大纲生成异常"""
    def __init__(self, message: str = "大纲生成失败"):
        super().__init__(message, details={"phase": "outline"})


class SlideGenerationException(PPTGenerationException):
    """幻灯片生成异常"""
    def __init__(self, message: str = "幻灯片生成失败"):
        super().__init__(message, details={"phase": "slides"})


class TaskNotFoundException(BaseAPIException):
    """任务未找到异常"""
    def __init__(self, task_id: str = None):
        message = "任务未找到"
        if task_id:
            message += f": {task_id}"
        super().__init__(message, status_code=404, error_code="TASK_NOT_FOUND")


class TaskExpiredException(BaseAPIException):
    """任务已过期异常"""
    def __init__(self, task_id: str = None):
        message = "任务已过期"
        if task_id:
            message += f": {task_id}"
        super().__init__(message, status_code=410, error_code="TASK_EXPIRED")


class InvalidParameterException(ValidationException):
    """无效参数异常"""
    def __init__(self, parameter: str, reason: str = None):
        message = f"无效的参数: {parameter}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, field=parameter)


class ExternalServiceException(BaseAPIException):
    """外部服务异常"""
    def __init__(self, service: str, message: str = "外部服务调用失败"):
        super().__init__(
            f"{service}: {message}",
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service}
        )


class LLMServiceException(ExternalServiceException):
    """LLM 服务异常"""
    def __init__(self, provider: str, message: str = "LLM 服务调用失败"):
        super().__init__(f"LLM ({provider})", message)


class DatabaseException(BaseAPIException):
    """数据库异常"""
    def __init__(self, message: str = "数据库操作失败"):
        super().__init__(message, status_code=500, error_code="DATABASE_ERROR")


class CacheException(BaseAPIException):
    """缓存异常"""
    def __init__(self, message: str = "缓存操作失败"):
        super().__init__(message, status_code=500, error_code="CACHE_ERROR")
