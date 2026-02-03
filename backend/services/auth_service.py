"""
认证服务

提供用户认证相关的业务逻辑：
- 用户注册
- 用户登录
- Token 刷新
- 用户登出
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models import User, Role, RefreshToken
from schemas import RegisterRequest, LoginRequest, TokenResponse
from infrastructure.security.jwt_handler import jwt_handler
from infrastructure.security.password_handler import password_handler
from infrastructure.exceptions.auth import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
    UserInactiveException,
    InvalidTokenException,
)

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务"""

    def __init__(self, db: Session):
        """
        初始化认证服务

        Args:
            db: 数据库会话
        """
        self.db = db

    def register(self, data: RegisterRequest) -> TokenResponse:
        """
        用户注册

        Args:
            data: 注册数据

        Returns:
            Token 响应
        """
        # 检查用户是否已存在
        existing_user = self.db.query(User).filter(
            or_(User.email == data.email, User.username == data.username)
        ).first()

        if existing_user:
            if existing_user.email == data.email:
                raise UserAlreadyExistsException(data.email)
            else:
                raise UserAlreadyExistsException(f"用户名 '{data.username}' 已被使用")

        # 验证并加密密码
        hashed_password = password_handler.validate_and_hash(data.password)

        # 创建用户
        user = User(
            email=data.email,
            username=data.username,
            hashed_password=hashed_password,
            full_name=data.full_name,
        )

        # 分配默认角色 (USER)
        default_role = self.db.query(Role).filter(Role.name == "USER").first()
        if not default_role:
            # 如果 USER 角色不存在，创建它
            default_role = Role(name="USER", description="普通用户")
            self.db.add(default_role)
            self.db.flush()

        user.roles.append(default_role)

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        logger.info(f"New user registered: {user.email}")

        # 生成令牌
        return self._create_tokens(user)

    def login(self, data: LoginRequest) -> TokenResponse:
        """
        用户登录

        Args:
            data: 登录数据

        Returns:
            Token 响应
        """
        # 查找用户（通过邮箱或用户名）
        user = self.db.query(User).filter(
            or_(User.email == data.username, User.username == data.username)
        ).first()

        # 验证密码
        if not user or not password_handler.verify_password(
            data.password, user.hashed_password
        ):
            raise InvalidCredentialsException()

        # 检查账户状态
        if not user.is_active:
            raise UserInactiveException()

        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        self.db.commit()

        logger.info(f"User logged in: {user.email}")

        # 生成令牌
        return self._create_tokens(user)

    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        刷新访问令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            新的 Token 响应
        """
        # 验证刷新令牌格式
        try:
            user_id = jwt_handler.verify_refresh_token(refresh_token)
        except InvalidTokenException:
            raise InvalidTokenException("刷新令牌无效或已过期")

        # 查找刷新令牌记录
        token_record = self.db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.is_revoked == False
        ).first()

        if not token_record:
            raise InvalidTokenException("刷新令牌无效或已撤销")

        # 验证用户 ID 是否匹配
        if str(token_record.user_id) != user_id:
            raise InvalidTokenException("令牌与用户不匹配")

        # 检查令牌是否过期
        if token_record.expires_at < datetime.utcnow():
            # 自动撤销过期令牌
            token_record.revoke()
            self.db.commit()
            raise InvalidTokenException("刷新令牌已过期")

        # 查找用户
        user = self.db.query(User).filter(User.id == token_record.user_id).first()
        if not user:
            raise InvalidTokenException("用户不存在")

        if not user.is_active:
            raise UserInactiveException()

        # 撤销旧刷新令牌
        token_record.revoke()
        self.db.commit()

        logger.info(f"Token refreshed for user: {user.email}")

        # 生成新令牌
        return self._create_tokens(user)

    def logout(self, refresh_token: str):
        """
        用户登出

        Args:
            refresh_token: 刷新令牌
        """
        token_record = self.db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token
        ).first()

        if token_record:
            token_record.revoke()
            self.db.commit()
            logger.info(f"User logged out, token revoked")

    def _create_tokens(self, user: User) -> TokenResponse:
        """
        创建访问令牌和刷新令牌

        Args:
            user: 用户实例

        Returns:
            Token 响应
        """
        # 获取用户角色
        roles = [role.name for role in user.roles]

        # 创建访问令牌
        access_token = jwt_handler.create_access_token(
            user_id=str(user.id),
            additional_claims={
                "email": user.email,
                "username": user.username,
                "roles": roles
            }
        )

        # 创建刷新令牌
        refresh_token_str = jwt_handler.create_refresh_token(str(user.id))

        # 保存刷新令牌到数据库
        config = jwt_handler
        refresh_token_record = RefreshToken.create(
            user_id=user.id,
            token=refresh_token_str,
            expires_days=config.refresh_token_expire_days
        )

        self.db.add(refresh_token_record)
        self.db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            expires_in=config.access_token_expire_minutes * 60
        )

    def verify_access_token(self, token: str) -> Optional[User]:
        """
        验证访问令牌并返回用户

        Args:
            token: 访问令牌

        Returns:
            用户实例，如果令牌无效则返回 None
        """
        try:
            user_id = jwt_handler.verify_token(token)
            user = self.db.query(User).filter(User.id == uuid.UUID(user_id)).first()
            return user
        except Exception:
            return None


# 全局服务实例（单例）
_auth_service: Optional[AuthService] = None


def get_auth_service(db: Session) -> AuthService:
    """
    获取认证服务实例

    Args:
        db: 数据库会话

    Returns:
        AuthService 实例
    """
    return AuthService(db)


def reset_auth_service():
    """重置认证服务（用于测试）"""
    global _auth_service
    _auth_service = None
