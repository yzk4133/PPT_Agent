"""
内容素材生成智能体 - LangChain 实现

该智能体根据框架和可选的研究结果为每个页面生成内容素材。

集成记忆系统，用于缓存和跨智能体数据共享。
"""

import logging
from typing import Dict, Any, Optional, List

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


# Prompt template for content generation
CONTENT_GENERATION_PROMPT = """你是一名专业的PPT内容创作专家。

{SKILL_INSTRUCTIONS}

你的任务是为PPT页面生成详细的内容素材。

页面信息：
- 页码：{page_no}
- 标题：{page_title}
- 页面类型：{page_type}
- 内容描述：{core_content}
- 预估字数：{word_count}字
- 是否需要图表：{need_chart}
- 是否需要配图：{need_image}

{research_section}

用户偏好设置：
- 语言：{language}
- 语调风格：{tone}
- 模板类型：{template_type}

请根据用户偏好调整内容风格：
1. **语言偏好**：
   - ZH-CN: 使用中文生成内容
   - EN-US: 使用英文生成内容

2. **语调风格（tone）**：
   - professional: 专业正式，使用专业术语，数据严谨
   - casual: 轻松随意，口语化表达，生动有趣
   - creative: 创意活泼，创新表达方式

3. **模板类型（template_type）**：
   - business: 商务风格，强调价值和效益，数据驱动
   - academic: 学术风格，强调方法和过程，引用标注
   - creative: 创意风格，不拘泥于固定结构，视觉元素丰富

请为这个页面生成PPT内容素材，包括：

1. **正文内容**（主要文字内容）
   - 根据页面类型调整内容结构
   - 使用要点列表或段落
   - 保持简洁有力
   - 应用用户指定的语调风格

2. **图表信息**（如果需要）
   - chart_type: 图表类型（bar/line/pie等）
   - chart_title: 图表标题
   - chart_data: 图表数据描述

3. **配图建议**（如果需要）
   - image_suggestion: 图片搜索建议
   - search_query: 用于搜索图片的关键词

输出格式（JSON，不要使用markdown包裹）：
{{
    "page_no": 页码,
    "content_text": "正文内容",
    "has_chart": true/false,
    "chart_data": {{
        "chart_type": "图表类型",
        "chart_title": "图表标题",
        "data_description": "数据描述"
    }},
    "has_image": true/false,
    "image_suggestion": {{
        "search_query": "图片搜索关键词",
        "description": "图片描述"
    }},
    "key_points": ["要点1", "要点2", "要点3"]
}}

注意事项：
- 正文内容要简洁、专业、有逻辑性
- 严格遵循用户指定的语言、语调和风格偏好
- 图表数据要合理，如果是示例数据请标注
- 图片建议要具体、可搜索
- 保持整体风格一致
"""


