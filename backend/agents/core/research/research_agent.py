"""
Research Agent

资料研究智能体（优化版），负责精准研究和整理外部资料。

改进：
1. 精准匹配：仅研究框架中标注 is_need_research=true 的页面
2. 权威来源：标注资料来源
3. 结构化整理：按页码组织研究结果
4. 可开关控制：根据 need_research 字段决定是否执行
"""

import json
import logging
import os
import sys
from typing import AsyncGenerator, Optional, Dict, Any, List

from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents import ParallelAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types
from google.adk.events.event import Event
from google.adk.agents.parallel_agent import (
    _create_branch_ctx_for_sub_agent,
    _merge_agent_run,
)

# 导入基础设施
from infrastructure.config.common_config import get_config

# 导入新的 MCP 工具
from agents.tools.mcp import web_search, vector_search

# 导入PromptManager
from prompts import PromptManager

logger = logging.getLogger(__name__)

# 使用PromptManager获取研究提示词模板
RESEARCH_TOPIC_AGENT_PROMPT = PromptManager.get_research_topic_prompt()

# 配置日志
logging.basicConfig(level=logging.INFO)

# 加载工具和模型配置
research_model = "deepseek-chat"

def research_agent_before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """研究Agent的模型前回调"""
    agent_name = callback_context.agent_name
    history_length = len(llm_request.contents)
    logger.info(f"{agent_name} research agent callback, history: {history_length}")
    return None

