"""
框架设计智能体 - LangChain 实现

该智能体根据结构化需求设计 PPT 框架（结构）。
使用 LangChain 模式，结合 LLM 链和 JSON 输出解析。
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from ...models.state import PPTGenerationState, update_state_progress
from ...models.framework import PPTFramework
from ..base_agent import BaseAgent, BaseToolAgent

logger = logging.getLogger(__name__)


# Prompt template for framework design
FRAMEWORK_DESIGNER_PROMPT = """你是一名专业的PPT结构设计专家。

{SKILL_INSTRUCTIONS}

你的任务是根据结构化需求，设计PPT的框架结构，包括每一页的标题、类型和内容描述。

需求信息：
- 主题：{ppt_topic}
- 页数：{page_num}
- 模板类型：{template_type}
- 使用场景：{scene}
- 核心模块：{core_modules}
- 是否需要研究：{need_research}
- 语言：{language}

请设计一个包含{page_num}页的PPT框架，按照以下JSON格式输出（不要使用markdown包裹，直接输出JSON）：
{{
    "total_page": 页数,
    "ppt_framework": [
        {{
            "page_no": 1,
            "title": "页面标题",
            "page_type": "cover|directory|content|chart|image|summary|thanks",
            "core_content": "核心内容描述",
            "is_need_chart": true/false,
            "is_need_research": true/false,
            "is_need_image": true/false,
            "content_type": "text_only|text_with_image|text_with_chart|text_with_both|image_only|chart_only",
            "keywords": ["关键词1", "关键词2"],
            "estimated_word_count": 预估字数,
            "layout_suggestion": "布局建议"
        }}
    ],
    "has_research_pages": true/false,
    "research_page_indices": [需要研究的页码列表],
    "chart_page_indices": [需要图表的页码列表],
    "image_page_indices": [需要配图的页码列表],
    "framework_type": "linear"
}}

