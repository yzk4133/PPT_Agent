"""
主工作流图 - LangChain/LangGraph 实现

主工作流图 - LangChain/LangGraph 实现

此模块使用 LangGraph 定义主要的 PPT 生成工作流。
它在一个声明式状态图中协调所有智能体。

架构：
- 具有 5 个主要节点的状态图
- 研究条件分支
- 页面流水线用于并行执行
- 通过状态跟踪进度
"""

import logging
import os
import uuid
import asyncio
from typing import Dict, Any, Optional, Literal

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from infrastructure.config import get_llm_config

from ..models.state import (
    PPTGenerationState,
    create_initial_state,
    update_state_progress,
    needs_research,
    validate_state_for_stage,
)
from ..core.requirements.requirement_agent import RequirementParserAgent, create_requirement_parser
from ..core.planning.framework_agent import FrameworkDesignerAgent, create_framework_designer
from ..core.research.research_agent import ResearchAgent, create_research_agent
from ..core.generation.content_agent import ContentMaterialAgent, create_content_agent
from ..core.rendering.renderer_agent import TemplateRendererAgent, create_renderer_agent
from .page_pipeline import PagePipeline, create_page_pipeline

logger = logging.getLogger(__name__)


class MasterGraph:
    """
    主工作流图 - LangGraph 实现

    这是 MultiAgentPPT 的主协调器，使用 LangGraph 的声明式工作流。

    工作流：
    entry -> requirement_parser -> framework_designer
        -> [need_research?]
            -> YES: research -> content_generation
            -> NO: content_generation
        -> template_renderer -> END

    与原架构对比：
    - 原 Google ADK: MasterCoordinatorAgentWithMemory
    - LangChain 版本: MasterGraph 使用 LangGraph StateGraph

    TODO: Phase 2 - 集成记忆系统（AgentMemoryMixin）
    """

    def __init__(
        self,
        requirement_agent: Optional[RequirementParserAgent] = None,
        framework_agent: Optional[FrameworkDesignerAgent] = None,
        research_agent: Optional[ResearchAgent] = None,
        content_agent: Optional[ContentMaterialAgent] = None,
        renderer_agent: Optional[TemplateRendererAgent] = None,
        page_pipeline: Optional[PagePipeline] = None,
        model: Optional[ChatOpenAI] = None,
        # Quality control parameters
        enable_quality_checks: bool = True,
        quality_threshold: float = 0.8,
        max_refinements: int = 3,
    ):
        """
        初始化主工作流图

        参数：
            requirement_agent: 需求解析智能体
            framework_agent: 框架设计智能体
            research_agent: 研究智能体
            content_agent: 内容生成智能体
            renderer_agent: 渲染智能体
            page_pipeline: 页面流水线
            model: 共享的LLM模型（如果为None则创建默认）
            enable_quality_checks: 是否启用质量检查（默认True）
            quality_threshold: 质量阈值（0.0-1.0，默认0.8）
            max_refinements: 最大改进次数（默认3）
        """
        # 质量控制设置
        self.enable_quality_checks = enable_quality_checks
        self.quality_threshold = quality_threshold
        self.max_refinements = max_refinements
        # 创建或使用提供的智能体
        self.model = model or self._create_default_model()

        self.requirement_agent = requirement_agent or create_requirement_parser(self.model)
        self.framework_agent = framework_agent or create_framework_designer(
            self.model, use_tools=False
        )
        self.research_agent = research_agent or create_research_agent(self.model, use_tools=False)
        self.content_agent = content_agent or create_content_agent(self.model, use_tools=False)
        self.renderer_agent = renderer_agent or create_renderer_agent(self.model)

        # 创建页面流水线
        self.page_pipeline = page_pipeline or create_page_pipeline(
            max_concurrency=int(os.getenv("PAGE_PIPELINE_CONCURRENCY", "3"))
        )

        # 构建状态图
        self.graph = self._build_graph()

        logger.info("[MasterGraph] Initialized with all agents")

    def _create_default_model(self) -> ChatOpenAI:
        """创建默认LLM模型"""
        llm_config = get_llm_config()

        if not llm_config.api_key:
            logger.warning("[MasterGraph] No API key found, using mock mode")
            return ChatOpenAI(
                model="gpt-4o-mini",
                api_key="sk-mock-key",
                temperature=0.0,
            )

        return ChatOpenAI(**llm_config.to_langchain_config())

    def _build_graph(self) -> StateGraph:
        """
        构建状态图

        返回：
            StateGraph 实例
        """
        # 创建状态图
        builder = StateGraph(PPTGenerationState)

        # 添加节点
        builder.add_node("requirement_parser", self.requirement_agent.run_node)
        builder.add_node("framework_designer", self.framework_agent.run_node)
        builder.add_node("research", self.research_agent.run_node)
        builder.add_node("content_generation", self.content_agent.run_node)
        builder.add_node("template_renderer", self.renderer_agent.run_node)

        # 添加质量控制节点（如果启用）
        if self.enable_quality_checks:
            from ..core.quality.nodes import check_content_quality, refine_content

            # 创建带阈值的检查节点
            def quality_check_with_threshold(state: PPTGenerationState) -> PPTGenerationState:
                import asyncio

                return asyncio.run(check_content_quality(state, threshold=self.quality_threshold))

            # 创建带模型引用的改进节点
            def refine_content_with_model(state: PPTGenerationState) -> PPTGenerationState:
                import asyncio

                return asyncio.run(refine_content(state, model=self.model))

            builder.add_node("quality_check", quality_check_with_threshold)
            builder.add_node("refine_content", refine_content_with_model)

            logger.info("[MasterGraph] Quality control nodes added")

        # 设置入口点
        builder.set_entry_point("requirement_parser")

        # 添加边 - 需求解析 -> 框架设计
        builder.add_edge("requirement_parser", "framework_designer")

        # 添加条件边 - 框架设计 -> [研究 or 内容生成]
        builder.add_conditional_edges(
            "framework_designer",
            self._should_research,
            {"research": "research", "content": "content_generation"},
        )

        # 添加边 - 研究 -> 内容生成
        builder.add_edge("research", "content_generation")

        # 添加边 - 内容生成 -> (质量检查 or 直接渲染)
        if self.enable_quality_checks:
            builder.add_edge("content_generation", "quality_check")

            # 质量检查 -> (改进 or 渲染)
            builder.add_conditional_edges(
                "quality_check",
                self._should_refine,
                {"refine": "refine_content", "proceed": "template_renderer"},
            )

            # 改进 -> 质量检查（循环）
            builder.add_edge("refine_content", "quality_check")

            logger.info("[MasterGraph] Quality control workflow integrated")
        else:
            # 跳过质量检查，直接渲染
            builder.add_edge("content_generation", "template_renderer")

        # 添加边 - 模板渲染 -> END
        builder.add_edge("template_renderer", END)

        # 编译图
        graph = builder.compile()

        logger.info("[MasterGraph] State graph built successfully")
        return graph

    def _should_research(self, state: PPTGenerationState) -> Literal["research", "content"]:
        """
        条件判断：是否需要研究

        参数：
            state: 当前状态

        返回：
            下一个节点名称
        """
        if needs_research(state):
            logger.info("[MasterGraph] Research needed, routing to research node")
            return "research"
        else:
            logger.info("[MasterGraph] No research needed, routing to content_generation node")
            return "content"

    def _should_refine(self, state: PPTGenerationState) -> Literal["refine", "proceed"]:
        """
        条件判断：是否需要改进内容

        参数：
            state: 当前状态

        返回：
            下一个节点名称 ("refine" 或 "proceed")
        """
        # 检查是否超过最大改进次数
        refinement_count = state.get("refinement_count", 0)

        if refinement_count >= self.max_refinements:
            logger.warning(
                f"[MasterGraph] Max refinements reached ({self.max_refinements}), proceeding to render"
            )
            return "proceed"

        # 使用质量评估结果决定
        from ..core.quality.nodes import should_refine_content

        decision = should_refine_content(state)

        if decision == "refine":
            logger.info(
                f"[MasterGraph] Quality below threshold, routing to refinement "
                f"(iteration {refinement_count + 1}/{self.max_refinements})"
            )
        else:
            logger.info(f"[MasterGraph] Quality threshold met, proceeding to render")

        return decision

    async def generate(
        self, user_input: str, task_id: Optional[str] = None, user_id: str = "anonymous"
    ) -> PPTGenerationState:
        """
        生成PPT（主入口）

        参数：
            user_input: 用户输入
            task_id: 任务ID（如果为None则自动生成）
            user_id: 用户ID

        返回：
            最终状态
        """
        # 生成任务ID
        if not task_id:
            task_id = f"task_{uuid.uuid4().hex[:8]}"

        logger.info(f"[MasterGraph] Starting PPT generation: task_id={task_id}")
        logger.info(f"[MasterGraph] User input: {user_input[:100]}...")

        # 创建初始状态
        initial_state = create_initial_state(
            user_input=user_input, task_id=task_id, user_id=user_id
        )

        try:
            # 执行工作流
            final_state = await self.graph.ainvoke(initial_state)

            # 检查是否有错误
            if final_state.get("error"):
                logger.error(
                    f"[MasterGraph] Generation completed with error: {final_state['error']}"
                )
            else:
                logger.info(f"[MasterGraph] Generation completed successfully")
                logger.info(
                    f"[MasterGraph] Output: {final_state.get('ppt_output', {}).get('file_path', 'N/A')}"
                )

            return final_state

        except Exception as e:
            logger.error(f"[MasterGraph] Generation failed: {e}", exc_info=True)

            # 更新状态中的错误
            final_state = initial_state
            final_state["error"] = str(e)
            final_state["current_stage"] = "failed"

            return final_state

    async def generate_with_callbacks(
        self,
        user_input: str,
        on_stage_complete: Optional[callable] = None,
        on_progress: Optional[callable] = None,
        on_error: Optional[callable] = None,
        task_id: Optional[str] = None,
        user_id: str = "anonymous",
    ) -> PPTGenerationState:
        """
        带流式回掉的生成

        使用 LangGraph 的 streaming 功能实现实时进度更新。

        参数：
            user_input: 用户输入
            on_stage_complete: 阶段完成回调 (stage_name, state)
            on_progress: 进度回调 (progress, message)
            on_error: 错误回调 (stage_name, error)
            task_id: 任务ID
            user_id: 用户ID

        返回：
            最终状态
        """
        # 生成任务ID
        if not task_id:
            task_id = f"task_{uuid.uuid4().hex[:8]}"

        logger.info(f"[MasterGraph] Starting streaming PPT generation: task_id={task_id}")

        # 创建初始状态
        initial_state = create_initial_state(
            user_input=user_input, task_id=task_id, user_id=user_id
        )

        # 创建进度跟踪器
        from .progress_tracker import create_progress_tracker

        tracker = create_progress_tracker(
            state=initial_state,
            on_progress=on_progress,
            on_stage_complete=on_stage_complete,
            on_error=on_error,
        )

        # 初始化进度
        tracker.update_stage("init", 0, "Initializing workflow")

        try:
            # 使用 LangGraph streaming
            # 兼容不同 LangGraph 版本：有些版本不会发送 __end__ 事件
            final_state = dict(initial_state)
            async for event in self.graph.astream(initial_state):
                # event 格式: {"node_name": {"key": "value"}} 或 {"__end__": final_state}
                for node_name, node_output in event.items():
                    if node_name == "__end__":
                        # 工作流完成
                        if isinstance(node_output, dict):
                            final_state.update(node_output)
                        else:
                            final_state = node_output
                        break

                    if isinstance(node_output, dict):
                        final_state.update(node_output)

                    # 更新进度
                    progress = self._get_stage_progress(node_name)
                    tracker.update_stage(node_name, progress, f"Processing {node_name}")

                    # 触发阶段完成回调
                    if on_stage_complete:
                        try:
                            if asyncio.iscoroutinefunction(on_stage_complete):
                                await on_stage_complete(node_name, node_output)
                            else:
                                on_stage_complete(node_name, node_output)
                        except Exception as cb_error:
                            logger.error(f"[MasterGraph] Stage complete callback error: {cb_error}")

            # 确保返回最终状态
            if final_state is None:
                final_state = initial_state

            # 标记完成
            tracker.stage_complete("complete", final_state)

            logger.info(f"[MasterGraph] Streaming generation completed")
            return final_state

        except Exception as e:
            logger.error(f"[MasterGraph] Streaming generation failed: {e}", exc_info=True)
            tracker.error("generation", e)
            raise

    def _get_stage_progress(self, stage: str) -> int:
        """
        获取阶段进度百分比

        Args:
            stage: 阶段名称

        Returns:
            进度百分比 (0-100)
        """
        from .progress_tracker import StageProgressMapper

        # 如果启用质量检查，调整进度权重
        if self.enable_quality_checks:
            # 质量/改进阶段占用额外约15%
            base_progress = StageProgressMapper.get_progress_for_stage(stage)
            if stage in ["quality_check", "refine_content"]:
                # 质量相关阶段
                if stage == "quality_check":
                    return 80
                else:  # refine_content
                    return 85
            return base_progress
        else:
            return StageProgressMapper.get_progress_for_stage(stage)


