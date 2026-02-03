"""
Flat Slide Outline Agent - 扁平化大纲生成 Agent

3阶段架构：
Stage 1: 需求分析 - 理解用户需求，制定调研计划
Stage 2: 并行调研 - 使用 MCP 工具并行检索资料
Stage 3: 大纲生成 - 汇总调研结果，生成结构化大纲

相比原始架构的改进：
- 从单一 LlmAgent 升级为 3阶段 Sequential
- 并行调研使用 Semaphore 控制并发
- 使用 UnifiedToolManager 统一管理 MCP 工具
- 集成 JSONFallbackParser 和 PartialSuccessHandler
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from google.adk.agents import BaseAgent, LlmAgent, SequentialAgent, ParallelAgent
from google.adk.agents.context import AgentContext
from google.adk.models.lite_llm import LiteLlm

# 导入通用基础设施
import sys
import os

# 添加 backend 目录到模块搜索路径
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from infrastructure.config.common_config import get_config
from infrastructure.config.settings import get_agent_config
from infrastructure.llm.common_model_factory import ModelFactory
from infrastructure.tools.tool_manager import UnifiedToolManager
from infrastructure.llm.fallback import JSONFallbackParser, PartialSuccessHandler, FallbackChain
from infrastructure.llm.retry_decorator import retry_with_exponential_backoff

logger = logging.getLogger(__name__)


class Stage1RequirementAnalysisAgent(LlmAgent):
    """
    Stage 1: 需求分析 Agent

    职责：
    1. 理解用户的PPT主题需求
    2. 分析需要调研的关键方向
    3. 生成结构化的调研计划（JSON格式）
    """

    def __init__(self, model):
        instruction = """你是一名专业的PPT大纲策划专家。

你的任务：
1. 仔细理解用户提供的PPT主题
2. 分析该主题需要调研的关键方向（通常3-5个方向）
3. 为每个调研方向生成具体的搜索查询（中英文各一个）

输出格式（严格JSON，不要任何markdown包裹）：
{
    "topic": "用户的PPT主题",
    "research_directions": [
        {
            "direction": "调研方向1",
            "query_zh": "中文搜索查询",
            "query_en": "English search query",
            "priority": "high|medium|low"
        },
        {
            "direction": "调研方向2",
            "query_zh": "中文搜索查询",
            "query_en": "English search query",
            "priority": "high|medium|low"
        }
    ]
}

注意事项：
- research_directions 数组长度必须在 3-5 之间
- query_zh 和 query_en 必须针对同一主题，但表达方式适配不同语言的搜索习惯
- priority 用于指导后续调研资源分配
"""
        super().__init__(
            model=model,
            name="requirement_analysis_agent",
            description="分析PPT需求并制定调研计划",
            instruction=instruction,
        )


class Stage2ParallelResearchAgent(ParallelAgent):
    """
    Stage 2: 并行调研 Agent

    职责：
    1. 接收 Stage 1 的调研计划
    2. 使用 MCP 工具并行执行搜索
    3. 使用 Semaphore 控制并发（max_concurrency=3）
    4. 处理部分失败场景（PartialSuccessHandler）

    注意：ParallelAgent 内部的 sub_agents 会被 ADK 自动并行执行
    """

    def __init__(self, model, mcp_tools: List[Any], max_concurrency: int = 3):
        self.model = model
        self.mcp_tools = mcp_tools
        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.json_parser = JSONFallbackParser()
        self.partial_handler = PartialSuccessHandler(min_success_rate=0.5)

        # ParallelAgent 暂时不传入 sub_agents，稍后动态创建
        super().__init__(
            name="parallel_research_agent",
            description="并行执行调研任务",
            sub_agents=[],  # 会在 _run_async_impl 中动态添加
        )

    async def _run_async_impl(self, ctx: AgentContext) -> None:
        """
        重写 ParallelAgent 的执行逻辑，添加：
        1. 解析 Stage 1 的调研计划（带 JSON 降级）
        2. 动态创建调研 sub-agents
        3. 使用 Semaphore 控制并发
        4. 处理部分失败
        """
        logger.info("[Stage2] 开始并行调研阶段")

        # 1. 获取 Stage 1 的输出
        stage1_output = ctx.session.state.get("stage1_research_plan", "")
        if not stage1_output:
            # 从 events 中查找最后一个 ResponseEvent
            for event in reversed(ctx.session.events):
                if hasattr(event, "text") and event.text:
                    stage1_output = event.text
                    break

        if not stage1_output:
            logger.error("[Stage2] 无法获取 Stage 1 的调研计划")
            ctx.add_response("错误：未能获取调研计划，请重试")
            return

        # 2. 解析 JSON（带降级策略）
        research_plan = self.json_parser.parse_with_fallback(
            stage1_output,
            default_structure={"topic": "未知主题", "research_directions": []},
        )

        directions = research_plan.get("research_directions", [])
        if not directions:
            logger.warning("[Stage2] 调研计划为空，使用默认查询")
            directions = [
                {
                    "direction": "通用背景",
                    "query_zh": research_plan.get("topic", ""),
                    "query_en": research_plan.get("topic", ""),
                    "priority": "high",
                }
            ]

        logger.info(f"[Stage2] 解析到 {len(directions)} 个调研方向")

        # 3. 动态创建 sub-agents（每个调研方向一个 LlmAgent）
        sub_agents = []
        for idx, direction in enumerate(directions):
            query = direction.get("query_zh", "") or direction.get("query_en", "")
            agent = LlmAgent(
                model=self.model,
                name=f"research_sub_agent_{idx}",
                description=f"调研方向：{direction.get('direction', f'方向{idx}')}",
                instruction=f"""你是一名专业调研员，负责调研以下主题：
