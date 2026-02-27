"""
User Preference Service

管理用户偏好、使用统计和满意度评分
"""
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from ..storage.models.user_profile import UserProfile
from ..storage.redis_cache import RedisCache

logger = logging.getLogger(__name__)


class UserPreferenceService:
    """
    用户偏好服务

    管理用户偏好、使用统计和满意度评分
    """

    def __init__(
        self,
        db_session: Optional[Session] = None,
        cache_client: Optional[RedisCache] = None,
        enable_cache: bool = True
    ):
        """
        初始化用户偏好服务

        Args:
            db_session: 数据库会话
            cache_client: Redis缓存客户端
            enable_cache: 是否启用缓存
        """
        self.db_session = db_session
        self.cache_client = cache_client
        self.logger = logging.getLogger(self.__class__.__name__)
        self.enable_cache = enable_cache and cache_client is not None

    def _get_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        从数据库获取用户配置

        Args:
            user_id: 用户ID

        Returns:
            UserProfile对象或None
        """
        if not self.db_session:
            return None

        try:
            return self.db_session.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
        except Exception as e:
            self.logger.error(f"[UserPreferenceService] Query profile error: {e}")
            return None

    # === 偏好管理 ===

    async def get_user_preferences(
        self,
        user_id: str,
        create_if_not_exists: bool = False
    ) -> Dict[str, Any]:
        """
        获取用户偏好

        Args:
            user_id: 用户ID
            create_if_not_exists: 如果不存在是否创建

        Returns:
            用户偏好字典
        """
        # 先从缓存获取
        if self.enable_cache:
            cached = await self.cache_client.get_user_preferences(user_id)
            if cached:
                self.logger.debug(f"[UserPreferenceService] Cache hit for user {user_id}")
                return cached

        # 从数据库获取
        profile = self._get_profile(user_id)

        if not profile and create_if_not_exists:
            # 创建新用户
            if not self.db_session:
                return {}

            profile = UserProfile(user_id=user_id)
            self.db_session.add(profile)
            self.db_session.commit()
            self.db_session.refresh(profile)
            self.logger.info(f"[UserPreferenceService] Created profile for user {user_id}")

        if profile:
            preferences = profile.to_dict()

            # 写入缓存
            if self.enable_cache:
                await self.cache_client.set_user_preferences(user_id, preferences)

            return preferences

        return {}

    async def update_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """
        更新用户偏好

        Args:
            user_id: 用户ID
            preferences: 偏好更新

        Returns:
            是否成功
        """
        if not self.db_session:
            return False

        try:
            profile = self._get_profile(user_id)

            if not profile:
                # 创建新用户
                profile = UserProfile(user_id=user_id)
                self.db_session.add(profile)

            # 更新偏好
            for key, value in preferences.items():
                profile.set_preference(key, value)

            self.db_session.commit()

            # 使缓存失效
            if self.enable_cache:
                await self.cache_client.delete_user_preferences(user_id)

            self.logger.info(
                f"[UserPreferenceService] Updated preferences for user {user_id}: "
                f"{list(preferences.keys())}"
            )
            return True

        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"[UserPreferenceService] Update preferences error: {e}")
            return False

    async def reset_preferences(self, user_id: str) -> bool:
        """
        重置用户偏好

        Args:
            user_id: 用户ID

        Returns:
            是否成功
        """
        return await self.update_preferences(user_id, {})

    # === 统计管理 ===

    async def increment_session_count(self, user_id: str) -> bool:
        """
        增加会话计数

        Args:
            user_id: 用户ID

        Returns:
            是否成功
        """
        if not self.db_session:
            return False

        try:
            profile = self._get_profile(user_id)
            if not profile:
                return False

            profile.increment_session_count()
            self.db_session.commit()

            # 使缓存失效
            if self.enable_cache:
                await self.cache_client.delete_user_preferences(user_id)

            return True

        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"[UserPreferenceService] Increment session count error: {e}")
            return False

    async def increment_generation_count(self, user_id: str) -> bool:
        """
        增加生成计数

        Args:
            user_id: 用户ID

        Returns:
            是否成功
        """
        if not self.db_session:
            return False

        try:
            profile = self._get_profile(user_id)
            if not profile:
                return False

            profile.increment_generation_count()
            self.db_session.commit()

            # 使缓存失效
            if self.enable_cache:
                await self.cache_client.delete_user_preferences(user_id)

            return True

        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"[UserPreferenceService] Increment generation count error: {e}")
            return False

    async def update_satisfaction_score(
        self,
        user_id: str,
        score: float
    ) -> bool:
        """
        更新满意度评分

        Args:
            user_id: 用户ID
            score: 满意度评分 (0.0-1.0)

        Returns:
            是否成功
        """
        if not self.db_session:
            return False

        try:
            profile = self._get_profile(user_id)
            if not profile:
                return False

            profile.update_satisfaction_score(score)
            self.db_session.commit()

            # 使缓存失效
            if self.enable_cache:
                await self.cache_client.delete_user_preferences(user_id)

            return True

        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"[UserPreferenceService] Update satisfaction score error: {e}")
            return False

    # === 偏好查询 ===

    async def get_preference(
        self,
        user_id: str,
        key: str,
        default: Any = None
    ) -> Any:
        """
        获取单个偏好

        Args:
            user_id: 用户ID
            key: 偏好键
            default: 默认值

        Returns:
            偏好值
        """
        preferences = await self.get_user_preferences(user_id)
        return preferences.get(key, default)

    async def set_preference(
        self,
        user_id: str,
        key: str,
        value: Any
    ) -> bool:
        """
        设置单个偏好

        Args:
            user_id: 用户ID
            key: 偏好键
            value: 偏好值

        Returns:
            是否成功
        """
        return await self.update_preferences(user_id, {key: value})

    async def get_all_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        获取所有偏好

        Args:
            user_id: 用户ID

        Returns:
            偏好字典
        """
        return await self.get_user_preferences(user_id)

    # === 批量操作 ===

    async def get_preferences_batch(
        self,
        user_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        批量获取用户偏好

        Args:
            user_ids: 用户ID列表

        Returns:
            用户ID到偏好的映射
        """
        if not self.db_session:
            return {uid: {} for uid in user_ids}

        try:
            profiles = self.db_session.query(UserProfile).filter(
                UserProfile.user_id.in_(user_ids)
            ).all()

            result = {uid: {} for uid in user_ids}
            for profile in profiles:
                result[profile.user_id] = profile.to_dict()

            return result

        except Exception as e:
            self.logger.error(f"[UserPreferenceService] Batch get preferences error: {e}")
            return {uid: {} for uid in user_ids}
