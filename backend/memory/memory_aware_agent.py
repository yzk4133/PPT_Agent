"""
记忆感知智能体基类（简化版）

该模块提供 MemoryAwareAgent 基类，为 Agent 提供核心记忆功能和用户偏好管理。

架构简化：
- 只保留核心记忆功能（remember/recall/forget）
- 只保留用户偏好个性化功能
- 移除工作空间共享（通过 LangGraph State 传递）
- 移除决策记录（过度设计）
"""

import logging
from typing import Any, Dict, List, Optional
from abc import ABC

logger = logging.getLogger(__name__)

# 导入工具函数
from .utils.scope_helper import infer_scope_from_key, get_scope_id

# 导入 UserPreferenceMixin
from .core.mixins import UserPreferenceMixin

# 导入服务层
_MEMORY_AVAILABLE = False
_MEMORY_SERVICES = {}

try:
    from .core.memory_system import get_global_memory_system
    from .services import UserPreferenceService

    _MEMORY_AVAILABLE = True
    _MEMORY_SERVICES = {
        "get_global_memory_system": get_global_memory_system,
        "UserPreferenceService": UserPreferenceService,
    }
    logger.info("MemoryAwareAgent: Memory services loaded")
except ImportError as e:
    logger.warning(f"MemoryAwareAgent: Memory services not available: {e}")


class MemoryAwareAgent(UserPreferenceMixin, ABC):
    """
    记忆感知智能体基类（简化版）

    为 LangChain Agent 提供核心记忆功能和用户偏好管理。

    用法:
        class MyAgent(MemoryAwareAgent):
            async def run_node(self, state: PPTGenerationState):
                # 从状态初始化记忆
                self._get_memory(state)

                # 使用记忆缓存
                await self.remember("key", "value")
                result = await self.recall("key")

                # 使用用户偏好
                prefs = await self.get_user_preferences()
                personalized = await self.apply_user_preferences_to_requirement(req)

                return state

    特性:
    - 核心记忆操作：remember(), recall(), forget()
    - 用户偏好管理：get_user_preferences(), apply_user_preferences_to_requirement()
    - 自动推断记忆作用域
    - 记忆不可用时优雅降级
    """

    def __init__(self, agent_name: Optional[str] = None, enable_memory: bool = True):
        """
        Initialize MemoryAwareAgent

        Args:
            agent_name: Agent name (uses class name if None)
            enable_memory: Whether to enable memory operations
        """
        self._agent_name = agent_name or self.__class__.__name__
        self._enable_memory = enable_memory and _MEMORY_AVAILABLE

        # 上下文信息（从state提取）
        self._task_id: Optional[str] = None
        self._user_id: Optional[str] = None
        self._session_id: Optional[str] = None

        # 聚合的服务（延迟初始化）
        self._memory_system = None
        self._user_pref_service = None

        logger.debug(
            f"[{self._agent_name}] MemoryAwareAgent initialized "
            f"(memory={'enabled' if self._enable_memory else 'disabled'})"
        )

    def _get_memory(
        self,
        state: Dict[str, Any],
        force_refresh: bool = False
    ) -> None:
        """
        初始化记忆服务和上下文

        从LangGraph状态中提取上下文（task_id, user_id, session_id）
        并初始化记忆服务。

        Args:
            state: LangChain state dictionary
            force_refresh: Force re-initialization
        """
        if not self._enable_memory:
            return

        # 1. 提取上下文（从state）
        if force_refresh or self._task_id is None:
            self._task_id = state.get("task_id")
            self._user_id = state.get("user_id", "anonymous")
            self._session_id = state.get("session_id", self._task_id)

            logger.debug(
                f"[{self._agent_name}] Context extracted: "
                f"task_id={self._task_id}, user_id={self._user_id}, "
                f"session_id={self._session_id}"
            )

        # 2. 初始化服务（只在第一次或force_refresh时）
        if force_refresh or self._memory_system is None:
            try:
                self._memory_system = _MEMORY_SERVICES["get_global_memory_system"]()
                self._user_pref_service = _MEMORY_SERVICES["UserPreferenceService"](
                    enable_cache=True
                )

                logger.info(f"[{self._agent_name}] Memory services initialized")

            except Exception as e:
                logger.error(f"[{self._agent_name}] Failed to initialize memory services: {e}")
                self._enable_memory = False

    @property
    def agent_name(self) -> str:
        """Get agent name"""
        return self._agent_name

    @property
    def has_memory(self) -> bool:
        """Check if memory is available and enabled"""
        return self._enable_memory and self._memory_system is not None

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def _get_context_dict(self) -> Dict[str, Optional[str]]:
        """
        获取上下文字典（用于工具函数）

        Returns:
            包含 task_id, user_id, session_id 的字典
        """
        return {
            "task_id": self._task_id,
            "user_id": self._user_id,
            "session_id": self._session_id,
        }

    # ========================================================================
    # 核心记忆操作
    # ========================================================================

    async def remember(
        self,
        key: str,
        value: Any,
        importance: float = 0.5,
        scope: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        存储信息到记忆（简化版：优雅降级）

        注意：在v5.0简化版中，此功能已被移除。
        建议使用LangGraph State在Agent间传递数据。

        Args:
            key: 记忆键
            value: 记忆值
            importance: 重要性评分 (0-1)
            scope: 记忆作用域 (TASK/USER/SESSION)
            tags: 可选标签

        Returns:
            是否成功存储
        """
        # 简化版中不再实现此功能
        logger.debug(
            f"[{self._agent_name}] remember() called but not implemented in v5.0. "
            f"Use LangGraph State instead."
        )
        return False

    async def recall(
        self,
        key: str,
        scope: Optional[str] = None,
        search_all_layers: bool = True,
    ) -> Optional[Any]:
        """
        从记忆中检索信息（简化版：优雅降级）

        注意：在v5.0简化版中，此功能已被移除。
        建议使用LangGraph State在Agent间传递数据。

        Args:
            key: 记忆键
            scope: 记忆作用域 (自动推断)
            search_all_layers: 是否搜索所有记忆层

        Returns:
            记忆值，未找到返回 None
        """
        # 简化版中不再实现此功能
        logger.debug(
            f"[{self._agent_name}] recall() called but not implemented in v5.0. "
            f"Use LangGraph State instead."
        )
        return None

    async def forget(self, key: str, scope: Optional[str] = None) -> bool:
        """
        从记忆中删除信息（简化版：优雅降级）

        注意：在v5.0简化版中，此功能已被移除。
        建议使用LangGraph State在Agent间传递数据。

        Args:
            key: 记忆键
            scope: 记忆作用域 (自动推断)

        Returns:
            是否成功删除
        """
        # 简化版中不再实现此功能
        logger.debug(
            f"[{self._agent_name}] forget() called but not implemented in v5.0. "
            f"Use LangGraph State instead."
        )
        return False
