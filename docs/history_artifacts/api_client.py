"""LLM API客户端封装

统一管理对各种LLM API的调用
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import httpx

from .config import get_config
from .exceptions import ContentException, ErrorCode


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    model: str
    tokens_used: int
    finish_reason: str


@dataclass
class LLMMessage:
    """LLM消息"""
    role: str  # system, user, assistant
    content: str


class AnthropicClient:
    """Anthropic API客户端"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.client = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            timeout=30.0
        )
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()

    async def complete(
        self,
        messages: List[LLMMessage],
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> LLMResponse:
        """发送完成请求"""
        if not self.client:
            raise RuntimeError("客户端未初始化，请使用async with")

        # 转换消息格式
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": api_messages
        }

        try:
            response = await self.client.post(self.base_url, json=payload)
            response.raise_for_status()

            data = response.json()

            return LLMResponse(
                content=data["content"][0]["text"],
                model=data["model"],
                tokens_used=data["usage"]["input_tokens"] + data["usage"]["output_tokens"],
                finish_reason=data["stop_reason"]
            )

        except httpx.HTTPError as e:
            raise ContentException(
                ErrorCode.LLM_API_ERROR,
                f"API调用失败: {str(e)}"
            )


class LLMClientFactory:
    """LLM客户端工厂"""

    @staticmethod
    async def create_client(provider: str = "anthropic"):
        """创建LLM客户端

        Args:
            provider: 提供商名称 (anthropic, openai)

        Returns:
            LLM客户端实例
        """
        config = get_config()

        if provider == "anthropic":
            return AnthropicClient(config.anthropic.api_key)
        else:
            raise ValueError(f"未知的提供商: {provider}")


# 使用示例的辅助函数
async def generate_completion(
    prompt: str,
    system_prompt: Optional[str] = None,
    provider: str = "anthropic"
) -> str:
    """便捷的补全生成函数

    Args:
        prompt: 用户提示词
        system_prompt: 系统提示词（可选）
        provider: LLM提供商

    Returns:
        生成的内容
    """
    messages = []

    if system_prompt:
        messages.append(LLMMessage(role="system", content=system_prompt))

    messages.append(LLMMessage(role="user", content=prompt))

    async with await LLMClientFactory.create_client(provider) as client:
        response = await client.complete(messages)
        return response.content
