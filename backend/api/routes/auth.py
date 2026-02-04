"""
认证相关路由

提供用户认证和授权相关的 API 端点：
- 用户注册
- 用户登录
- 刷新令牌
- 用户登出
- 获取用户信息
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from memory.storage.database import get_db_session
from schemas import RegisterRequest, LoginRequest, TokenResponse, UserProfile
from services import get_auth_service, get_user_service
from infrastructure.middleware.auth_middleware import get_current_user, get_current_user_optional
from infrastructure.middleware.rate_limit_middleware import rate_limit_check

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/auth", tags=["认证"])

# HTTP Bearer 认证方案
security = HTTPBearer()

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="创建新用户账户并返回访问令牌"
)
async def register(
    data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    用户注册

    - **email**: 邮箱地址（唯一）
    - **username**: 用户名（唯一）
    - **password**: 密码（至少 8 个字符，包含大小写字母和数字）
    - **full_name**: 全名（可选）

    返回访问令牌和刷新令牌。
    """
    # 限流检查（注册限制：5次/分钟）
    await rate_limit_check(request, limit=5, window=60)

    service = get_auth_service(db)
    return service.register(data)

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="用户登录",
    description="使用邮箱/用户名和密码登录"
)
async def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    用户登录

    - **username**: 邮箱或用户名
    - **password**: 密码

    返回访问令牌和刷新令牌。
    """
    # 限流检查（登录限制：10次/分钟）
    await rate_limit_check(request, limit=10, window=60)

    service = get_auth_service(db)
    return service.login(data)

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="刷新访问令牌",
    description="使用刷新令牌获取新的访问令牌"
)
async def refresh_token(
    data: dict,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    刷新访问令牌

    - **refresh_token**: 刷新令牌

    返回新的访问令牌和刷新令牌。
    """
    # 限流检查
    await rate_limit_check(request, limit=20, window=60)

    refresh_token = data.get("refresh_token")
    if not refresh_token:
        from infrastructure.exceptions.validation import MissingRequiredFieldException
        raise MissingRequiredFieldException("refresh_token")

    service = get_auth_service(db)
    return service.refresh_token(refresh_token)

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="用户登出",
    description="撤销刷新令牌"
)
async def logout(
    data: dict,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    用户登出

    - **refresh_token**: 刷新令牌（可选）

    撤销刷新令牌，使访问令牌失效。
    """
    refresh_token = data.get("refresh_token")
    if refresh_token:
        service = get_auth_service(db)
        service.logout(refresh_token)

    return None

@router.get(
    "/me",
    response_model=UserProfile,
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息"
)
async def get_current_user_info(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    获取当前用户信息

    返回当前登录用户的详细信息，包括角色。
    """
    service = get_user_service(db)
    return service.get_profile(current_user)

@router.patch(
    "/me",
    response_model=UserProfile,
    summary="更新当前用户信息",
    description="更新当前登录用户的详细信息"
)
async def update_current_user_info(
    update_data: dict,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    更新当前用户信息

    - **full_name**: 全名（可选）

    返回更新后的用户信息。
    """
    from schemas import UserProfileUpdate

    service = get_user_service(db)

    # 创建更新对象
    update_obj = UserProfileUpdate(**update_data)

    return service.update_profile(current_user, update_obj)

@router.get(
    "/verify",
    summary="验证令牌",
    description="验证当前访问令牌是否有效"
)
async def verify_token(
    current_user: Optional[str] = Depends(get_current_user_optional)
):
    """
    验证令牌

    返回当前令牌是否有效。
    """
    return {
        "valid": current_user is not None,
        "user_id": current_user
    }
