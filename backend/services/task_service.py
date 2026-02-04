"""
Task Service

任务管理服务，负责任务的生命周期管理。

功能：
- 任务创建
- 任务状态跟踪
- 任务结果检索
- 任务修订处理

集成 Master Coordinator 和 Revision Handler。
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

# 导入领域模型
from domain.models import Task, TaskStatus

# 导入Master Coordinator
from agents.orchestrator.agents.master_coordinator import master_coordinator_agent
from agents.orchestrator.components.progress_tracker import get_progress_tracker
from agents.orchestrator.components.revision_handler import (
    get_revision_handler,
    RevisionType,
    RevisionResult
)

logger = logging.getLogger(__name__)

class TaskService:
    """
    任务管理服务

    负责任务的完整生命周期管理。

    功能：
    - 任务创建
    - 任务状态跟踪
    - 任务结果检索
    - 任务修订处理
    """

    def __init__(self):
        """初始化任务服务"""
        self.master_coordinator = master_coordinator_agent
        self.progress_tracker = get_progress_tracker()
        self.revision_handler = get_revision_handler()

        # 任务存储（简化实现，生产环境应使用数据库）
        self._tasks: Dict[str, Task] = {}
        self._task_outputs: Dict[str, Dict[str, Any]] = {}

    async def create_task(
        self,
        user_input: str,
        user_id: str = "anonymous",
        session_id: str = ""
    ) -> Task:
        """
        创建任务

        Args:
            user_input: 用户输入
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            Task实例
        """
        # 生成任务ID
        task_id = self._generate_task_id()

        # 创建任务对象
        task = Task(
            id=task_id,
            raw_input=user_input,
            status=TaskStatus.PENDING
        )
        task.metadata.user_id = user_id
        task.metadata.session_id = session_id

        # 存储任务
        self._tasks[task_id] = task

        logger.info(f"Created task: {task_id} for user: {user_id}")

        return task

    async def execute_task(
        self,
        task: Task,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行任务

        Args:
            task: 任务对象
            context: 额外的上下文信息

        Returns:
            执行结果
        """
        logger.info(f"Executing task: {task.id}")

        # 注册任务到进度追踪器
        await self.progress_tracker.register_task(task)

        try:
            # 创建模拟的上下文（实际使用中应该由外部传入）
            from google.adk.agents.invocation_context import InvocationContext
            from google.adk.sessions import InMemorySessionService
            from google.genai import types

            # 简化实现 - 在实际使用中需要完整的上下文
            # 这里我们模拟执行过程

            # 更新任务状态
            task.status = TaskStatus.GENERATING

            # 执行各阶段（模拟）
            await self.progress_tracker.start_stage(task.id, "requirement_parsing")
            await asyncio.sleep(0.5)
            await self.progress_tracker.complete_stage(task.id, "requirement_parsing")

            await self.progress_tracker.start_stage(task.id, "framework_design")
            await asyncio.sleep(0.5)
            await self.progress_tracker.complete_stage(task.id, "framework_design")

            await self.progress_tracker.start_stage(task.id, "content_generation")
            await asyncio.sleep(1.0)
            await self.progress_tracker.complete_stage(task.id, "content_generation")

            await self.progress_tracker.start_stage(task.id, "template_rendering")
            await asyncio.sleep(0.5)
            await self.progress_tracker.complete_stage(task.id, "template_rendering")

            # 标记完成
            await self.progress_tracker.complete_task(task.id)
            task.mark_completed()

            # 存储输出
            output = {
                "task_id": task.id,
                "status": "completed",
                "file_path": f"output/ppt_{task.id}.pptx",
                "preview_data": {"total_pages": 10, "pages": []}
            }
            self._task_outputs[task.id] = output

            logger.info(f"Task completed: {task.id}")
            return output

        except Exception as e:
            logger.error(f"Task execution failed: {e}", exc_info=True)
            task.status = TaskStatus.FAILED
            task.error = str(e)

            return {
                "task_id": task.id,
                "status": "failed",
                "error": str(e)
            }

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息
        """
        task = self._tasks.get(task_id)
        if not task:
            return None

        # 从进度追踪器获取最新进度
        progress_info = await self.progress_tracker.get_task_progress(task_id)

        return {
            "task_id": task.id,
            "status": task.status.value,
            "progress": task.get_overall_progress(),
            "stages": {
                stage.value: {
                    "status": stage_progress.status.value,
                    "progress": stage_progress.progress,
                    "error": stage_progress.error
                }
                for stage, stage_progress in task.stages.items()
            },
            "created_at": task.metadata.created_at.isoformat(),
            "updated_at": task.metadata.updated_at.isoformat() if task.metadata.updated_at else None,
            "error": task.error
        }

    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务结果

        Args:
            task_id: 任务ID

        Returns:
            任务结果
        """
        return self._task_outputs.get(task_id)

    async def handle_revision(
        self,
        task_id: str,
        revision_request: Dict[str, Any]
    ) -> RevisionResult:
        """
        处理任务修订

        Args:
            task_id: 任务ID
            revision_request: 修订请求

        Returns:
            修订结果
        """
        logger.info(f"Handling revision for task: {task_id}")

        # 使用修订处理器
        result = await self.revision_handler.handle_revision(task_id, revision_request)

        # 更新任务的修订计数
        task = self._tasks.get(task_id)
        if task and result.success:
            task.metadata.revision_count += 1
            task.metadata.updated_at = datetime.now()

        return result

    async def list_tasks(
        self,
        user_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        列出任务

        Args:
            user_id: 用户ID（可选）
            status: 状态过滤（可选）
            limit: 最大返回数量

        Returns:
            任务列表
        """
        tasks = list(self._tasks.values())

        # 过滤
        if user_id:
            tasks = [t for t in tasks if t.metadata.user_id == user_id]

        if status:
            tasks = [t for t in tasks if t.status == status]

        # 排序（按创建时间倒序）
        tasks.sort(key=lambda t: t.metadata.created_at, reverse=True)

        # 限制数量
        tasks = tasks[:limit]

        # 转换为字典格式
        return [
            {
                "task_id": t.id,
                "status": t.status.value,
                "user_id": t.metadata.user_id,
                "created_at": t.metadata.created_at.isoformat(),
                "progress": t.get_overall_progress(),
                "raw_input": t.raw_input[:100] if t.raw_input else ""
            }
            for t in tasks
        ]

    async def delete_task(self, task_id: str) -> bool:
        """
        删除任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        if task_id in self._tasks:
            del self._tasks[task_id]
            if task_id in self._task_outputs:
                del self._task_outputs[task_id]
            await self.progress_tracker.unregister_task(task_id)
            logger.info(f"Deleted task: {task_id}")
            return True
        return False

    def _generate_task_id(self) -> str:
        """生成任务ID"""
        return f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(object())}"

# 全局任务服务实例
_global_task_service: Optional[TaskService] = None

def get_task_service() -> TaskService:
    """
    获取全局任务服务实例

    Returns:
        TaskService实例
    """
    global _global_task_service
    if _global_task_service is None:
        _global_task_service = TaskService()
    return _global_task_service

if __name__ == "__main__":
    # 测试代码
    async def test_task_service():
        print(f"Testing TaskService")
        print("=" * 60)

        service = TaskService()

        # 创建任务
        task = await service.create_task(
            user_input="生成一份AI介绍PPT",
            user_id="test_user"
        )

        print(f"Created task: {task.id}")
        print(f"Task status: {task.status.value}")

        # 执行任务
        result = await service.execute_task(task)
        print(f"\nExecution result: {result}")

        # 获取状态
        status = await service.get_task_status(task.id)
        print(f"\nTask status: {status}")

        # 列出任务
        tasks = await service.list_tasks(user_id="test_user")
        print(f"\nUser tasks: {len(tasks)}")

    asyncio.run(test_task_service())
