"""
Requirement Parser Agent with Memory Integration

将用户偏好系统集成到需求解析智能体中，实现：
1. 加载用户历史偏好（页数、语言、风格等）
2. 自动应用偏好到当前任务
3. 学习新的偏好模式
"""

import json
import logging
import os
from typing import AsyncGenerator, Optional, Dict, Any

from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types
from google.adk.events.event import Event

# 导入基础需求解析Agent
from .requirement_parser_agent import (
    RequirementParserAgent,
    REQUIREMENT_PARSER_PROMPT,
    before_model_callback,
)

# 导入领域模型
from domain.models import Requirement

# 导入记忆适配器
from ..base_agent_with_memory import AgentMemoryMixin

logger = logging.getLogger(__name__)

class RequirementParserAgentWithMemory(AgentMemoryMixin, RequirementParserAgent):
    """
    带记忆功能的需求解析智能体

    扩展功能:
    1. 用户偏好加载：自动加载用户历史偏好
    2. 偏好自动应用：将偏好应用到当前需求解析
    3. 偏好学习：从新的解析结果中学习偏好
    4. 偏好统计：统计用户常用配置
    """

    # 偏好映射配置
    PREFERENCE_MAPPING = {
        "default_slides": "page_num",
        "language": "language",
        "style_preference": "style_preference",
        "color_scheme": "color_scheme",
        "template_type": "template_type",
        "scene": "scene",
        "industry": "industry",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 配置
        self.enable_preference_learning = os.getenv(
            "ENABLE_PREFERENCE_LEARNING", "true"
        ).lower() == "true"
        self.min_samples_for_learning = int(
            os.getenv("MIN_SAMPLES_FOR_LEARNING", "3")
        )

        # 统计信息
        self.stats = {
            "preference_hits": 0,
            "preference_misses": 0,
            "learned_preferences": 0,
        }

        logger.info(
            f"[{self.agent_name}] 初始化完成: "
            f"learning={self.enable_preference_learning}, "
            f"min_samples={self.min_samples_for_learning}"
        )

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        执行需求解析（带记忆）

        覆盖父类方法，添加用户偏好逻辑
        """
        # 设置上下文
        self._setup_context(ctx)

        try:
            # ========== 1. 加载用户偏好 ==========
            user_id = self._get_user_id()
            user_preferences = await self.get_user_preferences(user_id)

            # ========== 2. 应用用户偏好到session state ==========
            await self._apply_user_preferences(ctx, user_preferences)

            # ========== 3. 执行原有的解析逻辑 ==========
            user_input = ctx.user_content.parts[0].text
            logger.info(
                f"[{self.agent_name}] received input: {user_input[:100]}..."
            )

            # 调用LLM解析
            async for event in super()._run_async_impl(ctx):
                yield event

            # ========== 4. 获取解析结果 ==========
            requirement_dict = ctx.session.state.get("structured_requirements", {})

            if requirement_dict:
                # ========== 5. 学习新的偏好 ==========
                await self._learn_from_requirement(
                    user_id, requirement_dict, user_input
                )

                # ========== 6. 记录决策 ==========
                await self._record_parse_decision(
                    user_id, requirement_dict, user_preferences
                )

                # 产生完成事件
                yield Event(
                    author=self.name,
                    content=types.Content(
                        parts=[types.Part(
                            text=f"需求解析完成（带记忆）：\n"
                            f"- 主题: {requirement_dict.get('ppt_topic', '')}\n"
                            f"- 页数: {requirement_dict.get('page_num', '')}\n"
                            f"- 模板: {requirement_dict.get('template_type', '')}\n"
                            f"- 偏好命中: {self.stats['preference_hits']}\n"
                            f"- 需要研究: {requirement_dict.get('need_research', False)}"
                        )]
                    ),
                )

        except Exception as e:
            logger.error(
                f"[{self.agent_name}] failed: {e}", exc_info=True
            )
            # 降级到父类逻辑
            async for event in super()._run_async_impl(ctx):
                yield event

    async def _apply_user_preferences(
        self,
        ctx: InvocationContext,
        user_preferences: Dict[str, Any],
    ):
        """
        应用用户偏好到上下文

        Args:
            ctx: 调用上下文
            user_preferences: 用户偏好字典
        """
        if not user_preferences:
            self.stats["preference_misses"] += 1
            return

        applied_count = 0

        # 应用页数偏好
        if "default_slides" in user_preferences:
            default_slides = user_preferences["default_slides"]
            ctx.session.state["slides_plan_num"] = default_slides
            logger.info(
                f"[{self.agent_name}] 应用用户偏好页数: {default_slides}"
            )
            applied_count += 1

        # 应用语言偏好
        if "language" in user_preferences:
            language = user_preferences["language"]
            ctx.session.state["language"] = language
            logger.info(f"[{self.agent_name}] 应用用户偏好语言: {language}")
            applied_count += 1

        # 应用模板类型偏好
        if "template_type" in user_preferences:
            template_type = user_preferences["template_type"]
            ctx.session.state["template_type"] = template_type
            logger.info(
                f"[{self.agent_name}] 应用用户偏好模板: {template_type}"
            )
            applied_count += 1

        # 应用风格偏好
        if "style_preference" in user_preferences:
            style = user_preferences["style_preference"]
            ctx.session.state["style_preference"] = style
            logger.info(f"[{self.agent_name}] 应用用户偏好风格: {style}")
            applied_count += 1

        # 应用配色方案偏好
        if "color_scheme" in user_preferences:
            color = user_preferences["color_scheme"]
            ctx.session.state["color_scheme"] = color
            logger.info(f"[{self.agent_name}] 应用用户偏好配色: {color}")
            applied_count += 1

        if applied_count > 0:
            self.stats["preference_hits"] += applied_count
            logger.info(
                f"[{self.agent_name}] 共应用了 {applied_count} 个用户偏好"
            )

    async def _learn_from_requirement(
        self,
        user_id: str,
        requirement: Dict[str, Any],
        user_input: str,
    ):
        """
        从需求解析结果中学习用户偏好

        Args:
            user_id: 用户ID
            requirement: 需求字典
            user_input: 用户原始输入
        """
        if not self.enable_preference_learning:
            return

        updates = {}

        # 学习页数偏好
        page_num = requirement.get("page_num")
        if page_num and page_num > 0:
            # 增加页数计数
            await self.increment_preference_counter(
                user_id=user_id,
                preference_key=f"page_num_{page_num}",
            )

            # 更新最常用页数
            most_common_page_num = await self._get_most_common_page_num(user_id)
            if most_common_page_num and most_common_page_num != page_num:
                updates["default_slides"] = most_common_page_num

        # 学习语言偏好
        language = requirement.get("language")
        if language:
            await self.increment_preference_counter(
                user_id=user_id,
                preference_key=f"language_{language}",
            )

            most_common_language = await self._get_most_common_language(user_id)
            if most_common_language:
                updates["language"] = most_common_language

        # 学习模板类型偏好
        template_type = requirement.get("template_type")
        if template_type:
            await self.increment_preference_counter(
                user_id=user_id,
                preference_key=f"template_type_{template_type}",
            )

            most_common_template = await self._get_most_common_template(user_id)
            if most_common_template:
                updates["template_type"] = most_common_template

        # 学习风格偏好
        style = requirement.get("style_preference")
        if style:
            updates["style_preference"] = style

        # 学习配色方案偏好
        color_scheme = requirement.get("color_scheme")
        if color_scheme:
            updates["color_scheme"] = color_scheme

        # 批量更新偏好
        if updates:
            await self.update_user_preferences(user_id=user_id, updates=updates)
            self.stats["learned_preferences"] += len(updates)
            logger.info(
                f"[{self.agent_name}] 学习了 {len(updates)} 个新偏好: {list(updates.keys())}"
            )

    async def _get_most_common_page_num(self, user_id: str) -> Optional[int]:
        """获取用户最常用的页数"""
        # 这里简化实现，实际可以从用户偏好服务中获取统计
        # 可以通过查询所有page_num_*计数器来确定
        # 暂时返回None，让具体实现中调用用户偏好服务的API
        return None

    async def _get_most_common_language(self, user_id: str) -> Optional[str]:
        """获取用户最常用的语言"""
        # 同上
        return None

    async def _get_most_common_template(self, user_id: str) -> Optional[str]:
        """获取用户最常用的模板类型"""
        # 同上
        return None

    async def _record_parse_decision(
        self,
        user_id: str,
        requirement: Dict[str, Any],
        user_preferences: Dict[str, Any],
    ):
        """
        记录解析决策

        Args:
            user_id: 用户ID
            requirement: 需求字典
            user_preferences: 用户偏好字典
        """
        await self.record_decision(
            decision_type="requirement_parse",
            selected_action=f"parsed_{requirement.get('page_num')}_pages",
            context={
                "user_id": user_id,
                "ppt_topic": requirement.get("ppt_topic", ""),
                "page_num": requirement.get("page_num"),
                "template_type": requirement.get("template_type"),
                "preferences_applied": self.stats["preference_hits"],
            },
            reasoning=f"根据用户偏好解析需求，应用了{self.stats['preference_hits']}个偏好",
            confidence_score=0.85,
        )

    def _setup_context(self, ctx: InvocationContext):
        """设置上下文信息"""
        task_id = ctx.session.state.get("task_id")
        user_id = ctx.session.state.get("user_id", "anonymous")

        self.set_context(
            task_id=task_id,
            user_id=user_id,
            session_id=task_id,
        )

# 创建全局实例
requirement_parser_agent_with_memory = RequirementParserAgentWithMemory(
    before_model_callback=before_model_callback
)

if __name__ == "__main__":
    # 测试代码
    async def test_agent():
        import asyncio

        agent = requirement_parser_agent_with_memory

        print(f"Testing {agent.__class__.__name__}")
        print("=" * 60)
        print(f"Agent name: {agent.name}")
        print(f"Memory enabled: {agent.is_memory_enabled()}")
        print(f"Preference learning: {agent.enable_preference_learning}")
        print(f"Min samples for learning: {agent.min_samples_for_learning}")

    asyncio.run(test_agent())
