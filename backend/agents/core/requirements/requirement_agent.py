"""
需求解析智能体 - LangChain 实现

该智能体解析用户输入，提取结构化的 PPT 生成需求。
使用 LangChain 模式，结合 LLM 链和 JSON 输出解析。
"""

import json
import logging
import os
from typing import Dict, Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI

from ...models.state import PPTGenerationState, update_state_progress
from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)


# Prompt template for requirement parsing
REQUIREMENT_PARSER_PROMPT = """你是一名专业的PPT需求分析专家。

你的任务是分析用户的自然语言输入，提取结构化的PPT生成需求。

用户输入：{user_input}

请按照以下JSON格式输出需求（不要使用markdown包裹，直接输出JSON）：
{{
    "ppt_topic": "PPT主题",
    "page_num": 页数（整数，10-30之间）,
    "language": "语言代码（ZH-CN或EN-US）",
    "template_type": "模板类型（business_template, academic_template, creative_template等）",
    "scene": "使用场景（business_report, academic_presentation, product_launch, training等）",
    "core_modules": ["核心模块1", "核心模块2"],
    "need_research": true/false,
    "style_preference": "风格偏好（professional, casual, creative等）",
    "color_scheme": "色彩方案建议（如果有）",
    "target_audience": "目标受众（如果有）"
}}

分析原则：
1. 如果用户指定了页数，使用用户指定的值；否则默认为10页
2. 检测输入语言：包含中文则为ZH-CN，否则为EN-US
3. 根据主题判断场景和模板类型
4. 如果主题需要专业知识（如技术、学术），设置need_research=true
5. 提取3-5个核心模块
"""


