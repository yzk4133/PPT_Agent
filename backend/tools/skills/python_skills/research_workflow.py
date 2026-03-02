"""
研究工作流程 Skill

为 ResearchAgent 提供系统化的研究工作流程
"""

import json
import logging
from typing import Dict, Any, List
from backend.tools.skills.base_skill import BaseSkill


logger = logging.getLogger(__name__)


class ResearchWorkflowSkill(BaseSkill):
    """
    研究工作流程 Skill

    工作流程：关键词提取 → 文献搜索 → 信息过滤 → 综合分析
    """

    name = "research_workflow"
    description = "系统化的研究工作流程：关键词提取 → 并行搜索 → 信息过滤 → 综合分析"
    version = "1.0.0"
    category = "research"

    def __init__(self, llm=None, search_tool=None):
        """
        初始化研究工作流程

        Args:
            llm: LLM 实例
            search_tool: 搜索工具实例（web_search）
        """
        super().__init__(llm)
        self.search_tool = search_tool

    async def execute(
        self, topic: str, num_sources: int = 5, depth: str = "medium", keywords: List[str] = None
    ) -> str:
        """
        执行研究工作流程

        Args:
            topic: 研究主题
            num_sources: 需要的来源数量（默认 5）
            depth: 研究深度 (shallow/medium/deep)
            keywords: 可选，预设关键词

        Returns:
            str: 综合摘要
        """
        try:
            logger.info(f"[ResearchSkill] 开始研究: {topic}")

            # 步骤 1: 提取关键词
            if keywords is None:
                keywords = await self._extract_keywords(topic)
                logger.info(f"[ResearchSkill] 提取关键词: {keywords}")
            else:
                logger.info(f"[ResearchSkill] 使用预设关键词: {keywords}")

            # 步骤 2: 并行搜索多个来源
            sources = await self._search_sources(keywords, num_sources)
            logger.info(f"[ResearchSkill] 搜索到 {len(sources)} 个来源")

            if not sources:
                return f"错误：未找到相关来源\n主题：{topic}\n关键词：{', '.join(keywords)}"

            # 步骤 3: 提取完整内容（如果需要）
            enriched_sources = await self._fetch_content(sources[:num_sources])

            # 步骤 4: 过滤和排序
            filtered_sources = await self._filter_sources(enriched_sources, topic)
            logger.info(f"[ResearchSkill] 过滤后保留 {len(filtered_sources)} 个来源")

            # 步骤 5: 综合信息
            synthesis = await self._synthesize_info(filtered_sources, topic, depth)
            logger.info(f"[ResearchSkill] 综合完成，深度: {depth}")

            # 直接返回综合摘要
            return synthesis

        except Exception as e:
            logger.error(f"[ResearchSkill] 执行失败: {e}", exc_info=True)
            return f"错误：{str(e)}"

    async def _extract_keywords(self, topic: str) -> List[str]:
        """
        步骤 1.1: 从主题提取关键词

        Args:
            topic: 研究主题

        Returns:
            关键词列表
        """
        if not self.llm:
            # 如果没有 LLM，简单分词
            return topic.split()

        prompt = f"""
        分析以下研究主题，提取 5-8 个关键搜索词。

        主题：{topic}

        要求：
        1. 提取核心概念和相关术语
        2. 包括同义词和相关表达
        3. 以 JSON 数组格式返回

        返回格式：["关键词1", "关键词2", ...]
        """

        try:
            result = await self.llm.ainvoke(prompt)
            # 清理 JSON 字符串
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
            return json.loads(result)
        except Exception as e:
            logger.warning(f"[ResearchSkill] 关键词提取失败，使用默认: {e}")
            return topic.split()

    async def _search_sources(self, keywords: List[str], num_sources: int) -> List[Dict[str, Any]]:
        """
        步骤 2: 搜索多个来源

        Args:
            keywords: 关键词列表
            num_sources: 需要的来源数量

        Returns:
            来源列表
        """
        if not self.search_tool:
            logger.warning("[ResearchSkill] 未配置搜索工具")
            return []

        sources = []
        num_per_keyword = max(1, num_sources // len(keywords))

        for keyword in keywords[:3]:  # 限制前 3 个关键词
            try:
                result = await self.search_tool.execute(query=keyword, num_results=num_per_keyword)

                if result.get("success"):
                    sources.extend(result.get("data", {}).get("results", []))

            except Exception as e:
                logger.warning(f"[ResearchSkill] 搜索 '{keyword}' 失败: {e}")

        # 去重
        seen_urls = set()
        unique_sources = []
        for source in sources:
            if source.get("url") not in seen_urls:
                seen_urls.add(source.get("url"))
                unique_sources.append(source)

        return unique_sources

    async def _fetch_content(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        步骤 3: 获取完整内容（可选）

        Args:
            sources: 来源列表

        Returns:
            带内容的来源列表
        """
        # TODO: 可以调用 fetch_url 工具获取完整内容
        # 目前先返回原始来源
        return sources

    async def _filter_sources(
        self, sources: List[Dict[str, Any]], topic: str
    ) -> List[Dict[str, Any]]:
        """
        步骤 4: 过滤和排序来源

        Args:
            sources: 来源列表
            topic: 研究主题

        Returns:
            过滤后的来源列表
        """
        if not self.llm:
            # 如果没有 LLM，返回原始列表
            return sources

        # 准备来源摘要
        sources_summary = []
        for i, source in enumerate(sources):
            sources_summary.append(
                {"index": i, "title": source.get("title", ""), "snippet": source.get("snippet", "")}
            )

        prompt = f"""
        评估以下搜索结果与研究主题的相关性，并选择最相关的 3-5 个。

        研究主题：{topic}

        搜索结果：
        {json.dumps(sources_summary, ensure_ascii=False, indent=2)}

        任务：
        1. 评估每个结果与主题的相关性（高/中/低）
        2. 选择最相关的 3-5 个结果
        3. 返回选中结果的索引（JSON 数组）

        返回格式：[0, 2, 4, ...]
        """

        try:
            result = await self.llm.ainvoke(prompt)
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]

            top_indices = json.loads(result)

            # 返回选中的来源
            filtered = []
            for i in top_indices:
                if 0 <= i < len(sources):
                    filtered.append(sources[i])

            return filtered if filtered else sources[:5]

        except Exception as e:
            logger.warning(f"[ResearchSkill] 过滤失败，返回原始列表: {e}")
            return sources[:5]

    async def _synthesize_info(self, sources: List[Dict[str, Any]], topic: str, depth: str) -> str:
        """
        步骤 5: 综合信息

        Args:
            sources: 来源列表
            topic: 研究主题
            depth: 综合深度

        Returns:
            综合摘要
        """
        if not self.llm:
            # 简单拼接
            return "\n".join([f"- {s.get('title', '')}: {s.get('snippet', '')}" for s in sources])

        # 根据深度调整指令
        depth_instructions = {
            "shallow": "简要总结（150字以内），突出核心要点",
            "medium": "中等详细度总结（300-500字），包含主要信息和数据",
            "deep": "详细综合分析（500字以上），深入分析多个来源，识别共性、差异和趋势",
        }

        instruction = depth_instructions.get(depth, depth_instructions["medium"])

        # 准备来源信息
        sources_text = "\n\n".join(
            [
                f"【来源{i+1}】\n标题: {s.get('title', '')}\n内容: {s.get('snippet', '')}"
                for i, s in enumerate(sources)
            ]
        )

        prompt = f"""
        基于以下研究资料，{instruction}：

        研究主题：{topic}

        研究资料：
        {sources_text}

        要求：
        1. 综合多个来源的信息
        2. 识别关键主题和趋势
        3. 如有冲突，指出不同观点
        4. 保持客观和中立
        5. 使用清晰的结构（分段、分点）
        """

        try:
            return await self.llm.ainvoke(prompt)
        except Exception as e:
            logger.error(f"[ResearchSkill] 综合失败: {e}")
            return "综合失败"


class ResearchKeywordSkill(BaseSkill):
    """
    关键词提取 Skill（研究工作流的子技能）
    """

    name = "research_keywords"
    description = "从研究主题中提取关键词"
    version = "1.0.0"
    category = "research"

    async def execute(self, topic: str, num_keywords: int = 8) -> Dict[str, Any]:
        """提取关键词"""
        # 简化实现
        keywords = topic.split()
        return {"success": True, "data": {"topic": topic, "keywords": keywords[:num_keywords]}}


class ResearchSynthesisSkill(BaseSkill):
    """
    信息综合 Skill（研究工作流的子技能）
    """

    name = "research_synthesis"
    description = "综合多个来源的信息"
    version = "1.0.0"
    category = "research"

    async def execute(
        self, sources: List[Dict[str, Any]], topic: str, depth: str = "medium"
    ) -> str:
        """综合信息"""
        synthesis = "\n".join([f"- {s.get('title', '')}: {s.get('snippet', '')}" for s in sources])

        return synthesis


# ============================================================================
# LangChain Tool 包装器
# ============================================================================

from langchain_core.tools import StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field


class ResearchWorkflowInput(BaseModel):
    """研究工作流程输入参数"""

    topic: str = Field(..., description="研究主题")
    num_sources: int = Field(default=5, description="需要的来源数量")
    depth: str = Field(default="medium", description="研究深度 (shallow/medium/deep)")
    keywords: List[str] = Field(default=None, description="可选，预设关键词")


# 创建 LangChain Tool
research_workflow_tool = StructuredTool.from_function(
    func=ResearchWorkflowSkill().execute,
    name="research_workflow",
    description="系统化的研究工作流程：关键词提取 → 并行搜索 → 信息过滤 → 综合分析",
    args_schema=ResearchWorkflowInput,
)
