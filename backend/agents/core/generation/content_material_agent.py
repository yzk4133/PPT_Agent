"""
Content Material Agent

内容素材智能体，负责生成PPT的文字内容、图表和配图。

功能：
1. 文字内容生成（融合研究结果）
2. 图表生成（基于数据）
3. 配图匹配（基于主题）
4. 与PPT渲染分离，专注素材生成
"""

import json
import logging
import os
import sys
from typing import AsyncGenerator, Optional, Dict, Any, List

from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types
from google.adk.events.event import Event

# 导入基础设施
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from infrastructure.llm.fallback import JSONFallbackParser

# 导入新的 MCP 工具
from agents.tools.mcp import search_images

# 导入PromptManager
from prompts import PromptManager

logger = logging.getLogger(__name__)

# 配置
content_model = "deepseek-chat"

# 获取XML PPT生成提示词（用于内容生成）
XML_PPT_AGENT_PROMPT = PromptManager.get_xml_ppt_generation_prompt()


class ContentMaterialAgent(LlmAgent):
    """
    内容素材智能体

    职责：
    1. 文字内容生成（融合研究结果）
    2. 图表生成（基于数据）
    3. 配图匹配（基于主题）

    与PPT渲染分离，专注素材生成

    支持单页生成模式用于页面级流水线并行
    """

    def __init__(self, **kwargs):
        super().__init__(
            model=content_model,
            name="ContentMaterialAgent",
            description="负责生成PPT的文字内容、图表和配图素材",
            instruction=XML_PPT_AGENT_PROMPT,
            output_key="content_material",
            tools=[search_images],  # 使用新的 MCP 工具
            **kwargs
        )

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        执行内容素材生成

        Args:
            ctx: 调用上下文
        """
        try:
            # 1. 获取框架和研究结果
            framework_dict = ctx.session.state.get("ppt_framework")
            research_results = ctx.session.state.get("research_results", [])

            if not framework_dict:
                raise ValueError("Missing ppt_framework in session state")

            pages = framework_dict.get("ppt_framework", [])
            logger.info(f"ContentMaterialAgent processing {len(pages)} pages")

            # 2. 为每页生成内容素材
            content_material_list = []

            for i, page in enumerate(pages):
                page_no = page.get("page_no", i + 1)
                page_title = page.get("title", "")
                page_type = page.get("page_type", "content")
                core_content = page.get("core_content", "")
                is_need_chart = page.get("is_need_chart", False)
                is_need_research = page.get("is_need_research", False)
                is_need_image = page.get("is_need_image", False)
                content_type = page.get("content_type", "text_only")
                keywords = page.get("keywords", [])

                # 查找相关研究结果
                research_content = ""
                if is_need_research:
                    for research in research_results:
                        if research.get("page_no") == page_no:
                            research_content = research.get("content", "")
                            break

                # 生成页面素材
                page_material = await self._generate_page_material(
                    ctx=ctx,
                    page_no=page_no,
                    page_title=page_title,
                    page_type=page_type,
                    core_content=core_content,
                    research_content=research_content,
                    is_need_chart=is_need_chart,
                    is_need_image=is_need_image,
                    content_type=content_type,
                    keywords=keywords,
                    page_index=i
                )

                content_material_list.append(page_material)

                # 更新进度
                progress = int((i + 1) / len(pages) * 100)
                logger.info(f"Generated material for page {page_no}/{len(pages)} ({progress}%)")

            # 3. 保存到上下文
            ctx.session.state["content_material"] = content_material_list

            logger.info(f"Content material generation completed: {len(content_material_list)} pages")

            # 4. 产生完成事件
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[types.Part(
                        text=f"内容素材生成完成：\n"
                        f"- 生成页面数: {len(content_material_list)}\n"
                        f"- 包含图表: {sum(1 for m in content_material_list if m.get('has_chart'))}页\n"
                        f"- 包含配图: {sum(1 for m in content_material_list if m.get('has_image'))}页"
                    )]
                ),
            )

        except Exception as e:
            logger.error(f"ContentMaterialAgent failed: {e}", exc_info=True)
            # 创建空素材列表作为兜底
            framework_dict = ctx.session.state.get("ppt_framework", {})
            pages = framework_dict.get("ppt_framework", [])
            ctx.session.state["content_material"] = [
                {"page_no": p.get("page_no", i + 1), "error": str(e)}
                for i, p in enumerate(pages)
            ]
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[types.Part(text=f"内容素材生成失败: {str(e)}")]
                ),
            )

    async def _generate_page_material(
        self,
        ctx: InvocationContext,
        page_no: int,
        page_title: str,
        page_type: str,
        core_content: str,
        research_content: str,
        is_need_chart: bool,
        is_need_image: bool,
        content_type: str,
        keywords: List[str],
        page_index: int
    ) -> Dict[str, Any]:
        """
        生成单个页面的内容素材

        Args:
            ctx: 调用上下文
            page_no: 页码
            page_title: 页面标题
            page_type: 页面类型
            core_content: 核心内容
            research_content: 研究内容
            is_need_chart: 是否需要图表
            is_need_image: 是否需要配图
            content_type: 内容类型
            keywords: 关键词
            page_index: 页面索引

        Returns:
            页面素材字典
        """
        # 构建页面提示
        page_prompt = self._build_page_prompt(
            page_no=page_no,
            page_title=page_title,
            page_type=page_type,
            core_content=core_content,
            research_content=research_content,
            is_need_chart=is_need_chart,
            is_need_image=is_need_image,
            content_type=content_type,
            keywords=keywords,
            total_pages=len(ctx.session.state.get("ppt_framework", {}).get("ppt_framework", []))
        )

        # 这里简化处理，直接返回结构化素材
        # 实际使用中可以通过LLM生成更详细的内容
        material = {
            "page_no": page_no,
            "page_title": page_title,
            "page_type": page_type,
            "content_text": self._generate_content_text(
                page_title, core_content, research_content, page_type
            ),
            "chart_data": None,
            "has_chart": False,
            "image_url": None,
            "has_image": False,
            "keywords": keywords,
            "content_type": content_type
        }

        # 生成图表数据
        if is_need_chart:
            material["chart_data"] = self._generate_chart_data(
                page_title, research_content, keywords
            )
            material["has_chart"] = True

        # 生成配图建议
        if is_need_image:
            material["image_suggestion"] = self._generate_image_suggestion(
                page_title, keywords
            )
            material["has_image"] = True

        return material

    def _build_page_prompt(
        self,
        page_no: int,
        page_title: str,
        page_type: str,
        core_content: str,
        research_content: str,
        is_need_chart: bool,
        is_need_image: bool,
        content_type: str,
        keywords: List[str],
        total_pages: int
    ) -> str:
        """
        构建页面生成提示

        Args:
            ... (同上)
            total_pages: 总页数

        Returns:
            页面提示
        """
        prompt_parts = [
            f"## 页面 {page_no}/{total_pages}",
            f"**标题**: {page_title}",
            f"**类型**: {page_type}",
            f"**核心内容**: {core_content}",
        ]

        if research_content:
            prompt_parts.append(f"**研究资料**: {research_content}")

        if is_need_chart:
            prompt_parts.append("**需要图表**: 是")

        if is_need_image:
            prompt_parts.append("**需要配图**: 是")

        if keywords:
            prompt_parts.append(f"**关键词**: {', '.join(keywords)}")

        prompt_parts.append(f"**内容类型**: {content_type}")

        return "\n".join(prompt_parts)

    def _generate_content_text(
        self, page_title: str, core_content: str, research_content: str, page_type: str
    ) -> str:
        """
        生成文字内容

        Args:
            page_title: 页面标题
            core_content: 核心内容
            research_content: 研究内容
            page_type: 页面类型

        Returns:
            文字内容
        """
        if page_type == "cover":
            return f"# {page_title}\n\n副标题\n\n汇报人\n\n日期"
        elif page_type == "directory":
            return "## 目录\n\n- 第一部分\n- 第二部分\n- 第三部分\n- 总结"
        elif page_type == "summary":
            return f"## {page_title}\n\n### 要点总结\n\n### 展望未来"
        else:
            # 内容页
            content = f"## {page_title}\n\n"
            content += f"### {core_content}\n\n"
            if research_content:
                content += f"### 详细说明\n\n{research_content[:200]}..."
            return content

    def _generate_chart_data(
        self, page_title: str, research_content: str, keywords: List[str]
    ) -> Dict[str, Any]:
        """
        生成图表数据

        Args:
            page_title: 页面标题
            research_content: 研究内容
            keywords: 关键词

        Returns:
            图表数据字典
        """
        # 简化实现，返回示例图表数据
        return {
            "chart_type": "bar",  # bar, line, pie, etc.
            "title": f"{page_title} - 数据图表",
            "data": {
                "labels": ["类别1", "类别2", "类别3", "类别4"],
                "datasets": [{
                    "label": "数据系列1",
                    "data": [12, 19, 3, 5]
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {
                        "position": "top"
                    }
                }
            }
        }

    def _generate_image_suggestion(self, page_title: str, keywords: List[str]) -> Dict[str, Any]:
        """
        生成配图建议

        Args:
            page_title: 页面标题
            keywords: 关键词

        Returns:
            配图建议字典
        """
        search_keywords = keywords + [page_title] if keywords else [page_title]
        return {
            "search_query": " ".join(search_keywords[:3]),
            "image_style": "professional",
            "color_scheme": "blue",
            "suggestion": f"建议搜索与 {page_title} 相关的配图"
        }

    async def generate_single_page(
        self,
        page,
        research_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成单个页面的内容素材（用于流水线并行）

        Args:
            page: PageDefinition对象
            research_result: 研究结果（可选）

        Returns:
            页面内容素材字典
        """
        try:
            # 提取页面信息
            page_no = page.page_no if hasattr(page, 'page_no') else page.get('page_no', 1)
            page_title = page.title if hasattr(page, 'title') else page.get('title', '')
            page_type = page.page_type.value if hasattr(page, 'page_type') and hasattr(page.page_type, 'value') else page.get('page_type', 'content')
            core_content = page.core_content if hasattr(page, 'core_content') else page.get('core_content', '')
            is_need_chart = page.is_need_chart if hasattr(page, 'is_need_chart') else page.get('is_need_chart', False)
            is_need_research = page.is_need_research if hasattr(page, 'is_need_research') else page.get('is_need_research', False)
            is_need_image = page.is_need_image if hasattr(page, 'is_need_image') else page.get('is_need_image', False)
            content_type = page.content_type.value if hasattr(page, 'content_type') and hasattr(page.content_type, 'value') else page.get('content_type', 'text_only')
            keywords = page.keywords if hasattr(page, 'keywords') else page.get('keywords', [])

            # 整合研究结果
            research_content = ""
            if research_result and is_need_research:
                research_content = research_result.get("content", "")

            # 生成页面素材
            material = await self._generate_page_material_async(
                page_no=page_no,
                page_title=page_title,
                page_type=page_type,
                core_content=core_content,
                research_content=research_content,
                is_need_chart=is_need_chart,
                is_need_image=is_need_image,
                content_type=content_type,
                keywords=keywords
            )

            logger.info(f"Single page content generated: page {page_no}")
            return material

        except Exception as e:
            logger.error(f"Single page content generation failed for page {page_no}: {e}")
            # 返回错误结果
            page_no_for_error = page.page_no if hasattr(page, 'page_no') else page.get('page_no', 1)
            page_title_for_error = page.title if hasattr(page, 'title') else page.get('title', '')
            return {
                "page_no": page_no_for_error,
                "page_title": page_title_for_error,
                "page_type": "content",
                "content_text": f"内容生成失败: {str(e)}",
                "chart_data": None,
                "has_chart": False,
                "image_suggestion": None,
                "has_image": False,
                "error": str(e)
            }

    async def _generate_page_material_async(
        self,
        page_no: int,
        page_title: str,
        page_type: str,
        core_content: str,
        research_content: str,
        is_need_chart: bool,
        is_need_image: bool,
        content_type: str,
        keywords: List[str]
    ) -> Dict[str, Any]:
        """
        异步生成页面素材

        Args:
            page_no: 页码
            page_title: 页面标题
            page_type: 页面类型
            core_content: 核心内容
            research_content: 研究内容
            is_need_chart: 是否需要图表
            is_need_image: 是否需要配图
            content_type: 内容类型
            keywords: 关键词

        Returns:
            页面素材字典
        """
        # 这里可以添加实际的LLM调用逻辑
        # 为了简化，直接使用同步方法生成

        material = {
            "page_no": page_no,
            "page_title": page_title,
            "page_type": page_type,
            "content_text": self._generate_content_text(
                page_title, core_content, research_content, page_type
            ),
            "chart_data": None,
            "has_chart": False,
            "image_url": None,
            "has_image": False,
            "keywords": keywords,
            "content_type": content_type
        }

        # 生成图表数据
        if is_need_chart:
            material["chart_data"] = self._generate_chart_data(
                page_title, research_content, keywords
            )
            material["has_chart"] = True

        # 生成配图建议
        if is_need_image:
            material["image_suggestion"] = self._generate_image_suggestion(
                page_title, keywords
            )
            material["has_image"] = True

        return material


