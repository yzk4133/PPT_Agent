from google.adk.agents.llm_agent import Agent
from google.adk.agents.sequential_agent import SequentialAgent

from .sub_agents.research_topic.agent import parallel_search_agent
from .sub_agents.split_topic.agent import split_topic_agent
from .sub_agents.ppt_writer.agent import ppt_generator_loop_agent
from google.adk.agents.callback_context import CallbackContext
from dotenv import load_dotenv
import os
import sys
import asyncio

# 在模块顶部加载环境变量
load_dotenv(".env")

# 导入用户偏好服务（可选）
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from persistent_memory import UserPreferenceService

    user_pref_service = UserPreferenceService(enable_cache=True)
    PERSISTENT_MEMORY_AVAILABLE = True
except ImportError:
    user_pref_service = None
    PERSISTENT_MEMORY_AVAILABLE = False


def before_agent_callback(callback_context: CallbackContext) -> None:
    """
    在调用LLM之前，从会话状态中获取当前幻灯片计划，并格式化LLM输入。
    集成用户偏好学习：自动加载历史偏好
    """
    metadata = callback_context.state.get("metadata", {})
    print(f"传入的metadata信息如下: {metadata}")

    # 获取user_id（如果有）
    user_id = metadata.get("user_id", "anonymous")
    callback_context.state["user_id"] = user_id

    # 尝试加载用户历史偏好
    if PERSISTENT_MEMORY_AVAILABLE and user_pref_service:
        try:
            # 异步调用需要在同步环境中运行
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            user_prefs = loop.run_until_complete(
                user_pref_service.get_user_preferences(
                    user_id, create_if_not_exists=True
                )
            )

            # 合并用户偏好和当前请求的metadata（当前请求优先）
            merged_metadata = {**user_prefs, **metadata}
            slides_plan_num = merged_metadata.get("numSlides") or merged_metadata.get(
                "default_slides", 10
            )
            language = merged_metadata.get("language", "EN-US")

            print(f"✅ 加载用户偏好: user={user_id}, prefs={user_prefs}")
        except Exception as e:
            print(f"⚠️ 加载用户偏好失败: {e}，使用默认值")
            slides_plan_num = metadata.get("numSlides", 10)
            language = metadata.get("language", "EN-US")
    else:
        slides_plan_num = metadata.get("numSlides", 10)
        language = metadata.get("language", "EN-US")

    # 设置幻灯片数量和语言
    callback_context.state["slides_plan_num"] = slides_plan_num
    callback_context.state["language"] = language
    # 返回 None，继续调用 LLM
    return None


root_agent = SequentialAgent(
    name="WritingSystemAgent",
    description="多Agent写作系统的总协调器",
    sub_agents=[split_topic_agent, parallel_search_agent, ppt_generator_loop_agent],
    before_agent_callback=before_agent_callback,
)
