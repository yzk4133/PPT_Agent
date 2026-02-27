"""
异常类模块

提供基础设施层的异常处理体系（简化版）。
"""

from .exceptions import (
    BaseAPIException,
    RateLimitExceededException,
)

__all__ = [
    "BaseAPIException",
    "RateLimitExceededException",
]
