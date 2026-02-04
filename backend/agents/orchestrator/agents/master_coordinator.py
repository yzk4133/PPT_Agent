"""
Master Coordinator Agent

主协调智能体 - 架构大脑

6大核心功能：
1. 需求入口与分发
2. 任务建模与调度（DAG）
3. 信息中转
4. 全流程校验（交叉校验）
5. 容错兜底（3次重试）
6. 进度与状态管理

支持三种执行模式：
- FULL: 完整执行所有阶段（一次性生成完整PPT）
- PHASE_1: 仅执行阶段1-2（需求解析+框架设计，生成大纲）
- PHASE_2: 从checkpoint继续执行阶段3-5（研究→内容→渲染）
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from typing import AsyncGenerator, Optional, Dict, Any, Callable
from datetime import datetime

from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from google.adk.events.event import Event

# 导入基础设施

# 导入领域模型
from domain.models import Task, TaskStatus, TaskStage
from domain.models.execution_mode import ExecutionMode
from domain.models.checkpoint import Checkpoint

# 导入子智能体
from agents.core.planning.requirements.requirement_parser_agent import requirement_parser_agent
from agents.core.planning.framework_designer_agent import framework_designer_agent
from agents.core.research.research_agent import optimized_research_agent
from agents.core.generation.content_material_agent import content_material_agent
from agents.core.rendering.template_renderer_agent import template_renderer_agent

# 导入进度追踪器
from agents.orchestrator.components.progress_tracker import get_progress_tracker, ProgressUpdate

# 导入页面流水线（可选）
try:
    from agents.orchestrator.components.page_pipeline import PagePipeline, PagePipelineConfig
    PAGE_PIPELINE_AVAILABLE = True
except ImportError:
    PAGE_PIPELINE_AVAILABLE = False
    PagePipeline = None
    PagePipelineConfig = None

logger = logging.getLogger(__name__)

class MasterCoordinatorAgent(BaseAgent):
    """
    主协调智能体 - 架构大脑

    6大核心功能：
    1. 需求入口与分发
    2. 任务建模与调度（DAG）
    3. 信息中转
    4. 全流程校验（交叉校验）
    5. 容错兜底（3次重试）
    6. 进度与状态管理

    支持三种执行模式：
    - FULL: 完整执行所有阶段（一次性生成完整PPT）
    - PHASE_1: 仅执行阶段1-2（需求解析+框架设计，生成大纲）
    - PHASE_2: 从checkpoint继续执行阶段3-5（研究→内容→渲染）
    """

    def __init__(
        self,
        checkpoint_manager=None,
        enable_page_pipeline: bool = True,
        page_pipeline_config=None,
        **kwargs
    ):
        """
        初始化MasterCoordinatorAgent

        Args:
            checkpoint_manager: Checkpoint管理器（用于两阶段执行）
            enable_page_pipeline: 是否启用页面级流水线并行
            page_pipeline_config: 页面流水线配置
            **kwargs: 其他参数
        """
        super().__init__(
            name="MasterCoordinatorAgent",
            description="主协调智能体，负责调度5个子智能体完成PPT生成",
            **kwargs
        )

        # 使用 object.__setattr__ 避免 Pydantic 的字段检查
        object.__setattr__(self, 'retry_limit', 3)
        object.__setattr__(self, 'progress_tracker', get_progress_tracker())
        object.__setattr__(self, 'checkpoint_manager', checkpoint_manager)
        object.__setattr__(self, 'enable_page_pipeline', enable_page_pipeline and PAGE_PIPELINE_AVAILABLE)
        object.__setattr__(self, 'page_pipeline_config', page_pipeline_config or (PagePipelineConfig() if PagePipelineConfig else None))

        # 子智能体映射
        object.__setattr__(self, '_sub_agents', {
            "requirement_parser": requirement_parser_agent,
            "framework_designer": framework_designer_agent,
            "research": optimized_research_agent,
            "content_material": content_material_agent,
            "template_renderer": template_renderer_agent
        })

        # 页面流水线（如果启用）
        page_pipeline = None
        if self.enable_page_pipeline and PagePipeline:
            page_pipeline = PagePipeline(
                research_agent=optimized_research_agent,
                content_agent=content_material_agent,
                config=self.page_pipeline_config
            )
        object.__setattr__(self, 'page_pipeline', page_pipeline)

        logger.info(
            f"MasterCoordinatorAgent initialized: "
            f"checkpoint_manager={checkpoint_manager is not None}, "
            f"page_pipeline={self.enable_page_pipeline}"
        )

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        执行主协调流程 - 支持三种执行模式

        Args:
            ctx: 调用上下文
        """
        # 获取执行模式（从session.state或默认FULL）
        execution_mode_str = ctx.session.state.get("execution_mode", "full")
        try:
            execution_mode = ExecutionMode.from_string(execution_mode_str)
        except ValueError:
            execution_mode = ExecutionMode.FULL
            ctx.session.state["execution_mode"] = ExecutionMode.FULL.value

        logger.info(f"MasterCoordinatorAgent started with execution mode: {execution_mode.value}")

        try:
            # 根据执行模式执行不同流程
            if execution_mode == ExecutionMode.FULL:
                async for event in self._run_full_mode(ctx):
                    yield event
            elif execution_mode == ExecutionMode.PHASE_1:
                async for event in self._run_phase_1(ctx):
                    yield event
            elif execution_mode == ExecutionMode.PHASE_2:
                async for event in self._run_phase_2(ctx):
                    yield event
            else:
                raise ValueError(f"Unknown execution mode: {execution_mode}")

        except Exception as e:
            logger.error(f"Task failed: {e}", exc_info=True)
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[types.Part(text=f"PPT生成失败: {str(e)}")]
                ),
                actions=types.EventActions(escalate=True)
            )

    async def _run_full_mode(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        完整执行模式（一次性生成完整PPT）

        Args:
            ctx: 调用上下文
        """
        # 1. 生成任务ID
        task_id = self._generate_task_id()
        ctx.session.state["task_id"] = task_id

        # 2. 保存原始用户输入
        user_input = ctx.user_content.parts[0].text
        ctx.session.state["raw_user_input"] = user_input

        # 3. 创建任务对象
        task = Task(id=task_id, raw_input=user_input)
        await self.progress_tracker.register_task(task)

        logger.info(f"FULL mode: task {task_id}")

        try:
            # 4. 执行各阶段
            # 阶段1：需求解析 (0% - 15%)
            await self._dispatch_stage(
                ctx, task, "requirement_parser", TaskStage.REQUIREMENT_PARSING, 15
            )

            # 阶段2：框架设计 (15% - 30%)
            await self._dispatch_stage(
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
                    await self._dispatch_stage(
                        ctx, task, "research", TaskStage.RESEARCH, 50
                    )

                await self._dispatch_stage(
                    ctx, task, "content_material", TaskStage.CONTENT_GENERATION, 80
                )

            # 阶段5：PPT模板渲染 (80% - 100%)
            await self._dispatch_stage(
                ctx, task, "template_renderer", TaskStage.TEMPLATE_RENDERING, 100
            )

            # 5. 交叉校验
            self._cross_validate(ctx, task)

            # 6. 标记任务完成
            await self.progress_tracker.complete_task(task_id)
            task.mark_completed()

            # 7. 更新任务对象到上下文
            ctx.session.state["task_object"] = task

            logger.info(f"Task completed: {task_id}")

            # 8. 产生完成事件
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[types.Part(
                        text=f"PPT生成完成！\n\n"
                        f"任务ID: {task_id}\n"
                        f"总耗时: {task.metadata.total_duration:.1f}秒\n"
                        f"生成页数: {ctx.session.state.get('ppt_framework', {}).get('total_page', 0)}页"
                    )]
                ),
            )

        except Exception as e:
            logger.error(f"Task failed: {e}", exc_info=True)
            task.status = TaskStatus.FAILED
            task.error = str(e)
            await self.progress_tracker.unregister_task(task_id)
            raise

    async def _run_phase_1(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        阶段1执行：生成大纲

        Args:
            ctx: 调用上下文
        """
        # 1. 生成任务ID
        task_id = self._generate_task_id()
        ctx.session.state["task_id"] = task_id

        # 2. 保存原始用户输入
        user_input = ctx.user_content.parts[0].text
        ctx.session.state["raw_user_input"] = user_input

        # 3. 创建任务对象
        task = Task(id=task_id, raw_input=user_input)
        await self.progress_tracker.register_task(task)

        logger.info(f"PHASE_1 mode: task {task_id}")

        try:
            # 4. 执行需求解析和框架设计
            await self._dispatch_stage(
                ctx, task, "requirement_parser", TaskStage.REQUIREMENT_PARSING, 50
            )

            await self._dispatch_stage(
                ctx, task, "framework_designer", TaskStage.FRAMEWORK_DESIGN, 100
            )

            # 5. 保存checkpoint
            if self.checkpoint_manager:
                checkpoint = await self.checkpoint_manager.save_checkpoint(
                    task_id=task_id,
                    user_id=getattr(ctx, 'user_id', 'anonymous'),
                    execution_mode=ExecutionMode.PHASE_1,
                    phase=2,  # 已完成阶段2
                    raw_input=user_input,
                    requirements=ctx.session.state.get("structured_requirements", {}),
                    framework=ctx.session.state.get("ppt_framework", {})
                )

                logger.info(f"Checkpoint saved: {checkpoint.task_id}")

                # 产生checkpoint保存事件
                yield Event(
                    author=self.name,
                    content=types.Content(
                        parts=[types.Part(
                            text=f"大纲生成完成！\n\n"
                            f"任务ID: {task_id}\n"
                            f"阶段: 需求解析 + 框架设计\n"
                            f"总页数: {ctx.session.state.get('ppt_framework', {}).get('total_page', 0)}页\n\n"
                            f"请编辑大纲后继续生成PPT。"
                        )]
                    ),
                )
            else:
                yield Event(
                    author=self.name,
                    content=types.Content(
                        parts=[types.Part(
                            text=f"大纲生成完成！\n\n"
                            f"任务ID: {task_id}\n"
                            f"注意: Checkpoint manager未配置，无法保存大纲状态。"
                        )]
                    ),
                )

        except Exception as e:
            logger.error(f"PHASE_1 failed: {e}", exc_info=True)
            task.status = TaskStatus.FAILED
            task.error = str(e)
            await self.progress_tracker.unregister_task(task_id)
            raise

    async def _run_phase_2(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        阶段2执行：从checkpoint继续生成PPT

        Args:
            ctx: 调用上下文
        """
        # 1. 获取task_id（从请求参数）
        task_id = ctx.session.state.get("task_id")
        if not task_id:
            raise ValueError("task_id is required for PHASE_2 execution")

        logger.info(f"PHASE_2 mode: task {task_id}")

        # 2. 加载checkpoint
        if not self.checkpoint_manager:
            raise ValueError("Checkpoint manager is required for PHASE_2 execution")

        checkpoint = await self.checkpoint_manager.load_checkpoint(task_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint not found for task_id: {task_id}")

        # 3. 恢复session state
        ctx.session.state["task_id"] = checkpoint.task_id
        ctx.session.state["structured_requirements"] = checkpoint.structured_requirements
        ctx.session.state["ppt_framework"] = checkpoint.ppt_framework
        ctx.session.state["raw_user_input"] = checkpoint.raw_user_input

        # 4. 创建任务对象
        task = Task(id=task_id, raw_input=checkpoint.raw_user_input)
        await self.progress_tracker.register_task(task)

        try:
            # 5. 继续执行阶段3-5
            requirement = checkpoint.structured_requirements
            need_research = requirement.get("need_research", False)

            if need_research and self.page_pipeline:
                # 使用流水线并行
                await self._execute_page_pipeline(ctx, task, 30, 80)
            else:
                # 原有串行逻辑
                if need_research:
                    await self._dispatch_stage(
                        ctx, task, "research", TaskStage.RESEARCH, 50
                    )

                await self._dispatch_stage(
                    ctx, task, "content_material", TaskStage.CONTENT_GENERATION, 80
                )

            # 阶段5：PPT模板渲染 (80% - 100%)
            await self._dispatch_stage(
                ctx, task, "template_renderer", TaskStage.TEMPLATE_RENDERING, 100
            )

            # 6. 交叉校验
            self._cross_validate(ctx, task)

            # 7. 标记任务和checkpoint完成
            await self.progress_tracker.complete_task(task_id)
            task.mark_completed()
            await self.checkpoint_manager.mark_completed(task_id)

            # 8. 更新任务对象到上下文
            ctx.session.state["task_object"] = task

            logger.info(f"Task completed: {task_id}")

            # 9. 产生完成事件
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[types.Part(
                        text=f"PPT生成完成！\n\n"
                        f"任务ID: {task_id}\n"
                        f"总耗时: {task.metadata.total_duration:.1f}秒\n"
                        f"生成页数: {ctx.session.state.get('ppt_framework', {}).get('total_page', 0)}页"
                    )]
                ),
            )

        except Exception as e:
            logger.error(f"PHASE_2 failed: {e}", exc_info=True)
            task.status = TaskStatus.FAILED
            task.error = str(e)
            await self.progress_tracker.unregister_task(task_id)
            raise

    async def _execute_page_pipeline(
        self,
        ctx: InvocationContext,
        task: Task,
        start_progress: int,
        end_progress: int
    ) -> None:
        """
        执行页面级流水线并行

        Args:
            ctx: 调用上下文
            task: 任务对象
            start_progress: 起始进度
            end_progress: 结束进度
        """
        if not self.page_pipeline:
            logger.warning("Page pipeline not available, falling back to serial execution")
            # 回退到串行执行
            requirement = ctx.session.state.get("structured_requirements", {})
            if requirement.get("need_research"):
                await self._dispatch_stage(ctx, task, "research", TaskStage.RESEARCH, 50)
            await self._dispatch_stage(ctx, task, "content_material", TaskStage.CONTENT_GENERATION, 80)
            return

        from domain.models.framework import PPTFramework

        # 获取框架
        framework_dict = ctx.session.state.get("ppt_framework")
        framework = PPTFramework.from_dict(framework_dict)

        logger.info(f"Executing page pipeline: {len(framework.pages)} pages")

        # 定义进度回调
        def progress_callback(progress: float):
            """进度回调"""
            # 映射进度到指定范围
            adjusted_progress = start_progress + (progress / 100) * (end_progress - start_progress)
            # 可以在这里触发进度更新事件

        # 执行流水线
        content_materials = await self.page_pipeline.execute_pages(
            framework=framework,
            ctx=ctx,
            progress_callback=progress_callback
        )

        # 保存结果
        ctx.session.state["content_material"] = content_materials

        logger.info(f"Page pipeline completed: {len(content_materials)} pages")

    async def _dispatch_stage(
        self,
        ctx: InvocationContext,
        task: Task,
        agent_name: str,
        stage: TaskStage,
        target_progress: int
    ) -> None:
        """
        调度子智能体执行（带重试）

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

        for attempt in range(self.retry_limit):
            try:
                logger.info(f"Executing {agent_name} (attempt {attempt + 1}/{self.retry_limit})")

                # 执行子智能体
                await agent.run_async(ctx)

                # 更新进度
                await self.progress_tracker.complete_stage(task.id, stage)

                logger.info(f"{agent_name} completed successfully")
                return

            except Exception as e:
                logger.warning(f"{agent_name} failed (attempt {attempt + 1}): {e}")

                if attempt < self.retry_limit - 1:
                    # 继续重试
                    await asyncio.sleep(1)
                    continue
                else:
                    # 达到最大重试次数，执行容错兜底
                    logger.error(f"{agent_name} failed after {self.retry_limit} attempts, using fallback")
                    self._handle_failure(ctx, task, agent_name, stage, e)
                    return

    def _handle_failure(
        self,
        ctx: InvocationContext,
        task: Task,
        agent_name: str,
        stage: TaskStage,
        error: Exception
    ) -> None:
        """
        容错兜底处理

        Args:
            ctx: 调用上下文
            task: 任务对象
            agent_name: 失败的智能体名称
            stage: 失败的阶段
            error: 错误信息
        """
        logger.warning(f"Handling failure for {agent_name}: {error}")

        if agent_name == "requirement_parser":
            # 使用默认需求
            from domain.models import Requirement
            default_req = Requirement(ppt_topic=task.raw_input[:100])
            ctx.session.state["structured_requirements"] = default_req.to_dict()

        elif agent_name == "framework_designer":
            # 使用默认框架
            from domain.models import PPTFramework, Requirement
            requirement_dict = ctx.session.state.get("structured_requirements", {})
            requirement = Requirement.from_dict(requirement_dict) if requirement_dict else Requirement(ppt_topic="默认主题")
            default_framework = PPTFramework.create_default(requirement.page_num, requirement.ppt_topic)
            ctx.session.state["ppt_framework"] = default_framework.to_dict()

        elif agent_name == "research":
            # 空研究结果
            ctx.session.state["research_results"] = []

        elif agent_name == "content_material":
            # 空内容素材
            framework = ctx.session.state.get("ppt_framework", {})
            pages = framework.get("ppt_framework", [])
            ctx.session.state["content_material"] = [
                {"page_no": p.get("page_no", i + 1), "content_text": ""}
                for i, p in enumerate(pages)
            ]

        elif agent_name == "template_renderer":
            # 生成XML文件作为兜底
            ctx.session.state["ppt_output"] = {
                "file_path": None,
                "preview_data": None,
                "error": str(error)
            }

    def _cross_validate(self, ctx: InvocationContext, task: Task) -> None:
        """
        交叉校验

        Args:
            ctx: 调用上下文
            task: 任务对象
        """
        logger.info("Performing cross-validation")

        # 校验需求与框架的一致性
        requirement = ctx.session.state.get("structured_requirements", {})
        framework = ctx.session.state.get("ppt_framework", {})

        if requirement and framework:
            req_page_num = requirement.get("page_num", 0)
            framework_page_num = framework.get("total_page", 0)

            if req_page_num != framework_page_num:
                logger.warning(f"Page count mismatch: requirement={req_page_num}, framework={framework_page_num}")

        # 校验研究结果与页面的匹配性
        research_results = ctx.session.state.get("research_results", [])
        research_page_indices = framework.get("research_page_indices", [])

        if len(research_results) != len(research_page_indices):
            logger.warning(f"Research results count mismatch: {len(research_results)} vs {len(research_page_indices)}")

        # 校验内容素材与框架的适配性
        content_material = ctx.session.state.get("content_material", [])
        framework_pages = framework.get("ppt_framework", [])

        if len(content_material) != len(framework_pages):
            logger.warning(f"Content material count mismatch: {len(content_material)} vs {len(framework_pages)}")

        logger.info("Cross-validation completed")

    def _generate_task_id(self) -> str:
        """生成任务ID"""
        return f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

# 创建全局实例
master_coordinator_agent = MasterCoordinatorAgent()

if __name__ == "__main__":
    # 测试代码
    import asyncio

    async def test_coordinator():
        print(f"Testing MasterCoordinatorAgent")
        print("=" * 60)

        agent = master_coordinator_agent
        print(f"Agent name: {agent.name}")
        print(f"Sub-agents: {list(agent._sub_agents.keys())}")

        # 测试任务ID生成
        task_id = agent._generate_task_id()
        print(f"Generated task_id: {task_id}")

    asyncio.run(test_coordinator())
