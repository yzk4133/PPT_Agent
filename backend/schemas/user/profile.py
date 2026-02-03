"""
用户相关 Schema
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserProfile(BaseModel):
    """用户配置"""

    id: str = Field(..., description="用户 ID")
    email: EmailStr = Field(..., description="邮箱地址")
    username: str = Field(..., description="用户名")
    full_name: Optional[str] = Field(None, description="全名")
    is_active: bool = Field(..., description="账户是否激活")
    is_verified: bool = Field(..., description="邮箱是否验证")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    roles: List[str] = Field(default_factory=list, description="角色列表")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "username": "johndoe",
                "full_name": "John Doe",
                "is_active": True,
                "is_verified": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "last_login": "2024-01-01T12:00:00Z",
                "roles": ["USER"]
            }
        }


class UserProfileUpdate(BaseModel):
    """用户配置更新"""

    full_name: Optional[str] = Field(None, max_length=255, description="全名")
    # 可以添加更多可更新字段

    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "John Smith"
            }
        }


class UserResponse(BaseModel):
    """用户响应（简化版）"""

    id: str = Field(..., description="用户 ID")
    email: EmailStr = Field(..., description="邮箱地址")
    username: str = Field(..., description="用户名")
    full_name: Optional[str] = Field(None, description="全名")
    roles: List[str] = Field(default_factory=list, description="角色列表")

    class Config:
        from_attributes = True
