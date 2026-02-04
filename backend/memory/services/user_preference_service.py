#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户偏好服务 - 学习和管理用户偏好
"""
import logging
from typing import Any, Dict, Optional
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError

from ..storage.database import get_db
from ..storage.models import UserProfile
from ..storage.redis_cache import RedisCache

logger = logging.getLogger(__name__)

class UserPreferenceService:
    """用户偏好管理服务"""

    # 默认偏好配置
    DEFAULT_PREFERENCES = {
        "language": "EN-US",
        "default_slides": 10,
        "style": "professional",
        "color_scheme": "blue",
        "font_size": "medium",
    }

    def __init__(self, enable_cache: bool = True):
        """
        初始化用户偏好服务

        Args:
            enable_cache: 是否启用Redis缓存
        """
        self.db = get_db()
        self.cache = RedisCache() if enable_cache else None
        logger.info("UserPreferenceService initialized")

    async def get_user_preferences(
        self, user_id: str, create_if_not_exists: bool = True
    ) -> Dict[str, Any]:
        """
        获取用户偏好

        Args:
            user_id: 用户ID
            create_if_not_exists: 不存在时是否创建默认偏好

        Returns:
            用户偏好字典
        """
        # 1. 先查缓存
        if self.cache:
            cached = await self.cache.get_user_preferences(user_id)
            if cached:
                logger.debug(f"User preferences cache hit: {user_id}")
                return cached.get("preferences", self.DEFAULT_PREFERENCES)

        # 2. 查数据库
        try:
            with self.db.get_session() as db_session:
                profile = (
                    db_session.query(UserProfile)
                    .filter(UserProfile.user_id == user_id)
                    .first()
                )

                if profile:
                    preferences = profile.preferences

                    # 回写缓存
                    if self.cache:
                        await self.cache.set_user_preferences(user_id, preferences)

                    return preferences

                elif create_if_not_exists:
                    # 创建默认偏好
                    return await self.create_user_profile(
                        user_id, self.DEFAULT_PREFERENCES
                    )

                else:
                    return self.DEFAULT_PREFERENCES

        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return self.DEFAULT_PREFERENCES

    async def create_user_profile(
        self, user_id: str, preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建用户配置

        Args:
            user_id: 用户ID
            preferences: 初始偏好（不提供则使用默认值）

        Returns:
            用户偏好字典
        """
        preferences = preferences or self.DEFAULT_PREFERENCES

        try:
            with self.db.get_session() as db_session:
                profile = UserProfile(
                    user_id=user_id,
                    preferences=preferences,
                    total_sessions=0,
                    successful_generations=0,
                    avg_satisfaction_score=0.0,
                    version=1,
                )

                db_session.add(profile)
                db_session.commit()
                db_session.refresh(profile)

                logger.info(f"Created user profile: {user_id}")

                # 写入缓存
                if self.cache:
                    await self.cache.set_user_preferences(user_id, preferences)

                return preferences

        except IntegrityError:
            # 已存在，重新查询
            logger.info(f"User profile already exists: {user_id}")
            return await self.get_user_preferences(user_id, create_if_not_exists=False)

        except Exception as e:
            logger.error(f"Failed to create user profile: {e}")
            return self.DEFAULT_PREFERENCES

    async def update_preferences(
        self, user_id: str, preferences: Dict[str, Any], merge: bool = True
    ) -> bool:
        """
        更新用户偏好

        Args:
            user_id: 用户ID
            preferences: 新偏好（merge=True时会与现有偏好合并）
            merge: 是否合并现有偏好

        Returns:
            是否更新成功
        """
        max_retries = 3

        for attempt in range(max_retries):
            try:
                with self.db.get_session() as db_session:
                    profile = (
                        db_session.query(UserProfile)
                        .filter(UserProfile.user_id == user_id)
                        .with_for_update()
                        .first()
                    )

                    if not profile:
                        # 不存在则创建
                        await self.create_user_profile(user_id, preferences)
                        return True

                    # 合并或替换偏好
                    if merge:
                        new_preferences = {**profile.preferences, **preferences}
                    else:
                        new_preferences = preferences

                    # 更新
                    old_version = profile.version
                    profile.preferences = new_preferences
                    profile.version = old_version + 1
                    profile.updated_at = datetime.utcnow()

                    db_session.commit()

                    logger.info(
                        f"Updated user preferences: {user_id} (v{old_version} -> v{profile.version})"
                    )

                    # 更新缓存
                    if self.cache:
                        await self.cache.set_user_preferences(user_id, new_preferences)

                    return True

            except (IntegrityError, StaleDataError) as e:
                # 乐观锁冲突，重试
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Preference update conflict, retrying ({attempt + 1}/{max_retries})"
                    )
                    continue
                else:
                    logger.error(
                        f"Failed to update preferences after {max_retries} attempts"
                    )
                    return False

            except Exception as e:
                logger.error(f"Failed to update preferences: {e}")
                return False

        return False

    async def learn_from_session(
        self,
        user_id: str,
        session_metadata: Dict[str, Any],
        successful: bool = True,
        modification_count: int = 0,
    ) -> None:
        """
        从会话中学习用户偏好

        Args:
            user_id: 用户ID
            session_metadata: 会话元数据（包含用户选择）
            successful: 是否成功完成
            modification_count: 用户修改次数（用于推断满意度）
        """
        try:
            with self.db.get_session() as db_session:
                profile = (
                    db_session.query(UserProfile)
                    .filter(UserProfile.user_id == user_id)
                    .with_for_update()
                    .first()
                )

                if not profile:
                    logger.warning(f"User profile not found for learning: {user_id}")
                    return

                # 更新使用统计
                profile.total_sessions += 1
                if successful:
                    profile.successful_generations += 1

                # 计算满意度（修改次数越少越满意）
                # 0次修改=1.0，1次=0.9，2次=0.8...最低0.5
                session_satisfaction = max(0.5, 1.0 - (modification_count * 0.1))

                # 更新平均满意度（移动平均）
                alpha = 0.2  # 学习率
                old_score = profile.avg_satisfaction_score
                new_score = old_score * (1 - alpha) + session_satisfaction * alpha
                profile.avg_satisfaction_score = new_score

                # 学习用户选择
                learned_prefs = {}
                if "language" in session_metadata:
                    learned_prefs["language"] = session_metadata["language"]
                if "numSlides" in session_metadata:
                    learned_prefs["default_slides"] = session_metadata["numSlides"]

                # 合并到用户偏好
                if learned_prefs:
                    profile.preferences = {**profile.preferences, **learned_prefs}

                profile.version += 1
                profile.updated_at = datetime.utcnow()

                db_session.commit()

                logger.info(
                    f"Learned from session: user={user_id}, "
                    f"satisfaction={session_satisfaction:.2f}, "
                    f"avg_score={new_score:.2f}"
                )

                # 更新缓存
                if self.cache:
                    await self.cache.set_user_preferences(user_id, profile.preferences)

        except Exception as e:
            logger.error(f"Failed to learn from session: {e}")

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户统计信息

        Args:
            user_id: 用户ID

        Returns:
            统计信息字典
        """
        try:
            with self.db.get_session() as db_session:
                profile = (
                    db_session.query(UserProfile)
                    .filter(UserProfile.user_id == user_id)
                    .first()
                )

                if not profile:
                    return {
                        "total_sessions": 0,
                        "successful_generations": 0,
                        "success_rate": 0.0,
                        "avg_satisfaction_score": 0.0,
                    }

                success_rate = (
                    profile.successful_generations / profile.total_sessions
                    if profile.total_sessions > 0
                    else 0.0
                )

                return {
                    "total_sessions": profile.total_sessions,
                    "successful_generations": profile.successful_generations,
                    "success_rate": success_rate,
                    "avg_satisfaction_score": profile.avg_satisfaction_score,
                    "created_at": profile.created_at.isoformat(),
                    "updated_at": profile.updated_at.isoformat(),
                }

        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            return {}
