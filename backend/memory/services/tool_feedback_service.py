#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工具执行反馈服务 - P1功能
追踪工具调用效果，支持数据驱动的工具优化
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import and_, desc, func
import uuid

from ..storage.database import get_db
from ..storage.models import ToolExecutionFeedback
from ..storage.redis_cache import RedisCache

logger = logging.getLogger(__name__)


class ToolFeedbackService:
    """工具执行反馈服务"""

    def __init__(self, enable_cache: bool = True):
        """
        初始化工具反馈服务

        Args:
            enable_cache: 是否启用Redis缓存
        """
        self.db = get_db()
        self.cache = RedisCache() if enable_cache else None
        logger.info("ToolFeedbackService initialized")

    async def record_tool_execution(
        self,
        session_id: str,
        user_id: str,
        tool_name: str,
        agent_name: str,
        input_params: Dict[str, Any],
        latency_ms: int,
        success: bool,
        output_summary: Optional[Dict[str, Any]] = None,
        error_type: Optional[str] = None,
        decision_id: Optional[str] = None,
    ) -> str:
        """
        记录工具执行

        Args:
            session_id: 会话ID
            user_id: 用户ID
            tool_name: 工具名称
            agent_name: 调用的Agent
            input_params: 输入参数
            latency_ms: 延迟（毫秒）
            success: 是否成功
            output_summary: 输出摘要
            error_type: 错误类型
            decision_id: 关联的决策ID

        Returns:
            反馈记录ID
        """
        try:
            with self.db.get_session() as db_session:
                feedback = ToolExecutionFeedback(
                    session_id=session_id,
                    user_id=user_id,
                    tool_name=tool_name,
                    agent_name=agent_name,
                    input_params=input_params,
                    output_summary=output_summary or {},
                    latency_ms=latency_ms,
                    success=success,
                    error_type=error_type,
                    decision_id=uuid.UUID(decision_id) if decision_id else None,
                )

                db_session.add(feedback)
                db_session.commit()
                db_session.refresh(feedback)

                feedback_id = str(feedback.id)
                logger.debug(
                    f"Recorded tool execution: {tool_name} by {agent_name} "
                    f"(success={success}, latency={latency_ms}ms)"
                )
                return feedback_id

        except Exception as e:
            logger.error(f"Failed to record tool execution: {e}")
            raise

    async def update_usage_feedback(
        self,
        feedback_id: str,
        used_in_final_output: bool,
        relevance_score: Optional[float] = None,
        user_feedback: Optional[str] = None,
    ) -> None:
        """
        更新工具使用反馈

        Args:
            feedback_id: 反馈记录ID
            used_in_final_output: 是否在最终输出中使用
            relevance_score: 相关性评分
            user_feedback: 用户反馈
        """
        try:
            with self.db.get_session() as db_session:
                feedback = (
                    db_session.query(ToolExecutionFeedback)
                    .filter(ToolExecutionFeedback.id == feedback_id)
                    .first()
                )

                if not feedback:
                    logger.warning(f"Feedback not found: {feedback_id}")
                    return

                feedback.used_in_final_output = used_in_final_output
                if relevance_score is not None:
                    feedback.relevance_score = relevance_score
                if user_feedback:
                    feedback.user_feedback = user_feedback

                db_session.commit()
                logger.debug(f"Updated tool usage feedback: {feedback_id}")

        except Exception as e:
            logger.error(f"Failed to update usage feedback: {e}")
            raise

    async def get_tool_performance(
        self,
        tool_name: str,
        time_range_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        获取工具性能统计

        Args:
            tool_name: 工具名称
            time_range_hours: 时间范围（小时）

        Returns:
            性能统计数据
        """
        try:
            with self.db.get_session() as db_session:
                cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)

                # 总调用次数
                total_calls = (
                    db_session.query(func.count(ToolExecutionFeedback.id))
                    .filter(
                        and_(
                            ToolExecutionFeedback.tool_name == tool_name,
                            ToolExecutionFeedback.created_at >= cutoff_time,
                        )
                    )
                    .scalar()
                )

                # 成功率
                successful_calls = (
                    db_session.query(func.count(ToolExecutionFeedback.id))
                    .filter(
                        and_(
                            ToolExecutionFeedback.tool_name == tool_name,
                            ToolExecutionFeedback.created_at >= cutoff_time,
                            ToolExecutionFeedback.success == True,
                        )
                    )
                    .scalar()
                )

                success_rate = (
                    (successful_calls / total_calls * 100) if total_calls > 0 else 0
                )

                # 平均延迟
                avg_latency = (
                    db_session.query(func.avg(ToolExecutionFeedback.latency_ms))
                    .filter(
                        and_(
                            ToolExecutionFeedback.tool_name == tool_name,
                            ToolExecutionFeedback.created_at >= cutoff_time,
                        )
                    )
                    .scalar()
                )

                # P95延迟
                latencies = (
                    db_session.query(ToolExecutionFeedback.latency_ms)
                    .filter(
                        and_(
                            ToolExecutionFeedback.tool_name == tool_name,
                            ToolExecutionFeedback.created_at >= cutoff_time,
                        )
                    )
                    .order_by(ToolExecutionFeedback.latency_ms)
                    .all()
                )
                p95_latency = 0
                if latencies:
                    p95_idx = int(len(latencies) * 0.95)
                    p95_latency = (
                        latencies[p95_idx][0]
                        if p95_idx < len(latencies)
                        else latencies[-1][0]
                    )

                # 使用率（在最终输出中被使用的比例）
                used_count = (
                    db_session.query(func.count(ToolExecutionFeedback.id))
                    .filter(
                        and_(
                            ToolExecutionFeedback.tool_name == tool_name,
                            ToolExecutionFeedback.created_at >= cutoff_time,
                            ToolExecutionFeedback.used_in_final_output == True,
                        )
                    )
                    .scalar()
                )

                usage_rate = (used_count / total_calls * 100) if total_calls > 0 else 0

                # 平均相关性评分
                avg_relevance = (
                    db_session.query(func.avg(ToolExecutionFeedback.relevance_score))
                    .filter(
                        and_(
                            ToolExecutionFeedback.tool_name == tool_name,
                            ToolExecutionFeedback.created_at >= cutoff_time,
                            ToolExecutionFeedback.relevance_score.isnot(None),
                        )
                    )
                    .scalar()
                )

                # 错误类型分布
                error_types = (
                    db_session.query(
                        ToolExecutionFeedback.error_type,
                        func.count(ToolExecutionFeedback.id).label("count"),
                    )
                    .filter(
                        and_(
                            ToolExecutionFeedback.tool_name == tool_name,
                            ToolExecutionFeedback.created_at >= cutoff_time,
                            ToolExecutionFeedback.success == False,
                        )
                    )
                    .group_by(ToolExecutionFeedback.error_type)
                    .all()
                )

                return {
                    "tool_name": tool_name,
                    "time_range_hours": time_range_hours,
                    "total_calls": total_calls or 0,
                    "success_rate": round(success_rate, 2),
                    "avg_latency_ms": round(avg_latency, 2) if avg_latency else 0,
                    "p95_latency_ms": p95_latency,
                    "usage_rate": round(usage_rate, 2),
                    "avg_relevance_score": (
                        round(avg_relevance, 2) if avg_relevance else None
                    ),
                    "error_distribution": {
                        error_type or "unknown": count
                        for error_type, count in error_types
                    },
                }

        except Exception as e:
            logger.error(f"Failed to get tool performance: {e}")
            return {
                "tool_name": tool_name,
                "error": str(e),
            }

    async def get_tool_rankings(
        self,
        metric: str = "success_rate",
        time_range_hours: int = 24,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取工具排名

        Args:
            metric: 排名指标（success_rate / usage_rate / avg_latency / call_count）
            time_range_hours: 时间范围（小时）
            limit: 返回数量

        Returns:
            工具排名列表
        """
        try:
            with self.db.get_session() as db_session:
                cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)

                # 获取所有工具列表
                tools = (
                    db_session.query(ToolExecutionFeedback.tool_name)
                    .filter(ToolExecutionFeedback.created_at >= cutoff_time)
                    .distinct()
                    .all()
                )

                # 计算每个工具的指标
                rankings = []
                for (tool_name,) in tools:
                    perf = await self.get_tool_performance(tool_name, time_range_hours)
                    rankings.append(perf)

                # 根据指标排序
                if metric == "success_rate":
                    rankings.sort(key=lambda x: x.get("success_rate", 0), reverse=True)
                elif metric == "usage_rate":
                    rankings.sort(key=lambda x: x.get("usage_rate", 0), reverse=True)
                elif metric == "avg_latency":
                    rankings.sort(key=lambda x: x.get("avg_latency_ms", float("inf")))
                elif metric == "call_count":
                    rankings.sort(key=lambda x: x.get("total_calls", 0), reverse=True)

                return rankings[:limit]

        except Exception as e:
            logger.error(f"Failed to get tool rankings: {e}")
            return []

    async def get_recent_executions(
        self,
        session_id: str,
        tool_name: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取最近的工具执行记录

        Args:
            session_id: 会话ID
            tool_name: 工具名称（可选）
            limit: 返回数量

        Returns:
            执行记录列表
        """
        try:
            with self.db.get_session() as db_session:
                query = db_session.query(ToolExecutionFeedback).filter(
                    ToolExecutionFeedback.session_id == session_id
                )

                if tool_name:
                    query = query.filter(ToolExecutionFeedback.tool_name == tool_name)

                executions = (
                    query.order_by(desc(ToolExecutionFeedback.created_at))
                    .limit(limit)
                    .all()
                )

                return [e.to_dict() for e in executions]

        except Exception as e:
            logger.error(f"Failed to get recent executions: {e}")
            return []

    async def analyze_tool_failures(
        self,
        tool_name: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        分析工具失败案例

        Args:
            tool_name: 工具名称（可选）
            limit: 返回数量

        Returns:
            失败案例列表
        """
        try:
            with self.db.get_session() as db_session:
                query = db_session.query(ToolExecutionFeedback).filter(
                    ToolExecutionFeedback.success == False
                )

                if tool_name:
                    query = query.filter(ToolExecutionFeedback.tool_name == tool_name)

                failures = (
                    query.order_by(desc(ToolExecutionFeedback.created_at))
                    .limit(limit)
                    .all()
                )

                return [
                    {
                        "tool_name": f.tool_name,
                        "agent_name": f.agent_name,
                        "input_params": f.input_params,
                        "error_type": f.error_type,
                        "latency_ms": f.latency_ms,
                        "created_at": f.created_at.isoformat(),
                    }
                    for f in failures
                ]

        except Exception as e:
            logger.error(f"Failed to analyze tool failures: {e}")
            return []
