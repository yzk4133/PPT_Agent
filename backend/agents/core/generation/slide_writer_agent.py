"""
Slide Writer Agent - 共享实现
负责生成PPT内容，包括单个幻灯片生成和循环生成所有幻灯片
"""

import json
import logging
import os
import sys
from typing import Dict, List, Any, AsyncGenerator, Optional
from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents import LoopAgent, BaseAgent
from google.adk.events import Event, EventActions
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse

# 导入配置和模型创建（从common模块）
from infrastructure.config.common_config import get_config
from infrastructure.llm.common_model_factory import create_model_with_fallback, create_model_with_fallback_simple
from utils.context_compressor import ContextCompressor

# 导入新的 MCP 工具
from agents.tools.mcp import search_images

# 导入PromptManager用于获取提示词模板
from prompts import PromptManager

# 导入CHECKER_AGENT_PROMPT
from prompts.templates.generation import CHECKER_AGENT_PROMPT

logger = logging.getLogger(__name__)

# ==================== Prompts ====================
# 使用PromptManager获取提示词模板（带有模板变量）
# 注意：这些模板包含占位符，需要在运行时填充
XML_PPT_AGENT_NEXT_PAGE_PROMPT_TEMPLATE = PromptManager.get_xml_ppt_generation_prompt
CHECKER_AGENT_PROMPT_TEMPLATE = PromptManager.get_checker_prompt

# ==================== Callback Functions ====================
def my_before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """模型前的回调"""
    agent_name = callback_context.agent_name
    history_length = len(llm_request.contents)
    metadata = callback_context.state.get("metadata")
    print(
        f"调用了{agent_name}模型前的callback, 现在Agent共有{history_length}条历史记录,metadata数据为：{metadata}"
    )
    logger.info(
        f"调用了{agent_name}模型前的callback, 现在Agent共有{history_length}条历史记录,metadata数据为：{metadata}"
    )
    return None

