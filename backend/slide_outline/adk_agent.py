import logging
import os
import litellm
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
litellm._turn_on_debug()

def create_model(model:str, provider: str):
    """
    创建模型，返回字符串或者LiteLlm
    LiteLlm(model="deepseek/deepseek-chat", api_key="xxx", api_base="")
    :return:
    """
    if provider == "google":
        # google的模型直接使用名称
        assert os.environ.get("GOOGLE_API_KEY"), "GOOGLE_API_KEY is not set"
        return model
    elif provider == "claude":
        # Claude 模型需要使用 LiteLlm，并遵循 LiteLLM 的模型命名规范
        assert os.environ.get("CLAUDE_API_KEY"), "CLAUDE_API_KEY is not set"
        # 正确的做法是使用 "claude/" 前缀
        if not model.startswith("anthropic/"):
            model = "anthropic/" + model

        return LiteLlm(
            model=model,  # 例如: "claude/claude-3-opus-20240229"
            api_key=os.environ.get("CLAUDE_API_KEY"),
        )
    elif provider == "openai":
        # openai的模型需要使用LiteLlm
        assert os.environ.get("OPENAI_API_KEY"), "OPENAI_API_KEY is not set"
        if not model.startswith("openai/"):
            # 表示兼容openai的模型请求
            model = "openai/" + model
        return LiteLlm(model=model, api_key=os.environ.get("OPENAI_API_KEY"), api_base="https://api.openai.com/v1")
    elif provider == "deepseek":
        # deepseek的模型需要使用LiteLlm
        assert os.environ.get("DEEPSEEK_API_KEY"),  "DEEPSEEK_API_KEY is not set"
        if not model.startswith("openai/"):
            # 表示兼容openai的模型请求
            model = "openai/" + model
        return LiteLlm(model=model, api_key=os.environ.get("DEEPSEEK_API_KEY"), api_base="https://api.deepseek.com/v1")
    elif provider == "ali":
        # huggingface的模型需要使用LiteLlm
        assert os.environ.get("ALI_API_KEY"), "ALI_API_KEY is not set"
        if not model.startswith("openai/"):
            # 表示兼容openai的模型请求
            model = "openai/" + model
        return LiteLlm(model=model, api_key=os.environ.get("ALI_API_KEY"), api_base="https://dashscope.aliyuncs.com/compatible-mode/v1")
    else:
        raise ValueError(f"Unsupported provider: {provider}")

def create_agent(model, provider, agent_name,agent_description,agent_instruction, mcptools=[]) -> LlmAgent:
    """Constructs the ADK agent."""
    logging.info(f"使用的模型供应商是: {provider}，模型是: {model}")
    model = create_model(model, provider)
    return LlmAgent(
        model=model,
        name=agent_name,
        description=agent_description,
        instruction=agent_instruction,
        tools=mcptools,
    )
