"""
JWT Handler 测试
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from infrastructure.security.jwt_handler import JWTHandler
from infrastructure.exceptions.auth import InvalidTokenException

@pytest.mark.unit
class TestJWTHandler:
    """测试 JWTHandler 类"""

    def test_jwt_handler_initialization(self):
        """测试 JWT 处理器初始化"""
        handler = JWTHandler()

        assert handler.secret_key is not None
        assert handler.algorithm in ["HS256", "HS384", "HS512"]
        assert handler.access_token_expire_minutes > 0
        assert handler.refresh_token_expire_days > 0

    @pytest.mark.asyncio
    async def test_create_access_token(self):
        """测试创建访问令牌"""
        handler = JWTHandler()

        token = handler.create_access_token("user123")

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_claims(self):
        """测试创建带额外声明的访问令牌"""
        handler = JWTHandler()

        additional_claims = {
            "username": "testuser",
            "role": "admin"
        }

        token = handler.create_access_token("user123", additional_claims)

        assert token is not None

        # 解码验证
        payload = handler.decode_token(token)
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["role"] == "admin"

    def test_create_refresh_token(self):
        """测试创建刷新令牌"""
        handler = JWTHandler()

        token = handler.create_refresh_token("user123")

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        # 验证类型
        payload = handler.decode_token(token)
        assert payload["type"] == "refresh"

    def test_decode_token_valid(self):
        """测试解码有效令牌"""
        handler = JWTHandler()

        token = handler.create_access_token("user123")
        payload = handler.decode_token(token)

        assert payload["sub"] == "user123"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_token_invalid(self):
        """测试解码无效令牌"""
        handler = JWTHandler()

        with pytest.raises(InvalidTokenException):
            handler.decode_token("invalid_token_string")

    def test_decode_token_with_wrong_secret(self):
        """测试使用错误密钥解码令牌"""
        handler = JWTHandler()

        token = handler.create_access_token("user123")

        # 修改密钥
        original_secret = handler.secret_key
        handler.secret_key = "wrong_secret_key"

        with pytest.raises(InvalidTokenException):
            handler.decode_token(token)

        # 恢复密钥
        handler.secret_key = original_secret

    def test_verify_token_valid(self):
        """测试验证有效令牌"""
        handler = JWTHandler()

        token = handler.create_access_token("user123")
        user_id = handler.verify_token(token)

        assert user_id == "user123"

    def test_verify_token_invalid_type(self):
        """测试验证错误类型的令牌"""
        handler = JWTHandler()

        # 创建刷新令牌
        refresh_token = handler.create_refresh_token("user123")

        # 尝试作为访问令牌验证
        with pytest.raises(InvalidTokenException, match="令牌类型错误"):
            handler.verify_token(refresh_token)

    def test_verify_token_missing_subject(self):
        """测试验证缺少 subject 的令牌"""
        from jose import jwt

        handler = JWTHandler()

        # 手动创建没有 sub 的令牌
        payload = {
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        token = jwt.encode(payload, handler.secret_key, algorithm=handler.algorithm)

        with pytest.raises(InvalidTokenException, match="令牌缺少用户信息"):
            handler.verify_token(token)

    def test_verify_refresh_token_valid(self):
        """测试验证有效刷新令牌"""
        handler = JWTHandler()

        token = handler.create_refresh_token("user123")
        user_id = handler.verify_refresh_token(token)

        assert user_id == "user123"

    def test_verify_refresh_token_invalid_type(self):
        """测试验证错误类型的刷新令牌"""
        handler = JWTHandler()

        # 创建访问令牌
        access_token = handler.create_access_token("user123")

        # 尝试作为刷新令牌验证
        with pytest.raises(InvalidTokenException, match="令牌类型错误"):
            handler.verify_refresh_token(access_token)

    def test_token_expiration(self):
        """测试令牌过期"""
        handler = JWTHandler()

        # 创建一个已过期的令牌（设置负的过期时间）
        import time
        from datetime import timedelta
        from jose import jwt

        # 临时修改过期时间
        original_expire = handler.access_token_expire_minutes
        handler.access_token_expire_minutes = -1

        token = handler.create_access_token("user123")

        # 恢复过期时间
        handler.access_token_expire_minutes = original_expire

        # 验证过期令牌应该失败
        with pytest.raises(InvalidTokenException):
            handler.verify_token(token)

    def test_token_claims_expiration(self):
        """测试令牌过期时间设置"""
        handler = JWTHandler()

        token = handler.create_access_token("user123")
        payload = handler.decode_token(token)

        # 验证过期时间大约是现在 + access_token_expire_minutes
        exp_timestamp = payload["exp"]
        expected_exp = datetime.utcnow() + timedelta(minutes=handler.access_token_expire_minutes)

        # 允许 5 秒误差
        time_diff = abs(datetime.fromtimestamp(exp_timestamp) - expected_exp)
        assert time_diff.total_seconds() < 5

    def test_refresh_token_expiration(self):
        """测试刷新令牌过期时间设置"""
        handler = JWTHandler()

        token = handler.create_refresh_token("user123")
        payload = handler.decode_token(token)

        # 验证过期时间大约是现在 + refresh_token_expire_days
        exp_timestamp = payload["exp"]
        expected_exp = datetime.utcnow() + timedelta(days=handler.refresh_token_expire_days)

        # 允许 5 秒误差
        time_diff = abs(datetime.fromtimestamp(exp_timestamp) - expected_exp)
        assert time_diff.total_seconds() < 5

    def test_multiple_tokens_same_user(self):
        """测试为同一用户创建多个令牌"""
        handler = JWTHandler()

        token1 = handler.create_access_token("user123")
        token2 = handler.create_access_token("user123")

        # 令牌应该不同（因为 iat 不同）
        assert token1 != token2

        # 但都应该有效
        assert handler.verify_token(token1) == "user123"
        assert handler.verify_token(token2) == "user123"

@pytest.mark.unit
class TestJWTHandlerEdgeCases:
    """测试 JWTHandler 边界情况"""

    def test_empty_user_id(self):
        """测试空用户 ID"""
        handler = JWTHandler()

        # 应该允许创建空 user_id 的令牌（虽然不推荐）
        token = handler.create_access_token("")

        assert token is not None

        # 验证时应该返回空字符串
        user_id = handler.verify_token(token)
        assert user_id == ""

    def test_special_characters_in_user_id(self):
        """测试用户 ID 中的特殊字符"""
        handler = JWTHandler()

        user_id = "user@example.com"
        token = handler.create_access_token(user_id)

        verified_id = handler.verify_token(token)
        assert verified_id == user_id

    def test_unicode_in_claims(self):
        """测试声明中的 Unicode 字符"""
        handler = JWTHandler()

        additional_claims = {
            "name": "测试用户",
            "emoji": "😀🎉"
        }

        token = handler.create_access_token("user123", additional_claims)
        payload = handler.decode_token(token)

        assert payload["name"] == "测试用户"
        assert payload["emoji"] == "😀🎉"

    def test_very_long_claims(self):
        """测试很长的声明"""
        handler = JWTHandler()

        additional_claims = {
            "long_data": "x" * 10000
        }

        token = handler.create_access_token("user123", additional_claims)

        # 应该仍然能够处理
        payload = handler.decode_token(token)
        assert len(payload["long_data"]) == 10000

@pytest.mark.unit
class TestJWTHandlerWithConfig:
    """测试带配置的 JWTHandler"""

    def test_custom_secret_from_env(self):
        """测试从环境变量获取自定义密钥"""
        import os

        original_secret = os.environ.get("JWT_SECRET_KEY")

        try:
            os.environ["JWT_SECRET_KEY"] = "test_secret_key_12345"

            # 重新创建 handler 以获取新密钥
            handler = JWTHandler()

            assert handler.secret_key == "test_secret_key_12345"

        finally:
            if original_secret:
                os.environ["JWT_SECRET_KEY"] = original_secret
            else:
                os.environ.pop("JWT_SECRET_KEY", None)

    def test_fallback_secret(self):
        """测试回退到默认密钥"""
        import os

        original_secret = os.environ.get("JWT_SECRET_KEY")

        try:
            # 移除环境变量
            os.environ.pop("JWT_SECRET_KEY", None)

            # 强制重新加载配置
            import infrastructure.config.common_config as config_module
            config_module._config_instance = None

            handler = JWTHandler()

            # 应该使用默认密钥
            assert handler.secret_key is not None

        finally:
            if original_secret:
                os.environ["JWT_SECRET_KEY"] = original_secret

            # 恢复配置
            import infrastructure.config.common_config as config_module
            config_module._config_instance = None
