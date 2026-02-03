"""
Presentation Routes

演示文稿相关的API路由
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, status

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from api.schemas.requests import (
    PresentationCreateRequest,
    ProgressQueryRequest
)
from api.schemas.responses import (
    PresentationCreateResponse,
    PresentationDetailResponse,
    PresentationProgressResponse,
    ErrorResponse
)
from services import PresentationService, create_presentation_from_request
from domain.models import PresentationRequest as CorePresentationRequest


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/presentation",
    tags=["presentation"]
)

# 全局服务实例（在生产环境中应该通过依赖注入）
_presentation_service: PresentationService = None
_background_tasks: Dict[str, Any] = {}


def set_presentation_service(service: PresentationService):
    """设置演示文稿服务实例"""
    global _presentation_service
    _presentation_service = service


@router.post(
    "/create",
    response_model=PresentationCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="创建演示文稿",
    description="根据大纲创建新的演示文稿"
)
async def create_presentation(
    request: PresentationCreateRequest,
    background_tasks: BackgroundTasks
):
    """
    创建演示文稿API

    接收大纲内容，异步生成PPT演示文稿。

    Args:
        request: 演示文稿创建请求
        background_tasks: 后台任务

    Returns:
        PresentationCreateResponse: 包含演示文稿ID的响应
    """
    try:
        # 转换请求为内部模型
        core_request = CorePresentationRequest(
            outline=request.outline,
            num_slides=request.num_slides,
            language=request.language.value,
            user_id=request.user_id,
            theme=request.theme,
            style=request.style,
            metadata=request.metadata
        )

        # 创建演示文稿
        presentation = await _presentation_service.create_presentation(core_request)

        # 添加后台生成任务
        background_tasks.add_task(
            _generate_presentation_background,
            presentation
        )

        return PresentationCreateResponse(
            presentation_id=presentation.id,
            title=presentation.title,
            status=presentation.status.value if hasattr(presentation.status, 'value') else presentation.status,
            message="演示文稿创建成功，正在生成中..."
        )

    except Exception as e:
        logger.error(f"创建演示文稿失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/progress/{presentation_id}",
    response_model=PresentationProgressResponse,
    summary="查询生成进度",
    description="查询演示文稿的生成进度"
)
async def get_progress(presentation_id: str):
    """
    查询生成进度API

    Args:
        presentation_id: 演示文稿ID

    Returns:
        PresentationProgressResponse: 包含进度信息的响应
    """
    # TODO: 实现进度查询逻辑
    # 这里应该从数据库或缓存中获取演示文稿的进度信息

    return PresentationProgressResponse(
        presentation_id=presentation_id,
        title="示例标题",
        status="generating",
        stages={
            "topics": {"stage": "topics", "completed": True, "count": 5},
            "research": {"stage": "research", "completed": False},
            "slides": {"stage": "slides", "completed": False}
        },
        created_at="2025-02-02T12:00:00"
    )


@router.get(
    "/detail/{presentation_id}",
    response_model=PresentationDetailResponse,
    summary="查询演示文稿详情",
    description="查询演示文稿的详细信息"
)
async def get_detail(presentation_id: str):
    """
    查询演示文稿详情API

    Args:
        presentation_id: 演示文稿ID

    Returns:
        PresentationDetailResponse: 包含详细信息的响应
    """
    # TODO: 实现详情查询逻辑
    # 这里应该从数据库中获取演示文稿的详细信息

    return PresentationDetailResponse(
        presentation_id=presentation_id,
        title="示例标题",
        outline="示例大纲...",
        status="completed",
        generated_content="```xml\n<PRESENTATION>\n...",
        progress={
            "status": "completed",
            "stages": {
                "topics": {"completed": True, "count": 5},
                "research": {"completed": True, "total": 5, "success": 5},
                "slides": {"completed": True, "total": 10}
            }
        },
        created_at="2025-02-02T12:00:00",
        completed_at="2025-02-02T12:05:00"
    )


async def _generate_presentation_background(presentation):
    """
    后台生成演示文稿的任务

    Args:
        presentation: 演示文稿实例
    """
    try:
        logger.info(f"开始后台生成演示文稿: {presentation.id}")

        # 获取上下文
        from domain.interfaces import AgentContext
        context = AgentContext(
            session_id=presentation.id,
            user_id=presentation.metadata.user_id if presentation.metadata else "anonymous"
        )

        # 生成演示文稿
        updated_presentation = await _presentation_service.generate_presentation(
            presentation, context
        )

        logger.info(f"演示文稿生成完成: {updated_presentation.id}")

        # TODO: 保存到数据库

    except Exception as e:
        logger.error(f"后台生成演示文稿失败: {e}")
        # TODO: 更新状态为失败


if __name__ == "__main__":
    # 测试代码
    import uvicorn
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    uvicorn.run(app, host="0.0.0.0", port=8000)
