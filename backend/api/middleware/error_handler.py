"""
Error Handler Middleware

FastAPI错误处理中间件，提供：
- 统一的异常捕获和处理
- 自动HTTP状态码映射
- 结构化错误响应
- 错误日志记录
"""

import logging
import traceback
from typing import Union, Dict, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException as FastAPIHTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

from ...domain.exceptions import (
    BaseApplicationError,
    APIError,
    get_http_status,
    exception_to_http_response,
)
from ...domain.exceptions.api_exceptions import HTTP_STATUS_MAP

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware:
    """
    错误处理中间件

    捕获所有异常并转换为统一的JSON响应格式
    """

    def __init__(self, app):
        """
        初始化中间件

        Args:
            app: FastAPI应用实例
        """
        self.app = app

    async def __call__(self, scope, receive, send):
        """
        ASGI调用接口

        Args:
            scope: ASGI scope
            receive: ASGI receive
            send: ASGI send
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 创建请求对象用于异常处理
        request = Request(scope, receive)

        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            # 处理异常
            response = await self._handle_exception(request, exc)
            await response(scope, receive, send)

    async def _handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """
        处理异常并返回JSON响应

        Args:
            request: FastAPI请求对象
            exc: 捕获的异常

        Returns:
            JSONResponse
        """
        # 记录错误日志
        self._log_exception(request, exc)

        # 处理不同类型的异常
        if isinstance(exc, BaseApplicationError):
            return await self._handle_application_error(exc)
        elif isinstance(exc, (RequestValidationError, FastAPIHTTPException, StarletteHTTPException)):
            return await self._handle_fastapi_error(exc)
        else:
            return await self._handle_unexpected_error(exc)

    async def _handle_application_error(self, exc: BaseApplicationError) -> JSONResponse:
        """
        处理应用级异常

        Args:
            exc: 应用异常

        Returns:
            JSONResponse
        """
        # 获取HTTP状态码
        http_status = get_http_status(exc)

        # 转换为响应格式
        response_body = exception_to_http_response(exc)

        return JSONResponse(
            status_code=http_status,
            content=response_body
        )

    async def _handle_fastapi_error(self, exc: Union[RequestValidationError, FastAPIHTTPException, StarletteHTTPException]) -> JSONResponse:
        """
        处理FastAPI内置异常

        Args:
            exc: FastAPI异常

        Returns:
            JSONResponse
        """
        if isinstance(exc, RequestValidationError):
            # Pydantic验证错误
            errors = []
            for error in exc.errors():
                errors.append({
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"]
                })

            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error_code": "ValidationError",
                    "message": "Request validation failed",
                    "details": {"errors": errors}
                }
            )

        elif isinstance(exc, (FastAPIHTTPException, StarletteHTTPException)):
            # HTTP异常
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error_code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                }
            )

        # 默认处理
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "InternalServerError",
                "message": "An unexpected error occurred",
            }
        )

    async def _handle_unexpected_error(self, exc: Exception) -> JSONResponse:
        """
        处理未预期的异常

        Args:
            exc: 异常对象

        Returns:
            JSONResponse
        """
        # 生产环境不暴露详细错误信息
        error_message = "An unexpected error occurred"

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "InternalServerError",
                "message": error_message,
                "details": {
                    "exception_type": type(exc).__name__
                } if logger.level <= logging.DEBUG else {}
            }
        )

    def _log_exception(self, request: Request, exc: Exception):
        """
        记录异常日志

        Args:
            request: 请求对象
            exc: 异常对象
        """
        # 请求信息
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "client": f"{request.client.host}:{request.client.port}" if request.client else None,
        }

        # 根据异常类型选择日志级别
        if isinstance(exc, (APIError, FastAPIHTTPException, StarletteHTTPException)):
            # 预期的API错误，使用WARNING级别
            logger.warning(
                f"API Error: {exc}",
                extra={
                    "request": request_info,
                    "exception_type": type(exc).__name__,
                    "details": getattr(exc, "details", {})
                }
            )
        elif isinstance(exc, BaseApplicationError):
            # 应用级错误
            logger.error(
                f"Application Error: {exc}",
                extra={
                    "request": request_info,
                    "exception_type": type(exc).__name__,
                    "error_code": getattr(exc, "code", None),
                    "details": getattr(exc, "details", {})
                }
            )
        else:
            # 未预期的错误，使用ERROR级别并包含堆栈跟踪
            logger.error(
                f"Unexpected Error: {exc}",
                extra={
                    "request": request_info,
                    "exception_type": type(exc).__name__,
                },
                exc_info=True
            )

def create_error_handler(app):
    """
    创建并注册错误处理中间件

    Args:
        app: FastAPI应用实例

    Returns:
        ErrorHandlerMiddleware实例
    """
    return ErrorHandlerMiddleware(app)
