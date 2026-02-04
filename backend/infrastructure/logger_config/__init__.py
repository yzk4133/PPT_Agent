"""
Infrastructure logging module

Provides unified logging system with:
- Structured JSON and text formats
- Console and file output
- Log rotation
- Request ID tracking
- Sensitive data masking
"""

from .logger_config import (
    # Core functions
    setup_logger,
    get_logger,
    set_request_id,
    get_request_id,

    # Context manager
    LoggerContext,

    # Decorator
    log_function_call,

    # Pre-configured loggers
    get_app_logger,
    get_api_logger,
    get_agent_logger,
    get_infrastructure_logger,

    # Formatters
    JSONFormatter,
    TextFormatter,

    # Filters
    SensitiveDataFilter,
)

__all__ = [
    # Core functions
    "setup_logger",
    "get_logger",
    "set_request_id",
    "get_request_id",

    # Context manager
    "LoggerContext",

    # Decorator
    "log_function_call",

    # Pre-configured loggers
    "get_app_logger",
    "get_api_logger",
    "get_agent_logger",
    "get_infrastructure_logger",

    # Formatters
    "JSONFormatter",
    "TextFormatter",

    # Filters
    "SensitiveDataFilter",
]