def before_agent_callback(callback_context: CallbackContext) -> None:
    """
    Agent调用前的回调
    """
    framework = callback_context.state.get("ppt_framework", {})
    research_results = callback_context.state.get("research_results", [])

    logger.info(f"ContentMaterialAgent preparing: {len(framework.get('ppt_framework', []))} pages, "
                f"{len(research_results)} research results")

    # 存储页数供后续使用
    pages = framework.get("ppt_framework", [])
    callback_context.state["total_pages"] = len(pages)

    return None


# 创建全局实例
content_material_agent = ContentMaterialAgent(
    before_agent_callback=before_agent_callback
)


if __name__ == "__main__":
    # 测试代码
    import asyncio
    from domain.models import Requirement, PPTFramework

    print(f"Testing ContentMaterialAgent")
    print("=" * 60)

    agent = content_material_agent

    # 测试内容生成
    content_text = agent._generate_content_text(
        page_title="行业分析",
        core_content="电商行业的发展趋势",
        research_content="根据最新报告，电商行业持续增长...",
        page_type="content"
    )
    print(f"Generated content text:\n{content_text}")

    # 测试图表数据生成
    chart_data = agent._generate_chart_data(
        page_title="销售数据",
        research_content="618期间销售额突破100亿",
        keywords=["销售", "618"]
    )
    print(f"\nGenerated chart data: {json.dumps(chart_data, indent=2, ensure_ascii=False)}")
