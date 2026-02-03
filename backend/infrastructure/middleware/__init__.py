"""
中间件模块

提供各种中间件：
- 认证中间件
- 限流中间件
- 错误处理中间件
"""

from .auth_middleware import (
    get_current_user,
    get_current_user_optional,
    get_current_user_with_db,
    RequireAuth,
    require_auth,
    optional_auth,
)
from .rate_limit_middleware import (
    RateLimiter,
    rate_limiter,
    rate_limit_check,
    strict_rate_limit_check,
    loose_rate_limit_check,
)
from .error_handler import (
    api_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
    setup_exception_handlers,
)

__all__ = [
    # Auth middleware
    "get_current_user",
    "get_current_user_optional",
    "get_current_user_with_db",
    "RequireAuth",
    "require_auth",
    "optional_auth",

    # Rate limit middleware
    "RateLimiter",
    "rate_limiter",
    "rate_limit_check",
    "strict_rate_limit_check",
    "loose_rate_limit_check",

    # Error handler
    "api_exception_handler",
    "http_exception_handler",
    "validation_exception_handler",
    "general_exception_handler",
    "setup_exception_handlers",
]
