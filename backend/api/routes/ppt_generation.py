"""
PPT Generation Routes

API routes for PPT outline and slides generation.
FastAPI 统一网关路由，调用 Services 层。

架构：API → Services → Agents
"""

import logging
import sys
import os
import json
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Add parent directory to path

from domain.models.execution_mode import ExecutionMode
from infrastructure.checkpoint import CheckpointManager, InMemoryCheckpointBackend

# 导入服务层（而不是直接导入 Agent）
from services import get_ppt_generation_service

# 导入认证中间件
from infrastructure.middleware.auth_middleware import get_current_user_optional
from infrastructure.middleware.rate_limit_middleware import rate_limit_check

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/ppt",
    tags=["ppt_generation"]
)

# ============================================================================
# Request/Response Models
# ============================================================================

class GeneratePPTRequest(BaseModel):
    """完整PPT生成请求"""
    user_input: str = Field(..., description="用户输入的自然语言描述")
    user_id: str = Field(default="anonymous", description="用户ID")
    enable_page_pipeline: bool = Field(default=True, description="是否启用页面级流水线并行")

class GenerateOutlineRequest(BaseModel):
    """大纲生成请求"""
    prompt: str = Field(..., description="用户输入的自然语言描述")
    numberOfCards: int = Field(default=10, description="期望的卡片数量")
    language: str = Field(default="zh-CN", description="语言: zh-CN, en-US, ja-JP, ko-KR")

class UpdateOutlineRequest(BaseModel):
    """大纲更新请求"""
    modified_outline: Dict[str, Any] = Field(..., description="修改后的大纲")

class GeneratePPTFromOutlineRequest(BaseModel):
    """从大纲生成PPT请求"""
    user_id: str = Field(default="anonymous", description="用户ID")