方向：{direction.get('direction', '')}
查询：{query}

请使用可用的搜索工具进行深入调研，输出格式：
- 调研方向：{direction.get('direction', '')}
- 关键发现：（列出3-5个要点）
- 参考来源：（如果有）
""",
                tools=self.mcp_tools,  # 注入 MCP 工具
            )
            sub_agents.append(agent)

        # 4. 更新 ParallelAgent 的 sub_agents
        self._sub_agents = sub_agents

        # 5. 使用 Semaphore 控制并发（ADK 会自动并行执行 sub_agents）
        # 注意：这里 ADK 的 ParallelAgent 会自动并行，我们在外层用 semaphore 限制总并发
        async with self.semaphore:
            # 调用父类的并行执行逻辑
            await super()._run_async_impl(ctx)

        # 6. 收集结果并处理部分失败
        research_results = []
        for event in ctx.session.events:
            if hasattr(event, "text") and event.text:
                research_results.append(event.text)

        # 使用 PartialSuccessHandler 验证成功率
        validation_result = self.partial_handler.handle_parallel_results(
            results=research_results, task_name="parallel_research"
        )

        if not validation_result["should_proceed"]:
            logger.error(
                f"[Stage2] 调研成功率不足：{validation_result['success_rate']:.1%}"
            )
            ctx.add_response(
                f"调研失败率过高（{validation_result['failed_count']}/{validation_result['total_count']}），请重试"
            )
            return

        logger.info(
            f"[Stage2] 调研完成，成功率：{validation_result['success_rate']:.1%}"
        )

        # 7. 保存调研结果到 state（供 Stage 3 使用）
        ctx.session.state["stage2_research_results"] = research_results
        ctx.session.state["stage2_success_count"] = validation_result["success_count"]


class Stage3OutlineComposerAgent(LlmAgent):
    """
    Stage 3: 大纲生成 Agent

    职责：
    1. 汇总 Stage 2 的调研结果
    2. 生成结构化的PPT大纲
    3. 确保大纲逻辑清晰、层次分明
    """

    def __init__(self, model):
        instruction = """你是一名专业的PPT大纲编写专家。

你的任务：
1. 仔细阅读前面的调研结果
2. 提炼关键信息，组织逻辑结构
3. 生成结构化的PPT大纲

输出格式（Markdown）：
# PPT主题：[主题名称]

## 1. [章节1标题]
### 1.1 [小节标题]
- 关键点1
- 关键点2

### 1.2 [小节标题]
- 关键点1
- 关键点2

## 2. [章节2标题]
（以此类推）

## 总结与展望

注意事项：
- 大纲应包含 3-5 个主要章节
- 每个章节应有 2-4 个小节
- 每个小节应列出 2-3 个关键点
- 确保逻辑流畅，层次清晰
- 基于调研结果，不要编造信息
"""
        super().__init__(
            model=model,
            name="outline_composer_agent",
            description="生成结构化PPT大纲",
            instruction=instruction,
        )

    async def _run_async_impl(self, ctx: AgentContext) -> None:
        """
        重写执行逻辑，添加调研结果汇总
        """
        logger.info("[Stage3] 开始大纲生成阶段")

        # 1. 获取 Stage 2 的调研结果
        research_results = ctx.session.state.get("stage2_research_results", [])
        success_count = ctx.session.state.get("stage2_success_count", 0)

        if not research_results:
            logger.warning("[Stage3] 未找到调研结果，尝试从 events 中提取")
            research_results = []
            for event in ctx.session.events:
                if hasattr(event, "text") and event.text and len(event.text) > 50:
                    research_results.append(event.text)

        # 2. 汇总调研结果并注入到上下文
        summary = f"""
以下是针对用户PPT主题的调研结果（成功调研 {success_count}/{len(research_results)} 个方向）：

