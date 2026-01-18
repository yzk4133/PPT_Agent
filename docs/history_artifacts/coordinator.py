"""任务协调器 - 负责任务分解和Agent调度

这是整个系统的核心组件，负责任务编排和流程控制
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """任务定义"""
    id: str
    name: str
    description: str
    required_agent: str
    dependencies: List[str]
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None


class TaskCoordinator:
    """任务协调器"""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.agents: Dict[str, Any] = {}
        self.execution_graph: Dict[str, List[str]] = {}

    def register_agent(self, name: str, agent: Any):
        """注册可用的Agent"""
        self.agents[name] = agent

    def decompose_requirement(self, user_input: str) -> List[Task]:
        """将用户需求分解为任务列表

        Args:
            user_input: 用户的自然语言输入

        Returns:
            分解后的任务列表
        """
        # 这里会调用AI模型进行任务分解
        # 返回标准化的任务列表
        tasks = [
            Task(
                id="task_1",
                name="生成大纲",
                description="根据用户需求生成PPT大纲",
                required_agent="content_generator",
                dependencies=[]
            ),
            Task(
                id="task_2",
                name="设计建议",
                description="为内容提供设计建议",
                required_agent="design_agent",
                dependencies=["task_1"]
            ),
            Task(
                id="task_3",
                name="生成代码",
                description="生成PPTX代码",
                required_agent="code_generator",
                dependencies=["task_1", "task_2"]
            ),
        ]

        for task in tasks:
            self.tasks[task.id] = task

        return tasks

    def build_execution_graph(self):
        """构建任务执行图（DAG）"""
        for task_id, task in self.tasks.items():
            self.execution_graph[task_id] = task.dependencies

    async def execute(self, tasks: List[Task]) -> Dict[str, Any]:
        """执行任务列表

        Args:
            tasks: 要执行的任务列表

        Returns:
            执行结果汇总
        """
        results = {}

        # 按依赖关系排序执行
        for task in tasks:
            # 检查依赖是否完成
            if not self._check_dependencies(task, results):
                raise Exception(f"任务 {task.id} 的依赖未满足")

            # 执行任务
            try:
                task.status = TaskStatus.IN_PROGRESS
                agent = self.agents.get(task.required_agent)
                if not agent:
                    raise Exception(f"找不到Agent: {task.required_agent}")

                result = await agent.process(task)
                task.result = result
                task.status = TaskStatus.COMPLETED
                results[task.id] = result

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                raise

        return results

    def _check_dependencies(self, task: Task, results: Dict[str, Any]) -> bool:
        """检查任务依赖是否满足"""
        for dep_id in task.dependencies:
            if dep_id not in results:
                return False
        return True

    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        return {
            "total_tasks": len(self.tasks),
            "completed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED),
            "pending": sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
        }
