"""
统一异常处理中间件

提供全局的异常捕获和标准化错误响应
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Union
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)


class APIException(Exception):
    """
    API异常基类

    使用示例:
        >>> raise APIException("资源不存在", status_code=404, error_code="NOT_FOUND")
    """

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = None,
        details: dict = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "API_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class ResourceNotFoundError(APIException):
    """资源未找到异常"""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type}未找到: {resource_id}",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class ValidationError(APIException):
    """业务验证错误"""

    def __init__(self, message: str, field: str = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details={"field": field} if field else {},
        )


class ServiceUnavailableError(APIException):
    """服务不可用"""

    def __init__(self, service_name: str):
        super().__init__(
            message=f"服务暂时不可用: {service_name}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service_name},
        )


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """
    处理API异常

    返回标准化的错误响应
    """
    logger.error(
        f"API Error: {exc.message}",
        extra={
            "error_code": exc.error_code,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path,
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    处理参数验证异常（Pydantic）

    返回详细的验证错误信息
    """
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    logger.warning(
        f"Validation Error: {request.url.path}",
        extra={"errors": errors, "method": request.method},
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "请求参数验证失败",
                "details": {"errors": errors},
            },
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path,
        },
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    处理HTTP异常（如404, 405等）
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {"code": f"HTTP_{exc.status_code}", "message": exc.detail},
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理未捕获的异常

    记录完整堆栈，返回通用错误响应
    """
    # 记录完整异常信息
    logger.exception(
        f"Unhandled exception: {type(exc).__name__}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        },
    )

    # 生产环境不暴露具体错误
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误，请稍后重试",
            },
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path,
        },
    )


def register_exception_handlers(app):
    """
    注册所有异常处理器到FastAPI应用

    Args:
        app: FastAPI应用实例

    使用示例:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> register_exception_handlers(app)
    """
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