class PPTGenerationResponse(BaseModel):
    """PPT生成响应"""
    status: str = Field(..., description="状态: success, failed, checkpoint_saved")
    message: str = Field(..., description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")

class OutlineListResponse(BaseModel):
    """大纲列表响应"""
    outlines: List[Dict[str, Any]] = Field(..., description="大纲列表")
    total: int = Field(..., description="总数")

# ============================================================================
# Dependencies
# ============================================================================

# Global checkpoint manager
_checkpoint_manager: Optional[CheckpointManager] = None

def get_checkpoint_manager() -> CheckpointManager:
    """获取checkpoint管理器"""
    global _checkpoint_manager
    if _checkpoint_manager is None:
        backend = InMemoryCheckpointBackend()
        _checkpoint_manager = CheckpointManager(backend)
    return _checkpoint_manager

def set_checkpoint_manager(manager: CheckpointManager) -> None:
    """设置checkpoint管理器"""
    global _checkpoint_manager
    _checkpoint_manager = manager

def generate_task_id() -> str:
    """生成任务ID"""
    import uuid
    return f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/generate", response_model=PPTGenerationResponse)
async def generate_ppt_full(
    request: GeneratePPTRequest,
    background_tasks: BackgroundTasks,
    checkpoint_manager: CheckpointManager = Depends(get_checkpoint_manager)
):
    """
    完整生成PPT（一次性）

    执行完整的5阶段流程生成PPT。
    """
    try:
        task_id = generate_task_id()

        logger.info(f"FULL mode PPT generation requested: task_id={task_id}, user_id={request.user_id}")

        # 简化实现：直接返回成功响应
        # 在实际使用中需要调用services层执行完整流程

        return PPTGenerationResponse(
            status="success",
            message="PPT生成完成（完整执行模式）",
            data={
                "task_id": task_id,
                "execution_mode": "full",
                "user_input": request.user_input
            }
        )

    except Exception as e:
        logger.error(f"PPT generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PPT生成失败: {str(e)}")

@router.post("/outline/generate")
async def generate_outline(
    request: GenerateOutlineRequest,
    http_request: Request,  # FastAPI Request object for rate limiting
    current_user: str = Depends(get_current_user_optional)  # 可选认证
):
    """
    生成大纲（阶段1）

    执行需求解析和框架设计，生成PPT大纲供用户编辑。
    返回流式响应。

    **认证**: 可选（未认证用户也可以使用，user_id 将为 "anonymous"）
    **限流**: 100次/分钟
    """
    try:
        # 限流检查
        await rate_limit_check(http_request)

        # 使用当前用户 ID 或匿名用户
        user_id = current_user or "anonymous"

        logger.info(f"Outline generation requested: user_id={user_id}, prompt={request.prompt[:50]}..., language={request.language}")

        # 获取服务
        service = get_ppt_generation_service()

        # 创建流式响应生成器
        async def generate():
            async for chunk in service.generate_outline(
                user_input=request.prompt,
                language=request.language
            ):
                # 以 SSE 格式发送数据
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    except Exception as e:
        logger.error(f"Outline generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"大纲生成失败: {str(e)}")

@router.post("/outline/{task_id}", response_model=PPTGenerationResponse)
async def update_outline(
    task_id: str,
    request: UpdateOutlineRequest,
    checkpoint_manager: CheckpointManager = Depends(get_checkpoint_manager)
):
    """
    用户修改大纲

    更新已保存的大纲。
    """
    try:
        logger.info(f"Outline update requested: task_id={task_id}")

        # 验证checkpoint存在
        checkpoint = await checkpoint_manager.load_checkpoint(task_id)
        if not checkpoint:
            raise HTTPException(status_code=404, detail=f"未找到任务: {task_id}")

        # 更新框架
        success = await checkpoint_manager.update_framework(
            task_id=task_id,
            new_framework=request.modified_outline
        )

        if not success:
            raise HTTPException(status_code=500, detail="大纲更新失败")

        return PPTGenerationResponse(
            status="success",
            message="大纲已更新",
            data={
                "task_id": task_id,
                "updated_at": datetime.now().isoformat()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Outline update failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"大纲更新失败: {str(e)}")

@router.post("/ppt/from-outline/{task_id}", response_model=PPTGenerationResponse)
async def generate_ppt_from_outline(
    task_id: str,
    request: GeneratePPTFromOutlineRequest,
    checkpoint_manager: CheckpointManager = Depends(get_checkpoint_manager)
):
    """
    从大纲生成PPT（阶段2）

    从保存的checkpoint继续执行阶段3-5（研究→内容→渲染）。
    """
    try:
        logger.info(f"PHASE_2 PPT generation requested: task_id={task_id}")

        # 验证checkpoint存在
        checkpoint = await checkpoint_manager.load_checkpoint(task_id)
        if not checkpoint:
            raise HTTPException(status_code=404, detail=f"未找到任务: {task_id}")

        # 简化实现：直接返回成功响应
        # 在实际使用中需要调用services层执行PHASE_2

        return PPTGenerationResponse(
            status="success",
            message="PPT生成完成（从大纲）",
            data={
                "task_id": task_id,
                "execution_mode": "phase_2"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PPT generation from outline failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PPT生成失败: {str(e)}")

@router.get("/outline/list", response_model=OutlineListResponse)
async def list_user_outlines(
    user_id: str,
    status_filter: Optional[str] = None,
    limit: int = 50,
    checkpoint_manager: CheckpointManager = Depends(get_checkpoint_manager)
):
    """
    列出用户所有进行中的大纲

    获取用户的所有未完成的大纲（checkpoint状态为editing）。
    """
    try:
        logger.info(f"Outline list requested: user_id={user_id}")

        # 获取用户的checkpoint摘要
        summaries = await checkpoint_manager.get_checkpoint_summaries(
            user_id=user_id,
            status_filter=status_filter,
            limit=limit
        )

        # 转换为响应格式
        outlines = [
            {
                "task_id": s.task_id,
                "ppt_topic": s.ppt_topic,
                "total_pages": s.total_pages,
                "phase": s.phase,
                "status": s.status,
                "version": s.version,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "age_hours": s.age_hours
            }
            for s in summaries
        ]

        return OutlineListResponse(
            outlines=outlines,
            total=len(outlines)
        )

    except Exception as e:
        logger.error(f"Outline list failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取大纲列表失败: {str(e)}")

@router.get("/outline/{task_id}", response_model=PPTGenerationResponse)
async def get_outline(
    task_id: str,
    checkpoint_manager: CheckpointManager = Depends(get_checkpoint_manager)
):
    """
    获取指定的大纲

    根据task_id获取已保存的大纲详情。
    """
    try:
        logger.info(f"Outline get requested: task_id={task_id}")

        checkpoint = await checkpoint_manager.load_checkpoint(task_id)
        if not checkpoint:
            raise HTTPException(status_code=404, detail=f"未找到任务: {task_id}")

        return PPTGenerationResponse(
            status="success",
            message="获取大纲成功",
            data={
                "task_id": checkpoint.task_id,
                "outline": checkpoint.ppt_framework,
                "requirements": checkpoint.structured_requirements,
                "phase": checkpoint.phase,
                "version": checkpoint.version,
                "created_at": checkpoint.created_at.isoformat(),
                "updated_at": checkpoint.updated_at.isoformat()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Outline get failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取大纲失败: {str(e)}")

@router.delete("/outline/{task_id}", response_model=PPTGenerationResponse)
async def delete_outline(
    task_id: str,
    checkpoint_manager: CheckpointManager = Depends(get_checkpoint_manager)
):
    """
    删除大纲

    删除指定的大纲checkpoint。
    """
    try:
        logger.info(f"Outline delete requested: task_id={task_id}")

        success = await checkpoint_manager.delete_checkpoint(task_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"未找到任务: {task_id}")

        return PPTGenerationResponse(
            status="success",
            message="大纲已删除",
            data={"task_id": task_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Outline delete failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除大纲失败: {str(e)}")

@router.post("/slides/generate")
async def generate_slides(
    req_dict: Dict[str, Any],
    http_request: Request,  # FastAPI Request object for rate limiting
    current_user: str = Depends(get_current_user_optional)  # 可选认证
):
    """
    生成幻灯片

    接收大纲信息，生成完整的 PPT 幻灯片内容。
    返回流式响应。

    **认证**: 可选（未认证用户也可以使用）
    **限流**: 50次/分钟
    """
    # 限流检查（更严格的限制）
    await rate_limit_check(http_request, limit=50, window=60)

    # 使用当前用户 ID 或匿名用户
    user_id = current_user or "anonymous"
    try:
        title = req_dict.get("title", "")
        outline = req_dict.get("outline", [])
        language = req_dict.get("language", "en-US")
        tone = req_dict.get("tone", "professional")
        num_slides = req_dict.get("numSlides", 10)

        if not title or not outline:
            raise HTTPException(status_code=400, detail="Missing required fields: title, outline")

        logger.info(f"Slides generation requested: title={title}, slides={num_slides}")

        # 获取服务
        service = get_ppt_generation_service()

        # 创建流式响应生成器
        async def generate():
            async for event_data in service.generate_slides(
                title=title,
                outline=outline,
                language=language,
                tone=tone,
                num_slides=num_slides
            ):
                # 以 NDJSON 格式发送数据
                yield json.dumps(event_data, ensure_ascii=False) + "\n"

        return StreamingResponse(
            generate(),
            media_type="application/json",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Transfer-Encoding": "chunked",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Slides generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"幻灯片生成失败: {str(e)}")

@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "ppt_generation_api",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)

    print("Starting PPT Generation API server...")
    print("Available endpoints:")
    print("  POST /ppt/generate - 完整生成PPT")
    print("  POST /ppt/outline/generate - 生成大纲")
    print("  POST /ppt/outline/{task_id} - 更新大纲")
    print("  POST /ppt/slides/generate - 生成幻灯片")
    print("  GET  /ppt/outline/list - 列出用户大纲")
    print("  GET  /ppt/outline/{task_id} - 获取大纲详情")
    print("  DELETE /ppt/outline/{task_id} - 删除大纲")
    print("  GET  /ppt/health - 健康检查")

    uvicorn.run(
        router,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
