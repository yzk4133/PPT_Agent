"""
Requirement Parser Agent

需求解析智能体，负责将用户的自然语言需求转化为结构化需求清单。

功能：
1. 从自然语言中提取核心要素（主题、场景、行业、受众、页数、模板类型）
2. 模糊需求补全（默认值）
3. 需求结构化（输出标准化JSON）
4. 自校验（完整性、合理性校验）
"""

import json
import logging
import re
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
from domain.models import Requirement, SceneType, TemplateType

logger = logging.getLogger(__name__)

# 使用PromptManager获取提示词模板
REQUIREMENT_PARSER_PROMPT = PromptManager.get_requirement_parser_prompt()


class RequirementParserAgent(LlmAgent):
    """
    需求解析智能体

    职责：
    1. 从自然语言中提取核心要素（主题、场景、行业、受众、页数、模板类型）
    2. 模糊需求补全（默认值）
    3. 需求结构化（输出标准化JSON）
    4. 自校验（完整性、合理性校验）
    """

    def __init__(self, **kwargs):
        super().__init__(
            model="deepseek-chat",
            name="RequirementParserAgent",
            description="负责将用户的自然语言需求转化为结构化需求清单",
            instruction=REQUIREMENT_PARSER_PROMPT,
            output_key="structured_requirements",
            **kwargs
        )

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        执行需求解析

        Args:
            ctx: 调用上下文
        """
        try:
            # 1. 提取用户输入
            user_input = ctx.user_content.parts[0].text
            logger.info(f"RequirementParserAgent received input: {user_input[:100]}...")

            # 2. 调用LLM解析
            async for event in super()._run_async_impl(ctx):
                yield event

            # 3. 获取LLM输出并解析
            llm_output = ctx.session.state.get("structured_requirements", "")
            logger.info(f"LLM output: {llm_output[:200]}...")

            # 4. 使用降级策略解析JSON
            parse_result = JSONFallbackParser.parse_with_fallback(
                llm_output,
                default_structure=self._get_default_requirement(user_input)
            )

            if not parse_result.success:
                logger.error(f"JSON parsing failed: {parse_result.error}")
                # 使用默认结构
                parsed = self._get_default_requirement(user_input)
            else:
                parsed = parse_result.data
                if parse_result.level != "primary":
                    logger.warning(f"Using fallback strategy: {parse_result.level}")

            # 5. 创建Requirement对象并进行校验和补全
            requirement = Requirement.from_dict(parsed)
            is_valid, errors = requirement.validate()

            if not is_valid:
                logger.warning(f"Requirement validation errors: {errors}")
                # 尝试修正
                self._fix_requirement(requirement, errors)

            # 6. 填充默认值
            requirement.fill_defaults()

            # 7. 保存到上下文
            ctx.session.state["structured_requirements"] = requirement.to_dict()
            ctx.session.state["requirement_object"] = requirement

            logger.info(f"Requirement parsed successfully: {requirement}")

            # 8. 产生完成事件
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[types.Part(
                        text=f"需求解析完成：\n"
                        f"- 主题: {requirement.ppt_topic}\n"
                        f"- 场景: {requirement.scene.value}\n"
                        f"- 页数: {requirement.page_num}\n"
                        f"- 模板: {requirement.template_type.value}\n"
                        f"- 需要研究: {'是' if requirement.need_research else '否'}"
                    )]
                ),
            )

        except Exception as e:
            logger.error(f"RequirementParserAgent failed: {e}", exc_info=True)
            # 使用默认结构作为兜底
            user_input = ctx.user_content.parts[0].text
            default_req = self._get_default_requirement(user_input)
            ctx.session.state["structured_requirements"] = default_req
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[types.Part(text=f"使用默认配置: {default_req}")]
                ),
            )

    def _get_default_requirement(self, user_input: str) -> Dict[str, Any]:
        """
        获取默认需求结构

        Args:
            user_input: 用户输入

        Returns:
            默认需求字典
        """
        # 尝试从输入中提取页数
        page_num = self._extract_page_num(user_input)

        # 尝试判断场景
        scene = self._detect_scene(user_input)

        # 尝试判断模板类型
        template_type = self._detect_template_type(user_input)

        return {
            "ppt_topic": user_input[:100] if user_input else "未命名主题",
            "scene": scene.value,
            "industry": "通用",
            "audience": "普通观众",
            "page_num": page_num,
            "template_type": template_type.value,
            "core_modules": [],
            "need_research": False,
            "special_require": [],
            "language": "ZH-CN" if self._is_chinese(user_input) else "EN-US",
            "keywords": [],
            "style_preference": "",
            "color_scheme": ""
        }

    def _extract_page_num(self, text: str) -> int:
        """
        从文本中提取页数

        Args:
            text: 输入文本

        Returns:
            页数
        """
        # 匹配常见的页数表达方式
        patterns = [
            r'(\d+)\s*[页页张张]',
            r'(\d+)\s*pages?',
            r'page[s]?\s*[:：]?\s*(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    num = int(match.group(1))
                    if 1 <= num <= 100:
                        return num
                except ValueError:
                    continue

        return 10  # 默认值

    def _detect_scene(self, text: str) -> SceneType:
        """
        检测场景类型

        Args:
            text: 输入文本

        Returns:
            场景类型
        """
        text_lower = text.lower()

        keywords = {
            SceneType.BUSINESS_REPORT: ["汇报", "报告", "总结", "review", "report", "business", "工作"],
            SceneType.CAMPUS_DEFENSE: ["答辩", "论文", "毕业", "defense", "thesis", "校园"],
            SceneType.PRODUCT_PRESENTATION: ["产品", "宣讲", "演示", "product", "presentation", "介绍"],
            SceneType.TRAINING: ["培训", "教学", "教程", "training", "tutorial", "课程"],
            SceneType.CONFERENCE: ["会议", "演讲", "conference", "speech", "峰会"],
        }

        for scene, words in keywords.items():
            if any(word in text_lower for word in words):
                return scene

        return SceneType.OTHER

    def _detect_template_type(self, text: str) -> TemplateType:
        """
        检测模板类型

        Args:
            text: 输入文本

        Returns:
            模板类型
        """
        text_lower = text.lower()

        keywords = {
            TemplateType.BUSINESS: ["商务", "正式", "专业", "business", "formal", "professional"],
            TemplateType.ACADEMIC: ["学术", "科研", "academic", "research", "科学"],
            TemplateType.CREATIVE: ["创意", "活泼", "时尚", "creative", "vibrant", "fashion"],
            TemplateType.SIMPLE: ["简约", "简洁", "极简", "simple", "minimal", "clean"],
            TemplateType.TECH: ["科技", "技术", "tech", "technology", "科技感"],
        }

        for template, words in keywords.items():
            if any(word in text_lower for word in words):
                return template

        return TemplateType.BUSINESS  # 默认

    def _is_chinese(self, text: str) -> bool:
        """
        判断是否为中文

        Args:
            text: 输入文本

        Returns:
            是否为中文
        """
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        return chinese_chars > len(text) * 0.3

    def _fix_requirement(self, requirement: Requirement, errors: list) -> None:
        """
        修正需求中的错误

        Args:
            requirement: 需求对象
            errors: 错误列表
        """
        for error in errors:
            if "页数" in error:
                if requirement.page_num < 1:
                    requirement.page_num = 10
                elif requirement.page_num > 100:
                    requirement.page_num = 100

            elif "核心模块" in error:
                if len(requirement.core_modules) > requirement.page_num:
                    requirement.core_modules = requirement.core_modules[:requirement.page_num]


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    模型调用前的回调函数

    将用户输入添加到请求中
    """
    user_input = callback_context.user_content.parts[0].text
    callback_context.state["raw_user_input"] = user_input

    # 将用户输入添加到请求中
    llm_request.contents.append(
        types.Content(role="user", parts=[types.Part(text=user_input)])
    )

    logger.info(f"RequirementParserAgent processing: {user_input[:50]}...")
    return None


# 创建全局实例
requirement_parser_agent = RequirementParserAgent(
    before_model_callback=before_model_callback
)


if __name__ == "__main__":
    # 测试代码
    async def test_agent():
        import asyncio
        from google.adk.sessions import InMemorySessionService
        from google.adk.runners import Runner

        agent = requirement_parser_agent

        # 创建测试输入
        test_input = "做一份2025电商618销售复盘PPT，商务风模板，15页"

        print(f"Testing RequirementParserAgent with input: {test_input}")
        print("=" * 60)

        # 简单测试默认方法
        default_req = agent._get_default_requirement(test_input)
        print(f"Default requirement: {json.dumps(default_req, indent=2, ensure_ascii=False)}")

        print(f"\nExtracted page_num: {agent._extract_page_num(test_input)}")
        print(f"Detected scene: {agent._detect_scene(test_input)}")
        print(f"Detected template: {agent._detect_template_type(test_input)}")
        print(f"Is Chinese: {agent._is_chinese(test_input)}")

    asyncio.run(test_agent())
