"""
PPT Generation Routes

简化的 PPT 生成 API 路由，只保留核心功能。
"""

import logging
import json
import os
import sys
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# 添加 backend 到路径
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from models.execution_mode import ExecutionMode
from infrastructure.checkpoint import CheckpointManager, InMemoryCheckpointBackend
from infrastructure.middleware import rate_limit_middleware
from infrastructure.exceptions import RateLimitExceededException

# 导入服务（现在在 api 层）
from api.ppt_service import PptGenerationServiceLangChain, get_ppt_generation_service_langchain

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ppt", tags=["PPT Generation"])

# ============================================================================
# Request/Response Models
# ============================================================================


class GeneratePPTRequest(BaseModel):
    """一次性完整生成 PPT"""

    user_input: str = Field(..., description="用户输入的自然语言描述")
    language: str = Field(default="zh-CN", description="语言: zh-CN, en-US")
    num_slides: int = Field(default=10, description="幻灯片数量", ge=1, le=50)


class GenerateSlidesRequest(BaseModel):
    """从大纲生成幻灯片"""

    title: str = Field(..., description="PPT 标题")
    outline: list = Field(..., description="大纲列表")
    language: str = Field(default="zh-CN", description="语言")
    tone: str = Field(default="professional", description="风格")
    num_slides: int = Field(default=10, description="幻灯片数量", ge=1, le=50)


class GenerateOutlineRequest(BaseModel):
    """生成大纲请求"""

    prompt: str = Field(..., description="用户输入主题")
    numberOfCards: int = Field(default=10, description="期望卡片数量", ge=1, le=50)
    language: str = Field(default="zh-CN", description="语言")


class PPTResponse(BaseModel):
    """PPT 生成响应"""

    status: str
    message: str
    data: Dict[str, Any] = Field(default={})


# ============================================================================
# Helper Functions
# ============================================================================

_checkpoint_manager: CheckpointManager = None


def get_checkpoint_manager() -> CheckpointManager:
    """获取 checkpoint 管理器"""
    global _checkpoint_manager
    if _checkpoint_manager is None:
        backend = InMemoryCheckpointBackend()
        _checkpoint_manager = CheckpointManager(backend)
    return _checkpoint_manager


# ============================================================================
# API Endpoints - 只保留 3 个核心端点
# ============================================================================


@router.post("/outline/generate")
async def generate_outline(request: GenerateOutlineRequest, http_request: Request):
    """
    生成大纲（前端第一段）

    返回 SSE 流，格式：
    data: {"content": "..."}
    """
    try:
        await rate_limit_middleware.rate_limit_check(http_request, limit=50, window=60)

        logger.info(
            f"Outline generation request: prompt={request.prompt[:50]}..., cards={request.numberOfCards}"
        )

        service = get_ppt_generation_service_langchain()

        async def event_stream():
            try:
                user_input = f"{request.prompt}\n\n页数要求：{request.numberOfCards}页"
                async for chunk in service.generate_outline(
                    user_input=user_input,
                    language=request.language,
                    expected_cards=request.numberOfCards,
                ):
                    payload = {"content": chunk}
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.error(f"Outline generation error: {e}", exc_info=True)
                err_payload = {"content": f"错误：{str(e)}"}
                yield f"data: {json.dumps(err_payload, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "X-Generation-Contract": "outline-v2",
            },
        )

    except RateLimitExceededException:
        raise
    except Exception as e:
        logger.error(f"Outline generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"大纲生成失败: {str(e)}")


@router.post("/generate", response_model=PPTResponse)
async def generate_ppt(request: GeneratePPTRequest, http_request: Request):
    """
    一次性完整生成 PPT（最简单的使用方式）

    **限流**: 30次/分钟
    """
    try:
        # 限流检查
        await rate_limit_middleware.rate_limit_check(http_request, limit=30, window=60)

        logger.info(f"PPT generation request: {request.user_input[:50]}...")

        # 获取服务
        service = get_ppt_generation_service_langchain()

        # 生成 PPT
        result_data = {}

        async def generate():
            """流式生成 PPT"""
            try:
                async for event in service.generate_ppt_full(
                    user_input=request.user_input,
                    user_id="anonymous",
                    enable_page_pipeline=True,
                ):
                    # 以 JSON 格式发送进度
                    if isinstance(event, dict):
                        yield json.dumps(event, ensure_ascii=False) + "\n"
            except Exception as e:
                logger.error(f"PPT generation error: {e}", exc_info=True)
                error_event = {"type": "error", "message": str(e)}
                yield json.dumps(error_event, ensure_ascii=False) + "\n"

        return StreamingResponse(
            generate(),
            media_type="application/json",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Generation-Contract": "ppt-v2",
            },
        )

    except RateLimitExceededException:
        raise
    except Exception as e:
        logger.error(f"PPT generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PPT生成失败: {str(e)}")


@router.post("/slides/generate")
async def generate_slides(request: GenerateSlidesRequest, http_request: Request):
    """
    从大纲生成幻灯片（两阶段模式的第二步）

    适用场景：
    1. 用户已经通过其他方式生成或编辑了大纲
    2. 需要根据大纲生成完整的 PPT

    **限流**: 50次/分钟
    """
    try:
        # 限流检查
        await rate_limit_middleware.rate_limit_check(http_request, limit=50, window=60)

        logger.info(f"Slides generation: title={request.title}, slides={request.num_slides}")

        # 获取服务
        service = get_ppt_generation_service_langchain()

        async def generate():
            """流式生成幻灯片"""
            try:
                # 转换 outline 为字符串
                outline_text = "\n".join(
                    [f"{i+1}. {item}" for i, item in enumerate(request.outline)]
                )

                async for event in service.generate_slides(
                    title=request.title,
                    outline=request.outline,
                    language=request.language,
                    tone=request.tone,
                    num_slides=request.num_slides,
                ):
                    if isinstance(event, dict):
                        yield json.dumps(event, ensure_ascii=False) + "\n"
            except Exception as e:
                logger.error(f"Slides generation error: {e}", exc_info=True)
                error_event = {"type": "error", "message": str(e)}
                yield json.dumps(error_event, ensure_ascii=False) + "\n"

        return StreamingResponse(
            generate(),
            media_type="application/json",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Generation-Contract": "slides-v2",
            },
        )

    except RateLimitExceededException:
        raise
    except Exception as e:
        logger.error(f"Slides generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"幻灯片生成失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "ppt_generation_api",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================================
# 主程序入口（用于直接运行此路由测试）
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)

    print("Starting PPT Generation API server...")
    print("Available endpoints:")
    print("  POST /ppt/outline/generate  - 生成大纲")
    print("  POST /ppt/generate         - 一次性完整生成 PPT")
    print("  POST /ppt/slides/generate   - 从大纲生成幻灯片")
    print("  GET  /ppt/health            - 健康检查")

    uvicorn.run(router, host="0.0.0.0", port=8001, log_level="info")
