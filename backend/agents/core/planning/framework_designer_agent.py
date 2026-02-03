"""
Framework Designer Agent

框架设计智能体，负责设计PPT的整体结构。

功能：
1. 根据需求设计PPT页序（封面→目录→内容页→总结）
2. 为每页定义标题、核心内容方向、是否需要图表/研究资料
3. 模板布局适配（标注图表区、配图区）
4. 自校验（页数匹配、逻辑连贯、模板适配）
"""

import json
import logging
import os
import sys
from typing import AsyncGenerator, Optional, Dict, Any

from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types
from google.adk.events.event import Event

# 导入基础设施
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from infrastructure.llm.fallback import JSONFallbackParser

# 导入PromptManager
from prompts import PromptManager

# 导入领域模型
from domain.models import PPTFramework, PageDefinition, PageType, ContentType, Requirement

logger = logging.getLogger(__name__)

# 使用PromptManager获取提示词模板
FRAMEWORK_DESIGNER_PROMPT = PromptManager.get_framework_designer_prompt()


class FrameworkDesignerAgent(LlmAgent):
    """
    框架设计智能体

    职责：
    1. 根据需求设计PPT页序（封面→目录→内容页→总结）
    2. 为每页定义标题、核心内容方向、是否需要图表/研究资料
    3. 模板布局适配（标注图表区、配图区）
    4. 自校验（页数匹配、逻辑连贯、模板适配）
    """

    def __init__(self, **kwargs):
        super().__init__(
            model="deepseek-chat",
            name="FrameworkDesignerAgent",
            description="负责设计PPT的整体结构，包括页序和每页定义",
            instruction=FRAMEWORK_DESIGNER_PROMPT,
            output_key="ppt_framework",
            **kwargs
        )

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        执行框架设计

        Args:
            ctx: 调用上下文
        """
        try:
            # 1. 获取结构化需求
            requirement_dict = ctx.session.state.get("structured_requirements")
            if not requirement_dict:
                raise ValueError("Missing structured_requirements in session state")

            requirement = Requirement.from_dict(requirement_dict)
            logger.info(f"FrameworkDesignerAgent received requirement: {requirement}")

            # 2. 调用LLM设计框架
            async for event in super()._run_async_impl(ctx):
                yield event

            # 3. 获取LLM输出并解析
            llm_output = ctx.session.state.get("ppt_framework", "")
            logger.info(f"LLM output: {llm_output[:200]}...")

            # 4. 使用降级策略解析JSON
            parse_result = JSONFallbackParser.parse_with_fallback(
                llm_output,
                default_structure=self._get_default_framework(requirement)
            )

            if not parse_result.success:
                logger.error(f"JSON parsing failed: {parse_result.error}")
                # 使用默认框架
                framework_dict = self._get_default_framework(requirement)
            else:
                framework_dict = parse_result.data
                if parse_result.level != "primary":
                    logger.warning(f"Using fallback strategy: {parse_result.level}")

            # 5. 创建PPTFramework对象
            framework = PPTFramework.from_dict(framework_dict)

            # 6. 自校验
            is_valid, errors = framework.validate(requirement.page_num)
            if not is_valid:
                logger.warning(f"Framework validation errors: {errors}")
                # 尝试修正
                self._fix_framework(framework, requirement.page_num, errors)

            # 7. 确保页面数量匹配
            self._adjust_page_count(framework, requirement.page_num)

            # 8. 保存到上下文
            ctx.session.state["ppt_framework"] = framework.to_dict()
            ctx.session.state["framework_object"] = framework

            logger.info(f"Framework designed successfully: {framework}")

            # 9. 产生完成事件
            research_pages = len(framework.research_page_indices)
            chart_pages = len(framework.chart_page_indices)
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[types.Part(
                        text=f"框架设计完成：\n"
                        f"- 总页数: {framework.total_page}\n"
                        f"- 需要研究的页面: {research_pages}页\n"
                        f"- 需要图表的页面: {chart_pages}页\n"
                        f"- 框架类型: {framework.framework_type}"
                    )]
                ),
            )

        except Exception as e:
            logger.error(f"FrameworkDesignerAgent failed: {e}", exc_info=True)
            # 使用默认框架作为兜底
            requirement_dict = ctx.session.state.get("structured_requirements", {})
            requirement = Requirement.from_dict(requirement_dict) if requirement_dict else Requirement(ppt_topic="默认主题")
            default_framework = self._get_default_framework(requirement)
            ctx.session.state["ppt_framework"] = default_framework
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[types.Part(text=f"使用默认框架: {default_framework['total_page']}页")]
                ),
            )

    def _get_default_framework(self, requirement: Requirement) -> Dict[str, Any]:
        """
        获取默认框架

        Args:
            requirement: 需求对象

        Returns:
            默认框架字典
        """
        framework = PPTFramework.create_default(requirement.page_num, requirement.ppt_topic)

        # 根据需求调整
        for page in framework.pages:
            # 如果需要研究，在内容页上添加研究标记
            if requirement.need_research and page.page_type == PageType.CONTENT:
                # 每隔一页添加研究标记
                if (page.page_no % 3) == 0:
                    page.is_need_research = True
                    page.keywords = requirement.keywords.copy()

            # 根据模板类型调整风格
            if requirement.template_type.value == "business_template":
                page.layout_suggestion = "正式、简洁、商务风格"
            elif requirement.template_type.value == "creative_template":
                page.layout_suggestion = "活泼、时尚、创意风格"
            elif requirement.template_type.value == "tech_template":
                page.layout_suggestion = "现代、科技感、蓝色调"

        return framework.to_dict()

    def _fix_framework(self, framework: PPTFramework, expected_page_num: int, errors: list) -> None:
        """
        修正框架中的错误

        Args:
            framework: 框架对象
            expected_page_num: 期望页数
            errors: 错误列表
        """
        # 检查页数是否匹配
        if framework.total_page != expected_page_num:
            self._adjust_page_count(framework, expected_page_num)

        # 检查是否有封面
        has_cover = any(p.page_type == PageType.COVER for p in framework.pages)
        if not has_cover and framework.pages:
            framework.pages[0].page_type = PageType.COVER

        # 检查是否有总结
        has_summary = any(p.page_type in (PageType.SUMMARY, PageType.THANKS) for p in framework.pages)
        if not has_summary and framework.pages:
            framework.pages[-1].page_type = PageType.SUMMARY

        # 重新编号
        framework._renumber_pages()

    def _adjust_page_count(self, framework: PPTFramework, target_page_num: int) -> None:
        """
        调整页面数量

        Args:
            framework: 框架对象
            target_page_num: 目标页数
        """
        current_count = len(framework.pages)

        if current_count < target_page_num:
            # 添加页面
            while len(framework.pages) < target_page_num:
                page_no = len(framework.pages) + 1
                if page_no == target_page_num:
                    # 最后一页是总结
                    new_page = PageDefinition(
                        page_no=page_no,
                        title="总结",
                        page_type=PageType.SUMMARY,
                        core_content="总结和展望",
                        content_type=ContentType.TEXT_ONLY
                    )
                else:
                    # 中间页是内容页
                    new_page = PageDefinition(
                        page_no=page_no,
                        title=f"第{page_no - 2}部分",
                        page_type=PageType.CONTENT,
                        core_content=f"第{page_no - 2}部分的核心内容",
                        content_type=ContentType.TEXT_WITH_CHART if (page_no % 2 == 0) else ContentType.TEXT_ONLY
                    )
                framework.pages.append(new_page)

        elif current_count > target_page_num:
            # 删除多余的中间页（保留封面、目录和总结）
            content_pages = [p for p in framework.pages
                           if p.page_type == PageType.CONTENT and
                           p.page_no not in (1, 2, current_count)]
            pages_to_remove = current_count - target_page_num

            for _ in range(min(pages_to_remove, len(content_pages))):
                if content_pages:
                    page_to_remove = content_pages.pop()
                    framework.pages.remove(page_to_remove)

        # 重新编号
        framework._renumber_pages()
        framework.total_page = len(framework.pages)
        framework._update_indices()


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    模型调用前的回调函数

    将结构化需求添加到请求中
    """
    requirement_dict = callback_context.state.get("structured_requirements")
    if not requirement_dict:
        logger.warning("No structured_requirements found in callback")
        return None

    requirement_str = json.dumps(requirement_dict, ensure_ascii=False, indent=2)

    # 将需求添加到请求中
    llm_request.contents.append(
        types.Content(role="user", parts=[types.Part(text=requirement_str)])
    )

    logger.info(f"FrameworkDesignerAgent processing requirement: {requirement_dict.get('ppt_topic', 'Unknown')}")
    return None


# 创建全局实例
framework_designer_agent = FrameworkDesignerAgent(
    before_model_callback=before_model_callback
)


if __name__ == "__main__":
    # 测试代码
    import asyncio
    from domain.models import Requirement, SceneType, TemplateType

    requirement = Requirement(
        ppt_topic="2025电商618销售复盘",
        scene=SceneType.BUSINESS_REPORT,
        page_num=15,
        template_type=TemplateType.BUSINESS,
        need_research=True
    )

    print(f"Testing FrameworkDesignerAgent")
    print("=" * 60)

    agent = framework_designer_agent
    default_framework = agent._get_default_framework(requirement)

    print(f"Default framework: {json.dumps(default_framework, indent=2, ensure_ascii=False)}")
