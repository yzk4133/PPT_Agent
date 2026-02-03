"""
Topic Splitter Agent - 共享实现
将研究大纲拆分为独立的研究主题
"""

from google.adk.agents.llm_agent import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types
from typing import Optional

# 导入配置和模型创建（从common模块）
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from infrastructure.config.common_config import get_config
from infrastructure.llm.common_model_factory import create_model_with_fallback, create_model_with_fallback_simple

# 导入PromptManager用于获取提示词模板
from cognition.prompts import PromptManager

# 使用PromptManager获取提示词模板
SPLIT_TOPIC_AGENT_PROMPT = PromptManager.get_split_topic_prompt()


def my_before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    """模型调用前的回调函数"""
    user_input = callback_context.user_content.parts[0].text
    callback_context.state["outline"] = user_input
    print("调用了SplitTopicAgent的Outline的callback，存储outline信息")

    # 将用户输入添加到请求中
    llm_request.contents.append(
        types.Content(role="user", parts=[types.Part(text=user_input)])
    )
    # 返回 None，继续调用 LLM
    return None


# 创建全局实例
split_topic_agent = Agent(
    name="SplitTopicAgent",
    model="deepseek-chat",  # Simple model string for litellm
    description="专门负责分析写作大纲并将其拆分成独立的研究主题",
    instruction=SPLIT_TOPIC_AGENT_PROMPT,
    output_key="split_topics",
    before_model_callback=my_before_model_callback
)
