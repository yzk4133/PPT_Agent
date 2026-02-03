"""
注册相关 Schema
"""

from pydantic import BaseModel, EmailStr, Field, validator


class RegisterRequest(BaseModel):
    """用户注册请求"""

    email: EmailStr = Field(..., description="邮箱地址")
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=8, max_length=100, description="密码")
    full_name: str = Field(None, max_length=255, description="全名")

    @validator("username")
    def validate_username(cls, v):
        """验证用户名格式"""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "SecurePass123",
                "full_name": "John Doe"
            }
        }