def my_after_model_callback(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """模型后的回调"""
    agent_name = callback_context.agent_name
    response_parts = llm_response.content.parts
    part_texts = []
    for one_part in response_parts:
        part_text = one_part.text
        if part_text is not None:
            part_texts.append(part_text)
    part_text_content = "\n".join(part_texts)
    metadata = callback_context.state.get("metadata")
    print(
        f"调用了{agent_name}模型后的callback, 这次模型回复{response_parts}条信息,metadata数据为：{metadata},回复内容是: {part_text_content}"
    )
    logger.info(
        f"调用了{agent_name}模型后的callback, 这次模型回复{response_parts}条信息,metadata数据为：{metadata},回复内容是: {part_text_content}"
    )
    return None

def my_writer_before_agent_callback(callback_context: CallbackContext) -> None:
    """
    在调用LLM之前，从会话状态中获取当前幻灯片计划，并格式化LLM输入。

    改进：使用上下文压缩器减少 token 消耗
    """
    current_slide_index: int = callback_context.state.get(
        "current_slide_index", 0
    )
    slides_plan_num = callback_context.state.get("slides_plan_num")

    research_outputs_content: str = callback_context.state.get(
        "research_outputs_content"
    )
    if not research_outputs_content:
        raise ValueError(
            "research_outputs_content is missing in session state. Please ensure research_outputs_content ran successfully."
        )

    formatted_slide_outline = f"Page {current_slide_index + 1}"

    print(f"--- 正在生成第{current_slide_index + 1}页PPT ---")
    logger.info(f"--- 正在生成第{current_slide_index + 1}页PPT ---")
    page_num = f"{current_slide_index + 1}/{slides_plan_num}"

    callback_context.state["research_doc"] = research_outputs_content
    callback_context.state["page_num"] = page_num

    rewrite_reason = callback_context.state.get("rewrite_reason")
    if rewrite_reason:
        print(f"[PPTWriterSubAgent] 上一轮校验失败，收到重写建议: {rewrite_reason}")
        callback_context.state["other_suggestion"] = (
            f"⚠️ 上一轮审核未通过，请特别注意以下问题：" + rewrite_reason
        )
        callback_context.state["rewrite_reason"] = ""
    else:
        callback_context.state["other_suggestion"] = ""

    # 第一页和其它页只有历史记录和页码不一样
    if current_slide_index == 0:
        callback_context.state["history_slides_xml"] = ""
        callback_context.state["context_compressor"] = ContextCompressor(
            max_history_slides=3,
            include_all_titles=True,
            track_duplicates=True
        )
    else:
        all_generated_slides_content: List[str] = callback_context.state.get(
            "generated_slides_content", []
        )

        compressor: ContextCompressor = callback_context.state.get("context_compressor")
        if not compressor:
            compressor = ContextCompressor(max_history_slides=3)
            callback_context.state["context_compressor"] = compressor

        history_slides_xml = compressor.compress_history(
            all_generated_slides_content,
            current_slide_index
        )

        original_length = len("\n\n".join(all_generated_slides_content))
        compressed_length = len(history_slides_xml)
        savings = compressor.get_token_savings(original_length, compressed_length)

        logger.info(
            f"📊 上下文压缩: 原始={savings['original_chars']}字符 "
            f"→ 压缩={savings['compressed_chars']}字符 "
            f"(节省 {savings['saved_percentage']}%, "
            f"约 {savings['estimated_saved_tokens']} tokens)"
        )

        callback_context.state["history_slides_xml"] = history_slides_xml

    return None

def my_after_agent_callback(callback_context: CallbackContext) -> None:
    """
    在LLM生成内容后，将其存储到会话状态中。供下一页ppt生成使用
    """
    model_last_output_content = callback_context._invocation_context.session.events[-1]
    response_parts = model_last_output_content.content.parts
    part_texts = []
    for one_part in response_parts:
        part_text = one_part.text
        if part_text is not None:
            part_texts.append(part_text)
    part_text_content = "\n".join(part_texts)

    all_generated_slides_content: List[str] = callback_context.state.get(
        "generated_slides_content", []
    )
    all_generated_slides_content.append(part_text_content)

    callback_context.state["generated_slides_content"] = all_generated_slides_content
    print(
        f"--- Stored content for slide {callback_context.state.get('current_slide_index', 0) + 1} ---"
    )

# ==================== Agents ====================
class PPTWriterSubAgent(LlmAgent):
    """PPT写入子Agent"""

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        slides_plan_num: int = ctx.session.state.get("slides_plan_num")
        current_slide_index: int = ctx.session.state.get("current_slide_index", 0)
        ctx.session.state["_events_before_ppt_writer"] = len(ctx.session.events)

        if current_slide_index == 0:
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[
                        types.Part(
                            text="""```xml
<PRESENTATION>
"""
                        )
                    ]
                ),
            )

        async for event in super()._run_async_impl(ctx):
            print(f"{self.name} 收到事件：{event}")
            logger.info(f"{self.name} 收到事件：{event}")
            yield event

        if current_slide_index == slides_plan_num - 1:
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[
                        types.Part(
                            text="""
</PRESENTATION>```"""
                        )
                    ]
                ),
            )

ppt_writer_sub_agent = PPTWriterSubAgent(
    model="deepseek-chat",  # Simple model string for litellm
    name="PPTWriterSubAgent",
    description="根据每一页的幻灯片计划内容，写出完整的XML格式的PPT单页内容",
    instruction=XML_PPT_AGENT_NEXT_PAGE_PROMPT_TEMPLATE(),
    before_agent_callback=my_writer_before_agent_callback,
    after_agent_callback=my_after_agent_callback,
    before_model_callback=my_before_model_callback,
    after_model_callback=my_after_model_callback,
    tools=[search_images],  # 使用新的 MCP 工具
)

