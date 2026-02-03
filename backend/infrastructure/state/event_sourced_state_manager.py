"""
Event Sourced State Manager

State management using event sourcing pattern with domain models.
"""

import sys
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from infrastructure.events.event_store import EventStore, EventSourcedState, EventType
from domain.models.state import (
    RequirementState,
    FrameworkState,
    ResearchState,
    ContentState
)
from domain.events.task_events import TaskEventType, TaskEvent


class AgentStateManager:
    """
    智能体状态管理器 - 基于事件溯源

    使用领域模型和事件溯源模式管理智能体执行状态。

    使用示例:
        state_manager = AgentStateManager(event_store)

        # 初始化任务
        await state_manager.initialize_task("task_001", "生成AI介绍PPT")

        # 保存需求
        requirement = RequirementState(ppt_topic="AI介绍", page_num=10)
        await state_manager.save_requirement(requirement)

        # 保存框架
        framework = FrameworkState(total_page=10, ppt_framework=[...])
        await state_manager.save_framework(framework)

        # 获取当前状态
        state = state_manager.get_current_state()

        # 回滚到指定版本
        await state_manager.rollback(2)
    """

    def __init__(self, event_store: Optional[EventStore] = None, aggregate_id: Optional[str] = None):
        """
        初始化状态管理器

        Args:
            event_store: 事件存储
            aggregate_id: 聚合ID（任务ID）
        """
        self.event_store = event_store
        self.aggregate_id = aggregate_id or self._generate_id()
        self.event_sourced_state = EventSourcedState(
            event_store=event_store,
            aggregate_id=self.aggregate_id,
            aggregate_type="task"
        )
        self._version = 0
        self._pending_events: List[TaskEvent] = []

    def _generate_id(self) -> str:
        """生成聚合ID"""
        import uuid
        return f"task_{uuid.uuid4().hex[:16]}"

    @property
    def version(self) -> int:
        """获取当前版本"""
        return self._version

    async def initialize_task(self, task_id: str, user_input: str, user_id: str = "anonymous") -> None:
        """
        初始化任务

        Args:
            task_id: 任务ID
            user_input: 用户输入
            user_id: 用户ID
        """
        self.aggregate_id = task_id
        self.event_sourced_state._aggregate_id = task_id

        await self.raise_event(
            event_type=TaskEventType.TASK_CREATED,
            data={
                "task_id": task_id,
                "raw_user_input": user_input,
                "user_id": user_id
            }
        )

    async def save_requirement(self, requirement: RequirementState) -> None:
        """
        保存需求解析结果

        Args:
            requirement: 需求状态对象
        """
        await self.raise_event(
            event_type=TaskEventType.REQUIREMENT_PARSED,
            data={
                "requirement": requirement.to_dict(),
                "state_changes": {"structured_requirements": requirement.to_dict()}
            }
        )

    async def save_framework(self, framework: FrameworkState) -> None:
        """
        保存框架设计结果

        Args:
            framework: 框架状态对象
        """
        await self.raise_event(
            event_type=TaskEventType.FRAMEWORK_DESIGNED,
            data={
                "framework": framework.to_dict(),
                "state_changes": {"ppt_framework": framework.to_dict()}
            }
        )

    async def save_research(self, research: ResearchState) -> None:
        """
        保存研究结果

        Args:
            research: 研究状态对象
        """
        await self.raise_event(
            event_type=TaskEventType.RESEARCH_COMPLETED,
            data={
                "research": research.to_dict(),
                "state_changes": {"research_results": research.to_dict()}
            }
        )

    async def save_content(self, content: ContentState) -> None:
        """
        保存内容生成结果

        Args:
            content: 内容状态对象
        """
        await self.raise_event(
            event_type=TaskEventType.CONTENT_GENERATED,
            data={
                "content": content.to_dict(),
                "state_changes": {"content_material": content.to_dict()}
            }
        )

    async def save_output(self, output: Dict[str, Any]) -> None:
        """
        保存最终输出

        Args:
            output: 输出字典
        """
        await self.raise_event(
            event_type=TaskEventType.PPT_RENDERED,
            data={
                "output": output,
                "state_changes": {"ppt_output": output}
            }
        )

    async def save_checkpoint(
        self,
        phase: int,
        checkpoint_data: Dict[str, Any]
    ) -> None:
        """
        保存checkpoint事件

        Args:
            phase: 阶段
            checkpoint_data: Checkpoint数据
        """
        await self.raise_event(
            event_type=TaskEventType.CHECKPOINT_SAVED,
            data={
                "phase": phase,
                "checkpoint_data": checkpoint_data
            }
        )

    async def raise_event(
        self,
        event_type: TaskEventType,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> None:
        """
        抛出事件

        Args:
            event_type: 事件类型
            data: 事件数据
            correlation_id: 关联ID
        """
        self._version += 1

        event = TaskEvent(
            event_type=event_type,
            version=self._version,
            data=data,
            timestamp=datetime.now(),
            correlation_id=correlation_id or self.aggregate_id
        )

        self._pending_events.append(event)

        # 应用到状态
        if "state_changes" in data:
            self.event_sourced_state._state.update(data["state_changes"])

    async def commit(self) -> None:
        """提交所有待处理事件"""
        for event in self._pending_events:
            # 转换为EventStore的Event类型
            from infrastructure.events.event_store import Event as StoreEvent
            store_event = StoreEvent(
                event_id=f"evt_{event.timestamp.timestamp()}",
                event_type=EventType(event.event_type.value),
                aggregate_id=self.aggregate_id,
                aggregate_type="task",
                version=event.version,
                data=event.data,
                timestamp=event.timestamp,
                correlation_id=event.correlation_id
            )
            self.event_sourced_state._pending_events.append(store_event)

        await self.event_sourced_state.commit()
        self._pending_events.clear()

    def get_current_state(self) -> Dict[str, Any]:
        """
        获取当前状态

        Returns:
            当前状态字典
        """
        return self.event_sourced_state.state.copy()

    def get_state_at_version(self, version: int) -> Dict[str, Any]:
        """
        获取指定版本的状态

        Args:
            version: 版本号

        Returns:
            该版本的状态
        """
        # 重放到指定版本
        original_events = self.event_sourced_state.get_events()
        original_state = self.event_sourced_state._state.copy()

        self.event_sourced_state.replay(to_version=version)
        state = self.get_current_state()

        # 恢复原始状态
        self.event_sourced_state._state = original_state

        return state

    async def rollback(self, version: int) -> None:
        """
        回滚到指定版本

        Args:
            version: 目标版本
        """
        self.event_sourced_state.rollback(version)
        self._version = version

    def get_event_history(self) -> List[Dict[str, Any]]:
        """
        获取事件历史

        Returns:
            事件历史列表
        """
        events = self.event_sourced_state.get_events()
        return [e.to_dict() for e in events]

    def get_pending_events(self) -> List[TaskEvent]:
        """获取待处理事件"""
        return self._pending_events.copy()


# Global state manager factory
_global_state_manager: Optional[AgentStateManager] = None


def get_state_manager(event_store=None, aggregate_id=None) -> AgentStateManager:
    """获取全局状态管理器实例"""
    global _global_state_manager
    if _global_state_manager is None:
        _global_state_manager = AgentStateManager(event_store, aggregate_id)
    return _global_state_manager


def set_state_manager(manager: AgentStateManager) -> None:
    """设置全局状态管理器实例"""
    global _global_state_manager
    _global_state_manager = manager


if __name__ == "__main__":
    # 测试代码
    import asyncio
    from infrastructure.events.event_store import InMemoryEventStore

    async def test_state_manager():
        print("Testing AgentStateManager")

        # 创建事件存储
        event_store = InMemoryEventStore()
        state_manager = AgentStateManager(
            event_store=event_store,
            aggregate_id="task_test_001"
        )

        # 初始化任务
        await state_manager.initialize_task(
            task_id="task_test_001",
            user_input="做一份AI介绍PPT",
            user_id="user_test_001"
        )

        # 保存需求
        requirement = RequirementState(
            ppt_topic="AI技术介绍",
            page_num=10,
            scene="business_report"
        )
        await state_manager.save_requirement(requirement)

        # 保存框架
        from domain.models.state import FrameworkPageState
        framework = FrameworkState(
            total_page=10,
            ppt_framework=[
                FrameworkPageState(page_no=1, title="封面", page_type="cover")
            ]
        )
        await state_manager.save_framework(framework)

        # 提交事件
        await state_manager.commit()

        # 获取状态
        state = state_manager.get_current_state()
        print(f"\nCurrent state:")
        print(f"  Task ID: {state.get('task_id')}")
        print(f"  Raw input: {state.get('raw_user_input')}")
        print(f"  Requirement: {state.get('structured_requirements', {}).get('ppt_topic')}")
        print(f"  Framework pages: {state.get('ppt_framework', {}).get('total_page', 0)}")

        # 获取事件历史
        events = state_manager.get_event_history()
        print(f"\nEvent history: {len(events)} events")
        for event in events:
            print(f"  - {event['event_type']} (v{event['version']})")

    asyncio.run(test_state_manager())
