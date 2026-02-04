"""
[DEPRECATED] Infrastructure Exceptions

⚠️ DEPRECATION NOTICE ⚠️

此文件已弃用！基础设施异常已移至 infrastructure.exceptions 模块。

正确的导入方式:
    # 错误 (old):
    from domain.exceptions import DatabaseError

    # 正确 (new):
    from infrastructure.exceptions import DatabaseConnectionError
    from infrastructure.exceptions import LLMAPIError

此文件保留用于向后兼容，但将在未来版本中移除。

================================================================================

Infrastructure Exceptions (Legacy)

基础设施层异常，包括数据库、LLM、缓存等
"""

import warnings
from typing import Optional, Dict, Any
from .base_exceptions import BaseApplicationError, RecoverableError
import logging

logger = logging.getLogger(__name__)

# 发出弃用警告
warnings.warn(
    "domain.exceptions.infrastructure_exceptions is deprecated. "
    "Use 'infrastructure.exceptions' instead.",
    DeprecationWarning,
    stacklevel=2
)

# ========================================================================
# 数据库异常
# ========================================================================

class DatabaseError(BaseApplicationError):
    """数据库异常基类"""
    pass

class DatabaseConnectionError(DatabaseError, RecoverableError):
    """
    数据库连接错误

    通常可以重试的连接失败
    """

    def __init__(
        self,
        message: str = "Database connection failed",
        host: Optional[str] = None,
        port: Optional[int] = None,
        **kwargs
    ):
        details = {}
        if host:
            details["host"] = host
        if port:
            details["port"] = port
        super().__init__(message, details=details, **kwargs)

class DatabaseOperationError(DatabaseError):
    """
    数据库操作错误

    执行SQL语句时发生的错误
    """

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None,
        query: Optional[str] = None,
        **kwargs
    ):
        details = {}
        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table
        if query:
            details["query"] = query[:200] + "..." if len(query) > 200 else query
        super().__init__(message, details=details, **kwargs)

class DatabaseQueryError(DatabaseOperationError):
    """数据库查询错误"""
    pass

class DatabaseTransactionError(DatabaseError):
    """数据库事务错误"""
    pass

# ========================================================================
# LLM 异常
# ========================================================================

class LLMError(BaseApplicationError):
    """LLM异常基类"""
    pass

class LLMProviderError(LLMError, RecoverableError):
    """
    LLM提供商错误

    LLM服务提供商返回的错误
    """

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ):
        details = {}
        if provider:
            details["provider"] = provider
        if model:
            details["model"] = model
        super().__init__(message, details=details, **kwargs)

class LLMRateLimitError(LLMProviderError):
    """
    LLM速率限制错误

    超过了API调用速率限制
    """

    def __init__(
        self,
        message: str = "LLM API rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if retry_after is not None:
            details["retry_after_seconds"] = retry_after
        super().__init__(message, details=details, **kwargs)

class LLMTimeoutError(LLMError, RecoverableError):
    """
    LLM超时错误

    LLM请求超时
    """

    def __init__(
        self,
        message: str = "LLM request timeout",
        timeout_seconds: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        super().__init__(message, details=details, **kwargs)

class LLMInvalidResponseError(LLMError):
    """
    LLM响应无效错误

    LLM返回了无效或无法解析的响应
    """

    def __init__(
        self,
        message: str = "Invalid LLM response",
        response_snippet: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if response_snippet:
            details["response_snippet"] = response_snippet[:500]
        super().__init__(message, details=details, **kwargs)

# ========================================================================
# 缓存异常
# ========================================================================

class CacheError(BaseApplicationError):
    """缓存异常基类"""
    pass

class CacheConnectionError(CacheError, RecoverableError):
    """
    缓存连接错误

    缓存服务连接失败
    """

    def __init__(
        self,
        message: str = "Cache connection failed",
        cache_type: Optional[str] = None,  # "redis", "memcached", etc.
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if cache_type:
            details["cache_type"] = cache_type
        super().__init__(message, details=details, **kwargs)

class CacheOperationError(CacheError):
    """
    缓存操作错误

    缓存读写操作失败
    """

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        key: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if operation:
            details["operation"] = operation
        if key:
            details["key"] = key
        super().__init__(message, details=details, **kwargs)

# ========================================================================
# 网络异常
# ========================================================================

class NetworkError(RecoverableError):
    """网络异常基类"""
    pass

class HTTPRequestError(NetworkError):
    """
    HTTP请求错误

    HTTP请求失败
    """

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if url:
            details["url"] = url
        if status_code is not None:
            details["status_code"] = status_code
        super().__init__(message, details=details, **kwargs)

# ========================================================================
# 配置异常
# ========================================================================

class ConfigurationError(BaseApplicationError):
    """
    配置错误

    应用配置不正确或缺失
    """

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, details=details, **kwargs)
