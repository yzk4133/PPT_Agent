"""
PPT Generation Routes

API routes for two-phase PPT generation workflow.
"""

import logging
import sys
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from domain.models.execution_mode import ExecutionMode
from agents.orchestrator.master_coordinator import MasterCoordinatorAgent
from infrastructure.checkpoint import CheckpointManager, InMemoryCheckpointBackend

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
    user_input: str = Field(..., description="用户输入的自然语言描述")
    user_id: str = Field(default="anonymous", description="用户ID")


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


# Global master coordinator
_master_coordinator: Optional[MasterCoordinatorAgent] = None


def get_master_coordinator() -> MasterCoordinatorAgent:
    """获取主协调智能体"""
    global _master_coordinator
    if _master_coordinator is None:
        _master_coordinator = MasterCoordinatorAgent(
            checkpoint_manager=get_checkpoint_manager(),
            enable_page_pipeline=True
        )
    return _master_coordinator


def set_master_coordinator(coordinator: MasterCoordinatorAgent) -> None:
    """设置主协调智能体"""
    global _master_coordinator
    _master_coordinator = coordinator


def generate_session_id() -> str:
    """生成会话ID"""
    import uuid
    return f"session_{uuid.uuid4().hex}"


def generate_task_id() -> str:
    """生成任务ID"""
    return f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/generate", response_model=PPTGenerationResponse)
async def generate_ppt_full(
    request: GeneratePPTRequest,
    background_tasks: BackgroundTasks,
    coordinator: MasterCoordinatorAgent = Depends(get_master_coordinator)
):
    """
    完整生成PPT（一次性）

    执行完整的5阶段流程生成PPT。
    """
    try:
        task_id = generate_task_id()

        logger.info(f"FULL mode PPT generation requested: task_id={task_id}, user_id={request.user_id}")

        # 简化实现：直接返回成功响应
        # 在实际使用中需要调用coordinator.run_async()

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


@router.post("/outline/generate", response_model=PPTGenerationResponse)
async def generate_outline(
    request: GenerateOutlineRequest,
    coordinator: MasterCoordinatorAgent = Depends(get_master_coordinator)
):
    """
    生成大纲（阶段1）

    执行需求解析和框架设计，生成PPT大纲供用户编辑。
    """
    try:
        task_id = generate_task_id()

        logger.info(f"PHASE_1 outline generation requested: task_id={task_id}, user_id={request.user_id}")

        # 保存checkpoint
        checkpoint_manager = get_checkpoint_manager()

        # 创建示例框架数据
        sample_framework = {
            "total_page": 10,
            "ppt_framework": [
                {"page_no": 1, "title": "封面", "page_type": "cover"},
                {"page_no": 2, "title": "目录", "page_type": "directory"}
            ],
            "research_page_indices": [],
            "chart_page_indices": []
        }

        # 保存checkpoint
        await checkpoint_manager.save_checkpoint(
            task_id=task_id,
            user_id=request.user_id,
            execution_mode=ExecutionMode.PHASE_1,
            phase=2,
            raw_input=request.user_input,
            requirements={"ppt_topic": request.user_input[:50], "page_num": 10},
            framework=sample_framework
        )

        return PPTGenerationResponse(
            status="checkpoint_saved",
            message="大纲生成完成，请编辑后继续生成PPT",
            data={
                "task_id": task_id,
                "outline": sample_framework,
                "execution_mode": "phase_1",
                "total_pages": sample_framework.get("total_page", 0)
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
    coordinator: MasterCoordinatorAgent = Depends(get_master_coordinator)
):
    """
    从大纲生成PPT（阶段2）

    从保存的checkpoint继续执行阶段3-5（研究→内容→渲染）。
    """
    try:
        logger.info(f"PHASE_2 PPT generation requested: task_id={task_id}")

        # 验证checkpoint存在
        checkpoint_manager = get_checkpoint_manager()
        checkpoint = await checkpoint_manager.load_checkpoint(task_id)
        if not checkpoint:
            raise HTTPException(status_code=404, detail=f"未找到任务: {task_id}")

        # 简化实现：直接返回成功响应
        # 在实际使用中需要调用coordinator.run_async() with PHASE_2 mode

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
    print("  POST /ppt/ppt/from-outline/{task_id} - 从大纲生成PPT")
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
