"""
资料研究智能体 - LangChain 实现，带工具支持

该智能体为需要外部信息的页面执行研究任务。
集成 LangChain 工具，用于网络搜索和数据检索。
"""

import json
import logging
from typing import Dict, Any, Optional, List

from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from ...models.state import (
    PPTGenerationState,
    update_state_progress,
    get_framework_pages,
    get_research_pages,
)
from ...models.framework import PageDefinition
from ..base_agent import BaseAgent, BaseToolAgent

logger = logging.getLogger(__name__)


# Prompt template for research
RESEARCH_PROMPT = """你是一名专业的研究助理。

{SKILL_INSTRUCTIONS}

你的任务是为PPT页面收集相关的研究资料和背景信息。

页面信息：
- 页码：{page_no}
- 标题：{page_title}
- 内容描述：{core_content}
- 关键词：{keywords}

请为这个页面生成相关的研究资料，包括：
1. 背景知识
2. 关键数据或事实
3. 相关案例或例子
4. 参考来源

输出格式要求：
- 使用要点列表格式
- 保持简洁但信息丰富
- 确保信息的准确性和相关性
- 如果有具体数据，注明来源或说明是"示例数据"

研究资料：
"""


class ResearchAgent(BaseToolAgent):
    """
    资料研究智能体 - 支持 LangChain 原生工具集成

    职责：
    1. 为需要研究的页面收集资料
    2. 生成背景信息和相关数据
    3. 为内容生成提供信息支持
    4. LLM 自主决定是否使用搜索工具

    特性：
    - 支持并行研究（在PagePipeline中）
    - 使用LLM生成研究资料
    - 集成搜索工具（web_search, fetch_url, weixin_search）
    - ReAct Agent 自主决定工具调用

    使用方式：
    ```python
    # 默认配置（带搜索工具）
    agent = ResearchAgent()

    # 自定义配置（包含 SKILL 类别用于研究工作流程）
    agent = ResearchAgent(
        model=custom_model,
        temperature=0.3,
        tool_categories=["SEARCH", "SKILL"]  # 包含研究技能
    )
    ```

    可用工具（通过 SKILL 类别）：
    - research_workflow: 结构化研究工作流程
    """

    def __init__(
        self,
        model: Optional[ChatOpenAI] = None,
        temperature: float = 0.3,
        agent_name: str = "ResearchAgent",
        enable_memory: bool = False,
        use_tools: bool = True,
        use_skills: bool = True,  # 是否使用研究相关的技能（Python + MD）
        tool_categories: Optional[List[str]] = None,
    ):
        """
        初始化研究智能体

        Args:
            model: LangChain LLM实例
            temperature: LLM温度参数
            agent_name: Agent名称
            enable_memory: 是否启用记忆功能
            use_skills: 是否使用研究相关的技能（包含 Python + MD Skills）
            tool_categories: 兼容旧调用参数（可选）

        注意：
        - 现在所有工具（Python Skills + MD Skills）都统一在 NativeToolRegistry 中管理
        - 使用 tool_names 精确指定需要的工具
        """
        # 构建工具名称列表
        tool_names = []

        if tool_categories is not None:
            use_skills = "SKILL" in tool_categories
            use_tools = use_skills or ("SEARCH" in tool_categories)

        if use_tools:
            # 添加搜索工具（Domain Tools）
            tool_names.extend(["web_search", "fetch_url", "weixin_search"])

        # 如果启用技能，添加研究相关的 Skills
        if use_tools and use_skills:
            tool_names.extend(
                [
                    # Python Skills
                    "research_workflow",
                    # MD Skills (Guides)
                    "research_guide",
                ]
            )

        # 调用 BaseToolAgent 的初始化
        super().__init__(
            model=model,
            temperature=temperature,
            tool_names=tool_names,  # 使用 tool_names
            agent_name=agent_name,
            enable_memory=enable_memory,
        )

        # 创建研究链（降级方案）
        self.chain = self._create_chain()

    def _create_chain(self) -> Runnable:
        """创建 LLM 研究链（用于工具失败时降级）"""
        enhanced_prompt = RESEARCH_PROMPT.replace("{SKILL_INSTRUCTIONS}", "")
        enhanced_prompt = enhanced_prompt.replace("\n\n你的任务", "\n你的任务")
        prompt = ChatPromptTemplate.from_template(enhanced_prompt)
        return prompt | self.model

    async def run_node(self, state: PPTGenerationState) -> PPTGenerationState:
        """兼容工作流节点调用接口"""
        return await self.execute_task(state)

    async def execute_task(self, state: PPTGenerationState) -> PPTGenerationState:
        """
        执行研究任务

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        # 获取框架
        framework = state.get("ppt_framework", {})
        pages = framework.get("ppt_framework", [])

        if not pages:
            raise ValueError("Missing pages in ppt_framework")

        # 获取需要研究的页码
        research_indices = framework.get("research_page_indices", [])

        if not research_indices:
            logger.info(f"[{self.agent_name}] No pages need research")
            research_results = []
        else:
            # 研究所有需要研究的页面
            research_results = await self.research_all_pages(pages, research_indices, state)

            # Cache research results (if memory enabled)
            if self.has_memory:
                await self.remember(
                    "research_results",
                    {"count": len(research_results), "results": research_results},
                    importance=0.7,
                )

        # Pass results through LangGraph State
        state["research_results"] = research_results or []

        # 研究阶段的进度是30% -> 50%
        update_state_progress(state, "research", 50)

        logger.info(
            f"[{self.agent_name}] Task completed: {len(research_results) if research_results else 0} pages researched"
        )
        return state

    async def research_page(
        self, page: Dict[str, Any], state: Optional[PPTGenerationState] = None
    ) -> Dict[str, Any]:
        """
        研究单个页面（LLM 自主判断是否使用工具）

        Args:
            page: 页面定义字典
            state: 可选的状态（用于记忆上下文）

        Returns:
            研究结果字典
        """
        page_no = page.get("page_no", 1)
        title = page.get("title", "")
        core_content = page.get("core_content", "")
        keywords = page.get("keywords", [])

        logger.info(f"[{self.agent_name}] Researching page {page_no}: {title}")

        # Check cache (if memory enabled)
        if self.has_memory:
            cache_key = f"research_page_{page_no}_{hash(title + core_content)}"
            cached = await self.recall(cache_key)
            if cached:
                logger.info(f"[{self.agent_name}] Using cached research for page {page_no}")
                return cached

        # 使用工具研究或直接 LLM 研究
        if self.has_tools():
            research_content = await self._research_with_agent(title, core_content, keywords)
        else:
            research_content = await self._research_with_llm(title, core_content, keywords)

        result = {
            "page_no": page_no,
            "title": title,
            "research_content": research_content,
            "keywords": keywords,
            "status": "completed",
            "has_tools": self.has_tools(),
        }

        # Cache result (if memory enabled)
        if self.has_memory:
            cache_key = f"research_page_{page_no}_{hash(title + core_content)}"
            await self.remember(cache_key, result, importance=0.7)

        return result

    async def _research_with_agent(self, title: str, core_content: str, keywords: List[str]) -> str:
        """
        使用 ReAct Agent 进行研究（LLM 自主判断是否使用工具）

        Args:
            title: 页面标题
            core_content: 核心内容
            keywords: 关键词列表

        Returns:
            研究内容字符串
        """
        search_query = f"{title} {core_content} {' '.join(keywords[:3])}"

        logger.info(f"[{self.agent_name}] Researching with agent: {search_query}")

        # 构建研究查询
        query = f"""