# 工厂函数


def create_master_graph(
    model: Optional[ChatOpenAI] = None,
    max_concurrency: int = 3,
    enable_quality_checks: bool = True,
    quality_threshold: float = 0.8,
    max_refinements: int = 3,
) -> MasterGraph:
    """
    创建主工作流图

    参数：
        model: LangChain LLM 实例
        max_concurrency: 页面流水线最大并发数
        enable_quality_checks: 是否启用质量检查（默认True）
        quality_threshold: 质量阈值（0.0-1.0，默认0.8）
        max_refinements: 最大改进次数（默认3）

    返回：
        MasterGraph 实例
    """
    return MasterGraph(
        model=model,
        page_pipeline=create_page_pipeline(max_concurrency=max_concurrency),
        enable_quality_checks=enable_quality_checks,
        quality_threshold=quality_threshold,
        max_refinements=max_refinements,
    )


# 便捷函数


async def generate_ppt(
    user_input: str,
    model: Optional[ChatOpenAI] = None,
    task_id: Optional[str] = None,
    user_id: str = "anonymous",
) -> Dict[str, Any]:
    """
    直接生成 PPT（便捷函数）

    参数：
        user_input: 用户输入
        model: 可选的 LLM 模型
        task_id: 可选的任务 ID
        user_id: 用户 ID

    返回：
        最终状态字典
    """
    graph = create_master_graph(model)
    state = await graph.generate(user_input, task_id, user_id)
    return state


if __name__ == "__main__":
    import asyncio

    async def test():
        # 测试主工作流
        test_inputs = [
            "生成一份关于人工智能的PPT，15页，学术风格",
            "创建一份关于Q3销售报告的商务演示文稿，10页",
        ]

        graph = create_master_graph()

        for test_input in test_inputs:
            print(f"\n{'='*60}")
            print(f"Input: {test_input}")
            print(f"{'='*60}")

            import time

            start_time = time.time()

            result = await graph.generate(test_input)

            elapsed = time.time() - start_time

            print(f"\nResults:")
            print(f"  Task ID: {result.get('task_id')}")
            print(f"  Status: {result.get('current_stage')}")
            print(f"  Progress: {result.get('progress')}%")
            print(f"  Elapsed time: {elapsed:.2f}s")

            if result.get("error"):
                print(f"  Error: {result['error']}")
            else:
                ppt_output = result.get("ppt_output", {})
                print(f"  Output file: {ppt_output.get('file_path')}")
                print(f"  Total pages: {ppt_output.get('total_pages')}")

    asyncio.run(test())
