"""
需求解析智能体 - 精简版本（符合测试文档v2.0要求）

核心职责：
1. 解析用户自然语言输入，提取结构化需求
2. 混合解析策略：LLM为主，规则降级为辅
3. 返回PPTRequirement模型（Pydantic验证）
4. 支持超时控制和重试机制

移除功能（保持精简）：
- 记忆功能（不在需求中）
- 用户偏好个性化（不在需求中）

符合测试文档v2.0要求：
✅ 异步方法支持
✅ 超时控制（timeout参数）
✅ 重试机制（max_retries参数）
✅ 验证与推断方法（_validate_and_infer, _infer_defaults）
✅ 工作流节点方法（run, run_node）
"""

import asyncio
import logging
import re
from typing import Optional, Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from .models import PPTRequirement, Language, TemplateType, Scene, Tone
from .prompts import REQUIREMENT_PARSER_PROMPT
from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)


class RequirementParserAgent(BaseAgent):
    """
    需求解析智能体 - 精简版本

    核心功能：
    1. 解析用户自然语言输入
    2. 提取结构化的PPT生成需求
    3. 使用Pydantic验证并返回PPTRequirement模型

    解析策略：
    - 优先使用LLM解析（更准确）
    - 失败时降级到规则提取（更可靠）
    """

    def __init__(
        self,
        model: Optional[ChatOpenAI] = None,
        temperature: float = 0.0,
        agent_name: str = "RequirementParserAgent",
        enable_memory: bool = False,
        timeout: int = 10,
        max_retries: int = 1,
    ):
        """
        初始化需求解析智能体

        Args:
            model: LangChain LLM实例
            temperature: 温度参数（0.0确保确定性输出）
            agent_name: Agent名称
            enable_memory: 是否启用记忆（保留兼容性）
            timeout: LLM调用超时时间（秒）
            max_retries: LLM调用失败时的重试次数
        """
        # 调用父类BaseAgent的初始化
        super().__init__(
            model=model,
            temperature=temperature,
            agent_name=agent_name,
            enable_memory=enable_memory,
        )

        # 添加测试文档要求的参数
        self.timeout = timeout
        self.max_retries = max_retries

        # 创建解析链
        self._setup_parser_chain()

        logger.info(
            f"[{self.agent_name}] Initialized with model={self.model.model_name}, "
            f"timeout={timeout}s, max_retries={max_retries}"
        )

    def _setup_parser_chain(self):
        """设置LLM解析链"""
        prompt = ChatPromptTemplate.from_template(REQUIREMENT_PARSER_PROMPT)
        parser = JsonOutputParser()

        self.parser_chain = prompt | self.model | parser

    async def parse(self, user_input: str) -> PPTRequirement:
        """
        解析用户输入，返回PPTRequirement模型

        解析策略（带重试）：
        1. 使用LLM解析（带重试机制）
        2. 失败后降级到规则提取
        3. 使用Pydantic验证并返回模型

        Args:
            user_input: 用户自然语言输入

        Returns:
            PPTRequirement: 验证后的需求模型

        Raises:
            ValueError: 输入为空
        """
        if not user_input or not user_input.strip():
            raise ValueError("用户输入不能为空")

        logger.info(f"[{self.agent_name}] Parsing: {user_input[:100]}...")

        # 策略1: 使用LLM解析（带重试机制）
        requirement_dict = None
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                requirement_dict = await self._parse_with_llm(user_input)
                logger.info(
                    f"[{self.agent_name}] LLM parsing succeeded "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )
                break

            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(
                        f"[{self.agent_name}] LLM parsing failed "
                        f"(attempt {attempt + 1}/{self.max_retries + 1}): {e}, retrying..."
                    )
                    await asyncio.sleep(0.5 * (attempt + 1))  # 指数退避
                else:
                    logger.warning(
                        f"[{self.agent_name}] LLM parsing failed after "
                        f"{self.max_retries + 1} attempts: {e}, using fallback"
                    )

        # 如果LLM解析失败，使用降级策略
        if requirement_dict is None:
            requirement_dict = self._parse_with_fallback(user_input)

        # 策略2: 使用Pydantic验证并创建模型
        try:
            requirement = PPTRequirement(**requirement_dict)
            language_value = (
                requirement.language.value
                if hasattr(requirement.language, "value")
                else str(requirement.language)
            )
            logger.info(
                f"[{self.agent_name}] Parsed: {requirement.ppt_topic}, "
                f"{requirement.page_num}页, {language_value}"
            )
            return requirement

        except Exception as e:
            logger.error(f"[{self.agent_name}] Pydantic validation failed: {e}")
            # 如果Pydantic验证失败，使用验证推断方法
            try:
                return self._validate_and_infer(requirement_dict)
            except Exception as e2:
                logger.error(f"[{self.agent_name}] Validation also failed: {e2}")
                # 最后兜底：创建基本需求
                return self._create_basic_requirement(user_input)

    def _infer_defaults(self, raw_dict: dict) -> dict:
        """
        推断缺失字段的默认值

        Args:
            raw_dict: 原始字典

        Returns:
            填充默认值后的字典
        """
        # 推断 template_type
        if "template_type" not in raw_dict or not raw_dict["template_type"]:
            raw_dict["template_type"] = "business_template"

        # 推断 scene
        if "scene" not in raw_dict or not raw_dict["scene"]:
            raw_dict["scene"] = "business_report"

        # 推断 tone
        if "tone" not in raw_dict or not raw_dict["tone"]:
            raw_dict["tone"] = "professional"

        # 推断 core_modules
        if "core_modules" not in raw_dict:
            raw_dict["core_modules"] = []

        # 推断 need_research
        if "need_research" not in raw_dict:
            raw_dict["need_research"] = False

        return raw_dict

    def _validate_and_infer(self, raw_dict: dict) -> PPTRequirement:
        """
        验证并推断原始字典，返回PPTRequirement模型

        功能：
        1. 填充缺失字段的默认值
        2. 修正超出范围的值（如page_num）
        3. 验证枚举值的有效性
        4. 创建PPTRequirement模型

        Args:
            raw_dict: 原始字典

        Returns:
            验证后的PPTRequirement模型

        Raises:
            ValidationError: 验证失败
        """
        # 先填充默认值
        raw_dict = self._infer_defaults(raw_dict.copy())

        # 修正 page_num 超出范围的情况
        if "page_num" in raw_dict:
            page_num = raw_dict["page_num"]
            if isinstance(page_num, int):
                # 修正到 5-50 范围
                raw_dict["page_num"] = max(5, min(50, page_num))
            else:
                # 如果不是整数，使用默认值
                raw_dict["page_num"] = 10

        # 确保 language 是枚举对象
        if "language" in raw_dict:
            lang_value = raw_dict["language"]
            if isinstance(lang_value, str):
                try:
                    raw_dict["language"] = Language(lang_value)
                except ValueError:
                    # 无效枚举值，根据主题推断
                    topic = raw_dict.get("ppt_topic", "")
                    has_chinese = any("\u4e00" <= c <= "\u9fff" for c in topic)
                    raw_dict["language"] = Language.ZH_CN if has_chinese else Language.EN_US

        # 创建 PPTRequirement 模型
        return PPTRequirement(**raw_dict)

    async def _parse_with_llm(self, user_input: str) -> dict:
        """
        使用LLM解析用户输入（带超时控制）

        Args:
            user_input: 用户输入

        Returns:
            解析后的字典

        Raises:
            asyncio.TimeoutError: LLM调用超时
            Exception: LLM调用失败或返回无效JSON
        """
        # 使用 asyncio.wait_for 实现超时控制
        result = await asyncio.wait_for(
            self.parser_chain.ainvoke({"user_input": user_input}),
            timeout=self.timeout,
        )

        if not isinstance(result, dict):
            raise ValueError(f"LLM返回非字典类型: {type(result)}")

        return result

    def _fallback_parse(self, user_input: str) -> dict:
        """
        降级解析：使用规则提取（别名方法）

        为了兼容测试代码，提供 _fallback_parse 作为 _parse_with_fallback 的别名

        Args:
            user_input: 用户输入

        Returns:
            解析后的字典
        """
        return self._parse_with_fallback(user_input)

    def _parse_with_fallback(self, user_input: str) -> dict:
        """
        降级解析：使用规则提取（不依赖LLM）

        功能：
        1. 主题提取：取前100字符
        2. 页数提取：正则匹配数字+页/page
        3. 语言检测：中文字符检测
        4. 场景匹配：关键词识别
        5. 页数限制：自动修正到5-50范围

        Args:
            user_input: 用户输入

        Returns:
            解析后的字典
        """
        # 1. 主题提取（前100字符）
        ppt_topic = user_input[:100].strip()

        # 2. 页数提取（正则匹配）
        page_num = 10  # 默认值
        page_patterns = [
            r'(\d+)\s*页',           # 15页
            r'(\d+)\s*page',         # 15page
            r'(\d+)\s*pages',        # 15pages
            r'page\s*:\s*(\d+)',     # page:15
            r'页\s*[:：]\s*(\d+)',   # 页：15
        ]
        for pattern in page_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                try:
                    extracted_page = int(match.group(1))
                    # 页数限制（5-50范围）
                    page_num = max(5, min(50, extracted_page))
                    break
                except (ValueError, IndexError):
                    pass

        # 3. 语言检测（检查中文字符）
        has_chinese = any("\u4e00" <= c <= "\u9fff" for c in user_input)
        language = "ZH-CN" if has_chinese else "EN-US"

        # 4. 场景匹配（关键词识别）
        template_type = "business_template"
        scene = "business_report"
        tone = "professional"
        need_research = False

        # 转换为小写进行匹配
        input_lower = user_input.lower()

        # 学术场景识别
        academic_keywords = [
            '学术', '研究', '论文', '科研', '实验', '理论',
            'academic', 'research', 'paper', 'thesis', 'study'
        ]
        if any(keyword in input_lower for keyword in academic_keywords):
            template_type = "academic_template"
            scene = "academic_presentation"
            need_research = True

        # 创意场景识别
        creative_keywords = [
            '创意', '设计', '艺术', '创新', '灵感',
            'creative', 'design', 'art', 'innovative', 'inspiration'
        ]
        if any(keyword in input_lower for keyword in creative_keywords):
            template_type = "creative_template"
            tone = "creative"
            if scene == "business_report":  # 如果没有被学术覆盖
                scene = "product_launch"

        # 返回字典（包含所有必需字段）
        return {
            "ppt_topic": ppt_topic,
            "page_num": page_num,
            "language": language,
            "template_type": template_type,
            "scene": scene,
            "tone": tone,
            "core_modules": [],
            "need_research": need_research,
        }

    def _create_basic_requirement(self, user_input: str) -> PPTRequirement:
        """
        创建基本需求（当所有解析策略都失败时）

        Args:
            user_input: 用户输入

        Returns:
            基本的PPTRequirement
        """
        has_chinese = any("\u4e00" <= c <= "\u9fff" for c in user_input)

        return PPTRequirement(
            ppt_topic=user_input[:100],
            page_num=10,
            language=Language.ZH_CN if has_chinese else Language.EN_US,
        )

    async def run_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        工作流节点方法：解析状态中的用户输入

        Args:
            state: 包含 user_input 的状态字典

        Returns:
            更新后的状态字典，包含解析结果

        Raises:
            ValueError: 如果 state 中缺少 user_input
        """
        user_input = state.get("user_input")
        if not user_input:
            raise ValueError("Missing user_input in state")

        # 解析需求
        requirement = await self.parse(user_input)

        # 将结果添加到状态中
        state["requirement"] = requirement
        state["structured_requirements"] = requirement.model_dump()

        return state

    async def run(self, *args, **kwargs) -> PPTRequirement:
        """
        Agent主要执行方法

        支持多种调用方式：
        1. run(user_input="...") -> PPTRequirement
        2. run(state={...}) -> Dict
        3. await agent("...") -> PPTRequirement

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            解析结果
        """
        # 如果传入了 state，调用 run_node
        if "state" in kwargs:
            return await self.run_node(kwargs["state"])

        if args and isinstance(args[0], dict):
            return await self.run_node(args[0])

        # 否则解析 user_input
        user_input = kwargs.get("user_input")
        if user_input:
            return await self.parse(user_input)

        if args and isinstance(args[0], str):
            return await self.parse(args[0])

        raise ValueError(
            "RequirementParserAgent.run requires user_input (str) or state (dict)"
        )


# 工厂函数
def create_requirement_parser(
    model: Optional[ChatOpenAI] = None,
    temperature: float = 0.0,
    agent_name: str = "RequirementParserAgent",
    enable_memory: bool = False,
    timeout: int = 10,
    max_retries: int = 1,
) -> RequirementParserAgent:
    """
    创建需求解析智能体

    Args:
        model: LangChain LLM实例
        temperature: 温度参数
        agent_name: Agent名称
        enable_memory: 是否启用记忆
        timeout: LLM调用超时时间（秒）
        max_retries: LLM调用失败时的重试次数

    Returns:
        RequirementParserAgent实例
    """
    return RequirementParserAgent(
        model=model,
        temperature=temperature,
        agent_name=agent_name,
        enable_memory=enable_memory,
        timeout=timeout,
        max_retries=max_retries,
    )