class PPTCheckerAgent(LlmAgent):
    """PPT检查Agent"""

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        current_slide_index: int = ctx.session.state.get("current_slide_index", 0)
        generated_slides_content: List[str] = ctx.session.state.get(
            "generated_slides_content", []
        )
        rewrite_retry_count_map: Dict[int, int] = ctx.session.state.get(
            "rewrite_retry_count_map", {}
        )

        if current_slide_index >= len(generated_slides_content):
            print(f"[PPTCheckerAgent] 没有找到当前页内容 index={current_slide_index}")
            yield Event(author=self.name, actions=EventActions())
            return

        current_slide = generated_slides_content[current_slide_index]
        history_slides = "\n\n".join(generated_slides_content[:current_slide_index])
        ctx.session.state["_events_before_ppt_checker"] = len(ctx.session.events)
        ctx.session.state["slide_to_check"] = current_slide
        ctx.session.state["history_slides"] = history_slides

        async for event in super()._run_async_impl(ctx):
            print(f"{self.name} 检查结果事件：{event}")
            result = event.content.parts[0].text.strip()

            if "需要重写" in result:
                retry_count = rewrite_retry_count_map.get(current_slide_index, 0)
                if retry_count < 3:
                    ctx.session.state["rewrite_reason"] = result
                    print(
                        f"[PPTCheckerAgent] 第 {retry_count + 1} 次尝试重写 slide {current_slide_index + 1}"
                    )
                    ctx.session.state["generated_slides_content"].pop()
                    if current_slide_index == 0:
                        ctx.session.state["current_slide_index"] = -1
                    else:
                        ctx.session.state["current_slide_index"] = (
                            current_slide_index - 1
                        )
                    rewrite_retry_count_map[current_slide_index] = retry_count + 1
                    ctx.session.state["rewrite_retry_count_map"] = (
                        rewrite_retry_count_map
                    )
                else:
                    print(
                        f"[PPTCheckerAgent] 第 {retry_count} 次重写失败，已达最大次数，跳过当前页"
                    )
                    yield Event(
                        author=self.name,
                        content=types.Content(
                            parts=[
                                types.Part(
                                    text="写失败，已达最大次数，跳过当前页检查，使用最后一次生成的结果"
                                )
                            ]
                        ),
                    )

            yield event

ppt_checker_agent = PPTCheckerAgent(
    model="deepseek-chat",  # Simple model string for litellm
    name="PPTCheckerAgent",
    description="检查幻灯片内容是否合格",
    instruction=CHECKER_AGENT_PROMPT,
)

def my_super_before_agent_callback(callback_context: CallbackContext):
    """
    在Loop Agent调用之前，进行数据处理
    """
    slides_plan_num = callback_context.state.get("slides_plan_num")
    if slides_plan_num is None:
        print(f"slides_plan_num没有设置，设定默认值: {slides_plan_num}")
        logger.info(f"slides_plan_num没有设置，设定默认值: {slides_plan_num}")
        slides_plan_num = 10
    callback_context.state["slides_plan_num"] = slides_plan_num

    if "rewrite_retry_count_map" not in callback_context.state:
        callback_context.state["rewrite_retry_count_map"] = {}

    research_output_keys = callback_context.state.get("research_output_keys", [])
    assert (
        len(research_output_keys) > 0
    ), "没有获取到research_output_keys，请检查research agent的输出代码"

    research_outputs = []
    for research_output_key in research_output_keys:
        research_output = callback_context.state.get(research_output_key, "")
        assert (
            research_output
        ), f"没有获取到{research_output}的agent的输出，请检查research agent的输出"
        research_outputs.append(research_output_key + "\n" + research_output)
    research_outputs_content = "\n\n".join(research_outputs)
    callback_context.state["research_outputs_content"] = research_outputs_content
    return None

class SlideLoopConditionAgent(BaseAgent):
    """循环条件检查Agent"""

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        slides_plan_num: int = ctx.session.state.get("slides_plan_num")
        current_slide_index: int = ctx.session.state.get("current_slide_index", 0)

        if not slides_plan_num:
            print("No slides_plan_num found. Terminating loop.")
            logger.info("No slides_plan_num found. Terminating loop.")
            yield Event(author=self.name, actions=EventActions(escalate=True))
            return

        # 检查是否所有幻灯片都已处理
        if current_slide_index >= slides_plan_num - 1:
            print(f"--- All {slides_plan_num} slides processed. Terminating loop. ---")
            logger.info(
                f"--- All {slides_plan_num} slides processed. Terminating loop. ---"
            )
            yield Event(
                author=self.name, actions=EventActions(escalate=True)
            )
        else:
            new_slide_index = current_slide_index + 1
            ctx.session.state["current_slide_index"] = new_slide_index
            print(f"--- 开始生成第 {new_slide_index + 1} / {slides_plan_num} 幻灯片---")
            logger.info(
                f"--- 开始生成第 {new_slide_index + 1} / {slides_plan_num} 幻灯片---"
            )
            yield Event(
                author=self.name, actions=EventActions()
            )

# 创建PPT生成循环Agent
ppt_generator_loop_agent = LoopAgent(
    name="PPTGeneratorLoopAgent",
    max_iterations=100,
    sub_agents=[
        ppt_writer_sub_agent,
        ppt_checker_agent,
        SlideLoopConditionAgent(
            name="SlideCounter"
        ),
    ],
    before_agent_callback=my_super_before_agent_callback,
)
