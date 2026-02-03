"""
记忆系统REST API - Memory System REST API

提供监控和管理接口：

1. GET  /api/memory/stats - 全局统计
2. GET  /api/memory/promotions - 提升历史
3. GET  /api/memory/users/{id}/preferences - 用户偏好
4. GET  /api/memory/agents/{name}/performance - Agent性能
5. POST /api/memory/promote - 手动提升数据
6. POST /api/memory/cleanup - 执行清理
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field

# 导入服务
from ..core.hierarchical_memory_manager import (
    HierarchicalMemoryManager,
    get_global_memory_manager,
    MemoryScope,
    MemoryLayer,
)
from ..core.promotion_engine import PromotionConfig
from ..services.user_preference_service import UserPreferenceService
from ..services.agent_decision_service import AgentDecisionService
from ..services.shared_workspace_service import SharedWorkspaceService
from ..services.distributed_lock_service import get_lock_service
from ..services.lifecycle_manager_service import get_lifecycle_manager
from ..database import get_db

logger = logging.getLogger(__name__)


# ============================================================================
# 路由器
# ============================================================================

router = APIRouter(prefix="/api/memory", tags=["memory"])


# ============================================================================
# 响应模型
# ============================================================================

class MemoryStatsResponse(BaseModel):
    """内存统计响应"""
    l1_transient: Dict[str, Any] = Field(description="L1层统计")
    l2_short_term: Dict[str, Any] = Field(description="L2层统计")
    l3_long_term: Dict[str, Any] = Field(description="L3层统计")
    promotion: Dict[str, Any] = Field(description="提升统计")
    total_data_count: int = Field(description="总数据量")
    promotion_engine: Optional[Dict[str, Any]] = Field(None, description="提升引擎统计")


class PromotionEventResponse(BaseModel):
    """提升事件响应"""
    event_id: str
    timestamp: str
    key: str
    from_layer: str
    to_layer: str
    reason: str
    scope: str
    scope_id: str
    access_count: int
    importance: float
    session_count: int
    explanation: str
    success: bool


class UserPreferencesResponse(BaseModel):
    """用户偏好响应"""
    user_id: str
    preferences: Dict[str, Any]
    total_sessions: int
    avg_satisfaction_score: float


class AgentPerformanceResponse(BaseModel):
    """Agent性能响应"""
    agent_name: str
    total_decisions: int
    success_rate: float
    avg_execution_time_ms: float
    common_actions: List[Dict[str, Any]]
    recent_decisions: List[Dict[str, Any]]


class PromoteRequest(BaseModel):
    """提升请求"""
    key: str = Field(description="数据键")
    scope: str = Field(description="作用域")
    scope_id: str = Field(description="作用域ID")
    reason: str = Field(default="manual_promotion", description="提升原因")


class PromoteResponse(BaseModel):
    """提升响应"""
    success: bool
    message: str


class CleanupResponse(BaseModel):
    """清理响应"""
    decayed_count: int
    archived_count: int
    cleaned_count: int
    message: str


# ============================================================================
# API端点
# ============================================================================

@router.get("/stats", response_model=MemoryStatsResponse)
async def get_memory_stats():
    """
    获取全局统计信息

    返回各层的统计信息，包括：
    - L1瞬时内存：命中率、数据量、容量
    - L2短期内存：Redis状态、命中率
    - L3长期内存：记录数、平均重要性
    - 提升统计：提升次数、原因分布
    """
    try:
        manager = get_global_memory_manager()
        stats = await manager.get_stats()
        return MemoryStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/promotions", response_model=List[PromotionEventResponse])
async def get_promotion_history(
    limit: int = Query(100, ge=1, le=1000, description="最大返回数"),
    from_layer: Optional[str] = Query(None, description="筛选源层级"),
    to_layer: Optional[str] = Query(None, description="筛选目标层级"),
    reason: Optional[str] = Query(None, description="筛选原因"),
    key: Optional[str] = Query(None, description="筛选键"),
):
    """
    获取提升历史

    返回数据提升事件列表，支持筛选。
    """
    try:
        manager = get_global_memory_manager()
        events = await manager.get_promotion_history(
            limit=limit,
            from_layer=MemoryLayer(from_layer) if from_layer else None,
            to_layer=MemoryLayer(to_layer) if to_layer else None,
            reason=reason,
            key=key,
        )
        return [PromotionEventResponse(**event) for event in events]
    except Exception as e:
        logger.error(f"Failed to get promotion history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    user_id: str = Path(..., description="用户ID")
):
    """
    获取用户偏好

    返回用户的偏好配置和统计信息。
    """
    try:
        service = UserPreferenceService()
        preferences = await service.get_user_preferences(user_id)

        if preferences is None:
            raise HTTPException(status_code=404, detail="User not found")

        return UserPreferencesResponse(**preferences)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_name}/performance", response_model=AgentPerformanceResponse)
async def get_agent_performance(
    agent_name: str = Path(..., description="Agent名称"),
    session_id: Optional[str] = Query(None, description="会话ID筛选"),
    limit: int = Query(50, ge=1, le=500, description="返回数量"),
):
    """
    获取Agent性能统计

    返回Agent的决策统计、成功率和常用操作。
    """
    try:
        service = AgentDecisionService()

        # 获取决策统计
        decisions = await service.get_agent_decisions(
            agent_name=agent_name,
            session_id=session_id,
            limit=limit,
        )

        if not decisions:
            return AgentPerformanceResponse(
                agent_name=agent_name,
                total_decisions=0,
                success_rate=0.0,
                avg_execution_time_ms=0.0,
                common_actions=[],
                recent_decisions=[],
            )

        # 计算统计
        total = len(decisions)
        successful = sum(1 for d in decisions if d.get("outcome") == "success")
        success_rate = successful / total if total > 0 else 0.0

        avg_time = sum(
            d.get("execution_time_ms", 0) for d in decisions
            if d.get("execution_time_ms")
        ) / total if total > 0 else 0.0

        # 统计常用操作
        action_counts = {}
        for d in decisions:
            action = d.get("selected_action", "unknown")
            action_counts[action] = action_counts.get(action, 0) + 1

        common_actions = [
            {"action": action, "count": count}
            for action, count in sorted(action_counts.items(), key=lambda x: -x[1])[:10]
        ]

        return AgentPerformanceResponse(
            agent_name=agent_name,
            total_decisions=total,
            success_rate=success_rate,
            avg_execution_time_ms=avg_time,
            common_actions=common_actions,
            recent_decisions=decisions[:10],
        )
    except Exception as e:
        logger.error(f"Failed to get agent performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/promote", response_model=PromoteResponse)
async def promote_memory(request: PromoteRequest):
    """
    手动提升数据到L3

    将指定的数据提升到L3长期存储层。
    """
    try:
        manager = get_global_memory_manager()

        # 解析作用域
        try:
            scope = MemoryScope(request.scope)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid scope: {request.scope}")

        # 执行提升
        success = await manager.promote_to_l3(
            key=request.key,
            scope=scope,
            scope_id=request.scope_id,
        )

        if success:
            return PromoteResponse(
                success=True,
                message=f"Successfully promoted {request.key} to L3"
            )
        else:
            return PromoteResponse(
                success=False,
                message=f"Failed to promote {request.key} (not found)"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to promote memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup", response_model=CleanupResponse)
async def perform_cleanup():
    """
    执行清理任务

    执行数据生命周期管理，包括：
    - 更新衰减重要性
    - 归档冷数据
    - 清理过期数据
    """
    try:
        db = get_db()
        lifecycle = get_lifecycle_manager(db)

        # 执行生命周期任务
        await lifecycle.perform_lifecycle_tasks()

        stats = await lifecycle.get_lifecycle_stats()

        return CleanupResponse(
            decayed_count=lifecycle.stats.get("decayed_count", 0),
            archived_count=lifecycle.stats.get("archived_count", 0),
            cleaned_count=lifecycle.stats.get("cleaned_count", 0),
            message="Cleanup completed successfully",
        )

    except Exception as e:
        logger.error(f"Failed to perform cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lifecycle")
async def get_lifecycle_stats():
    """
    获取生命周期统计

    返回数据温度分布和归档统计。
    """
    try:
        db = get_db()
        lifecycle = get_lifecycle_manager(db)
        stats = await lifecycle.get_lifecycle_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get lifecycle stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    健康检查

    检查各层服务的可用性。
    """
    try:
        manager = get_global_memory_manager()
        stats = await manager.get_stats()

        # 检查各层状态
        l1_healthy = stats["l1_transient"].get("data_count", 0) >= 0
        l2_healthy = stats["l2_short_term"].get("redis_available", False)
        l3_healthy = stats["l3_long_term"].get("total_records", 0) >= 0

        return {
            "status": "healthy" if all([l1_healthy, l2_healthy, l3_healthy]) else "degraded",
            "l1_transient": "ok" if l1_healthy else "error",
            "l2_short_term": "ok" if l2_healthy else "error",
            "l3_long_term": "ok" if l3_healthy else "error",
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


# ============================================================================
# FastAPI应用集成
# ============================================================================

def create_memory_api_app():
    """创建记忆系统API应用"""
    from fastapi import FastAPI

    app = FastAPI(
        title="MultiAgentPPT Memory System API",
        description="Memory system monitoring and management API",
        version="1.0.0",
    )

    app.include_router(router)

    return app


if __name__ == "__main__":
    import uvicorn

    app = create_memory_api_app()
    uvicorn.run(app, host="0.0.0.0", port=8001)
