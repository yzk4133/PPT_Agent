"""
Services Module

业务服务层，负责业务编排

统一的服务层架构：
- PptGenerationService: PPT 生成服务（主要服务）
- TaskService: 任务管理服务
- AuthService: 认证服务
- UserService: 用户服务
"""

from .ppt_generation_service import (
    PptGenerationService,
    get_ppt_generation_service,
    reset_ppt_generation_service
)
from .task_service import (
    TaskService,
    get_task_service
)
from .auth_service import (
    AuthService,
    get_auth_service,
    reset_auth_service
)
from .user_service import (
    UserService,
    get_user_service,
    reset_user_service
)
from .presentation_service import PresentationService
from .outline_service import OutlineService

__all__ = [
    "PptGenerationService",
    "get_ppt_generation_service",
    "reset_ppt_generation_service",
    "TaskService",
    "get_task_service",
    "AuthService",
    "get_auth_service",
    "reset_auth_service",
    "UserService",
    "get_user_service",
    "reset_user_service",
    "PresentationService",
    "OutlineService",
]
