"""
Agent记忆适配器 - 为现有Agent添加记忆能力

⚠️ 此文件已废弃，请使用新的扁平化路径：
    from memory.integration import AgentMemoryMixin

为了向后兼容，此文件会重新导出 AgentMemoryMixin
"""

import logging

logger = logging.getLogger(__name__)

# 重新导出新的记忆系统接口（向后兼容）
try:
    from memory.integration import AgentMemoryMixin

    logger.info("✅ 已从新路径导入 AgentMemoryMixin: memory.integration")
except ImportError as e:
    logger.warning(f"⚠️ 无法从新路径导入记忆系统: {e}")

    # 创建空类作为后备
    class AgentMemoryMixin:
        """
        空的混入类 - 当记忆系统不可用时使用

        提供与真实 AgentMemoryMixin 相同的方法签名，但所有操作都是空操作
        """

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # 使用 object.__setattr__ 避免 Pydantic 的字段检查
            object.__setattr__(self, 'memory_enabled', False)
            object.__setattr__(self, 'agent_name', self.__class__.__name__)
            object.__setattr__(self, 'task_id', None)
            object.__setattr__(self, 'user_id', None)
            object.__setattr__(self, 'session_id', None)

        # 空操作方法
        async def remember(self, *args, **kwargs):
            return False

        async def recall(self, *args, **kwargs):
            return None

        async def forget(self, *args, **kwargs):
            return False

        async def share_data(self, *args, **kwargs):
            return None

        async def get_shared_data(self, *args, **kwargs):
            return None

        async def list_shared_data(self, *args, **kwargs):
            return []

        async def get_user_preferences(self, *args, **kwargs):
            return {}

        async def update_user_preferences(self, *args, **kwargs):
            return

        async def increment_preference_counter(self, *args, **kwargs):
            return

        async def record_decision(self, *args, **kwargs):
            return

        async def get_similar_decisions(self, *args, **kwargs):
            return []

        def set_context(self, *args, **kwargs):
            return

        def is_memory_enabled(self) -> bool:
            return False

    logger.warning("⚠️ 使用空实现的后备 AgentMemoryMixin")


__all__ = ["AgentMemoryMixin"]
