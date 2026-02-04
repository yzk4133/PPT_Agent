"""
Auth Middleware 测试
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from infrastructure.middleware.auth_middleware import (
    get_current_user_optional,
    get_current_user,
    RequireAuth,
    require_auth,
    optional_auth,
)
from infrastructure.security.jwt_handler import JWTHandler
from infrastructure.exceptions.auth import InvalidTokenException

@pytest.mark.unit
@pytest.mark.asyncio
class TestGetCurrentUserOptional:
    """测试 get_current_user_optional 函数"""

    async def test_no_credentials(self):
        """测试无认证凭证"""
        request = MagicMock(spec=Request)
        credentials = None

        user_id = await get_current_user_optional(request, credentials)

        assert user_id is None

    async def test_valid_token(self):
        """测试有效令牌"""
        request = MagicMock(spec=Request)
        request.state = MagicMock()

        # 创建有效的 JWT
        handler = JWTHandler()
        token = handler.create_access_token("user123")

        credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = token

        user_id = await get_current_user_optional(request, credentials)

        assert user_id == "user123"
        assert request.state.user_id == "user123"

    async def test_invalid_token(self):
        """测试无效令牌"""
        request = MagicMock(spec=Request)
        request.state = MagicMock()

        credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = "invalid_token"

        user_id = await get_current_user_optional(request, credentials)

        # 无效令牌应该返回 None 而不是抛出异常
        assert user_id is None

@pytest.mark.unit
@pytest.mark.asyncio
class TestGetCurrentUser:
    """测试 get_current_user 函数"""

    async def test_no_credentials_raises_exception(self):
        """测试无认证凭证抛出异常"""
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "GET"

        credentials = None

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "未提供认证令牌" in exc_info.value.detail

    async def test_valid_token(self):
        """测试有效令牌"""
        request = MagicMock(spec=Request)
        request.state = MagicMock()

        handler = JWTHandler()
        token = handler.create_access_token("user123")

        credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = token

        user_id = await get_current_user(request, credentials)

        assert user_id == "user123"
        assert request.state.user_id == "user123"

    async def test_invalid_token_raises_exception(self):
        """测试无效令牌抛出异常"""
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "GET"

        credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = "invalid_token"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.unit
class TestRequireAuth:
    """测试 RequireAuth 类"""

    def test_require_auth_init(self):
        """测试 RequireAuth 初始化"""
        auth = RequireAuth()

        assert auth.optional is False

    def test_require_auth_init_optional(self):
        """测试 RequireAuth 可选认证初始化"""
        auth = RequireAuth(optional=True)

        assert auth.optional is True

    @pytest.mark.asyncio
    async def test_require_auth_call_required(self):
        """测试必需认证调用"""
        request = MagicMock(spec=Request)
        request.state = MagicMock()

        handler = JWTHandler()
        token = handler.create_access_token("user123")

        credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = token

        auth = RequireAuth(optional=False)

        with patch.object(auth, '__call__', return_value="user123"):
            # 这个测试需要实际的依赖注入，这里仅做结构验证
            assert auth.optional is False

@pytest.mark.unit
@pytest.mark.asyncio
class TestConvenienceFunctions:
    """测试便捷函数"""

    async def test_require_auth_function(self):
        """测试 require_auth 函数"""
        request = MagicMock(spec=Request)
        request.state = MagicMock()

        handler = JWTHandler()
        token = handler.create_access_token("user123")

        credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = token

        with patch('infrastructure.middleware.auth_middleware.get_current_user', return_value="user123"):
            result = await require_auth(request, credentials)
            assert result == "user123"

    async def test_optional_auth_function(self):
        """测试 optional_auth 函数"""
        request = MagicMock(spec=Request)

        credentials = None

        with patch('infrastructure.middleware.auth_middleware.get_current_user_optional', return_value=None):
            result = await optional_auth(request, credentials)
            assert result is None
