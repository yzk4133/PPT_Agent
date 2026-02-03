"""
Agent记忆适配器 - 为现有Agent添加记忆能力

通过Mixin模式为Agent提供记忆相关功能：
- 基础记忆操作 (remember/recall)
- 共享工作空间 (share_data/get_shared_data)
- 用户偏好管理 (get_user_preferences/update_user_preferences)
- 决策记录 (record_decision)
"""

import logging
import os
from typing import Any, Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# 导入记忆系统（可选依赖）
_MEMORY_AVAILABLE = False
_memory_services = {}

try:
    from memory import (
        get_global_memory_manager,
        HierarchicalMemoryManager,
        MemoryScope,
    )
    from memory.services import (
        SharedWorkspaceService,
        UserPreferenceService,
        AgentDecisionService,
        DecisionRecord,
    )

    _MEMORY_AVAILABLE = True
    _memory_services = {
        "manager": get_global_memory_manager,
        "MemoryScope": MemoryScope,
        "SharedWorkspaceService": SharedWorkspaceService,
        "UserPreferenceService": UserPreferenceService,
        "AgentDecisionService": AgentDecisionService,
        "DecisionRecord": DecisionRecord,
    }
    logger.info("记忆系统模块加载成功")
except ImportError as e:
    logger.warning(f"记忆系统未安装，Agent将以无记忆模式运行: {e}")


