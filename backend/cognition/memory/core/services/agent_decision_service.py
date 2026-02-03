#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent决策追踪服务 - P0功能
追踪和分析Agent的决策过程，帮助优化Agent行为
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import and_, desc, func

from .database import get_db
from .models import AgentDecision
from .redis_cache import RedisCache

logger = logging.getLogger(__name__)


class AgentDecisionService:
    """Agent决策追踪服务"""

    # 决策类型常量
    TOOL_SELECTION = "tool_selection"
    SUB_AGENT_ROUTING = "sub_agent_routing"
    PARAMETER_CHOICE = "parameter_choice"
    CONTENT_GENERATION = "content_generation"

    # 结果状态
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"

    def __init__(self, enable_cache: bool = True):
        """
        初始化决策追踪服务

        Args:
            enable_cache: 是否启用Redis缓存
        """
        self.db = get_db()
        self.cache = RedisCache() if enable_cache else None
        logger.info("AgentDecisionService initialized")

    async def record_decision(
        self,
        session_id: str,
        user_id: str,
        agent_name: str,
        decision_type: str,
        context: Dict[str, Any],
        selected_action: str,
        alternatives: Optional[List[str]] = None,
        reasoning: Optional[str] = None,
        confidence_score: Optional[float] = None,
    ) -> str:
        """
        记录Agent决策

        Args:
            session_id: 会话ID
            user_id: 用户ID
            agent_name: Agent名称
            decision_type: 决策类型
            context: 决策上下文
            selected_action: 选择的动作
            alternatives: 考虑过的其他选项
            reasoning: 推理过程
            confidence_score: 置信度

        Returns:
            决策记录ID
        """
        try:
            with self.db.get_session() as db_session:
                decision = AgentDecision(
                    session_id=session_id,
                    user_id=user_id,
                    agent_name=agent_name,
                    decision_type=decision_type,
                    context=context,
                    selected_action=selected_action,
                    alternatives=alternatives or [],
                    reasoning=reasoning,
                    confidence_score=confidence_score,
                )

                db_session.add(decision)
                db_session.commit()
                db_session.refresh(decision)

                decision_id = str(decision.id)
                logger.info(
                    f"Recorded decision: {agent_name} -> {selected_action} (id={decision_id})"
                )
                return decision_id

        except Exception as e:
            logger.error(f"Failed to record decision: {e}")
            raise

    async def update_decision_outcome(
        self,
        decision_id: str,
        outcome: str,
        execution_time_ms: int,
        error_message: Optional[str] = None,
        token_usage: Optional[Dict[str, int]] = None,
    ) -> None:
        """
        更新决策执行结果

        Args:
            decision_id: 决策ID
            outcome: 执行结果（success/failure/partial/timeout）
            execution_time_ms: 执行耗时（毫秒）
            error_message: 错误信息
            token_usage: Token使用情况
        """
        try:
            with self.db.get_session() as db_session:
                decision = (
                    db_session.query(AgentDecision)
                    .filter(AgentDecision.id == decision_id)
                    .first()
                )

                if not decision:
                    logger.warning(f"Decision not found: {decision_id}")
                    return

                decision.outcome = outcome
                decision.execution_time_ms = execution_time_ms
                decision.error_message = error_message
                decision.token_usage = token_usage

                db_session.commit()
                logger.debug(f"Updated decision outcome: {decision_id} -> {outcome}")

        except Exception as e:
            logger.error(f"Failed to update decision outcome: {e}")
            raise

    async def get_recent_decisions(
        self,
        session_id: str,
        agent_name: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取最近的决策记录

        Args:
            session_id: 会话ID
            agent_name: Agent名称（可选）
            limit: 返回数量

        Returns:
            决策记录列表
        """
        try:
            with self.db.get_session() as db_session:
                query = db_session.query(AgentDecision).filter(
                    AgentDecision.session_id == session_id
                )

                if agent_name:
                    query = query.filter(AgentDecision.agent_name == agent_name)

                decisions = (
                    query.order_by(desc(AgentDecision.created_at)).limit(limit).all()
                )

                return [d.to_dict() for d in decisions]

        except Exception as e:
            logger.error(f"Failed to get recent decisions: {e}")
            return []

    async def analyze_agent_performance(
        self,
        agent_name: str,
        time_range_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        分析Agent性能

        Args:
            agent_name: Agent名称
            time_range_hours: 时间范围（小时）

        Returns:
            性能分析结果
        """
        try:
            with self.db.get_session() as db_session:
                cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)

                # 总决策数
                total_decisions = (
                    db_session.query(func.count(AgentDecision.id))
                    .filter(
                        and_(
                            AgentDecision.agent_name == agent_name,
                            AgentDecision.created_at >= cutoff_time,
                        )
                    )
                    .scalar()
                )

                # 成功率
                successful = (
                    db_session.query(func.count(AgentDecision.id))
                    .filter(
                        and_(
                            AgentDecision.agent_name == agent_name,
                            AgentDecision.created_at >= cutoff_time,
                            AgentDecision.outcome == self.SUCCESS,
                        )
                    )
                    .scalar()
                )

                success_rate = (
                    (successful / total_decisions * 100) if total_decisions > 0 else 0
                )

                # 平均执行时间
                avg_time = (
                    db_session.query(func.avg(AgentDecision.execution_time_ms))
                    .filter(
                        and_(
                            AgentDecision.agent_name == agent_name,
                            AgentDecision.created_at >= cutoff_time,
                            AgentDecision.execution_time_ms.isnot(None),
                        )
                    )
                    .scalar()
                )

                # 决策类型分布
                decision_types = (
                    db_session.query(
                        AgentDecision.decision_type,
                        func.count(AgentDecision.id).label("count"),
                    )
                    .filter(
                        and_(
                            AgentDecision.agent_name == agent_name,
                            AgentDecision.created_at >= cutoff_time,
                        )
                    )
                    .group_by(AgentDecision.decision_type)
                    .all()
                )

                # 最常选择的动作
                top_actions = (
                    db_session.query(
                        AgentDecision.selected_action,
                        func.count(AgentDecision.id).label("count"),
                    )
                    .filter(
                        and_(
                            AgentDecision.agent_name == agent_name,
                            AgentDecision.created_at >= cutoff_time,
                        )
                    )
                    .group_by(AgentDecision.selected_action)
                    .order_by(desc("count"))
                    .limit(5)
                    .all()
                )

                return {
                    "agent_name": agent_name,
                    "time_range_hours": time_range_hours,
                    "total_decisions": total_decisions or 0,
                    "success_rate": round(success_rate, 2),
                    "avg_execution_time_ms": round(avg_time, 2) if avg_time else 0,
                    "decision_type_distribution": {
                        dt: count for dt, count in decision_types
                    },
                    "top_actions": [
                        {"action": action, "count": count}
                        for action, count in top_actions
                    ],
                }

        except Exception as e:
            logger.error(f"Failed to analyze agent performance: {e}")
            return {
                "agent_name": agent_name,
                "error": str(e),
            }

    async def get_failure_patterns(
        self,
        agent_name: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        获取失败模式分析

        Args:
            agent_name: Agent名称（可选）
            limit: 返回数量

        Returns:
            失败案例列表
        """
        try:
            with self.db.get_session() as db_session:
                query = db_session.query(AgentDecision).filter(
                    AgentDecision.outcome.in_([self.FAILURE, self.TIMEOUT])
                )

                if agent_name:
                    query = query.filter(AgentDecision.agent_name == agent_name)

                failures = (
                    query.order_by(desc(AgentDecision.created_at)).limit(limit).all()
                )

                return [
                    {
                        "agent_name": f.agent_name,
                        "decision_type": f.decision_type,
                        "selected_action": f.selected_action,
                        "outcome": f.outcome,
                        "error_message": f.error_message,
                        "context": f.context,
                        "created_at": f.created_at.isoformat(),
                    }
                    for f in failures
                ]

        except Exception as e:
            logger.error(f"Failed to get failure patterns: {e}")
            return []

    async def get_decision_by_id(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取决策详情

        Args:
            decision_id: 决策ID

        Returns:
            决策详情
        """
        try:
            with self.db.get_session() as db_session:
                decision = (
                    db_session.query(AgentDecision)
                    .filter(AgentDecision.id == decision_id)
                    .first()
                )

                if decision:
                    return decision.to_dict()
                return None

        except Exception as e:
            logger.error(f"Failed to get decision by id: {e}")
            return None
