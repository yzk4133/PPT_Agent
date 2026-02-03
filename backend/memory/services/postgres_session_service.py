#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PostgreSQL会话服务 - 实现ADK的SessionService接口
支持乐观锁并发控制
"""
import logging
from typing import Any, Dict, Optional
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_

from google.adk.sessions.session_service import SessionService
from google.adk.sessions.session import Session as ADKSession

from ..storage.database import get_db
from ..storage.models import Session as DBSession
from ..storage.redis_cache import RedisCache

logger = logging.getLogger(__name__)


class OptimisticLockError(Exception):
    """乐观锁冲突异常"""

    pass


class PostgresSessionService(SessionService):
    """基于PostgreSQL的持久化会话服务"""

    def __init__(self, enable_cache: bool = True):
        """
        初始化会话服务

        Args:
            enable_cache: 是否启用Redis缓存
        """
        self.db = get_db()
        self.cache = RedisCache() if enable_cache else None
        logger.info(
            f"PostgresSessionService initialized (cache_enabled={enable_cache})"
        )

    async def create_session(
        self,
        app_name: str,
        user_id: str,
        session_id: str,
        state: Optional[Dict[str, Any]] = None,
    ) -> ADKSession:
        """
        创建新会话

        Args:
            app_name: 应用名称
            user_id: 用户ID
            session_id: 会话ID
            state: 初始状态

        Returns:
            ADK会话对象
        """
        state = state or {}

        try:
            with self.db.get_session() as db_session:
                # 检查会话是否已存在
                existing = (
                    db_session.query(DBSession)
                    .filter(
                        and_(
                            DBSession.user_id == user_id,
                            DBSession.app_name == app_name,
                            DBSession.session_id == session_id,
                        )
                    )
                    .first()
                )

                if existing:
                    logger.info(
                        f"Session already exists: {session_id}, returning existing"
                    )
                    return self._db_session_to_adk(existing)

                # 创建新会话记录
                db_record = DBSession(
                    user_id=user_id,
                    app_name=app_name,
                    session_id=session_id,
                    state=state,
                    version=1,
                )

                db_session.add(db_record)
                db_session.commit()
                db_session.refresh(db_record)

                logger.info(f"Created session: {session_id} for user: {user_id}")

                # 写入缓存
                if self.cache:
                    await self.cache.set_session(session_id, db_record.to_dict())

                return self._db_session_to_adk(db_record)

        except IntegrityError as e:
            logger.warning(f"Session creation conflict (race condition): {e}")
            # 发生冲突，重新查询返回已存在的会话
            return await self.get_session(app_name, user_id, session_id)

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise

    async def get_session(
        self, app_name: str, user_id: str, session_id: str
    ) -> Optional[ADKSession]:
        """
        获取会话（先查缓存再查数据库）

        Args:
            app_name: 应用名称
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            ADK会话对象，不存在返回None
        """
        # 1. 先查缓存
        if self.cache:
            cached = await self.cache.get_session(session_id)
            if cached:
                logger.debug(f"Session cache hit: {session_id}")
                return self._dict_to_adk(cached)

        # 2. 缓存未命中，查数据库
        try:
            with self.db.get_session() as db_session:
                db_record = (
                    db_session.query(DBSession)
                    .filter(
                        and_(
                            DBSession.user_id == user_id,
                            DBSession.app_name == app_name,
                            DBSession.session_id == session_id,
                        )
                    )
                    .first()
                )

                if db_record:
                    logger.debug(f"Session found in DB: {session_id}")

                    # 回写缓存
                    if self.cache:
                        await self.cache.set_session(session_id, db_record.to_dict())

                    return self._db_session_to_adk(db_record)
                else:
                    logger.debug(f"Session not found: {session_id}")
                    return None

        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            raise

    async def update_session(
        self, app_name: str, user_id: str, session_id: str, state: Dict[str, Any]
    ) -> ADKSession:
        """
        更新会话状态（使用乐观锁）

        Args:
            app_name: 应用名称
            user_id: 用户ID
            session_id: 会话ID
            state: 新状态

        Returns:
            更新后的ADK会话对象

        Raises:
            OptimisticLockError: 版本冲突时抛出
        """
        max_retries = 3

        for attempt in range(max_retries):
            try:
                with self.db.get_session() as db_session:
                    # 查询当前记录
                    db_record = (
                        db_session.query(DBSession)
                        .filter(
                            and_(
                                DBSession.user_id == user_id,
                                DBSession.app_name == app_name,
                                DBSession.session_id == session_id,
                            )
                        )
                        .with_for_update()
                        .first()
                    )

                    if not db_record:
                        raise ValueError(f"Session not found: {session_id}")

                    # 记录旧版本号
                    old_version = db_record.version

                    # 更新状态和版本号
                    db_record.state = state
                    db_record.version = old_version + 1
                    db_record.updated_at = datetime.utcnow()

                    # 提交（乐观锁检查在这里触发）
                    db_session.commit()
                    db_session.refresh(db_record)

                    logger.info(
                        f"Updated session: {session_id} (v{old_version} -> v{db_record.version})"
                    )

                    # 更新缓存
                    if self.cache:
                        await self.cache.set_session(session_id, db_record.to_dict())

                    return self._db_session_to_adk(db_record)

            except IntegrityError as e:
                # 版本冲突，重试
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Optimistic lock conflict, retrying ({attempt + 1}/{max_retries})"
                    )
                    continue
                else:
                    logger.error(f"Optimistic lock failed after {max_retries} attempts")
                    raise OptimisticLockError(
                        f"Failed to update session after {max_retries} retries"
                    )

            except Exception as e:
                logger.error(f"Failed to update session: {e}")
                raise

        raise OptimisticLockError("Unexpected retry loop exit")

    async def delete_session(
        self, app_name: str, user_id: str, session_id: str
    ) -> bool:
        """
        删除会话

        Args:
            app_name: 应用名称
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            是否删除成功
        """
        try:
            with self.db.get_session() as db_session:
                deleted_count = (
                    db_session.query(DBSession)
                    .filter(
                        and_(
                            DBSession.user_id == user_id,
                            DBSession.app_name == app_name,
                            DBSession.session_id == session_id,
                        )
                    )
                    .delete()
                )

                db_session.commit()

                # 删除缓存
                if self.cache and deleted_count > 0:
                    await self.cache.delete_session(session_id)

                logger.info(f"Deleted session: {session_id} (count={deleted_count})")
                return deleted_count > 0

        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            raise

    def _db_session_to_adk(self, db_record: DBSession) -> ADKSession:
        """将数据库记录转换为ADK会话对象"""
        return ADKSession(
            id=db_record.session_id,
            app_name=db_record.app_name,
            user_id=db_record.user_id,
            state=db_record.state or {},
            created_time=db_record.created_at,
        )

    def _dict_to_adk(self, data: Dict[str, Any]) -> ADKSession:
        """将字典转换为ADK会话对象"""
        return ADKSession(
            id=data["session_id"],
            app_name=data["app_name"],
            user_id=data["user_id"],
            state=data.get("state", {}),
            created_time=datetime.fromisoformat(data["created_at"]),
        )
