"""
JWT Token 处理器
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt

from infrastructure.config.common_config import get_config
from infrastructure.exceptions.auth import InvalidTokenException

class JWTHandler:
    """JWT Token 处理器"""

    def __init__(self):
        config = get_config()
        self.secret_key = self._get_secret_key(config)
        self.algorithm = getattr(config, 'jwt_algorithm', 'HS256')
        self.access_token_expire_minutes = getattr(config, 'access_token_expire_minutes', 30)
        self.refresh_token_expire_days = getattr(config, 'refresh_token_expire_days', 30)

    def _get_secret_key(self, config) -> str:
        """获取 JWT 密钥"""
        # Try to get from config attributes
        secret_key = getattr(config, 'jwt_secret_key', None)
        if not secret_key:
            # Fallback to environment variable
            import os
            secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        return secret_key

    def create_access_token(
        self,
        user_id: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        创建访问令牌

        Args:
            user_id: 用户 ID
            additional_claims: 额外的声明信息

        Returns:
            JWT 访问令牌
        """
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }

        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        """
        创建刷新令牌

        Args:
            user_id: 用户 ID

        Returns:
            JWT 刷新令牌
        """
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        解码并验证令牌

        Args:
            token: JWT 令牌

        Returns:
            解码后的 payload

        Raises:
            InvalidTokenException: 令牌无效或已过期
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except JWTError as e:
            raise InvalidTokenException(str(e))

    def verify_token(self, token: str) -> str:
        """
        验证令牌并返回用户 ID

        Args:
            token: JWT 访问令牌

        Returns:
            用户 ID

        Raises:
            InvalidTokenException: 令牌无效、过期或类型错误
        """
        payload = self.decode_token(token)

        if payload.get("type") != "access":
            raise InvalidTokenException("令牌类型错误")

        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenException("令牌缺少用户信息")

        return user_id

    def verify_refresh_token(self, token: str) -> str:
        """
        验证刷新令牌并返回用户 ID

        Args:
            token: JWT 刷新令牌

        Returns:
            用户 ID

        Raises:
            InvalidTokenException: 令牌无效、过期或类型错误
        """
        payload = self.decode_token(token)

        if payload.get("type") != "refresh":
            raise InvalidTokenException("令牌类型错误")

        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenException("令牌缺少用户信息")

        return user_id

# 全局实例
jwt_handler = JWTHandler()
