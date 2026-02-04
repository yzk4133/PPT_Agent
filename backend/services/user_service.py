"""
用户服务

提供用户管理相关的业务逻辑：
- 用户配置管理
- 权限检查
"""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from models import User, Permission
from schemas import UserProfile, UserProfileUpdate
from infrastructure.exceptions import ResourceNotFoundException, AuthorizationException

logger = logging.getLogger(__name__)

class UserService:
    """用户服务"""

    def __init__(self, db: Session):
        """
        初始化用户服务

        Args:
            db: 数据库会话
        """
        self.db = db

    def get_profile(self, user_id: str) -> UserProfile:
        """
        获取用户配置

        Args:
            user_id: 用户 ID

        Returns:
            用户配置
        """
        import uuid
        user = self.db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            raise ResourceNotFoundException("用户", user_id)
        return UserProfile.from_orm(user)

    def get_profile_by_email(self, email: str) -> UserProfile:
        """
        通过邮箱获取用户配置

        Args:
            email: 邮箱地址

        Returns:
            用户配置
        """
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise ResourceNotFoundException("用户", email)
        return UserProfile.from_orm(user)

    def update_profile(
        self,
        user_id: str,
        update_data: UserProfileUpdate
    ) -> UserProfile:
        """
        更新用户配置

        Args:
            user_id: 用户 ID
            update_data: 更新数据

        Returns:
            更新后的用户配置
        """
        import uuid
        from datetime import datetime

        user = self.db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            raise ResourceNotFoundException("用户", user_id)

        # 更新字段
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(user, field, value)

        user.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(user)

        logger.info(f"User profile updated: {user.email}")

        return UserProfile.from_orm(user)

    def has_permission(self, user_id: str, permission_name: str) -> bool:
        """
        检查用户是否有指定权限

        Args:
            user_id: 用户 ID
            permission_name: 权限名称

        Returns:
            是否有权限
        """
        import uuid
        user = self.db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            return False

        # 检查用户的所有角色
        for role in user.roles:
            if role.has_permission(permission_name):
                return True

        return False

    def has_role(self, user_id: str, role_name: str) -> bool:
        """
        检查用户是否有指定角色

        Args:
            user_id: 用户 ID
            role_name: 角色名称

        Returns:
            是否有角色
        """
        import uuid
        user = self.db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            return False

        return user.has_role(role_name)

    def require_permission(self, user_id: str, permission_name: str):
        """
        要求用户必须有指定权限，否则抛出异常

        Args:
            user_id: 用户 ID
            permission_name: 权限名称

        Raises:
            AuthorizationException: 用户没有该权限
        """
        if not self.has_permission(user_id, permission_name):
            raise AuthorizationException(permission_name)

    def require_role(self, user_id: str, role_name: str):
        """
        要求用户必须有指定角色，否则抛出异常

        Args:
            user_id: 用户 ID
            role_name: 角色名称

        Raises:
            AuthorizationException: 用户没有该角色
        """
        if not self.has_role(user_id, role_name):
            raise AuthorizationException(f"需要角色: {role_name}")

    def get_all_permissions(self, user_id: str) -> List[str]:
        """
        获取用户的所有权限

        Args:
            user_id: 用户 ID

        Returns:
            权限名称列表
        """
        import uuid
        user = self.db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            return []

        permissions = set()
        for role in user.roles:
            for permission in role.permissions:
                permissions.add(permission.name)

        return list(permissions)

# 全局服务实例（单例）
_user_service: Optional[UserService] = None

def get_user_service(db: Session) -> UserService:
    """
    获取用户服务实例

    Args:
        db: 数据库会话

    Returns:
        UserService 实例
    """
    return UserService(db)

def reset_user_service():
    """重置用户服务（用于测试）"""
    global _user_service
    _user_service = None
