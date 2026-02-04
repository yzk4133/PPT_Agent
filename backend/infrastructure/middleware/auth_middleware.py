"""
认证中间件

提供 FastAPI 认证依赖项：
- get_current_user_optional: 可选认证（允许匿名访问）
- get_current_user: 必需认证（需要登录）
"""

import logging
import uuid
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from infrastructure.security.jwt_handler import jwt_handler
from infrastructure.exceptions.auth import InvalidTokenException
from models import User
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# HTTP Bearer 认证方案
security = HTTPBearer(auto_error=False)

async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    获取当前用户（可选）

    如果有 token 则验证，否则返回 None。
    适用于允许匿名访问但需要获取用户信息的端点。

    Args:
        request: FastAPI 请求对象
        credentials: HTTP 认证凭证

    Returns:
        用户 ID，如果未认证则返回 None
    """
    if not credentials:
        return None

    try:
        user_id = jwt_handler.verify_token(credentials.credentials)
        request.state.user_id = user_id
        return user_id
    except InvalidTokenException as e:
        logger.warning(f"Invalid token in optional auth: {e.message}")
        return None

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    获取当前用户（必需）

    如果没有有效 token 则抛出 401 异常。
    适用于需要登录才能访问的端点。

    Args:
        request: FastAPI 请求对象
        credentials: HTTP 认证凭证

    Returns:
        用户 ID

    Raises:
        HTTPException: 认证失败
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = jwt_handler.verify_token(credentials.credentials)
        request.state.user_id = user_id
        return user_id
    except InvalidTokenException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_with_db(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(lambda: None)  # 需要从数据库导入 get_db
) -> Optional[User]:
    """
    获取当前用户模型（包含数据库查询）

    从数据库加载完整的用户信息。

    Args:
        request: FastAPI 请求对象
        credentials: HTTP 认证凭证
        db: 数据库会话

    Returns:
        用户模型实例，如果未认证则返回 None
    """
    user_id = await get_current_user_optional(request, credentials)
    if not user_id:
        return None

    # 这里需要从依赖注入获取 db，调用方需要提供 db 依赖
    # 为了避免循环导入，这里假设 db 已经通过依赖注入提供
    if db is None:
        logger.warning("Database session not available for user lookup")
        return None

    try:
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        return user
    except Exception as e:
        logger.error(f"Error loading user from database: {e}")
        return None

class RequireAuth:
    """
    路由认证装饰器类

    用于在路由中声明认证要求。

    示例：
        @router.get("/protected")
        async def protected_route(
            user_id: str = Depends(RequireAuth())
        ):
            return {"user_id": user_id}

        @router.get("/public")
        async def public_route(
            user_id: Optional[str] = Depends(RequireAuth(optional=True))
        ):
            return {"user_id": user_id}
    """

    def __init__(self, optional: bool = False):
        """
        初始化认证要求

        Args:
            optional: 是否可选认证
        """
        self.optional = optional

    def __call__(self, request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
        """
        调用认证检查

        Args:
            request: FastAPI 请求对象
            credentials: HTTP 认证凭证

        Returns:
            用户 ID 或 None
        """
        if self.optional:
            return get_current_user_optional(request, credentials)
        return get_current_user(request, credentials)

# 便捷依赖函数
async def require_auth(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """需要认证的依赖（便捷函数）"""
    return await get_current_user(request, credentials)

async def optional_auth(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """可选认证的依赖（便捷函数）"""
    return await get_current_user_optional(request, credentials)
