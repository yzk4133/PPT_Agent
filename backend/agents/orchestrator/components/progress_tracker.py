"""
Progress Tracker

进度追踪器，用于跟踪PPT生成任务的细粒度进度。
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field

from domain.models import Task, TaskStage, TaskStatus


logger = logging.getLogger(__name__)


@dataclass
class ProgressUpdate:
    """
    进度更新事件

    Attributes:
        task_id: 任务ID
        stage: 当前阶段
        progress: 进度百分比 (0-100)
        status: 状态
        message: 状态消息
        timestamp: 时间戳
    """
    task_id: str
    stage: TaskStage
    progress: int
    status: TaskStatus
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "stage": self.stage.value,
            "progress": self.progress,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()
        }


class ProgressTracker:
    """
    进度追踪器

    跟踪任务执行过程中各个阶段的进度，并提供实时通知机制。

    各阶段进度分配：
    - 需求解析: 0% - 15%
    - 框架设计: 15% - 30%
    - 资料研究: 30% - 50% (可选)
    - 内容生成: 50% - 80%
    - 模板渲染: 80% - 100%
    """

    # 各阶段的进度范围
    STAGE_RANGES = {
        TaskStage.REQUIREMENT_PARSING: (0, 15),
        TaskStage.FRAMEWORK_DESIGN: (15, 30),
        TaskStage.RESEARCH: (30, 50),
        TaskStage.CONTENT_GENERATION: (50, 80),
        TaskStage.TEMPLATE_RENDERING: (80, 100)
    }

    def __init__(self):
        """初始化进度追踪器"""
        self._tasks: Dict[str, Task] = {}
        self._subscribers: Dict[str, list[Callable[[ProgressUpdate], None]]] = {}
        self._lock = asyncio.Lock()

    async def register_task(self, task: Task) -> None:
        """
        注册任务

        Args:
            task: 任务实例
        """
        async with self._lock:
            self._tasks[task.id] = task
            logger.info(f"Registered task: {task.id}")

    async def unregister_task(self, task_id: str) -> None:
        """
        注销任务

        Args:
            task_id: 任务ID
        """
        async with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
            if task_id in self._subscribers:
                del self._subscribers[task_id]
            logger.info(f"Unregistered task: {task_id}")

    async def start_stage(self, task_id: str, stage: TaskStage, message: str = "") -> None:
        """
        开始一个阶段

        Args:
            task_id: 任务ID
            stage: 阶段
            message: 状态消息
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return

            task.start_stage(stage)
            await self._notify(ProgressUpdate(
                task_id=task_id,
                stage=stage,
                progress=0,
                status=task.status,
                message=message or f"开始{self._get_stage_name(stage)}"
            ))

    async def update_progress(
        self,
        task_id: str,
        stage: TaskStage,
        stage_progress: int,
        message: str = ""
    ) -> None:
        """
        更新阶段进度

        Args:
            task_id: 任务ID
            stage: 阶段
            stage_progress: 阶段内进度 (0-100)
            message: 状态消息
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return

            # 计算总体进度
            overall_progress = self._calculate_overall_progress(stage, stage_progress)
            task.update_stage_progress(stage, overall_progress)

            await self._notify(ProgressUpdate(
                task_id=task_id,
                stage=stage,
                progress=overall_progress,
                status=task.status,
                message=message
            ))

    async def complete_stage(self, task_id: str, stage: TaskStage, message: str = "") -> None:
        """
        完成一个阶段

        Args:
            task_id: 任务ID
            stage: 阶段
            message: 状态消息
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return

            # 获取该阶段的最终进度
            _, end_progress = self.STAGE_RANGES.get(stage, (0, 100))
            task.update_stage_progress(stage, end_progress)
            task.complete_stage(stage)

            await self._notify(ProgressUpdate(
                task_id=task_id,
                stage=stage,
                progress=end_progress,
                status=TaskStatus.COMPLETED,
                message=message or f"{self._get_stage_name(stage)}完成"
            ))

    async def fail_stage(
        self,
        task_id: str,
        stage: TaskStage,
        error: str,
        retry_count: int = 0
    ) -> None:
        """
        标记阶段失败

        Args:
            task_id: 任务ID
            stage: 阶段
            error: 错误信息
            retry_count: 重试次数
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return

            task.increment_retry(stage)
            task.fail_stage(stage, error)

            await self._notify(ProgressUpdate(
                task_id=task_id,
                stage=stage,
                progress=task.get_overall_progress(),
                status=TaskStatus.FAILED,
                message=f"阶段失败: {error} (重试 {retry_count}/3)"
            ))

    async def complete_task(self, task_id: str) -> None:
        """
        完成任务

        Args:
            task_id: 任务ID
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return

            task.mark_completed()

            await self._notify(ProgressUpdate(
                task_id=task_id,
                stage=TaskStage.TEMPLATE_RENDERING,
                progress=100,
                status=TaskStatus.COMPLETED,
                message="任务完成"
            ))

    def subscribe(
        self,
        task_id: str,
        callback: Callable[[ProgressUpdate], None]
    ) -> None:
        """
        订阅任务进度更新

        Args:
            task_id: 任务ID
            callback: 回调函数
        """
        if task_id not in self._subscribers:
            self._subscribers[task_id] = []
        self._subscribers[task_id].append(callback)
        logger.info(f"Subscribed to task: {task_id}")

    def unsubscribe(
        self,
        task_id: str,
        callback: Callable[[ProgressUpdate], None]
    ) -> None:
        """
        取消订阅

        Args:
            task_id: 任务ID
            callback: 回调函数
        """
        if task_id in self._subscribers:
            try:
                self._subscribers[task_id].remove(callback)
                logger.info(f"Unsubscribed from task: {task_id}")
            except ValueError:
                pass

    async def get_task_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务进度

        Args:
            task_id: 任务ID

        Returns:
            任务进度信息
        """
        task = self._tasks.get(task_id)
        if not task:
            return None
        return task.to_dict()

    def _calculate_overall_progress(self, stage: TaskStage, stage_progress: int) -> int:
        """
        计算总体进度

        Args:
            stage: 当前阶段
            stage_progress: 阶段内进度 (0-100)

        Returns:
            总体进度 (0-100)
        """
        start, end = self.STAGE_RANGES.get(stage, (0, 100))
        range_size = end - start
        return int(start + (stage_progress / 100 * range_size))

    def _get_stage_name(self, stage: TaskStage) -> str:
        """获取阶段名称"""
        stage_names = {
            TaskStage.REQUIREMENT_PARSING: "需求解析",
            TaskStage.FRAMEWORK_DESIGN: "框架设计",
            TaskStage.RESEARCH: "资料研究",
            TaskStage.CONTENT_GENERATION: "内容生成",
            TaskStage.TEMPLATE_RENDERING: "模板渲染"
        }
        return stage_names.get(stage, stage.value)

    async def _notify(self, update: ProgressUpdate) -> None:
        """
        通知订阅者

        Args:
            update: 进度更新
        """
        subscribers = self._subscribers.get(update.task_id, [])
        if subscribers:
            for callback in subscribers:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(update)
                    else:
                        callback(update)
                except Exception as e:
                    logger.error(f"Error notifying subscriber: {e}")


# 全局进度追踪器实例
_global_tracker: Optional[ProgressTracker] = None


def get_progress_tracker() -> ProgressTracker:
    """
    获取全局进度追踪器实例

    Returns:
        ProgressTracker实例
    """
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = ProgressTracker()
    return _global_tracker


if __name__ == "__main__":
    # 测试代码
    async def test_tracker():
        tracker = ProgressTracker()

        # 创建测试任务
        from domain.models import Task
        task = Task(id="test_001", raw_input="测试任务")
        await tracker.register_task(task)

        # 订阅进度更新
        updates = []
        def callback(update):
            updates.append(update)
            print(f"Progress: {update.progress}% - {update.message}")

        tracker.subscribe(task.id, callback)

        # 模拟进度更新
        await tracker.start_stage(task.id, TaskStage.REQUIREMENT_PARSING)
        await tracker.update_progress(task.id, TaskStage.REQUIREMENT_PARSING, 50, "解析中...")
        await tracker.complete_stage(task.id, TaskStage.REQUIREMENT_PARSING)

        await tracker.start_stage(task.id, TaskStage.FRAMEWORK_DESIGN)
        await tracker.complete_stage(task.id, TaskStage.FRAMEWORK_DESIGN)

        await tracker.complete_task(task.id)

        print(f"Total updates: {len(updates)}")

    asyncio.run(test_tracker())
