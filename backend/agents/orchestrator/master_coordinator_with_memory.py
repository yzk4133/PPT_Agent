"""
Master Coordinator Agent with Memory Integration

将记忆系统集成到主协调智能体中，实现：
1. 任务状态记忆和追踪
2. 进度监控增强
3. 跨会话任务恢复
4. 决策记录和分析
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import AsyncGenerator, Optional, Dict, Any

from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.genai import types
from google.adk.events.event import Event

# 导入基础主协调智能体
from .master_coordinator import MasterCoordinatorAgent

# 导入领域模型
from domain.models import Task, TaskStatus, TaskStage

# 导入记忆适配器
from ..core.base_agent_with_memory import AgentMemoryMixin

logger = logging.getLogger(__name__)


class MasterCoordinatorAgentWithMemory(AgentMemoryMixin, MasterCoordinatorAgent):
    """
    带记忆功能的主协调智能体

    扩展功能:
    1. 任务状态记忆：保存任务状态到记忆系统
    2. 进度追踪增强：记录详细的进度信息
    3. 跨会话任务恢复：可以从记忆中恢复任务状态
    4. 决策记录：记录所有协调决策
    5. 性能统计：收集和分析任务执行数据
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 配置
        self.enable_task_memory = os.getenv("ENABLE_TASK_MEMORY", "true").lower() == "true"
        self.enable_performance_tracking = os.getenv(
            "ENABLE_PERFORMANCE_TRACKING", "true"
        ).lower() == "true"

        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cache_hit_tasks": 0,
        }

        logger.info(
            f"[{self.agent_name}] 初始化完成: "
            f"task_memory={self.enable_task_memory}, "
            f"performance_tracking={self.enable_performance_tracking}"
        )

    async def _run_full_mode(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        完整执行模式（带记忆）

        覆盖父类方法，添加任务记忆逻辑
        """
        # 设置上下文
        self._setup_context(ctx)

        # 1. 生成任务ID
        task_id = self._generate_task_id()
        ctx.session.state["task_id"] = task_id
        self.task_id = task_id

        # 2. 保存原始用户输入
        user_input = ctx.user_content.parts[0].text
        ctx.session.state["raw_user_input"] = user_input

        # 3. 创建任务对象
        task = Task(id=task_id, raw_input=user_input)
        await self.progress_tracker.register_task(task)

        self.stats["total_tasks"] += 1

        logger.info(f"[{self.agent_name}] FULL mode: task {task_id}")

        # ========== 4. 保存初始任务状态到记忆 ==========
        if self.enable_task_memory:
            await self._save_task_initial_state(task_id, user_input, ctx)

        try:
            # ========== 5. 检查是否有可复用的历史任务 ==========
            if self.enable_task_memory:
                similar_task = await self._find_similar_task(user_input)
                if similar_task:
                    # 可以考虑复用历史任务的部分结果
                    await self.record_decision(
                        decision_type="task_reuse",
                        selected_action="similar_task_found",
                        context={
                            "current_task": task_id,
                            "similar_task": similar_task.get("task_id"),
                        },
                        reasoning="发现相似历史任务",
                        confidence_score=0.8,
                    )

            # 6. 执行各阶段（带状态记录）
            # 阶段1：需求解析 (0% - 15%)
            await self._dispatch_stage_with_memory(
                ctx, task, "requirement_parser", TaskStage.REQUIREMENT_PARSING, 15
            )

            # 阶段2：框架设计 (15% - 30%)
            await self._dispatch_stage_with_memory(
                ctx, task, "framework_designer", TaskStage.FRAMEWORK_DESIGN, 30
            )

            # 阶段3+4: 页面级流水线并行（研究 + 内容生成）
            requirement = ctx.session.state.get("structured_requirements", {})
            need_research = requirement.get("need_research", False)

            if need_research and self.page_pipeline:
                # 使用流水线并行
                await self._execute_page_pipeline(ctx, task, 30, 80)
            else:
                # 原有串行逻辑
                if need_research:
                    await self._dispatch_stage_with_memory(
                        ctx, task, "research", TaskStage.RESEARCH, 50
                    )

                await self._dispatch_stage_with_memory(
                    ctx, task, "content_material", TaskStage.CONTENT_GENERATION, 80
                )

            # 阶段5：PPT模板渲染 (80% - 100%)
            await self._dispatch_stage_with_memory(
                ctx, task, "template_renderer", TaskStage.TEMPLATE_RENDERING, 100
            )

            # 7. 交叉校验
            self._cross_validate(ctx, task)

            # 8. 标记任务完成
            await self.progress_tracker.complete_task(task_id)
            task.mark_completed()

            self.stats["completed_tasks"] += 1

            # ========== 9. 保存最终任务状态到记忆 ==========
            if self.enable_task_memory:
                await self._save_task_final_state(task_id, task, ctx)

            # 10. 更新任务对象到上下文
            ctx.session.state["task_object"] = task

            logger.info(f"[{self.agent_name}] Task completed: {task_id}")

            # 11. 产生完成事件
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[types.Part(
                        text=f"PPT生成完成（带记忆）：\n\n"
                        f"任务ID: {task_id}\n"
                        f"总耗时: {task.metadata.total_duration:.1f}秒\n"
                        f"生成页数: {ctx.session.state.get('ppt_framework', {}).get('total_page', 0)}页\n"
                        f"总任务数: {self.stats['total_tasks']}\n"
                        f"完成任务数: {self.stats['completed_tasks']}"
                    )]
                ),
            )

        except Exception as e:
            logger.error(f"[{self.agent_name}] Task failed: {e}", exc_info=True)
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self.stats["failed_tasks"] += 1

            # ========== 保存失败状态到记忆 ==========
            if self.enable_task_memory:
                await self._save_task_error_state(task_id, e, ctx)

            await self.progress_tracker.unregister_task(task_id)
            raise

    async def _dispatch_stage_with_memory(
        self,
        ctx: InvocationContext,
        task: Task,
        agent_name: str,
        stage: TaskStage,
        target_progress: int,
    ) -> None:
        """
        调度子智能体执行（带重试和记忆）

        覆盖父类方法，添加状态记录

        Args:
            ctx: 调用上下文
            task: 任务对象
            agent_name: 子智能体名称
            stage: 当前阶段
            target_progress: 目标进度
        """
        agent = self._sub_agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent not found: {agent_name}")

        await self.progress_tracker.start_stage(task.id, stage)

        # ========== 记录阶段开始 ==========
        if self.enable_task_memory:
            await self.remember(
                key=f"stage_{stage.value}_start",
                value={
                    "stage": stage.value,
                    "agent": agent_name,
                    "start_time": datetime.now().isoformat(),
                },
                importance=0.5,
                scope="TASK",
                tags=["stage", "progress"],
            )

        for attempt in range(self.retry_limit):
            try:
                logger.info(
                    f"[{self.agent_name}] Executing {agent_name} (attempt {attempt + 1}/{self.retry_limit})"
                )

                # 执行子智能体
                await agent.run_async(ctx)

                # ========== 记录阶段完成 ==========
                if self.enable_task_memory:
                    await self.remember(
                        key=f"stage_{stage.value}_complete",
                        value={
                            "stage": stage.value,
                            "agent": agent_name,
                            "end_time": datetime.now().isoformat(),
                            "attempts": attempt + 1,
                        },
                        importance=0.6,
                        scope="TASK",
                        tags=["stage", "progress", "complete"],
                    )

                # 更新进度
                await self.progress_tracker.complete_stage(task.id, stage)

                logger.info(f"[{self.agent_name}] {agent_name} completed successfully")
                return

            except Exception as e:
                logger.warning(
                    f"[{self.agent_name}] {agent_name} failed (attempt {attempt + 1}): {e}"
                )

                if attempt < self.retry_limit - 1:
                    # 继续重试
                    await asyncio.sleep(1)
                    continue
                else:
                    # 达到最大重试次数，执行容错兜底
                    logger.error(
                        f"[{self.agent_name}] {agent_name} failed after {self.retry_limit} attempts, using fallback"
                    )
                    self._handle_failure(ctx, task, agent_name, stage, e)
                    return

    async def _save_task_initial_state(
        self, task_id: str, user_input: str, ctx: InvocationContext
    ):
        """保存任务初始状态到记忆"""
        await self.remember(
            key="task_initial_state",
            value={
                "task_id": task_id,
                "user_input": user_input,
                "start_time": datetime.now().isoformat(),
                "status": "started",
            },
            importance=0.9,
            scope="TASK",
            tags=["task", "initial"],
        )

        # 同时保存到用户级作用域（用于跨任务分析）
        user_id = self._get_user_id()
        await self.remember(
            key=f"task_{task_id}",
            value={
                "task_id": task_id,
                "user_input": user_input[:500],  # 截断以节省空间
                "start_time": datetime.now().isoformat(),
            },
            importance=0.7,
            scope="USER",
            scope_id=user_id,
            tags=["task_history"],
        )

    async def _save_task_final_state(
        self, task_id: str, task: Task, ctx: InvocationContext
    ):
        """保存任务最终状态到记忆"""
        framework = ctx.session.state.get("ppt_framework", {})

        await self.remember(
            key="task_final_state",
            value={
                "task_id": task_id,
                "end_time": datetime.now().isoformat(),
                "status": "completed",
                "total_duration": task.metadata.total_duration,
                "total_pages": framework.get("total_page", 0),
            },
            importance=0.9,
            scope="TASK",
            tags=["task", "final"],
        )

        # 更新用户级任务历史
        user_id = self._get_user_id()
        await self.remember(
            key=f"task_{task_id}_result",
            value={
                "task_id": task_id,
                "status": "completed",
                "end_time": datetime.now().isoformat(),
                "total_pages": framework.get("total_page", 0),
            },
            importance=0.6,
            scope="USER",
            scope_id=user_id,
            tags=["task_history"],
        )

    async def _save_task_error_state(
        self, task_id: str, error: Exception, ctx: InvocationContext
    ):
        """保存任务错误状态到记忆"""
        await self.remember(
            key="task_error_state",
            value={
                "task_id": task_id,
                "error": str(error),
                "error_type": type(error).__name__,
                "time": datetime.now().isoformat(),
            },
            importance=0.8,
            scope="TASK",
            tags=["task", "error"],
        )

    async def _find_similar_task(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        查找相似的历史任务

        Args:
            user_input: 用户输入

        Returns:
            相似任务信息，如果没有返回None
        """
        user_id = self._get_user_id()

        # 简化实现：可以使用向量搜索找到相似任务
        # 这里返回None，实际使用中可以实现语义搜索
        return None

    def _setup_context(self, ctx: InvocationContext):
        """设置上下文信息"""
        task_id = ctx.session.state.get("task_id", self._generate_task_id())
        user_id = ctx.session.state.get("user_id", "anonymous")

        self.set_context(
            task_id=task_id,
            user_id=user_id,
            session_id=task_id,
        )


# 创建全局实例
master_coordinator_agent_with_memory = MasterCoordinatorAgentWithMemory()


if __name__ == "__main__":
    # 测试代码
    async def test_coordinator():
        print(f"Testing MasterCoordinatorAgentWithMemory")
        print("=" * 60)

        agent = master_coordinator_agent_with_memory

        print(f"Agent name: {agent.name}")
        print(f"Memory enabled: {agent.is_memory_enabled()}")
        print(f"Task memory: {agent.enable_task_memory}")
        print(f"Performance tracking: {agent.enable_performance_tracking}")

    asyncio.run(test_coordinator())