class OptimizedResearchAgent(ParallelAgent):
    """
    优化的资料研究智能体

    改进：
    1. 精准匹配：仅研究框架中标注 is_need_research=true 的页面
    2. 权威来源：标注资料来源
    3. 结构化整理：按页码组织研究结果
    4. 可开关控制：根据 need_research 字段决定是否执行
    5. 支持单页研究：用于页面级流水线并行
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 存储单页研究结果供流水线使用
        self._single_page_results: Dict[int, Dict[str, Any]] = {}

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        执行研究任务

        Args:
            ctx: 调用上下文
        """
        try:
            # 1. 获取框架
            framework_dict = ctx.session.state.get("ppt_framework")
            if not framework_dict:
                logger.warning("No ppt_framework found, skipping research")
                ctx.session.state["research_results"] = []
                yield Event(
                    author=self.name,
                    content=types.Content(
                        parts=[types.Part(text="无需研究资料")]
                    ),
                )
                return

            # 2. 提取需要研究的页面
            research_page_indices = framework_dict.get("research_page_indices", [])
            pages = framework_dict.get("ppt_framework", [])

            if not research_page_indices:
                logger.info("No pages marked for research")
                ctx.session.state["research_results"] = []
                yield Event(
                    author=self.name,
                    content=types.Content(
                        parts=[types.Part(text="框架中无需研究资料的页面")]
                    ),
                )
                return

            research_pages = [p for p in pages if p.get("is_need_research", False)]

            if not research_pages:
                logger.info("No research pages found after filtering")
                ctx.session.state["research_results"] = []
                yield Event(
                    author=self.name,
                    content=types.Content(
                        parts=[types.Part(text="没有需要研究资料的页面")]
                    ),
                )
                return

            logger.info(f"Found {len(research_pages)} pages requiring research")

            # 3. 为每个研究页面创建子智能体
            dynamic_sub_agents = []
            for page in research_pages:
                page_no = page.get("page_no", 1)
                page_title = page.get("title", "Untitled")
                core_content = page.get("core_content", "")
                keywords = page.get("keywords", [])

                # 创建定制化的指令
                custom_instruction = self._create_research_instruction(
                    page_no, page_title, core_content, keywords
                )

                new_research_agent = LlmAgent(
                    model=research_model,
                    name=f"research_page_{page_no}",
                    description=f"Research agent for page {page_no}",
                    instruction=custom_instruction,
                    tools=[web_search, vector_search],  # 使用新的 MCP 工具
                    output_key=f"research_page_{page_no}",
                    before_model_callback=research_agent_before_model_callback,
                )
                new_research_agent.parent_agent = self
                dynamic_sub_agents.append(new_research_agent)

            logger.info(f"Created {len(dynamic_sub_agents)} research sub-agents")

            # 4. 并行运行所有动态创建的Agent
            agent_runs = [
                sub_agent.run_async(_create_branch_ctx_for_sub_agent(self, sub_agent, ctx))
                for sub_agent in dynamic_sub_agents
            ]

            # 5. 合并并产生事件流
            async for event in _merge_agent_run(agent_runs):
                yield event

            # 6. 整理研究结果
            research_results = self._extract_research_results(ctx, research_pages)
            ctx.session.state["research_results"] = research_results

            logger.info(f"Research completed: {len(research_results)} pages")

            # 7. 产生完成事件
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[types.Part(
                        text=f"资料研究完成：\n"
                        f"- 研究页面数: {len(research_results)}\n"
                        f"- 研究结果已整理"
                    )]
                ),
            )

        except Exception as e:
            logger.error(f"ResearchAgent failed: {e}", exc_info=True)
            ctx.session.state["research_results"] = []
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[types.Part(text=f"研究失败: {str(e)}")]
                ),
            )

    def _create_research_instruction(
        self, page_no: int, page_title: str, core_content: str, keywords: List[str]
    ) -> str:
        """
        创建针对特定页面的研究指令

        Args:
            page_no: 页码
            page_title: 页面标题
            core_content: 核心内容
            keywords: 关键词

        Returns:
            研究指令
        """
        base_prompt = RESEARCH_TOPIC_AGENT_PROMPT

        additional_info = f"""

你需要研究的具体页面信息：
- 页码: {page_no}
- 页面标题: {page_title}
- 核心内容: {core_content}
- 关键词: {', '.join(keywords) if keywords else '无'}

请按照以下格式输出研究结果（JSON格式）：
{{
    "page_no": {page_no},
    "page_title": "{page_title}",
    "research_type": "数据类/案例类/观点类",
    "content": "你的研究结果...",
    "source": "资料来源（如：艾瑞咨询、国家统计局、行业报告等）",
    "is_visualizable": true/false,
    "data_points": ["关键数据点1", "关键数据点2"],
    "key_insights": ["关键洞察1", "关键洞察2"]
}}
"""

        return base_prompt + additional_info

    def _extract_research_results(
        self, ctx: InvocationContext, research_pages: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        提取并整理研究结果

        Args:
            ctx: 调用上下文
            research_pages: 需要研究的页面列表

        Returns:
            整理后的研究结果列表
        """
        research_results = []

        for page in research_pages:
            page_no = page.get("page_no", 1)
            output_key = f"research_page_{page_no}"
            output = ctx.session.state.get(output_key, "")

            if output:
                # 尝试解析JSON输出
                try:
                    # 清理可能的markdown标记
                    if isinstance(output, str):
                        if output.strip().startswith("```json"):
                            output = output.strip()[7:-3]
                        elif output.strip().startswith("```"):
                            output = output.strip()[3:-3]

                    parsed = json.loads(output)
                    research_results.append(parsed)
                except json.JSONDecodeError:
                    # 如果解析失败，创建基本结构
                    research_results.append({
                        "page_no": page_no,
                        "page_title": page.get("title", ""),
                        "research_type": "未知",
                        "content": str(output),
                        "source": "未知来源",
                        "is_visualizable": False,
                        "data_points": [],
                        "key_insights": []
                    })
            else:
                # 没有输出，创建占位符
                research_results.append({
                    "page_no": page_no,
                    "page_title": page.get("title", ""),
                    "research_type": "未完成",
                    "content": f"页面{page_no}的研究未完成",
                    "source": "",
                    "is_visualizable": False,
                    "data_points": [],
                    "key_insights": []
                })

        return research_results

    async def research_single_page(
        self,
        page_no: int,
        page_title: str,
        keywords: List[str],
        core_content: str
    ) -> Dict[str, Any]:
        """
        研究单个页面（用于流水线并行）

        Args:
            page_no: 页码
            page_title: 页面标题
            keywords: 关键词列表
            core_content: 核心内容

        Returns:
            研究结果字典
        """
        try:
            # 构建研究提示词
            prompt = self._create_research_instruction(
                page_no=page_no,
                page_title=page_title,
                core_content=core_content,
                keywords=keywords
            )

            # 创建临时子智能体进行研究
            from google.adk.agents.llm_agent import LlmAgent
            from google.adk.agents.invocation_context import InvocationContext

            # 创建简化的上下文
            temp_ctx = self._create_temp_context()

            # 创建临时研究子智能体
            temp_agent = LlmAgent(
                model=research_model,
                name=f"research_page_{page_no}",
                description=f"Research agent for page {page_no}",
                instruction=prompt,
                tools=[web_search, vector_search],  # 使用新的 MCP 工具
                output_key=f"research_page_{page_no}",
                before_model_callback=research_agent_before_model_callback,
            )

            # 执行研究
            await temp_agent.run_async(temp_ctx)

            # 提取结果
            output = temp_ctx.session.state.get(f"research_page_{page_no}", "")

            # 解析结果
            result = self._parse_single_page_result(output, page_no, page_title)

            # 缓存结果
            self._single_page_results[page_no] = result

            logger.info(f"Single page research completed: page {page_no}")
            return result

        except Exception as e:
            logger.error(f"Single page research failed for page {page_no}: {e}")
            # 返回错误结果
            return {
                "page_no": page_no,
                "page_title": page_title,
                "research_type": "失败",
                "content": f"研究失败: {str(e)}",
                "source": "",
                "data_points": [],
                "is_visualizable": False,
                "error": str(e)
            }

    def _create_temp_context(self) -> InvocationContext:
        """创建临时上下文用于单页研究"""
        # 简化实现：返回一个基本上下文
        # 在实际使用中，可能需要从父上下文复制必要信息
        from google.adk.agents.invocation_context import InvocationContext
        from google.adk.core.state import State

        # 创建临时状态
        temp_state = State()
        temp_state._data = {}

        # 创建基本上下文
        temp_ctx = InvocationContext(
            invocation_id=f"temp_{id(self)}",
            user_content=None,
            session=None,
            agent=None,
            state=temp_state
        )

        return temp_ctx

    def _parse_single_page_result(
        self,
        output: Any,
        page_no: int,
        page_title: str
    ) -> Dict[str, Any]:
        """
        解析单页研究结果

        Args:
            output: LLM输出
            page_no: 页码
            page_title: 页面标题

        Returns:
            研究结果字典
        """
        # 尝试解析JSON
        if isinstance(output, str):
            # 清理可能的markdown标记
            if output.strip().startswith("```json"):
                output = output.strip()[7:-3]
            elif output.strip().startswith("```"):
                output = output.strip()[3:-3]

            try:
                parsed = json.loads(output)
                return parsed
            except json.JSONDecodeError:
                pass

        # 创建基本结构
        return {
            "page_no": page_no,
            "page_title": page_title,
            "research_type": "通用类",
            "content": str(output) if output else "无研究结果",
            "source": "AI生成",
            "data_points": [],
            "is_visualizable": False
        }

    def get_single_page_result(self, page_no: int) -> Optional[Dict[str, Any]]:
        """
        获取已缓存的单页研究结果

        Args:
            page_no: 页码

        Returns:
            研究结果字典，如果不存在则返回None
        """
        return self._single_page_results.get(page_no)

    def clear_single_page_cache(self) -> None:
        """清空单页研究结果缓存"""
        self._single_page_results.clear()

# 创建全局实例
optimized_research_agent = OptimizedResearchAgent(
    name="OptimizedResearchAgent",
    description="优化的资料研究智能体，仅研究需要的页面并整理结果"
)

if __name__ == "__main__":
    # 测试代码
    async def test_agent():
        import asyncio

        # 模拟框架数据
        framework = {
            "total_page": 10,
            "ppt_framework": [
                {"page_no": 1, "title": "封面", "is_need_research": False},
                {"page_no": 4, "title": "行业数据", "is_need_research": True, "keywords": ["电商", "618"]},
                {"page_no": 7, "title": "市场分析", "is_need_research": True, "keywords": ["市场", "趋势"]},
            ],
            "research_page_indices": [4, 7]
        }

        print(f"Testing OptimizedResearchAgent")
        print("=" * 60)
        print(f"Research pages: {framework['research_page_indices']}")

        agent = optimized_research_agent
        print(f"Agent created: {agent.name}")

    asyncio.run(test_agent())
