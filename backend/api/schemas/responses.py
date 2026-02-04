"""
API Response Schemas

API响应模式定义
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class Status(str, Enum):
    """状态枚举"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    PROCESSING = "processing"

class BaseResponse(BaseModel):
    """
    基础响应
    """

    status: Status = Field(..., description="状态")
    message: str = Field(..., description="消息")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "操作成功",
                "timestamp": "2025-02-02T12:00:00"
            }
        }

class PresentationStatus(str, Enum):
    """演示文稿状态"""
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

class StageProgress(BaseModel):
    """
    阶段进度
    """

    stage: str = Field(..., description="阶段名称")
    completed: bool = Field(..., description="是否完成")
    count: Optional[int] = Field(None, description="数量")
    total: Optional[int] = Field(None, description="总数")
    success_rate: Optional[float] = Field(None, description="成功率")

class PresentationProgressResponse(BaseModel):
    """
    演示文稿进度响应
    """

    presentation_id: str = Field(..., description="演示文稿ID")
    title: str = Field(..., description="标题")
    status: PresentationStatus = Field(..., description="状态")
    stages: Dict[str, StageProgress] = Field(..., description="各阶段进度")
    created_at: str = Field(..., description="创建时间")
    completed_at: Optional[str] = Field(None, description="完成时间")

    class Config:
        json_schema_extra = {
            "example": {
                "presentation_id": "ppt_20250202_120000_user123",
                "title": "人工智能的发展历程",
                "status": "generating",
                "stages": {
                    "topics": {"stage": "topics", "completed": True, "count": 5},
                    "research": {
                        "stage": "research",
                        "completed": True,
                        "total": 5,
                        "success": 5,
                        "success_rate": 1.0
                    },
                    "slides": {"stage": "slides", "completed": False}
                },
                "created_at": "2025-02-02T12:00:00"
            }
        }

class PresentationCreateResponse(BaseModel):
    """
    演示文稿创建响应
    """

    presentation_id: str = Field(..., description="演示文稿ID")
    title: str = Field(..., description="标题")
    status: PresentationStatus = Field(..., description="状态")
    message: str = Field(..., description="消息")

    class Config:
        json_schema_extra = {
            "example": {
                "presentation_id": "ppt_20250202_120000_user123",
                "title": "人工智能的发展历程",
                "status": "generating",
                "message": "演示文稿生成中..."
            }
        }

class PresentationDetailResponse(BaseModel):
    """
    演示文稿详情响应
    """

    presentation_id: str = Field(..., description="演示文稿ID")
    title: str = Field(..., description="标题")
    outline: str = Field(..., description="大纲")
    status: PresentationStatus = Field(..., description="状态")
    generated_content: Optional[str] = Field(None, description="生成的内容")
    progress: Dict[str, Any] = Field(..., description="进度信息")
    created_at: str = Field(..., description="创建时间")
    completed_at: Optional[str] = Field(None, description="完成时间")

    class Config:
        json_schema_extra = {
            "example": {
                "presentation_id": "ppt_20250202_120000_user123",
                "title": "人工智能的发展历程",
                "outline": "人工智能的发展历程...",
                "status": "completed",
                "generated_content": "```xml\n<PRESENTATION>\n...",
                "progress": {
                    "status": "completed",
                    "stages": {
                        "topics": {"completed": True, "count": 5},
                        "research": {"completed": True, "total": 5, "success": 5},
                        "slides": {"completed": True, "total": 10}
                    }
                },
                "created_at": "2025-02-02T12:00:00",
                "completed_at": "2025-02-02T12:05:00"
            }
        }

class OutlineGenerateResponse(BaseModel):
    """
    大纲生成响应
    """

    outline: str = Field(..., description="生成的大纲")
    language: str = Field(..., description="语言")
    message: str = Field(..., description="消息")

    class Config:
        json_schema_extra = {
            "example": {
                "outline": "# 人工智能在医疗领域的应用\n\n## 1. 引言\n...",
                "language": "EN-US",
                "message": "大纲生成成功"
            }
        }

class UserPreferencesResponse(BaseModel):
    """
    用户偏好响应
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

class ErrorResponse(BaseModel):
    """
    错误响应
    """

    status: Status = Field(Status.ERROR, description="状态")
    error_code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "error_code": "INVALID_INPUT",
                "message": "输入参数无效",
                "details": {
                    "field": "outline",
                    "reason": "大纲内容过短"
                },
                "timestamp": "2025-02-02T12:00:00"
            }
        }

class HealthCheckResponse(BaseModel):
    """
    健康检查响应
    """

    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="版本")
    uptime: float = Field(..., description="运行时间（秒）")
    services: Dict[str, str] = Field(..., description="各服务状态")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime": 3600.0,
                "services": {
                    "agent": "ok",
                    "database": "ok",
                    "cache": "ok"
                }
            }
        }