设计原则：
1. 第1页必须是封面（cover）
2. 第2页通常是目录（directory）
3. 最后一页通常是总结或致谢（summary或thanks）
4. 根据核心模块合理分配内容页
5. 如果需要研究，为相关页面标记is_need_research=true并提供keywords
6. 图表页（chart）应该均匀分布
7. 确保总页数等于需求中的页数
8. page_no必须从1开始连续编号
"""


class FrameworkDesignerAgent(BaseToolAgent):
    """
    框架设计智能体 - 使用BaseToolAgent重构版本

    职责：
    1. 根据结构化需求设计PPT框架
    2. 生成每一页的标题、类型和内容描述
    3. 确保框架逻辑合理、结构清晰
    4. 缓存框架设计结果以避免重复生成

    特性：
    - 使用LangChain的Runnable链
    - 内置JSON输出解析
    - 降级策略：如果LLM解析失败，使用模板框架
    - 集成记忆系统：缓存框架设计，共享结构数据
    - 使用 LangChain Tools（ReAct Agent）让 LLM 自主选择工具

    使用工具（通过 SKILL 类别）：
    - topic_decomposition: 分解主题为子主题
    - section_planning: 规划章节结构
    """

    def __init__(
        self,
        model: Optional[ChatOpenAI] = None,
        temperature: float = 0.0,
        agent_name: str = "FrameworkDesignerAgent",
        enable_memory: bool = True,
        use_tools: bool = True,  # 是否使用 LangChain Tools (Python + MD Skills)
    ):
        """
        初始化框架设计智能体

        Args:
            model: LangChain LLM实例
            temperature: LLM温度参数
            agent_name: Agent名称
            enable_memory: 是否启用记忆功能
            use_tools: 是否使用 LangChain Tools（包含 Python Skills + MD Skills）

        注意：
        - 现在所有工具（Python Skills + MD Skills）都统一在 NativeToolRegistry 中管理
        - 使用 tool_names 精确指定需要的工具
        """
        # 构建工具名称列表（只加载框架设计相关的工具）
        tool_names = (
            [
                # Python Skills
                "framework_design",
                "topic_decomposition",
                "section_planning",
                # MD Skills (Guides)
                "framework_design_guide",
            ]
            if use_tools
            else []
        )

        # Call parent constructor (BaseToolAgent)
        super().__init__(
            model=model,
            temperature=temperature,
            tool_names=tool_names,  # 使用 tool_names 替代 tool_categories
            agent_name=agent_name,
            enable_memory=enable_memory,
        )

        # Create fallback chain
        self.chain = self._create_chain()

    def _create_chain(self) -> Runnable:
        """创建设计链（降级方案，不使用工具时）"""
        # Note: MD Skills are deprecated, removing SKILL_INSTRUCTIONS
        enhanced_prompt = FRAMEWORK_DESIGNER_PROMPT.replace("{SKILL_INSTRUCTIONS}", "")
        enhanced_prompt = enhanced_prompt.replace("\n\n请设计一个", "\n请设计一个")

        prompt = ChatPromptTemplate.from_template(enhanced_prompt)
        parser = JsonOutputParser()
        return prompt | self.model | parser

    async def run_node(self, state: PPTGenerationState) -> PPTGenerationState:
        """兼容工作流节点调用接口"""
        return await self.execute_task(state)

    async def execute_task(self, state: PPTGenerationState) -> PPTGenerationState:
        """
        执行框架设计任务

        This method now applies user preferences for personalization:
        1. Retrieves user preferences (template_type, prefer_more_charts, etc.)
        2. Applies template_type to influence framework structure
        3. Applies chart/image preferences if available
        4. Caches and shares the framework

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        # Initialize memory if enabled
        if self.enable_memory:
            self._get_memory(state)

        requirement = state.get("structured_requirements", {})
        topic = requirement.get("ppt_topic", "Unknown")
        page_num = requirement.get("page_num", 10)

        logger.info(f"[{self.agent_name}] Designing framework for: {topic}, pages: {page_num}")

        # Get user preferences if memory enabled
        user_preferences = {}
        if self.enable_memory:
            user_preferences = await self.get_user_preferences()
            logger.debug(f"[{self.agent_name}] Retrieved user preferences")

        # Apply user preferences to requirement
        # Note: template_type and page_num should already be applied by RequirementParserAgent
        # But we can apply additional preferences here
        template_type = requirement.get("template_type", "business_template")

        # Enhance requirement with user preferences for framework design
        design_context = {
            "ppt_topic": topic,
            "page_num": page_num,
            "template_type": template_type,
            "scene": requirement.get("scene", "business_report"),
            "core_modules": requirement.get("core_modules", []),
            "need_research": requirement.get("need_research", False),
            "language": requirement.get("language", "ZH-CN"),
        }

        # Add user preference context to the prompt
        if user_preferences:
            if user_preferences.get("prefer_more_charts"):
                design_context["prefer_more_charts"] = True
                logger.debug(f"[{self.agent_name}] Applied 'prefer_more_charts' preference")

            if user_preferences.get("prefer_more_images"):
                design_context["prefer_more_images"] = True
                logger.debug(f"[{self.agent_name}] Applied 'prefer_more_images' preference")

        # 使用 ReAct Agent 生成框架（通过 LangChain Tools）
        if self.has_tools():
            result = await self._design_with_tools(design_context, requirement)
        else:
            # 降级到 LLM 模式
            result = await self._design_with_llm(design_context)

        # Validate framework
        result = self._validate_and_fix(result, page_num)

        # Apply user preferences to adjust framework structure
        if user_preferences:
            result = self._apply_preferences_to_framework(result, user_preferences)

        # Cache the result (if memory enabled)
        if self.has_memory:
            await self.remember(f"framework_{page_num}_{template_type}", result, importance=0.8)

        # Update state (data passing through LangGraph State)
        state["ppt_framework"] = result
        update_state_progress(state, "framework_design", 30)

        logger.info(
            f"[{self.agent_name}] Framework designed successfully: {result['total_page']} pages"
        )
        return state

    def _validate_and_fix(
        self, framework: Dict[str, Any], expected_page_num: int
    ) -> Dict[str, Any]:
        """
        验证并修复框架

        Args:
            framework: 框架字典
            expected_page_num: 预期页数

        Returns:
            验证并修复后的框架字典
        """
        # 确保页数正确
        framework["total_page"] = expected_page_num

        # 验证pages数组
        pages = framework.get("ppt_framework", [])

        if len(pages) != expected_page_num:
            logger.warning(
                f"[{self.agent_name}] Page count mismatch: {len(pages)} != {expected_page_num}, fixing"
            )
            pages = self._fix_page_count(pages, expected_page_num)

        # 重新编号
        for i, page in enumerate(pages):
            page["page_no"] = i + 1

        framework["ppt_framework"] = pages

        # 更新索引
        research_indices = [p["page_no"] for p in pages if p.get("is_need_research", False)]
        chart_indices = [p["page_no"] for p in pages if p.get("is_need_chart", False)]
        image_indices = [p["page_no"] for p in pages if p.get("is_need_image", False)]

        framework["research_page_indices"] = research_indices
        framework["chart_page_indices"] = chart_indices
        framework["image_page_indices"] = image_indices
        framework["has_research_pages"] = len(research_indices) > 0

        return framework

    def _apply_preferences_to_framework(
        self, framework: Dict[str, Any], preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply user preferences to adjust framework structure

        This method modifies the framework based on user preferences:
        - prefer_more_charts: Add charts to content pages
        - prefer_more_images: Add images to content pages

        Args:
            framework: Generated framework
            preferences: User preferences dict

        Returns:
            Adjusted framework
        """
        pages = framework.get("ppt_framework", [])
        if not pages:
            return framework

        # Apply "prefer_more_charts" preference
        if preferences.get("prefer_more_charts", False):
            charts_added = 0
            for page in pages:
                # Add charts to content pages that don't have them yet
                if page.get("page_type") == "content" and not page.get("is_need_chart", False):
                    page["is_need_chart"] = True
                    page["content_type"] = "text_with_chart"
                    charts_added += 1

            if charts_added > 0:
                logger.info(
                    f"[{self.agent_name}] Added charts to {charts_added} pages based on user preference"
                )

        # Apply "prefer_more_images" preference
        if preferences.get("prefer_more_images", False):
            images_added = 0
            for page in pages:
                # Add images to content pages that don't have them yet
                if page.get("page_type") == "content" and not page.get("is_need_image", False):
                    page["is_need_image"] = True
                    # Update content_type if needed
                    if page.get("is_need_chart"):
                        page["content_type"] = "text_with_both"
                    else:
                        page["content_type"] = "text_with_image"
                    images_added += 1

            if images_added > 0:
                logger.info(
                    f"[{self.agent_name}] Added images to {images_added} pages based on user preference"
                )

        # Recalculate indices after modifications
        research_indices = [p["page_no"] for p in pages if p.get("is_need_research", False)]
        chart_indices = [p["page_no"] for p in pages if p.get("is_need_chart", False)]
        image_indices = [p["page_no"] for p in pages if p.get("is_need_image", False)]

        framework["chart_page_indices"] = chart_indices
        framework["image_page_indices"] = image_indices

        return framework

    def _fix_page_count(
        self, pages: List[Dict[str, Any]], target_count: int
    ) -> List[Dict[str, Any]]:
        """
        修复页数

        Args:
            pages: 当前页面列表
            target_count: 目标页数

        Returns:
            修复后的页面列表
        """
        current_count = len(pages)

        if current_count < target_count:
            # 添加缺失的页面
            for i in range(current_count, target_count):
                pages.append(
                    {
                        "page_no": i + 1,
                        "title": f"补充内容 {i + 1}",
                        "page_type": "content",
                        "core_content": "围绕主题展开关键要点与实践建议",
                        "is_need_chart": False,
                        "is_need_research": False,
                        "is_need_image": False,
                        "content_type": "text_only",
                        "keywords": [],
                        "estimated_word_count": 100,
                        "layout_suggestion": "",
                    }
                )
        elif current_count > target_count:
            # 删除多余的页面
            pages = pages[:target_count]

        return pages

    async def _design_with_tools(
        self, design_context: Dict[str, Any], requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用 ReAct Agent 设计框架（通过 LangChain Tools）

        LLM 自主选择工具：
        - topic_decomposition: 分解主题为子主题
        - section_planning: 规划章节结构

        Args:
            design_context: 设计上下文
            requirement: 原始需求（用于降级）

        Returns:
            框架字典
        """
        topic = design_context.get("ppt_topic", "")
        page_num = design_context.get("page_num", 10)

        # 构建查询
        query = f"""
请设计 PPT 框架：

需求信息：
- 主题：{topic}
- 页数：{page_num}
- 模板类型：{design_context.get('template_type', 'business')}
- 使用场景：{design_context.get('scene', 'report')}
- 核心模块：{', '.join(design_context.get('core_modules', [])[:5])}
- 是否需要研究：{design_context.get('need_research', False)}
- 语言：{design_context.get('language', 'ZH-CN')}

可用工具：
- topic_decomposition: 分解主题为子主题（num_parts, strategy, audience）
- section_planning: 规划章节结构

请返回 JSON 格式的框架，包含：
- total_page: 总页数
- ppt_framework: 页面列表（每页包含 page_no, title, page_type, core_content 等）
- research_page_indices: 需要研究的页码
- chart_page_indices: 需要图表的页码
- image_page_indices: 需要配图的页码

请确保：
1. 第1页是封面（cover）
2. 第2页通常是目录（directory）
3. 最后一页是总结或致谢（summary或thanks）
4. 总页数等于 {page_num}
"""

        try:
            logger.info(f"[{self.agent_name}] Using ReAct Agent for framework design")

            # 调用 ReAct Agent
            result = await self.execute_with_tools(query)

            # 解析结果
            framework = self._parse_framework_result(result, requirement)

            logger.info(f"[{self.agent_name}] Tool-based design completed")
            return framework

        except Exception as e:
            logger.warning(f"[{self.agent_name}] Tool execution failed: {e}, using LLM fallback")
            # 降级到 LLM 模式
            return await self._design_with_llm(design_context)

    async def _design_with_llm(self, design_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用 LLM 直接生成框架（降级方案）

        Args:
            design_context: 设计上下文

        Returns:
            框架字典
        """
        try:
            result = await self.chain.ainvoke(design_context)
            logger.info(f"[{self.agent_name}] LLM-based design completed")
            return result
        except Exception as e:
            logger.error(f"[{self.agent_name}] LLM generation failed: {e}")
            # 降级到模板框架
            return self._fallback_design(design_context)

    def _parse_framework_result(self, result: str, requirement: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析工具返回的字符串为框架字典

        Args:
            result: 工具返回的字符串
            requirement: 原始需求（用于降级）

        Returns:
            框架字典
        """
        import json

        try:
            # 尝试直接解析 JSON
            if result.strip().startswith("{"):
                data = json.loads(result)
                if isinstance(data, dict) and ("total_page" in data or "ppt_framework" in data):
                    return data

            # 尝试提取 JSON
            start = result.find("{")
            end = result.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(result[start:end])
                if isinstance(data, dict) and ("total_page" in data or "ppt_framework" in data):
                    return data

        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"[{self.agent_name}] JSON parsing failed: {e}")

        # 降级：使用模板框架
        logger.warning(f"[{self.agent_name}] Could not parse framework result, using fallback")
        return self._fallback_design(requirement)

    def _fallback_design(self, requirement: Dict[str, Any]) -> Dict[str, Any]:
        """
        降级设计：使用模板框架

        Args:
            requirement: 结构化需求

        Returns:
            框架字典
        """
        logger.info(f"[{self.agent_name}] Using fallback framework design")

        topic = requirement.get("ppt_topic", "")
        page_num = requirement.get("page_num", 10)
        need_research = requirement.get("need_research", False)
        core_modules = requirement.get("core_modules", [])

        # 使用PPTFramework类创建默认框架
        framework_obj = PPTFramework.create_default(page_num=page_num, topic=topic)

        # 如果有核心模块，尝试使用它们
        if core_modules and len(core_modules) >= 3:
            # 简单替换内容页标题
            from ...models.framework import PageType

            content_pages = [p for p in framework_obj.pages if p.page_type == PageType.CONTENT]
            module_index = 0
            for page in content_pages:
                if module_index < len(core_modules):
                    page.title = core_modules[module_index]
                    page.core_content = f"{core_modules[module_index]}的核心内容"
                    module_index += 1

        # 如果需要研究，标记部分页面
        if need_research:
            from ...models.framework import PageType

            content_pages = [p for p in framework_obj.pages if p.page_type == PageType.CONTENT]
            for i, page in enumerate(content_pages):
                if i % 2 == 0:  # 每隔一个内容页需要研究
                    page.is_need_research = True
                    page.keywords = [page.title, "相关资料"]

        framework_obj._update_indices()

        return framework_obj.to_dict()

    def get_fallback_result(self, state: PPTGenerationState) -> Optional[PPTGenerationState]:
        """
        降级策略：当execute_task失败时调用

        Args:
            state: 当前状态

        Returns:
            降级后的状态
        """
        requirement = state.get("structured_requirements", {})
        ppt_framework = self._fallback_design(requirement)

        state["ppt_framework"] = ppt_framework
        update_state_progress(state, "framework_design", 30)

        return state


# 工厂函数


def create_framework_designer(
    model: Optional[ChatOpenAI] = None,
    temperature: float = 0.0,
    enable_memory: bool = True,
    use_tools: bool = False,
) -> FrameworkDesignerAgent:
    """
    创建框架设计智能体

    Args:
        model: LangChain LLM 实例
        temperature: LLM 温度参数
        enable_memory: 是否启用记忆功能

    Returns:
        FrameworkDesignerAgent 实例
    """
    return FrameworkDesignerAgent(
        model=model,
        temperature=temperature,
        enable_memory=enable_memory,
        use_tools=use_tools,
    )


# 便捷函数


async def design_framework(
    requirement: Dict[str, Any], model: Optional[ChatOpenAI] = None
) -> Dict[str, Any]:
    """
    直接设计框架（便捷函数）

    Args:
        requirement: 结构化需求
        model: 可选的 LLM 模型

    Returns:
        PPT 框架字典
    """
    agent = create_framework_designer(model)
    state = {"structured_requirements": requirement}
    result_state = await agent.run_node(state)
    return result_state.get("ppt_framework")


if __name__ == "__main__":
    import asyncio

    async def test():
        # 测试框架设计
        test_requirements = [
            {
                "ppt_topic": "人工智能概述",
                "page_num": 10,
                "template_type": "business_template",
                "scene": "business_report",
                "core_modules": ["封面", "目录", "AI介绍", "应用场景", "未来展望", "总结"],
                "need_research": True,
                "language": "ZH-CN",
            },
            {
                "ppt_topic": "Q3 销售报告",
                "page_num": 8,
                "template_type": "business_template",
                "scene": "business_report",
                "core_modules": ["概述", "销售数据", "分析", "结论"],
                "need_research": False,
                "language": "EN-US",
            },
        ]

        agent = create_framework_designer()

        for req in test_requirements:
            print(f"\n主题: {req['ppt_topic']}")
            result = await design_framework(req)
            print(f"结果: {json.dumps(result, indent=2, ensure_ascii=False)}")

    asyncio.run(test())
