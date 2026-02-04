"""
Agent记忆适配器 - 为现有Agent添加记忆能力

通过Mixin模式为Agent提供记忆相关功能：
- 基础记忆操作 (remember/recall)
- 共享工作空间 (share_data/get_shared_data)
- 用户偏好管理 (get_user_preferences/update_user_preferences)
- 决策记录 (record_decision)
- 内存配额管理 (memory quota)
"""

import logging
import os
import threading
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict

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

# ============================================================================
# 内存配额管理器
# ============================================================================

class MemoryQuotaManager:
    """
    内存配额管理器

    功能：
    - 跟踪每个Agent的内存使用量
    - 当配额超限时触发清理
    - 提供内存使用统计
    """

    def __init__(self):
        # Agent内存使用统计 {agent_name: {"count": int, "last_cleanup": datetime}}
        self._memory_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "last_cleanup": None,
            "total_size_bytes": 0
        })
        self._lock = threading.Lock()

        # 配置
        self.max_memory_items_per_agent = int(os.getenv("MAX_MEMORY_ITEMS_PER_AGENT", "1000"))
        self.cleanup_threshold_percent = float(os.getenv("MEMORY_CLEANUP_THRESHOLD", "0.9"))
        self.cleanup_batch_size = int(os.getenv("MEMORY_CLEANUP_BATCH_SIZE", "100"))
        self.auto_cleanup_interval_minutes = int(os.getenv("MEMORY_AUTO_CLEANUP_INTERVAL", "30"))

    def track_memory_usage(self, agent_name: str, operation: str, estimated_size: int = 0):
        """
        跟踪内存操作

        Args:
            agent_name: Agent名称
            operation: 操作类型 (remember/delete)
            estimated_size: 估计的数据大小（字节）
        """
        with self._lock:
            stats = self._memory_stats[agent_name]

            if operation == "remember":
                stats["count"] += 1
                stats["total_size_bytes"] += estimated_size
            elif operation == "delete":
                stats["count"] = max(0, stats["count"] - 1)
                stats["total_size_bytes"] = max(0, stats["total_size_bytes"] - estimated_size)

    def should_cleanup(self, agent_name: str) -> bool:
        """
        检查是否需要清理

        Returns:
            True如果超过配额阈值
        """
        with self._lock:
            stats = self._memory_stats[agent_name]
            return stats["count"] >= self.max_memory_items_per_agent * self.cleanup_threshold_percent

    def get_memory_stats(self, agent_name: str) -> Dict[str, Any]:
        """获取Agent内存统计"""
        with self._lock:
            stats = self._memory_stats[agent_name].copy()
            stats["quota"] = self.max_memory_items_per_agent
            stats["usage_percent"] = min(100.0, (stats["count"] / self.max_memory_items_per_agent) * 100) if self.max_memory_items_per_agent > 0 else 0
            return stats

    def needs_periodic_cleanup(self, agent_name: str) -> bool:
        """
        检查是否需要定期清理

        Returns:
            True如果距离上次清理超过自动清理间隔
        """
        with self._lock:
            stats = self._memory_stats[agent_name]
            if stats["last_cleanup"] is None:
                return False

            elapsed = datetime.utcnow() - stats["last_cleanup"]
            return elapsed >= timedelta(minutes=self.auto_cleanup_interval_minutes)

    def mark_cleanup(self, agent_name: str):
        """标记清理已完成"""
        with self._lock:
            self._memory_stats[agent_name]["last_cleanup"] = datetime.utcnow()

    def reset_stats(self, agent_name: str):
        """重置Agent内存统计（用于测试或重置）"""
        with self._lock:
            self._memory_stats[agent_name] = {
                "count": 0,
                "last_cleanup": None,
                "total_size_bytes": 0
            }

# 全局配额管理器实例
_global_quota_manager: Optional[MemoryQuotaManager] = None