class RequirementParserAgent(BaseAgent):
    """
    需求解析智能体 - 使用BaseAgent重构版本

    职责：
    1. 解析用户自然语言输入
    2. 提取结构化的PPT生成需求
    3. 验证并填充默认值
    4. 应用用户偏好个性化（如果启用记忆）
    5. 缓存解析结果以避免重复解析

    特性：
    - 使用LangChain的Runnable链
    - 内置JSON输出解析
    - 降级策略：如果LLM解析失败，使用规则提取
    - 支持用户偏好个性化（需要启用记忆）
    """

    def __init__(
        self,
        model: Optional[ChatOpenAI] = None,
        temperature: float = 0.0,
        agent_name: str = "RequirementParserAgent",
        enable_memory: bool = False,  # 默认关闭，避免启动问题
    ):
        """
        初始化需求解析智能体

        Args:
            model: LangChain LLM实例
            temperature: 温度参数
            agent_name: Agent名称
            enable_memory: 是否启用记忆（默认关闭）
        """
        super().__init__(
            model=model or ChatOpenAI(model="gpt-4o-mini", temperature=temperature),
            temperature=temperature,
            agent_name=agent_name,
            enable_memory=enable_memory,
        )

        # 混入记忆功能（如果启用）
        self._memory_methods_bound = False
        if enable_memory:
            self._bind_memory_methods()

        # 创建解析链
        self._setup_parser_chain()

    def _bind_memory_methods(self):
        """绑定 MemoryAwareAgent 的方法"""
        try:
            from backend.memory import MemoryAwareAgent

            # 绑定方法
            self._get_memory = MemoryAwareAgent._get_memory.__get__(self, type(self))
            self.remember = MemoryAwareAgent.remember.__get__(self, type(self))
            self.recall = MemoryAwareAgent.recall.__get__(self, type(self))
            self.forget = MemoryAwareAgent.forget.__get__(self, type(self))
            self.apply_user_preferences_to_requirement = (
                MemoryAwareAgent.apply_user_preferences_to_requirement.__get__(self, type(self))
            )
            self.get_user_preferences = MemoryAwareAgent.get_user_preferences.__get__(
                self, type(self)
            )

            # 初始化 MemoryAwareAgent 属性
            self._task_id = None
            self._user_id = None
            self._session_id = None
            self._memory_manager = None
            self._user_pref_service = None
            self._MemoryScope = None

            self._memory_methods_bound = True
            logger.info(f"[{self.agent_name}] Memory methods bound")

        except ImportError as e:
            logger.warning(f"[{self.agent_name}] Cannot bind memory methods: {e}")

    @property
    def has_memory(self) -> bool:
        """检查是否有记忆功能"""
        if not getattr(self, "_memory_methods_bound", False):
            return False
        if not hasattr(self, "_memory_manager"):
            return False
        return self._memory_manager is not None

    @has_memory.setter
    def has_memory(self, value: bool):
        """兼容 BaseAgent 初始化时对 has_memory 的赋值"""
        self._has_memory_flag = bool(value)

    def _setup_parser_chain(self):
        """设置解析链"""
        prompt = ChatPromptTemplate.from_template(REQUIREMENT_PARSER_PROMPT)
        parser = JsonOutputParser()

        self.parser_chain = prompt | self.model | parser

    async def parse(self, user_input: str) -> Dict[str, Any]:
        """
        解析用户输入，提取结构化需求

        Args:
            user_input: 用户自然语言输入

        Returns:
            结构化需求字典
        """
        logger.info(f"[{self.agent_name}] Parsing: {user_input[:100]}...")

        try:
            # 使用LLM解析
            requirement = await self.parser_chain.ainvoke({"user_input": user_input})

            # 验证并填充默认值
            requirement = self._validate_and_fill_defaults(requirement)

            logger.info(f"[{self.agent_name}] Parsed: {requirement.get('ppt_topic')}")
            return requirement

        except Exception as e:
            logger.warning(f"[{self.agent_name}] LLM parsing failed: {e}, using fallback")
            # 降级：使用规则提取
            return self._fallback_parse(user_input)

    async def run(self, *args, **kwargs) -> Dict[str, Any]:
        """实现 BaseAgent 抽象接口"""
        if args and isinstance(args[0], dict):
            return await self.run_node(args[0])

        state = kwargs.get("state")
        if isinstance(state, dict):
            return await self.run_node(state)

        user_input = kwargs.get("user_input")
        if isinstance(user_input, str):
            return await self.parse(user_input)

        raise ValueError("RequirementParserAgent.run requires state dict or user_input string")

    def _validate_and_fill_defaults(self, requirement: Dict[str, Any]) -> Dict[str, Any]:
        """验证并填充默认值"""
        # 页数
        page_num = requirement.get("page_num")
        if not page_num or not isinstance(page_num, int) or page_num < 1:
            requirement["page_num"] = 10

        # 语言
        if not requirement.get("language"):
            topic = requirement.get("ppt_topic", "")
            has_chinese = any("\u4e00" <= c <= "\u9fff" for c in topic)
            requirement["language"] = "ZH-CN" if has_chinese else "EN-US"

        # 模板类型
        if not requirement.get("template_type"):
            requirement["template_type"] = "business_template"

        # 场景
        if not requirement.get("scene"):
            requirement["scene"] = "business_report"

        # 核心模块
        if not requirement.get("core_modules"):
            requirement["core_modules"] = []

        # 是否需要研究
        if "need_research" not in requirement:
            requirement["need_research"] = False

        return requirement

    def _fallback_parse(self, user_input: str) -> Dict[str, Any]:
        """降级解析：使用规则提取"""
        has_chinese = any("\u4e00" <= c <= "\u9fff" for c in user_input)

        return {
            "ppt_topic": user_input[:100],
            "page_num": 10,
            "language": "ZH-CN" if has_chinese else "EN-US",
            "template_type": "business_template",
            "scene": "business_report",
            "core_modules": [],
            "need_research": False,
            "style_preference": "professional",
        }

    async def run_node(self, state: PPTGenerationState) -> Dict[str, Any]:
        """
        执行需求解析节点

        This method now applies user preferences for personalization:
        1. Parses user input to extract explicit requirements
        2. Applies user preferences (language, page_num, tone, template_type)
        3. Records user interaction for learning

        Args:
            state: 当前状态

        Returns:
            更新后的状态，包含应用了用户偏好的需求
        """
        user_input = state.get("user_input", "")

        if not user_input:
            logger.warning(f"[{self.agent_name}] No user_input")
            raise ValueError("Missing user_input")

        # Step 1: Initialize memory if enabled
        if self.enable_memory:
            self._get_memory(state)
            logger.debug(f"[{self.agent_name}] Memory initialized")

        # Step 2: Parse user input to extract explicit requirements
        base_requirements = await self.parse(user_input)

        logger.info(
            f"[{self.agent_name}] Parsed base requirements: "
            f"topic={base_requirements.get('ppt_topic')}, "
            f"pages={base_requirements.get('page_num')}, "
            f"language={base_requirements.get('language')}"
        )

        # Step 3: Apply user preferences (if memory enabled)
        if self.enable_memory:
            personalized_requirements = await self.apply_user_preferences_to_requirement(
                base_requirements
            )

            logger.info(
                f"[{self.agent_name}] Applied user preferences: "
                f"language={personalized_requirements.get('language')}, "
                f"pages={personalized_requirements.get('page_num')}, "
                f"tone={personalized_requirements.get('tone')}, "
                f"template={personalized_requirements.get('template_type')}"
            )
        else:
            personalized_requirements = base_requirements

        logger.info(f"[{self.agent_name}] Completed: {personalized_requirements.get('ppt_topic')}")

        return {"structured_requirements": personalized_requirements}


# 工厂函数
def create_requirement_parser(
    model: Optional[ChatOpenAI] = None,
    temperature: float = 0.0,
    enable_memory: bool = False,
) -> RequirementParserAgent:
    """
    创建需求解析智能体

    Args:
        model: LangChain LLM实例
        temperature: 温度参数
        enable_memory: 是否启用记忆

    Returns:
        RequirementParserAgent实例
    """
    return RequirementParserAgent(
        model=model,
        temperature=temperature,
        enable_memory=enable_memory,
    )


if __name__ == "__main__":
    import asyncio

    async def test():
        # 测试需求解析
        test_inputs = [
            "生成一份关于人工智能的PPT，15页，学术风格",
            "Create a Q3 sales report presentation",
            "帮我做一个产品介绍PPT",
        ]

        agent = create_requirement_parser()

        for test_input in test_inputs:
            print(f"\nInput: {test_input}")
            result = await agent.parse(test_input)
            print(f"Result: {json.dumps(result, indent=2, ensure_ascii=False)}")

    asyncio.run(test())
