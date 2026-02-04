"""
技术异常类

Technical exceptions for infrastructure layer.
"""

from typing import Optional, Dict, Any
from .base import BaseAPIException

class BaseInfrastructureError(BaseAPIException):
    """
    Base infrastructure exception

    All infrastructure/technical exceptions should inherit from this class.
    """
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            status_code=500,
            error_code="INFRASTRUCTURE_ERROR",
            details=details,
            **kwargs
        )

class DatabaseConnectionError(BaseInfrastructureError):
    """数据库连接失败"""
    def __init__(self, message: str = "数据库连接失败", details: dict = None):
        super().__init__(
            message=message,
            details=details or {}
        )

class LLMAPIError(BaseInfrastructureError):
    """LLM API调用失败"""
    def __init__(self, provider: str, message: str = "LLM服务调用失败", details: dict = None):
        super().__init__(
            message=f"{provider}: {message}",
            details=details or {"provider": provider}
        )

class CacheMissError(BaseInfrastructureError):
    """缓存未命中"""
    def __init__(self, key: str = None, message: str = "缓存未命中"):
        if key:
            message = f"缓存未命中: {key}"
        super().__init__(message, details={"key": key} if key else {})

class FileSystemError(BaseInfrastructureError):
    """文件系统错误"""
    def __init__(self, path: str = None, message: str = "文件操作失败"):
        if path:
            message = f"文件操作失败: {path}"
        super().__init__(message, details={"path": path})

class MCPTimeoutError(BaseInfrastructureError):
    """MCP工具超时"""
    def __init__(self, tool_name: str, timeout_seconds: int = None, message: str = "MCP工具超时"):
        details = {"tool_name": tool_name}
        if timeout_seconds:
            details["timeout"] = timeout_seconds
        super().__init__(message, details=details)

class MCPConnectionError(BaseInfrastructureError):
    """MCP连接失败"""
    def __init__(self, tool_name: str, reason: str = "连接失败"):
        super().__init__(
            message=f"MCP工具连接失败: {tool_name}",
            details={"tool_name": tool_name, "reason": reason}
        )

class ConfigurationError(BaseInfrastructureError):
    """配置错误"""
    def __init__(self, config_file: str = None, message: str = "配置错误"):
        if config_file:
            message = f"配置文件错误: {config_file}"
        super().__init__(message, details={"config_file": config_file})

class RetryExhaustedError(BaseInfrastructureError):
    """重试次数耗尽"""
    def __init__(self, operation: str = "", max_retries: int = 3, message: str = "重试次数耗尽"):
        if operation:
            message = f"{operation} {message}"
        super().__init__(
            message,
            details={"operation": operation, "max_retries": max_retries}
        )