def get_global_quota_manager() -> MemoryQuotaManager:
    """获取全局配额管理器"""
    global _global_quota_manager
    if _global_quota_manager is None:
        _global_quota_manager = MemoryQuotaManager()
    return _global_quota_manager

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

        # 初始化记忆服务（使用私有属性，避免Pydantic验证问题）
        memory_enabled = _MEMORY_AVAILABLE and use_memory

        if memory_enabled:
            try:
                memory_manager = _memory_services["manager"]()
                MemoryScope = _memory_services["MemoryScope"]
                shared_workspace = _memory_services["SharedWorkspaceService"](
                    enable_cache=True
                )
                user_pref_service = _memory_services["UserPreferenceService"](
                    enable_cache=True
                )
                decision_service = _memory_services["AgentDecisionService"]()
                DecisionRecord = _memory_services["DecisionRecord"]
                quota_manager = get_global_quota_manager()

                # 使用私有属性（不经过Pydantic验证）
                self._memory_manager = memory_manager
                self._MemoryScope = MemoryScope
                self._shared_workspace = shared_workspace
                self._user_pref_service = user_pref_service
                self._decision_service = decision_service
                self._DecisionRecord = DecisionRecord
                self._quota_manager = quota_manager
                self._memory_enabled = True

                logger.info(f"[{self.__class__.__name__}] 记忆服务初始化成功")
            except Exception as e:
                logger.warning(f"[{self.__class__.__name__}] 记忆服务初始化失败: {e}")
                self._memory_enabled = False
        else:
            self._memory_enabled = False
            self._memory_manager = None
            self._MemoryScope = None
            self._shared_workspace = None
            self._user_pref_service = None
            self._decision_service = None
            self._DecisionRecord = None
            self._quota_manager = get_global_quota_manager()

            if not _MEMORY_AVAILABLE:
                logger.debug(f"[{self.__class__.__name__}] 记忆系统不可用，无记忆模式")
            else:
                logger.debug(
                    f"[{self.__class__.__name__}] 记忆功能已禁用（USE_AGENT_MEMORY=false）"
                )

        # Agent标识（使用私有属性）
        self._agent_name = self.__class__.__name__
        self._task_id = None
        self._user_id = None
        self._session_id = None

    # ========================================================================
    # 属性访问器（提供对私有属性的访问）
    # ========================================================================

    @property
    def memory_manager(self):
        """获取memory_manager（兼容旧代码）"""
        return self._memory_manager

    @property
    def MemoryScope(self):
        """获取MemoryScope（兼容旧代码）"""
        return self._MemoryScope

    @property
    def shared_workspace(self):
        """获取shared_workspace（兼容旧代码）"""
        return self._shared_workspace

    @property
    def user_pref_service(self):
        """获取user_pref_service（兼容旧代码）"""
        return self._user_pref_service

    @property
    def decision_service(self):
        """获取decision_service（兼容旧代码）"""
        return self._decision_service

    @property
    def DecisionRecord(self):
        """获取DecisionRecord（兼容旧代码）"""
        return self._DecisionRecord

    @property
    def memory_enabled(self) -> bool:
        """获取memory_enabled（兼容旧代码）"""
        return self._memory_enabled

    @property
    def agent_name(self) -> str:
        """获取agent_name（兼容旧代码）"""
        return self._agent_name

    @property
    def task_id(self) -> Optional[str]:
        """获取task_id（兼容旧代码）"""
        return self._task_id

    @property
    def user_id(self) -> Optional[str]:
        """获取user_id（兼容旧代码）"""
        return self._user_id

    @property
    def session_id(self) -> Optional[str]:
        """获取session_id（兼容旧代码）"""
        return self._session_id

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
            # 检查是否需要清理（配额管理）
            if self._quota_manager.should_cleanup(self._agent_name):
                logger.warning(
                    f"[{self._agent_name}] 内存配额即将耗尽，触发自动清理"
                )
                await self._cleanup_old_memories()

            # 自动确定作用域
            if scope is None:
                scope = self._infer_scope_from_key(key)

            if scope_id is None:
                scope_id = self._get_scope_id(scope)

            # 添加agent名称标签
            all_tags = tags or []
            all_tags.extend([self._agent_name, key])

            success = await self._memory_manager.set(
                key=f"{self._agent_name}:{key}",
                value=value,
                scope=self._MemoryScope[scope.upper()],
                scope_id=scope_id,
                importance=importance,
                tags=all_tags,
            )

            if success:
                # 估算数据大小并跟踪内存使用
                estimated_size = len(str(value)) if value else 0
                self._quota_manager.track_memory_usage(self._agent_name, "remember", estimated_size)
                logger.debug(f"[{self._agent_name}] 记忆保存: {key}")
            else:
                logger.error(f"[{self._agent_name}] 记忆保存失败: {key}")

            return success

        except Exception as e:
            logger.error(f"[{self._agent_name}] 记忆保存失败: {e}")
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
            self._user_id = user_id
        if task_id is not None:
            self._task_id = task_id
        if session_id is not None:
            self._session_id = session_id

        logger.debug(
            f"[{self._agent_name}] 上下文更新: user_id={user_id}, task_id={task_id}, session_id={session_id}"
        )

    def is_memory_enabled(self) -> bool:
        """检查记忆功能是否启用"""
        return self._memory_enabled

    # ========================================================================
    # 内存配额管理方法
    # ========================================================================

    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        获取内存使用统计

        Returns:
            内存统计信息字典
        """
        if not self.memory_enabled:
            return {"error": "Memory not enabled"}

        stats = self._quota_manager.get_memory_stats(self._agent_name)
        stats["agent_name"] = self._agent_name
        return stats

    async def cleanup_memory(self, aggressive: bool = False) -> Dict[str, int]:
        """
        手动清理内存

        Args:
            aggressive: 是否使用激进清理模式（清理更多数据）

        Returns:
            清理统计 {"l1": count, "l2": count, "l3": count}
        """
        if not self.memory_enabled:
            return {"error": "Memory not enabled"}

        logger.info(
            f"[{self._agent_name}] 手动触发内存清理 (aggressive={aggressive})"
        )

        result = await self._cleanup_old_memories(aggressive=aggressive)

        # 标记清理已完成
        self._quota_manager.mark_cleanup(self._agent_name)

        return result

    async def _cleanup_old_memories(self, aggressive: bool = False) -> Dict[str, int]:
        """
        内部方法：清理旧记忆

        Args:
            aggressive: 是否使用激进清理模式

        Returns:
            清理统计
        """
        if not self._memory_manager:
            return {"l1": 0, "l2": 0, "l3": 0}

        try:
            # 清理当前作用域的旧数据
            scope_id = self._get_scope_id("TASK")

            # 清理L1层（瞬时层）
            l1_count = await self._memory_manager.l1.clear_scope(
                self._MemoryScope.TASK, scope_id
            )

            # 如果是激进模式，也清理L2层
            l2_count = 0
            if aggressive:
                l2_count = await self._memory_manager.l2.clear_scope(
                    self._MemoryScope.TASK, scope_id
                )

            # L3层是长期存储，通常不自动清理，除非是激进模式
            l3_count = 0
            if aggressive:
                # L3层只清理当前任务的低重要性数据
                l3_count = await self._memory_manager.l3.clear_scope(
                    self._MemoryScope.TASK, scope_id
                )

            result = {"l1": l1_count, "l2": l2_count, "l3": l3_count}

            logger.info(
                f"[{self._agent_name}] 内存清理完成: L1={l1_count}, L2={l2_count}, L3={l3_count}"
            )

            # 更新配额统计
            self._quota_manager.reset_stats(self._agent_name)

            return result

        except Exception as e:
            logger.error(f"[{self._agent_name}] 内存清理失败: {e}")
            return {"l1": 0, "l2": 0, "l3": 0, "error": str(e)}