请为以下PPT页面内容生成研究资料：

页面信息：
- 标题：{title}
- 核心内容：{core_content}
- 关键词：{', '.join(keywords) if keywords else '无'}

请提供：
1. 背景知识
2. 关键数据或事实
3. 相关案例或例子
4. 参考来源

如果需要最新的信息，可以使用搜索工具。如果是通用知识，可以直接回答。
"""

        try:
            # 使用 BaseToolAgent 提供的 execute_with_tools 方法
            # ReAct Agent 会自主决定是否调用搜索工具
            result = await self.execute_with_tools(query)
            return result

        except Exception as e:
            logger.error(f"[{self.agent_name}] Agent research failed: {e}", exc_info=True)
            # 降级到 LLM 模式
            logger.info(f"[{self.agent_name}] Falling back to LLM-only mode")
            return await self._research_with_llm(title, core_content, keywords)

    async def _research_with_llm(self, title: str, core_content: str, keywords: List[str]) -> str:
        """使用LLM生成研究资料（降级方案）"""
        try:
            result = await self.chain.ainvoke(
                {
                    "page_no": 1,
                    "page_title": title,
                    "core_content": core_content,
                    "keywords": ", ".join(keywords) if keywords else "无",
                }
            )
            return result.content
        except Exception as e:
            logger.warning(f"[{self.agent_name}] LLM research failed: {e}")
            return f"关于「{title}」的研究资料\n\n- 背景知识：[待补充]\n- 关键数据：[待补充]\n- 相关案例：[待补充]"

    def _fallback_research(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """降级研究：返回占位内容"""
        page_no = page.get("page_no", 1)
        title = page.get("title", "")

        return {
            "page_no": page_no,
            "title": title,
            "research_content": f"关于「{title}」的研究资料\n\n- 背景知识：[待补充]\n- 关键数据：[待补充]\n- 相关案例：[待补充]",
            "keywords": page.get("keywords", []),
            "status": "fallback",
        }

    async def research_all_pages(
        self,
        pages: List[Dict[str, Any]],
        research_indices: List[int],
        state: Optional[PPTGenerationState] = None,
    ) -> List[Dict[str, Any]]:
        """
        研究所有需要研究的页面

        Args:
            pages: 所有页面列表
            research_indices: 需要研究的页码列表
            state: 可选的状态

        Returns:
            研究结果列表
        """
        logger.info(f"[{self.agent_name}] Researching {len(research_indices)} pages")

        # 筛选需要研究的页面
        pages_to_research = [p for p in pages if p.get("page_no") in research_indices]

        # 并行研究所有页面
        import asyncio

        tasks = [self.research_page(page, state) for page in pages_to_research]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        research_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"[{self.agent_name}] Page {i+1} research failed: {result}")
                # 添加降级结果
                research_results.append(self._fallback_research(pages_to_research[i]))
            else:
                research_results.append(result)

        logger.info(f"[{self.agent_name}] Completed {len(research_results)} page researches")
        return research_results

    def get_fallback_result(self, state: PPTGenerationState) -> Optional[PPTGenerationState]:
        """降级策略"""
        framework = state.get("ppt_framework", {})
        pages = framework.get("ppt_framework", [])

        # 为所有页面返回占位研究
        research_results = [
            self._fallback_research(page) for page in pages if page.get("is_need_research", False)
        ]

        state["research_results"] = research_results
        update_state_progress(state, "research", 50)

        return state


# 工厂函数


def create_research_agent(
    model: Optional[ChatOpenAI] = None,
    temperature: float = 0.3,
    tool_categories: Optional[List[str]] = None,
    enable_memory: bool = True,
    use_tools: bool = False,
) -> ResearchAgent:
    """
    创建研究智能体

    Args:
        model: LangChain LLM 实例
        temperature: LLM 温度参数
        tool_categories: 工具类别列表（默认 ["SEARCH"]）
        enable_memory: 是否启用记忆功能

    Returns:
        ResearchAgent 实例
    """
    return ResearchAgent(
        model=model,
        temperature=temperature,
        use_tools=use_tools,
        use_skills=use_tools,
        tool_categories=tool_categories,
        enable_memory=enable_memory,
    )


# 便捷函数


async def research_page(page: Dict[str, Any], model: Optional[ChatOpenAI] = None) -> Dict[str, Any]:
    """
    直接研究页面（便捷函数）

    Args:
        page: 页面定义
        model: 可选的 LLM 模型

    Returns:
        研究结果字典
    """
    agent = create_research_agent(model)
    return await agent.research_page(page)


if __name__ == "__main__":
    import asyncio

    async def test():
        # 测试研究功能
        test_page = {
            "page_no": 1,
            "title": "人工智能发展历程",
            "core_content": "介绍人工智能从诞生到现在的发展",
            "keywords": ["AI", "人工智能", "机器学习"],
        }

        # 测试 LLM-only 模式
        print("=== Testing LLM-only mode ===")
        agent_llm = create_research_agent(use_search_tools=False, enable_memory=False)
        result_llm = await agent_llm.research_page(test_page)
        print(f"Result:\n{result_llm['research_content'][:200]}...")

    asyncio.run(test())