class AgentMemoryMixin:
    """
    Agent记忆能力混入类

    为Agent提供记忆相关的方法，通过多重继承混入到现有Agent中

    使用方式:
        class MyAgent(AgentMemoryMixin, LlmAgent):
            pass

    特性:
        - 自动检测记忆系统可用性
        - 优雅降级：记忆系统不可用时静默失败
        - 环境变量控制：USE_AGENT_MEMORY=false 可禁用记忆功能
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 检查环境变量
        use_memory = os.getenv("USE_AGENT_MEMORY", "true").lower() == "true"

        # 初始化记忆服务
        self.memory_enabled = _MEMORY_AVAILABLE and use_memory

        if self.memory_enabled:
            try:
                self.memory_manager = _memory_services["manager"]()
                self.MemoryScope = _memory_services["MemoryScope"]
                self.shared_workspace = _memory_services["SharedWorkspaceService"](
                    enable_cache=True
                )
                self.user_pref_service = _memory_services["UserPreferenceService"](
                    enable_cache=True
                )
                self.decision_service = _memory_services["AgentDecisionService"]()
                self.DecisionRecord = _memory_services["DecisionRecord"]

                logger.info(f"[{self.__class__.__name__}] 记忆服务初始化成功")
            except Exception as e:
                logger.warning(f"[{self.__class__.__name__}] 记忆服务初始化失败: {e}")
                self.memory_enabled = False
        else:
            if not _MEMORY_AVAILABLE:
                logger.debug(f"[{self.__class__.__name__}] 记忆系统不可用，无记忆模式")
            else:
                logger.debug(
                    f"[{self.__class__.__name__}] 记忆功能已禁用（USE_AGENT_MEMORY=false）"
                )

        # Agent标识
        self.agent_name = self.__class__.__name__
        self.task_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.session_id: Optional[str] = None

    # ========================================================================
    # 基础记忆方法
    # ========================================================================

    async def remember(
        self,
        key: str,
        value: Any,
        importance: float = 0.5,
        scope: Optional[str] = None,
        scope_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        保存记忆

        Args:
            key: 记忆键
            value: 记忆值
            importance: 重要性（0-1）
            scope: 作用域（TASK/USER/WORKSPACE/SESSION）
            scope_id: 作用域ID（默认自动判断）
            tags: 标签列表

        Returns:
            是否成功
        """
        if not self.memory_enabled:
            return False

        try:
            # 自动确定作用域
            if scope is None:
                scope = self._infer_scope_from_key(key)

            if scope_id is None:
                scope_id = self._get_scope_id(scope)

            # 添加agent名称标签
            all_tags = tags or []
            all_tags.extend([self.agent_name, key])

            await self.memory_manager.set(
                key=f"{self.agent_name}:{key}",
                value=value,
                scope=self.MemoryScope[scope.upper()],
                scope_id=scope_id,
                importance=importance,
                tags=all_tags,
            )
            logger.debug(f"[{self.agent_name}] 记忆保存: {key}")
            return True

        except Exception as e:
            logger.error(f"[{self.agent_name}] 记忆保存失败: {e}")
            return False

    async def recall(
        self,
        key: str,
        scope: Optional[str] = None,
        scope_id: Optional[str] = None,
        search_all_layers: bool = True,
    ) -> Optional[Any]:
        """
        回忆记忆

        Args:
            key: 记忆键
            scope: 作用域
            scope_id: 作用域ID
            search_all_layers: 是否搜索所有层级

        Returns:
            记忆值，不存在返回None
        """
        if not self.memory_enabled:
            return None

        try:
            if scope is None:
                scope = self._infer_scope_from_key(key)

            if scope_id is None:
                scope_id = self._get_scope_id(scope)

            result = await self.memory_manager.get(
                key=f"{self.agent_name}:{key}",
                scope=self.MemoryScope[scope.upper()],
                scope_id=scope_id,
                search_all_layers=search_all_layers,
            )

            if result:
                value, metadata = result
                logger.debug(
                    f"[{self.agent_name}] 记忆召回: {key} (来自{metadata.layer.value})"
                )
                return value

            return None

        except Exception as e:
            logger.error(f"[{self.agent_name}] 记忆召回失败: {e}")
            return None

    async def forget(
        self,
        key: str,
        scope: Optional[str] = None,
        scope_id: Optional[str] = None,
    ) -> bool:
        """
        删除记忆

        Args:
            key: 记忆键
            scope: 作用域
            scope_id: 作用域ID

        Returns:
            是否成功
        """
        if not self.memory_enabled:
            return False

        try:
            if scope is None:
                scope = self._infer_scope_from_key(key)

            if scope_id is None:
                scope_id = self._get_scope_id(scope)

            await self.memory_manager.delete(
                key=f"{self.agent_name}:{key}",
                scope=self.MemoryScope[scope.upper()],
                scope_id=scope_id,
                delete_all_layers=True,
            )
            logger.debug(f"[{self.agent_name}] 记忆删除: {key}")
            return True

        except Exception as e:
            logger.error(f"[{self.agent_name}] 记忆删除失败: {e}")
            return False

    # ========================================================================
    # 共享工作空间方法
    # ========================================================================

    async def share_data(
        self,
        data_type: str,
        data_key: str,
        data_content: Any,
        target_agents: Optional[List[str]] = None,
        ttl_minutes: int = 60,
    ) -> Optional[str]:
        """
        共享数据到工作空间

        Args:
            data_type: 数据类型（research_result/framework/content等）
            data_key: 数据唯一标识
            data_content: 数据内容
            target_agents: 目标Agent列表（None=所有Agent可见）
            ttl_minutes: 有效期（分钟）

        Returns:
            共享数据ID
        """
        if not self.memory_enabled:
            return None

        try:
            session_id = self._get_session_id()

            data_id = await self.shared_workspace.share_data(
                session_id=session_id,
                data_type=data_type,
                source_agent=self.agent_name,
                data_key=data_key,
                data_content=data_content,
                target_agents=target_agents,
                ttl_minutes=ttl_minutes,
            )

            logger.info(f"[{self.agent_name}] 共享数据: {data_type}:{data_key}")
            return data_id

        except Exception as e:
            logger.error(f"[{self.agent_name}] 数据共享失败: {e}")
            return None

    async def get_shared_data(
        self,
        data_type: str,
        data_key: str,
    ) -> Optional[Any]:
        """
        从工作空间获取共享数据

        Args:
            data_type: 数据类型
            data_key: 数据唯一标识

        Returns:
            数据内容
        """
        if not self.memory_enabled:
            return None

        try:
            session_id = self._get_session_id()

            data = await self.shared_workspace.get_shared_data(
                session_id=session_id,
                data_key=data_key,
                accessing_agent=self.agent_name,
            )

            if data:
                logger.debug(
                    f"[{self.agent_name}] 获取共享数据: {data_type}:{data_key}"
                )

            return data

        except Exception as e:
            logger.error(f"[{self.agent_name}] 获取共享数据失败: {e}")
            return None

    async def list_shared_data(
        self,
        data_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        列出工作空间中的共享数据

        Args:
            data_type: 数据类型过滤器（None=所有类型）

        Returns:
            数据元信息列表
        """
        if not self.memory_enabled:
            return []

        try:
            session_id = self._get_session_id()

            data_list = await self.shared_workspace.list_shared_data(
                session_id=session_id,
                data_type=data_type,
            )

            return data_list

        except Exception as e:
            logger.error(f"[{self.agent_name}] 列出共享数据失败: {e}")
            return []

    # ========================================================================
    # 用户偏好方法
    # ========================================================================

    async def get_user_preferences(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        获取用户偏好

        Args:
            user_id: 用户ID

        Returns:
            用户偏好字典
        """
        if not self.memory_enabled:
            return {}

        try:
            preferences = await self.user_pref_service.get_user_preferences(
                user_id=user_id,
                create_if_not_exists=True,
            )
            return preferences or {}

        except Exception as e:
            logger.error(f"[{self.agent_name}] 获取用户偏好失败: {e}")
            return {}

    async def update_user_preferences(
        self,
        user_id: str,
        updates: Dict[str, Any],
    ):
        """
        更新用户偏好

        Args:
            user_id: 用户ID
            updates: 要更新的偏好字典
        """
        if not self.memory_enabled:
            return

        try:
            await self.user_pref_service.update_preferences(
                user_id=user_id,
                preferences=updates,
            )
            logger.info(f"[{self.agent_name}] 更新用户偏好: {list(updates.keys())}")

        except Exception as e:
            logger.error(f"[{self.agent_name}] 更新用户偏好失败: {e}")

    async def increment_preference_counter(
        self,
        user_id: str,
        preference_key: str,
    ):
        """
        增加偏好计数器（用于统计用户使用频率）

        Args:
            user_id: 用户ID
            preference_key: 偏好键
        """
        if not self.memory_enabled:
            return

        try:
            await self.user_pref_service.increment_counter(
                user_id=user_id,
                preference_key=preference_key,
            )
        except Exception as e:
            logger.error(f"[{self.agent_name}] 增加偏好计数失败: {e}")

    # ========================================================================
    # 决策记录方法
    # ========================================================================

    async def record_decision(
        self,
        decision_type: str,
        selected_action: str,
        context: Dict[str, Any],
        alternatives: Optional[List[str]] = None,
        reasoning: Optional[str] = None,
        confidence_score: float = 0.8,
    ):
        """
        记录Agent决策

        Args:
            decision_type: 决策类型（tool_selection/rerouting/parameter等）
            selected_action: 选择的动作
            context: 决策上下文
            alternatives: 备选方案列表
            reasoning: 推理过程
            confidence_score: 置信度（0-1）
        """
        if not self.memory_enabled:
            return

        try:
            decision = self.DecisionRecord(
                task_id=self.task_id or "unknown",
                agent_name=self.agent_name,
                decision_type=decision_type,
                context=context,
                selected_action=selected_action,
                alternatives=alternatives or [],
                reasoning=reasoning or "",
                confidence_score=confidence_score,
            )

            await self.decision_service.record_decision(decision)
            logger.debug(
                f"[{self.agent_name}] 记录决策: {decision_type} -> {selected_action}"
            )

        except Exception as e:
            logger.error(f"[{self.agent_name}] 记录决策失败: {e}")

    async def get_similar_decisions(
        self,
        context: Dict[str, Any],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        获取相似历史决策（用于决策参考）

        Args:
            context: 当前决策上下文
            limit: 返回数量

        Returns:
            相似决策列表
        """
        if not self.memory_enabled:
            return []

        try:
            similar_decisions = await self.decision_service.find_similar_decisions(
                agent_name=self.agent_name,
                context=context,
                limit=limit,
            )
            return similar_decisions

        except Exception as e:
            logger.error(f"[{self.agent_name}] 获取相似决策失败: {e}")
            return []

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def _infer_scope_from_key(self, key: str) -> str:
        """
        根据key推断作用域

        规则:
        - "state"或"status" → TASK（任务级）
        - "research"或"cache" → USER（用户级，可跨任务复用）
        - "preference" → USER（用户级）
        - 其他 → TASK（默认任务级）
        """
        key_lower = key.lower()

        if any(keyword in key_lower for keyword in ["state", "status", "progress"]):
            return "TASK"
        elif any(
            keyword in key_lower for keyword in ["research", "cache", "framework"]
        ):
            return "USER"
        elif "preference" in key_lower:
            return "USER"
        else:
            return "TASK"

    def _get_scope_id(self, scope: str) -> str:
        """
        获取作用域ID

        规则:
        - USER → 使用user_id
        - WORKSPACE → 使用session_id
        - 其他 → 使用task_id或session_id
        """
        if scope == "USER":
            return self._get_user_id() or "anonymous"
        elif scope == "WORKSPACE":
            return self._get_session_id()
        else:
            return self.task_id or self._get_session_id()

    def _get_user_id(self) -> Optional[str]:
        """获取用户ID"""
        return self.user_id

    def _get_session_id(self) -> str:
        """获取会话ID"""
        return self.session_id or self.task_id or "default_session"

    def _get_task_id(self) -> str:
        """获取任务ID"""
        return self.task_id or "default_task"

    def set_context(
        self,
        user_id: Optional[str] = None,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """
        设置上下文信息

        Args:
            user_id: 用户ID
            task_id: 任务ID
            session_id: 会话ID
        """
        if user_id is not None:
            self.user_id = user_id
        if task_id is not None:
            self.task_id = task_id
        if session_id is not None:
            self.session_id = session_id

        logger.debug(
            f"[{self.agent_name}] 上下文更新: user_id={user_id}, task_id={task_id}, session_id={session_id}"
        )

    def is_memory_enabled(self) -> bool:
        """检查记忆功能是否启用"""
        return self.memory_enabled
