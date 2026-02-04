"""
Error Handler 测试
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

from infrastructure.middleware.error_handler import (
    api_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
    setup_exception_handlers,
)
from infrastructure.exceptions import BaseAPIException

@pytest.mark.unit
@pytest.mark.asyncio
class TestAPIExceptionHandler:
    """测试自定义 API 异常处理器"""

    async def test_api_exception_handler(self):
        """测试 API 异常处理"""
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "GET"

        exc = BaseAPIException(
            status_code=400,
            error_code="TEST_ERROR",
            message="Test error message",
            details={"key": "value"}
        )

        response = await api_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 400

        # 验证响应内容
        import json
        content = json.loads(response.body.decode())

        assert content["status"] == "error"
        assert content["error_code"] == "TEST_ERROR"
        assert content["message"] == "Test error message"

    async def test_api_exception_handler_debug_mode(self):
        """测试调试模式下的详细信息"""
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "GET"

        exc = BaseAPIException(
            status_code=400,
            error_code="TEST_ERROR",
            message="Test error",
            details={"detail": "info"}
        )

        with patch('infrastructure.middleware.error_handler.get_config') as mock_config:
            mock_config.return_value.debug = True

            response = await api_exception_handler(request, exc)

            import json
            content = json.loads(response.body.decode())

            # 调试模式应该包含详细信息
            assert "details" in content
            assert "path" in content
            assert "method" in content

@pytest.mark.unit
@pytest.mark.asyncio
class TestHTTPExceptionHandler:
    """测试 HTTP 异常处理器"""

    async def test_http_exception_handler(self):
        """测试 HTTP 异常处理"""
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "GET"

        exc = StarletteHTTPException(status_code=404, detail="Not found")

        response = await http_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 404

        import json
        content = json.loads(response.body.decode())

        assert content["status"] == "error"
        assert content["error_code"] == "HTTP_ERROR"
        assert "Not found" in content["message"]

    async def test_http_exception_handler_debug_mode(self):
        """测试调试模式下的 HTTP 异常"""
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "POST"

        exc = StarletteHTTPException(status_code=500, detail="Server error")

        with patch('infrastructure.middleware.error_handler.get_config') as mock_config:
            mock_config.return_value.debug = True

            response = await http_exception_handler(request, exc)

            import json
            content = json.loads(response.body.decode())

            assert "path" in content
            assert "method" in content
            assert "status_code" in content

@pytest.mark.unit
@pytest.mark.asyncio
class TestValidationExceptionHandler:
    """测试验证异常处理器"""

    async def test_validation_exception_handler(self):
        """测试验证异常处理"""
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "POST"

        # 模拟验证错误
        errors = [{
            "loc": ["body", "field1"],
            "msg": "field required",
            "type": "value_error.missing"
        }]

        exc = RequestValidationError(errors)

        response = await validation_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 422

        import json
        content = json.loads(response.body.decode())

        assert content["status"] == "error"
        assert content["error_code"] == "VALIDATION_ERROR"
        assert "field1" in content["message"]

    async def test_validation_exception_handler_debug_mode(self):
        """测试调试模式下的验证异常"""
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "POST"

        errors = [{
            "loc": ["body", "field1"],
            "msg": "field required",
            "type": "value_error.missing"
        }]

        exc = RequestValidationError(errors)

        with patch('infrastructure.middleware.error_handler.get_config') as mock_config:
            mock_config.return_value.debug = True

            response = await validation_exception_handler(request, exc)

            import json
            content = json.loads(response.body.decode())

            assert "details" in content
            assert "errors" in content["details"]
            assert "path" in content

@pytest.mark.unit
@pytest.mark.asyncio
class TestGeneralExceptionHandler:
    """测试通用异常处理器"""

    async def test_general_exception_handler(self):
        """测试通用异常处理"""
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "GET"

        exc = Exception("Unexpected error")

        response = await general_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

        import json
        content = json.loads(response.body.decode())

        assert content["status"] == "error"
        assert content["error_code"] == "INTERNAL_ERROR"

    async def test_general_exception_handler_debug_mode(self):
        """测试调试模式下的通用异常"""
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "GET"

        exc = ValueError("Some error")

        with patch('infrastructure.middleware.error_handler.get_config') as mock_config:
            mock_config.return_value.debug = True

            response = await general_exception_handler(request, exc)

            import json
            content = json.loads(response.body.decode())

            # 调试模式应该包含详细信息
            assert "details" in content
            assert "type" in content["details"]
            assert "traceback" in content["details"]

@pytest.mark.unit
class TestSetupExceptionHandlers:
    """测试设置异常处理器"""

    def test_setup_exception_handlers(self):
        """测试设置异常处理器"""
        app = MagicMock()

        setup_exception_handlers(app)

        # 验证异常处理器被注册
        assert app.add_exception_handler.call_count == 4

@pytest.mark.unit
@pytest.mark.asyncio
class TestErrorHandlingIntegration:
    """测试错误处理集成"""

    async def test_exception_chaining(self):
        """测试异常链"""
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/test"
        request.method = "GET"

        # 测试不同类型的异常
        exceptions = [
            BaseAPIException(400, "TEST", "Test message"),
            StarletteHTTPException(404, "Not found"),
            RequestValidationError([]),
            Exception("Unexpected"),
        ]

        for exc in exceptions:
            if isinstance(exc, BaseAPIException):
                response = await api_exception_handler(request, exc)
            elif isinstance(exc, StarletteHTTPException):
                response = await http_exception_handler(request, exc)
            elif isinstance(exc, RequestValidationError):
                response = await validation_exception_handler(request, exc)
            else:
                response = await general_exception_handler(request, exc)

            assert isinstance(response, JSONResponse)
            assert response.status_code in [400, 404, 422, 500]
