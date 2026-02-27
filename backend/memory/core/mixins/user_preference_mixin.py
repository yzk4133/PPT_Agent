"""
User Preference Mixin

提供用户偏好管理功能：
- 获取用户偏好
- 应用用户偏好到需求
- 记录用户满意度
- 记录用户交互行为
"""

import logging
from typing import Any, Dict
from abc import ABC
from datetime import datetime

logger = logging.getLogger(__name__)


class UserPreferenceMixin(ABC):
    """
    用户偏好管理 Mixin

    为智能体提供用户偏好相关的操作方法。
    需要配合 UserPreferenceService 使用。
    """

    async def get_user_preferences(
        self,
        user_id: str = None,
    ) -> Dict[str, Any]:
        """
        获取用户偏好

        Args:
            user_id: 用户ID (使用state中的user_id如果为None)

        Returns:
            用户偏好字典，包含:
            - language: 主要语言 (ZH-CN, EN-US)
            - default_slides: 默认幻灯片数 (5-30)
            - tone: 内容语调 (professional, casual, creative)
            - template_type: 模板类型 (business, academic, creative)
            - auto_save: 是否自动保存
        """
        if not self.has_memory:
            return {}

        try:
            uid = user_id or self._user_id or "anonymous"

            preferences = await self._user_pref_service.get_user_preferences(
                user_id=uid,
                create_if_not_exists=True,
            )

            return preferences or {}

        except Exception as e:
            logger.error(f"[{self._agent_name}] Get user preferences error: {e}")
            return {}

    async def apply_user_preferences_to_requirement(
        self,
        requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply user preferences to requirement dict

        This is the core method for implementing personalization.

        Priority: User specified > User preferences > System defaults

        Args:
            requirement: Original requirement dict

        Returns:
            Requirement dict with preferences applied

        Example:
            >>> requirement = {"ppt_topic": "AI"}
            >>> personalized = await self.apply_user_preferences_to_requirement(requirement)
            >>> # personalized = {"ppt_topic": "AI", "language": "ZH-CN", "page_num": 15}
        """
        preferences = await self.get_user_preferences()

        if not preferences:
            logger.debug(f"[{self._agent_name}] No user preferences to apply")
            return requirement

        # Create copy to avoid modifying original
        personalized_requirement = requirement.copy()

        # Apply language preference (if user didn't specify)
        if "language" in preferences:
            if "language" not in personalized_requirement:
                personalized_requirement["language"] = preferences["language"]
                logger.debug(f"[{self._agent_name}] Applied language preference: {preferences['language']}")

        # Apply tone preference
        if "tone" in preferences:
            if "tone" not in personalized_requirement:
                personalized_requirement["tone"] = preferences["tone"]

        # Apply default_slides preference (if user didn't specify)
        if "default_slides" in preferences:
            if "page_num" not in personalized_requirement:
                personalized_requirement["page_num"] = preferences["default_slides"]
                logger.debug(f"[{self._agent_name}] Applied default_slides: {preferences['default_slides']}")

        # Apply template_type preference
        if "template_type" in preferences:
            if "template_type" not in personalized_requirement:
                personalized_requirement["template_type"] = preferences["template_type"]

        logger.info(
            f"[{self._agent_name}] Applied {len(preferences)} preferences to requirement"
        )

        return personalized_requirement

    async def record_user_satisfaction(
        self,
        score: float,
        feedback: str = ""
    ):
        """
        Record user satisfaction score

        Args:
            score: Satisfaction score (0.0 - 1.0)
            feedback: User feedback text

        Example:
            >>> await self.record_user_satisfaction(0.8, "内容不错，但图表太少")
        """
        if not self.has_memory:
            return

        if not self._user_id:
            logger.warning(f"[{self._agent_name}] No user_id available, cannot record satisfaction")
            return

        try:
            # Update user preferences with satisfaction data
            await self._user_pref_service.update_preferences(
                self._user_id,
                {
                    "last_satisfaction_score": score,
                    "last_feedback": feedback,
                    "last_interaction_at": self._get_current_timestamp()
                }
            )

            logger.info(f"[{self._agent_name}] Recorded user satisfaction: {score}/1.0")

        except Exception as e:
            logger.error(f"[{self._agent_name}] Failed to record user satisfaction: {e}")

    async def record_user_interaction(
        self,
        action: str,
        **context
    ):
        """
        Record user interaction behavior

        Args:
            action: Interaction type (e.g., "parse_requirement", "generate_content")
            **context: Additional context information

        Example:
            >>> await self.record_user_interaction(
            ...     action="parse_requirement",
            ...     input_length=20,
            ...     topic="AI"
            ... )
        """
        if not self.has_memory:
            return

        try:
            # 简化版中不再记录决策追踪
            logger.debug(
                f"[{self._agent_name}] User interaction: {action}, "
                f"context: {context}"
            )

        except Exception as e:
            logger.error(f"[{self._agent_name}] Failed to record user interaction: {e}")

    def _get_current_timestamp(self) -> str:
        """
        Get current timestamp in ISO format

        Returns:
            ISO format timestamp string
        """
        return datetime.now().isoformat()