{'='*60}
"""
        for idx, result in enumerate(research_results, 1):
            summary += f"\n调研结果 {idx}:\n{result}\n{'-'*60}\n"

        # 3. 将汇总结果添加到上下文（ADK 会自动传递给 LLM）
        ctx.add_response(summary)

        # 4. 调用父类的 LlmAgent 执行逻辑（会根据 instruction 生成大纲）
        await super()._run_async_impl(ctx)

        logger.info("[Stage3] 大纲生成完成")


class FlatSlideOutlineAgent(SequentialAgent):
    """
    Flat Slide Outline Agent - 扁平化大纲生成主 Agent

    架构：3阶段 Sequential
    Stage 1: RequirementAnalysisAgent（需求分析）
    Stage 2: ParallelResearchAgent（并行调研）
    Stage 3: OutlineComposerAgent（大纲生成）

    优势：
    - 扁平化架构：从单一 Agent 升级为 3阶段流程，但避免 4 层嵌套
    - 统一工具管理：使用 UnifiedToolManager 注册 MCP 工具
    - 并发控制：Semaphore 限制并发 (max_concurrency=3)
    - 降级策略：JSON 解析降级、部分失败处理、模型降级
    """

    def __init__(
        self,
        model_name: str,
        provider: str,
        mcp_tools: List[Any],
        max_concurrency: int = 3,
    ):
        """
        Args:
            model_name: 模型名称（如 "deepseek-chat"）
            provider: 模型提供方（如 "deepseek", "openai"）
            mcp_tools: MCP 工具列表（用于 Stage 2 调研）
            max_concurrency: 最大并发数（默认 3）
        """
        self.model_name = model_name
        self.provider = provider
        self.mcp_tools = mcp_tools
        self.max_concurrency = max_concurrency

        # 1. 使用 ModelFactory 创建模型（带降级）
        config = get_config()
        model_factory = ModelFactory(config)
        model_result = model_factory.create_model_with_fallback(
            model_name=model_name, provider=provider
        )

        if model_result.is_fallback:
            logger.warning(f"主模型不可用，已降级到：{model_result.fallback_provider}")

        self.model = model_result.model

        # 2. 创建 3 个阶段的 sub-agents
        stage1 = Stage1RequirementAnalysisAgent(model=self.model)
        stage2 = Stage2ParallelResearchAgent(
            model=self.model, mcp_tools=mcp_tools, max_concurrency=max_concurrency
        )
        stage3 = Stage3OutlineComposerAgent(model=self.model)

        # 3. 构建 SequentialAgent
        super().__init__(
            name="flat_slide_outline_agent",
            description="扁平化PPT大纲生成Agent（3阶段：需求分析→并行调研→大纲生成）",
            sub_agents=[stage1, stage2, stage3],
        )

    async def _run_async_impl(self, ctx: AgentContext) -> None:
        """
        重写执行逻辑，添加：
        1. 初始化 session state
        2. 错误处理和日志记录
        3. 执行时间统计
        """
        import time

        start_time = time.time()

        logger.info("=" * 60)
        logger.info(
            f"[FlatSlideOutlineAgent] 开始执行，模型：{self.model_name}（{self.provider}）"
        )
        logger.info(f"[FlatSlideOutlineAgent] 用户需求：{ctx.user_message}")
        logger.info("=" * 60)

        # 初始化 session state
        ctx.session.state.setdefault("agent_name", "flat_slide_outline_agent")
        ctx.session.state.setdefault("start_time", start_time)

        try:
            # 调用父类的 Sequential 执行逻辑（会按顺序执行 3 个 stage）
            await super()._run_async_impl(ctx)

            elapsed = time.time() - start_time
            logger.info("=" * 60)
            logger.info(f"[FlatSlideOutlineAgent] 执行完成，耗时：{elapsed:.2f}秒")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"[FlatSlideOutlineAgent] 执行失败：{str(e)}", exc_info=True)
            ctx.add_response(f"抱歉，大纲生成失败：{str(e)}")


# 工厂函数：用于 main_api.py 创建 agent
def create_flat_outline_agent(
    model_name: str, provider: str, mcp_tools: List[Any], max_concurrency: int = 3
) -> FlatSlideOutlineAgent:
    """
    创建扁平化大纲生成 Agent

    Args:
        model_name: 模型名称
        provider: 模型提供方
        mcp_tools: MCP 工具列表
        max_concurrency: 最大并发数

    Returns:
        FlatSlideOutlineAgent 实例
    """
    return FlatSlideOutlineAgent(
        model_name=model_name,
        provider=provider,
        mcp_tools=mcp_tools,
        max_concurrency=max_concurrency,
    )


# 导出的全局实例（供 __init__.py 使用）
flat_outline_agent = None  # 在 main_api.py 中实例化
