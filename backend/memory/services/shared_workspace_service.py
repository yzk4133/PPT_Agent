#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
共享工作空间服务 - P1功能
支持Multi-Agent协作，避免重复工作
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc, func
import uuid

from ..storage.database import get_db
from ..storage.models import SharedWorkspaceMemory
from ..storage.redis_cache import RedisCache

logger = logging.getLogger(__name__)


class SharedWorkspaceService:
    """Multi-Agent协作记忆服务"""

    # 数据类型常量
    RESEARCH_RESULT = "research_result"
    OUTLINE = "outline"
    AGENT_OUTPUT = "agent_output"
    INTERMEDIATE_DATA = "intermediate_data"
    TOOL_RESULT = "tool_result"

    def __init__(self, enable_cache: bool = True):
        """
        初始化共享工作空间服务

        Args:
            enable_cache: 是否启用Redis缓存
        """
        self.db = get_db()
        self.cache = RedisCache() if enable_cache else None
        logger.info("SharedWorkspaceService initialized")

    async def share_data(
        self,
        session_id: str,
        data_type: str,
        source_agent: str,
        data_key: str,
        data_content: Dict[str, Any],
        data_summary: Optional[str] = None,
        target_agents: Optional[List[str]] = None,
        ttl_minutes: int = 60,
    ) -> str:
        """
        共享数据到工作空间

        Args:
            session_id: 会话ID
            data_type: 数据类型
            source_agent: 产生数据的Agent
            data_key: 数据唯一标识
            data_content: 数据内容
            data_summary: 数据摘要
            target_agents: 目标Agent列表（None表示所有Agent可访问）
            ttl_minutes: 有效期（分钟）

        Returns:
            共享数据ID
        """
        try:
            with self.db.get_session() as db_session:
                # 检查是否已存在相同key的数据
                existing = (
                    db_session.query(SharedWorkspaceMemory)
                    .filter(
                        and_(
                            SharedWorkspaceMemory.session_id == session_id,
                            SharedWorkspaceMemory.data_key == data_key,
                        )
                    )
                    .first()
                )

                if existing:
                    # 更新已有数据
                    existing.data_content = data_content
                    existing.data_summary = data_summary
                    existing.source_agent = source_agent
                    existing.target_agents = target_agents
                    existing.ttl_minutes = ttl_minutes
                    existing.expires_at = datetime.utcnow() + timedelta(
                        minutes=ttl_minutes
                    )
                    existing.updated_at = datetime.utcnow()

                    db_session.commit()
                    data_id = str(existing.id)
                    logger.debug(f"Updated shared data: {data_key} by {source_agent}")
                else:
                    # 创建新数据
                    shared_data = SharedWorkspaceMemory(
                        session_id=session_id,
                        data_type=data_type,
                        source_agent=source_agent,
                        data_key=data_key,
                        data_content=data_content,
                        data_summary=data_summary,
                        target_agents=target_agents,
                        ttl_minutes=ttl_minutes,
                        expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes),
                    )

                    db_session.add(shared_data)
                    db_session.commit()
                    db_session.refresh(shared_data)

                    data_id = str(shared_data.id)
                    logger.info(
                        f"Shared data: {data_key} by {source_agent} -> {target_agents or 'all agents'}"
                    )

                # 缓存到Redis（如果启用）
                if self.cache:
                    cache_key = f"shared_workspace:{session_id}:{data_key}"
                    await self.cache.set(
                        cache_key, data_content, expire=ttl_minutes * 60
                    )

                return data_id

        except Exception as e:
            logger.error(f"Failed to share data: {e}")
            raise

    async def get_shared_data(
        self,
        session_id: str,
        data_key: str,
        accessing_agent: str,
    ) -> Optional[Dict[str, Any]]:
        """
        获取共享数据

        Args:
            session_id: 会话ID
            data_key: 数据键
            accessing_agent: 访问的Agent

        Returns:
            数据内容（如果存在且有权限）
        """
        try:
            # 先查缓存
            if self.cache:
                cache_key = f"shared_workspace:{session_id}:{data_key}"
                cached = await self.cache.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit for shared data: {data_key}")
                    return cached

            # 查数据库
            with self.db.get_session() as db_session:
                data = (
                    db_session.query(SharedWorkspaceMemory)
                    .filter(
                        and_(
                            SharedWorkspaceMemory.session_id == session_id,
                            SharedWorkspaceMemory.data_key == data_key,
                            SharedWorkspaceMemory.is_archived == False,
                            or_(
                                SharedWorkspaceMemory.expires_at.is_(None),
                                SharedWorkspaceMemory.expires_at > datetime.utcnow(),
                            ),
                        )
                    )
                    .first()
                )

                if not data:
                    logger.debug(f"Shared data not found: {data_key}")
                    return None

                # 检查访问权限
                if data.target_agents and accessing_agent not in data.target_agents:
                    logger.warning(
                        f"Access denied: {accessing_agent} cannot access {data_key}"
                    )
                    return None

                # 更新访问统计
                data.access_count += 1
                data.last_accessed_by = accessing_agent
                data.last_accessed_at = datetime.utcnow()
                db_session.commit()

                logger.debug(
                    f"Shared data accessed: {data_key} by {accessing_agent} "
                    f"(access_count={data.access_count})"
                )

                return data.data_content

        except Exception as e:
            logger.error(f"Failed to get shared data: {e}")
            return None

    async def list_shared_data(
        self,
        session_id: str,
        data_type: Optional[str] = None,
        source_agent: Optional[str] = None,
        include_expired: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        列出共享数据

        Args:
            session_id: 会话ID
            data_type: 数据类型（可选）
            source_agent: 源Agent（可选）
            include_expired: 是否包含已过期数据

        Returns:
            共享数据列表
        """
        try:
            with self.db.get_session() as db_session:
                query = db_session.query(SharedWorkspaceMemory).filter(
                    and_(
                        SharedWorkspaceMemory.session_id == session_id,
                        SharedWorkspaceMemory.is_archived == False,
                    )
                )

                if data_type:
                    query = query.filter(SharedWorkspaceMemory.data_type == data_type)

                if source_agent:
                    query = query.filter(
                        SharedWorkspaceMemory.source_agent == source_agent
                    )

                if not include_expired:
                    query = query.filter(
                        or_(
                            SharedWorkspaceMemory.expires_at.is_(None),
                            SharedWorkspaceMemory.expires_at > datetime.utcnow(),
                        )
                    )

                data_list = query.order_by(desc(SharedWorkspaceMemory.created_at)).all()

                return [
                    {
                        "id": str(d.id),
                        "data_key": d.data_key,
                        "data_type": d.data_type,
                        "source_agent": d.source_agent,
                        "data_summary": d.data_summary,
                        "access_count": d.access_count,
                        "last_accessed_by": d.last_accessed_by,
                        "created_at": d.created_at.isoformat(),
                        "expires_at": (
                            d.expires_at.isoformat() if d.expires_at else None
                        ),
                    }
                    for d in data_list
                ]

        except Exception as e:
            logger.error(f"Failed to list shared data: {e}")
            return []

    async def check_data_exists(
        self,
        session_id: str,
        data_key: str,
    ) -> bool:
        """
        检查数据是否存在

        Args:
            session_id: 会话ID
            data_key: 数据键

        Returns:
            是否存在
        """
        try:
            with self.db.get_session() as db_session:
                exists = (
                    db_session.query(SharedWorkspaceMemory.id)
                    .filter(
                        and_(
                            SharedWorkspaceMemory.session_id == session_id,
                            SharedWorkspaceMemory.data_key == data_key,
                            SharedWorkspaceMemory.is_archived == False,
                            or_(
                                SharedWorkspaceMemory.expires_at.is_(None),
                                SharedWorkspaceMemory.expires_at > datetime.utcnow(),
                            ),
                        )
                    )
                    .first()
                )
                return exists is not None

        except Exception as e:
            logger.error(f"Failed to check data exists: {e}")
            return False

    async def delete_shared_data(
        self,
        session_id: str,
        data_key: str,
    ) -> bool:
        """
        删除共享数据（归档）

        Args:
            session_id: 会话ID
            data_key: 数据键

        Returns:
            是否成功
        """
        try:
            with self.db.get_session() as db_session:
                data = (
                    db_session.query(SharedWorkspaceMemory)
                    .filter(
                        and_(
                            SharedWorkspaceMemory.session_id == session_id,
                            SharedWorkspaceMemory.data_key == data_key,
                        )
                    )
                    .first()
                )

                if data:
                    data.is_archived = True
                    db_session.commit()
                    logger.info(f"Archived shared data: {data_key}")

                    # 删除缓存
                    if self.cache:
                        cache_key = f"shared_workspace:{session_id}:{data_key}"
                        await self.cache.delete(cache_key)

                    return True
                return False

        except Exception as e:
            logger.error(f"Failed to delete shared data: {e}")
            return False

    async def cleanup_expired_data(self) -> int:
        """
        清理过期数据

        Returns:
            清理的数据数量
        """
        try:
            with self.db.get_session() as db_session:
                expired = (
                    db_session.query(SharedWorkspaceMemory)
                    .filter(
                        and_(
                            SharedWorkspaceMemory.expires_at <= datetime.utcnow(),
                            SharedWorkspaceMemory.is_archived == False,
                        )
                    )
                    .all()
                )

                count = len(expired)
                for data in expired:
                    data.is_archived = True

                db_session.commit()
                logger.info(f"Cleaned up {count} expired shared data")
                return count

        except Exception as e:
            logger.error(f"Failed to cleanup expired data: {e}")
            return 0

    async def get_workspace_stats(
        self,
        session_id: str,
    ) -> Dict[str, Any]:
        """
        获取工作空间统计信息

        Args:
            session_id: 会话ID

        Returns:
            统计信息
        """
        try:
            with self.db.get_session() as db_session:
                # 总数据量
                total_data = (
                    db_session.query(func.count(SharedWorkspaceMemory.id))
                    .filter(
                        and_(
                            SharedWorkspaceMemory.session_id == session_id,
                            SharedWorkspaceMemory.is_archived == False,
                        )
                    )
                    .scalar()
                )

                # 按数据类型分组
                by_type = (
                    db_session.query(
                        SharedWorkspaceMemory.data_type,
                        func.count(SharedWorkspaceMemory.id).label("count"),
                    )
                    .filter(
                        and_(
                            SharedWorkspaceMemory.session_id == session_id,
                            SharedWorkspaceMemory.is_archived == False,
                        )
                    )
                    .group_by(SharedWorkspaceMemory.data_type)
                    .all()
                )

                # 按源Agent分组
                by_agent = (
                    db_session.query(
                        SharedWorkspaceMemory.source_agent,
                        func.count(SharedWorkspaceMemory.id).label("count"),
                    )
                    .filter(
                        and_(
                            SharedWorkspaceMemory.session_id == session_id,
                            SharedWorkspaceMemory.is_archived == False,
                        )
                    )
                    .group_by(SharedWorkspaceMemory.source_agent)
                    .all()
                )

                # 总访问次数
                total_accesses = (
                    db_session.query(func.sum(SharedWorkspaceMemory.access_count))
                    .filter(
                        and_(
                            SharedWorkspaceMemory.session_id == session_id,
                            SharedWorkspaceMemory.is_archived == False,
                        )
                    )
                    .scalar()
                )

                return {
                    "session_id": session_id,
                    "total_shared_data": total_data or 0,
                    "total_accesses": total_accesses or 0,
                    "by_data_type": {dt: count for dt, count in by_type},
                    "by_source_agent": {agent: count for agent, count in by_agent},
                }

        except Exception as e:
            logger.error(f"Failed to get workspace stats: {e}")
            return {
                "session_id": session_id,
                "error": str(e),
            }