class ContentMaterialAgent(BaseToolAgent):
    """
    内容素材生成智能体 - 使用BaseToolAgent重构版本

    职责：
    1. 为每一页生成详细内容
    2. 生成图表数据（如果需要）
    3. 提供配图建议（如果需要）
    4. 确保内容质量和风格统一
    5. 缓存生成的内容以避免重复生成

    特性：
    - 支持并行内容生成（在PagePipeline中）
    - 使用研究结果丰富内容
    - JSON格式输出，便于后续处理
    - 集成记忆系统：缓存内容，共享数据
    - 使用 LangChain Tools（ReAct Agent）让 LLM 自主选择工具

    使用工具（通过 SKILL 类别）：
    - content_generation: 结构化内容生成工作流程
    - content_optimization: 优化已生成内容的表达
    - content_quality_check: 检查内容质量并给出评分
    """

    def __init__(
        self,
        model: Optional[ChatOpenAI] = None,
        temperature: float = 0.5,
        agent_name: str = "ContentMaterialAgent",
        enable_memory: bool = True,
        use_tools: bool = True,  # 是否使用 LangChain Tools (Python + MD Skills)
    ):
        """
        初始化内容生成智能体

        Args:
            model: LangChain LLM实例
            temperature: LLM温度参数
            agent_name: Agent名称
            enable_memory: 是否启用记忆功能
            use_tools: 是否使用 LangChain Tools（包含 Python Skills + MD Skills）

        注意：
        - 现在所有工具（Python Skills + MD Skills）都统一在 NativeToolRegistry 中管理
        - 使用 tool_names 精确指定需要的工具，避免加载不必要的工具
        """
        # Determine tool names (只加载内容生成相关的工具)
        tool_names = (
            [
                # Python Skills
                "content_generation",
                "content_optimization",
                "content_quality_check",
                # MD Skills (Guides)
                "content_generation_prompts",
                "quality_check_guide",
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
        # No manual loading needed - they're available through execute_with_tools()

    def _create_chain(self) -> Runnable:
        """创建生成链（降级方案，不使用工具时）"""
        # Note: MD Skills are deprecated, removing SKILL_INSTRUCTIONS
        enhanced_prompt = CONTENT_GENERATION_PROMPT.replace("{SKILL_INSTRUCTIONS}", "")
        enhanced_prompt = enhanced_prompt.replace("\n\n你的任务", "\n你的任务")

        prompt = ChatPromptTemplate.from_template(enhanced_prompt)
        return prompt | self.model

    async def run_node(self, state: PPTGenerationState) -> PPTGenerationState:
        """兼容工作流节点调用接口"""
        return await self.execute_task(state)

    async def execute_task(self, state: PPTGenerationState) -> PPTGenerationState:
        """
        执行内容生成任务

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        # 使用便捷方法获取共享的研究数据
        shared_research = await self.retrieve_shared_data("research", "main_research")
        if shared_research:
            logger.info(f"[{self.agent_name}] Using shared research data")
            # 合并共享的研究数据到state中
            existing_research = state.get("research_results", [])
            state["research_results"] = existing_research + shared_research

        # 获取框架
        framework = state.get("ppt_framework", {})
        pages = framework.get("ppt_framework", [])

        if not pages:
            raise ValueError("Missing pages in ppt_framework")

        # 获取研究结果
        research_results = state.get("research_results", [])

        # 生成所有页面的内容
        content_materials = await self.generate_content_for_all_pages(
            pages, research_results, state
        )

        # 使用便捷方法记住生成的内容
        await self.save_to_cache(
            "generated_content_materials",
            {"count": len(content_materials), "materials": content_materials},
            importance=0.5,
            scope="TASK",
            state=state,
        )

        # 更新状态
        state["content_materials"] = content_materials

        # 内容生成阶段的进度是50% -> 80%
        update_state_progress(state, "content_generation", 80)

        logger.info(f"[{self.agent_name}] Task completed: {len(content_materials)} pages generated")
        return state

    def _get_research_for_page(self, page_no: int, research_results: List[Dict[str, Any]]) -> str:
        """
        获取页面的研究资料

        Args:
            page_no: 页码
            research_results: 研究结果列表

        Returns:
            研究资料字符串
        """
        for research in research_results:
            if research.get("page_no") == page_no:
                content = research.get("research_content", "")
                return f"\n研究资料：\n{content}\n"
        return "\n研究资料：无\n"

    async def generate_content_for_page(
        self,
        page: Dict[str, Any],
        research_results: List[Dict[str, Any]],
        state: Optional[PPTGenerationState] = None,
    ) -> Dict[str, Any]:
        """
        为单个页面生成内容

        This method now applies user preferences for personalization:
        1. Retrieves user preferences (language, tone, template_type)
        2. Applies language preference to generation prompt
        3. Applies tone preference (professional, casual, creative)
        4. Applies template_type preference (business, academic, creative)

        Args:
            page: 页面定义字典
            research_results: 研究结果列表
            state: 可选的状态（用于记忆上下文）

        Returns:
            内容素材字典
        """
        page_no = page.get("page_no", 1)
        title = page.get("title", "")
        page_type = page.get("page_type", "content")
        core_content = page.get("core_content", "")

        # 使用便捷方法检查缓存
        cache_key = f"content_page_{page_no}_{hash(title + core_content)}"
        cached = await self.check_cache(cache_key, state)
        if cached:
            logger.info(f"[{self.agent_name}] Using cached content for page {page_no}")
            return cached

        word_count = page.get("estimated_word_count", 100)
        need_chart = page.get("is_need_chart", False)
        need_image = page.get("is_need_image", False)

        logger.info(f"[{self.agent_name}] Generating content for page {page_no}: {title}")

        # 获取研究资料
        research_section = self._get_research_for_page(page_no, research_results)

        # ===== 新增：获取并应用用户偏好 =====
        user_preferences = {}
        generation_context = {
            "page_no": page_no,
            "page_title": title,
            "page_type": page_type,
            "core_content": core_content,
            "word_count": word_count,
            "need_chart": "是" if need_chart else "否",
            "need_image": "是" if need_image else "否",
            "research_section": research_section,
        }

        # 从state获取requirement中的偏好
        if state and self.enable_memory:
            user_preferences = await self.get_user_preferences()
            requirement = state.get("structured_requirements", {})

            # 应用语言偏好
            language = user_preferences.get("language") or requirement.get("language", "ZH-CN")
            generation_context["language"] = language

            # 应用语调偏好
            tone = user_preferences.get("tone") or requirement.get("tone", "professional")
            generation_context["tone"] = tone

            # 应用模板类型偏好
            template_type = user_preferences.get("template_type") or requirement.get(
                "template_type", "business"
            )
            generation_context["template_type"] = template_type

            logger.debug(
                f"[{self.agent_name}] Applied preferences for page {page_no}: "
                f"language={language}, tone={tone}, template={template_type}"
            )

        try:
            # ===== 使用 ReAct Agent 生成内容（通过 LangChain Tools）=====
            if self.has_tools():
                # 使用 execute_with_tools() 让 LLM 自主选择工具
                content_data = await self._generate_with_tools(page, generation_context)
            else:
                # 降级到直接使用 LLM
                content_data = await self._generate_with_llm(generation_context, page_no, page)

            # 添加页码
            content_data["page_no"] = page_no

            # 使用便捷方法缓存生成的内容
            await self.save_to_cache(
                cache_key, content_data, importance=0.6, scope="TASK", state=state
            )

            logger.info(f"[{self.agent_name}] Content generated for page {page_no}")
            return content_data

        except Exception as e:
            logger.warning(
                f"[{self.agent_name}] Generation failed for page {page_no}: {e}, using fallback"
            )

            # 降级策略：生成简单的占位内容
            return self._fallback_content(page, research_results)

    def _fallback_content(
        self, page: Dict[str, Any], research_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        降级内容生成：返回简单内容

        Args:
            page: 页面定义
            research_results: 研究结果

        Returns:
            占位内容
        """
        page_no = page.get("page_no", 1)
        title = page.get("title", "")
        core_content = page.get("core_content", "")
        page_type = page.get("page_type", "content")

        # 根据页面类型生成不同内容
        if page_type == "cover":
            content_text = f"{title}\n\n汇报人\n日期"
        elif page_type == "directory":
            content_text = "目录：\n- 第一章\n- 第二章\n- 第三章\n- 总结"
        elif page_type == "summary" or page_type == "thanks":
            content_text = "感谢聆听\n欢迎提问与交流"
        else:
            content_text = core_content or f"{title}的内容"

        return {
            "page_no": page_no,
            "content_text": content_text,
            "has_chart": page.get("is_need_chart", False),
            "chart_data": (
                {}
                if not page.get("is_need_chart")
                else {
                    "chart_type": "bar",
                    "chart_title": f"{title}数据",
                    "data_description": "示例数据",
                }
            ),
            "has_image": page.get("is_need_image", False),
            "image_suggestion": (
                {}
                if not page.get("is_need_image")
                else {"search_query": title, "description": f"与{title}相关的图片"}
            ),
            "key_points": [title, core_content[:50] if core_content else ""],
        }

    async def _generate_with_tools(
        self, page: Dict[str, Any], generation_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用 ReAct Agent 生成内容（通过 LangChain Tools）

        LLM 自主选择工具：
        - content_generation: 生成内容
        - content_quality_check: 检查内容质量
        - content_optimization: 优化内容

        Args:
            page: 页面定义
            generation_context: 生成上下文

        Returns:
            内容素材字典
        """
        page_no = page.get("page_no", 1)
        title = page.get("title", "")

        # 构建查询
        # 注意：现在 MD Skills 已自动包含在 SKILL 类别中
        tools_description = """可用工具：
- content_generation: 结构化内容生成工作流程
- content_generation_prompts: 内容生成指南（level 1-3，获取分层指导）
- content_quality_check: 检查内容质量并给出评分
- quality_check_guide: 质量检查指南（level 1-3）
- content_optimization: 优化已生成内容的表达

提示：如果不确定如何生成高质量内容，可以先调用 content_generation_prompts(level=1) 获取快速指南。"""

        query = f"""
请为 PPT 页面生成内容：

页面信息：
- 页码：{page_no}
- 标题：{title}
- 页面类型：{page.get('page_type', 'content')}
- 核心内容：{page.get('core_content', '')}
- 预估字数：{page.get('estimated_word_count', 200)}字
- 是否需要图表：{page.get('is_need_chart', False)}
- 是否需要配图：{page.get('is_need_image', False)}

用户偏好：
- 语言：{generation_context.get('language', 'ZH-CN')}
- 语调：{generation_context.get('tone', 'professional')}
- 模板类型：{generation_context.get('template_type', 'business')}

研究资料：
{generation_context.get('research_section', '无')}

{tools_description}

请确保：
1. 质量分数 >= 0.8
2. 返回 JSON 格式，包含：title, subtitle, key_points, content_text 等
3. 严格遵循用户偏好设置
"""

        try:
            logger.info(f"[{self.agent_name}] Using ReAct Agent for page {page_no}")

            # 调用 ReAct Agent
            result = await self.execute_with_tools(query)

            # 解析结果
            content_data = self._parse_result(result, page)

            logger.info(f"[{self.agent_name}] Tool-based generation completed for page {page_no}")
            return content_data

        except Exception as e:
            logger.warning(f"[{self.agent_name}] Tool execution failed: {e}, using LLM fallback")
            # 降级到 LLM 模式
            return await self._generate_with_llm(generation_context, page_no, page)

    def _parse_result(self, result: str, page: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析工具返回的字符串为结构化数据

        Args:
            result: 工具返回的字符串
            page: 页面定义（用于降级）

        Returns:
            内容素材字典
        """
        import json

        try:
            # 尝试直接解析 JSON
            if result.strip().startswith("{"):
                data = json.loads(result)
                if isinstance(data, dict) and ("title" in data or "key_points" in data):
                    return data

            # 尝试提取 JSON
            start = result.find("{")
            end = result.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(result[start:end])
                if isinstance(data, dict) and ("title" in data or "key_points" in data):
                    return data

        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"[{self.agent_name}] JSON parsing failed: {e}")

        # 降级：从文本中提取信息
        lines = result.split("\n")
        title = page.get("title", "")
        key_points = []

        for line in lines:
            line = line.strip()
            if line.startswith("标题:") or line.startswith("title:"):
                title = line.split(":", 1)[1].strip()
            elif line.startswith(("要点:", "关键点:", "-")):
                point = line.split(":", 1)[1].strip() if ":" in line else line.lstrip("-").strip()
                if point:
                    key_points.append(point)

        return {
            "title": title,
            "subtitle": "",
            "key_points": key_points[:5] if key_points else [page.get("core_content", "")[:50]],
            "content_text": result,
            "has_chart": page.get("is_need_chart", False),
            "has_image": page.get("is_need_image", False),
        }

    async def _generate_with_llm(
        self,
        generation_context: Dict[str, Any],
        page_no: int,
        page: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        使用 LLM 直接生成内容（降级方案）

        Args:
            generation_context: 生成上下文
            page_no: 页码

        Returns:
            内容素材字典
        """
        # 使用 LLM 生成内容
        result = await self.chain.ainvoke(generation_context)

        # 解析 JSON 结果（兼容 markdown 代码块或包裹文本）
        import json
        import re

        content = (result.content or "").strip()
        content_data = None

        try:
            content_data = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            code_block_match = re.search(
                r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", content, re.IGNORECASE
            )
            if code_block_match:
                try:
                    content_data = json.loads(code_block_match.group(1))
                except (json.JSONDecodeError, ValueError):
                    content_data = None

            if content_data is None:
                start = content.find("{")
                end = content.rfind("}") + 1
                if start != -1 and end > start:
                    try:
                        content_data = json.loads(content[start:end])
                    except (json.JSONDecodeError, ValueError):
                        content_data = None

        if not isinstance(content_data, dict):
            if page is not None:
                logger.warning(
                    f"[{self.agent_name}] LLM returned non-JSON content for page {page_no}, using structured text parser"
                )
                content_data = self._parse_result(content, page)
            else:
                raise ValueError("LLM content is not valid JSON")

        logger.info(f"[{self.agent_name}] Content generated by LLM for page {page_no}")
        return content_data

    async def generate_content_for_all_pages(
        self,
        pages: List[Dict[str, Any]],
        research_results: List[Dict[str, Any]],
        state: Optional[PPTGenerationState] = None,
    ) -> List[Dict[str, Any]]:
        """
        为所有页面生成内容

        Args:
            pages: 所有页面列表
            research_results: 研究结果列表
            state: 可选的状态（用于记忆上下文）

        Returns:
            内容素材列表
        """
        logger.info(f"[{self.agent_name}] Generating content for {len(pages)} pages")

        # 并行生成所有页面的内容
        import asyncio

        tasks = [self.generate_content_for_page(page, research_results, state) for page in pages]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        content_materials = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"[{self.agent_name}] Page {i+1} generation failed: {result}")
                # 添加降级结果
                content_materials.append(self._fallback_content(pages[i], research_results))
            else:
                content_materials.append(result)

        logger.info(
            f"[{self.agent_name}] Completed content generation for {len(content_materials)} pages"
        )
        return content_materials

    def get_fallback_result(self, state: PPTGenerationState) -> Optional[PPTGenerationState]:
        """降级策略"""
        framework = state.get("ppt_framework", {})
        pages = framework.get("ppt_framework", [])

        # 为所有页面生成简单内容
        content_materials = [self._fallback_content(page, []) for page in pages]

        state["content_materials"] = content_materials
        update_state_progress(state, "content_generation", 80)

        return state


# 工厂函数


def create_content_agent(
    model: Optional[ChatOpenAI] = None,
    temperature: float = 0.5,
    enable_memory: bool = True,
    use_tools: bool = False,
) -> ContentMaterialAgent:
    """
    创建内容生成智能体

    Args:
        model: LangChain LLM 实例
        temperature: LLM 温度参数
        enable_memory: 是否启用记忆功能

    Returns:
        ContentMaterialAgent 实例
    """
    return ContentMaterialAgent(
        model=model,
        temperature=temperature,
        enable_memory=enable_memory,
        use_tools=use_tools,
    )


# 便捷函数


async def generate_content(
    page: Dict[str, Any],
    research_results: List[Dict[str, Any]] = None,
    model: Optional[ChatOpenAI] = None,
) -> Dict[str, Any]:
    """
    直接生成页面内容（便捷函数）

    Args:
        page: 页面定义
        research_results: 研究结果
        model: 可选的 LLM 模型

    Returns:
        内容素材字典
    """
    agent = create_content_agent(model)
    return await agent.generate_content_for_page(page, research_results or [])


if __name__ == "__main__":
    import asyncio

    async def test():
        # 测试内容生成
        test_pages = [
            {
                "page_no": 1,
                "title": "人工智能概述",
                "page_type": "cover",
                "core_content": "AI介绍封面",
                "is_need_chart": False,
                "is_need_image": True,
                "estimated_word_count": 50,
            },
            {
                "page_no": 3,
                "title": "AI发展历程",
                "page_type": "content",
                "core_content": "介绍人工智能从诞生到现在的发展",
                "is_need_chart": True,
                "is_need_image": False,
                "estimated_word_count": 200,
            },
        ]

        test_research = [{"page_no": 3, "research_content": "人工智能诞生于1956年达特茅斯会议..."}]

        agent = create_content_agent()

        for page in test_pages:
            print(f"\n正在为第 {page['page_no']} 页生成内容: {page['title']}")
            result = await agent.generate_content_for_page(page, test_research)
            print(f"结果:\n{result['content_text'][:200]}...")

    asyncio.run(test())
