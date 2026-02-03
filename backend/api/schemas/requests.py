"""
API Request Schemas

API请求模式定义
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class Language(str, Enum):
    """支持的语言"""
    EN_US = "EN-US"
    ZH_CN = "ZH-CN"
    JA_JP = "JA-JP"
    KO_KR = "KO-KR"


class PresentationCreateRequest(BaseModel):
    """
    演示文稿创建请求
    """

    outline: str = Field(..., description="PPT大纲内容", min_length=10)
    num_slides: int = Field(10, description="幻灯片数量", ge=1, le=100)
    language: Language = Field(Language.EN_US, description="语言")
    user_id: str = Field("anonymous", description="用户ID")
    theme: str = Field("", description="主题")
    style: str = Field("", description="风格")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "outline": "人工智能的发展历程和应用",
                "num_slides": 10,
                "language": "EN-US",
                "user_id": "user123"
            }
        }


class OutlineGenerateRequest(BaseModel):
    """
    大纲生成请求
    """

    topic: str = Field(..., description="主题", min_length=2)
    language: Language = Field(Language.EN_US, description="语言")
    user_id: str = Field("anonymous", description="用户ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "人工智能在医疗领域的应用",
                "language": "EN-US",
                "user_id": "user123"
            }
        }


class ProgressQueryRequest(BaseModel):
    """
    进度查询请求
    """

    presentation_id: str = Field(..., description="演示文稿ID")

    class Config:
        json_schema_extra = {
            "example": {
                "presentation_id": "ppt_20250202_120000_user123"
            }
        }


class UserPreferencesUpdateRequest(BaseModel):
    """
    用户偏好更新请求
    """

    user_id: str = Field(..., description="用户ID")
    preferences: Dict[str, Any] = Field(..., description="偏好设置")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "preferences": {
                    "language": "EN-US",
                    "default_slides": 10,
                    "theme": "modern"
                }
            }
        }


class HealthCheckRequest(BaseModel):
    """
    健康检查请求
    """

    class Config:
        json_schema_extra = {
            "example": {}
        }
