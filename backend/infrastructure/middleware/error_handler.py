"""
统一异常处理

提供全局异常处理中间件：
- 自定义 API 异常处理
- 通用异常处理
- 错误日志记录
"""

import logging
import traceback
from datetime import datetime
from typing import Any, Dict
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from infrastructure.exceptions import BaseAPIException
from infrastructure.config.common_config import get_config

logger = logging.getLogger(__name__)


async def api_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """
    自定义 API 异常处理

    Args:
        request: FastAPI 请求对象
        exc: 自定义 API 异常

    Returns:
        JSON 响应
    """
    # 记录错误日志
    logger.error(
        f"API Exception: {exc.error_code} - {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "details": exc.details,
        },
    )

    # 构建响应
    response_data: Dict[str, Any] = {
        "status": "error",
        "error_code": exc.error_code,
        "message": exc.message,
        "detail": exc.message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    # 开发环境返回详细信息
    config = get_config()
    if config.debug:
        response_data["details"] = exc.details
        response_data["path"] = request.url.path
        response_data["method"] = request.method

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    HTTP 异常处理

    Args:
        request: FastAPI 请求对象
        exc: HTTP 异常

    Returns:
        JSON 响应
    """
    # 记录错误日志
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
    )

    # 构建响应
    response_data: Dict[str, Any] = {
        "status": "error",
        "error_code": "HTTP_ERROR",
        "message": str(exc.detail),
        "detail": str(exc.detail),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    # 开发环境返回详细信息
    config = get_config()
    if config.debug:
        response_data["path"] = request.url.path
        response_data["method"] = request.method
        response_data["status_code"] = exc.status_code

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    请求验证异常处理

    Args:
        request: FastAPI 请求对象
        exc: 请求验证异常

    Returns:
        JSON 响应
    """
    # 记录错误日志
    logger.warning(
        f"Validation Exception: {exc.errors()}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": exc.errors(),
        },
    )

    # 提取第一个错误信息
    errors = exc.errors()
    first_error = errors[0] if errors else {}

    # 构友好的错误消息
    field = first_error.get("loc", ["unknown"])[-1]
    message = first_error.get("msg", "验证失败")
    error_type = first_error.get("type", "validation_error")

    response_data: Dict[str, Any] = {
        "status": "error",
        "error_code": "VALIDATION_ERROR",
        "message": f"字段 '{field}' {message}",
        "detail": f"字段 '{field}' {message}",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    # 开发环境返回详细信息
    config = get_config()
    if config.debug:
        response_data["details"] = {
            "field": field,
            "error_type": error_type,
            "errors": errors,
        }
        response_data["path"] = request.url.path

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data,
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用异常处理

    Args:
        request: FastAPI 请求对象
        exc: 通用异常

    Returns:
        JSON 响应
    """
    # 记录完整错误堆栈
    logger.exception(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
    )

    # 生产环境隐藏详细错误信息
    config = get_config()
    if config.debug:
        message = str(exc)
        details = {
            "type": type(exc).__name__,
            "traceback": traceback.format_exc(),
        }
    else:
        message = "服务器内部错误"
        details = {}

    response_data: Dict[str, Any] = {
        "status": "error",
        "error_code": "INTERNAL_ERROR",
        "message": message,
        "detail": message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    if details:
        response_data["details"] = details

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data,
    )


def setup_exception_handlers(app):
    """
    设置全局异常处理器

    Args:
        app: FastAPI 应用实例
    """
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    app.add_exception_handler(BaseAPIException, api_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Exception handlers registered")
