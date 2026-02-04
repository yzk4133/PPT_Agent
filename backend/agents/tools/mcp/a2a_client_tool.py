"""
A2A客户端MCP工具

This module wraps the A2A client as an MCP tool for use with agents.
"""

import logging
import uuid
import httpx
from typing import Any, Optional
from a2a.client import A2AClient
from a2a.types import MessageSendParams, SendStreamingMessageRequest

from .base_mcp_tool import BaseMCPTool

logger = logging.getLogger(__name__)


class A2AClientTool(BaseMCPTool):
    """
    A2A客户端工具

    Wraps the A2A (Agent-to-Agent) client for use with MCP tool framework.
    """

    def __init__(self):
        super().__init__(name="a2a_client", description="A2A客户端工具，用于与其他Agent进行通信")

    async def execute(
        self,
        prompt: str,
        model: str = "deepseek-chat",
        stream: bool = False,
        tool_context: Optional[Any] = None
    ) -> str:
        """
        执行A2A客户端调用

        Args:
            prompt: 要发送的提示消息
            model: 模型名称
            stream: 是否使用流式响应
            tool_context: 工具上下文（可选）

        Returns:
            JSON格式的响应字符串
        """
        try:
            timeout = httpx.Timeout(30.0)

            async with httpx.AsyncClient(timeout=timeout) as httpx_client:
                # 初始化客户端
                client = await A2AClient.get_client_from_agent_card_url(
                    httpx_client, 'http://localhost:10011'
                )

                # 生成唯一请求ID
                request_id = uuid.uuid4().hex

                # 构造消息参数
                send_message_payload = {
                    'message': {
                        'role': 'user',
                        'parts': [{'type': 'text', 'text': prompt}],
                        'messageId': request_id
                    }
                }

                if stream:
                    # 流式请求
                    streaming_request = SendStreamingMessageRequest(
                        id=request_id,
                        params=MessageSendParams(**send_message_payload)
                    )

                    responses = []
                    stream_response = client.send_message_streaming(streaming_request)
                    async for chunk in stream_response:
                        responses.append(chunk.model_dump(mode='json', exclude_none=True))

                    return self._success({
                        "response": responses,
                        "model": model,
                        "streaming": True
                    })
                else:
                    # 非流式请求
                    from a2a.types import SendMessageRequest
                    message_request = SendMessageRequest(
                        id=request_id,
                        params=MessageSendParams(**send_message_payload)
                    )

                    response = client.send_message(message_request)
                    return self._success({
                        "response": response.model_dump(mode='json', exclude_none=True),
                        "model": model,
                        "streaming": False
                    })

        except Exception as e:
            logger.error(f"A2A client error: {e}")
            return self._error(f"A2A调用失败: {str(e)}")


# 创建全局实例和导出函数
_a2a_tool = A2AClientTool()


async def a2a_client(
    prompt: str,
    model: str = "deepseek-chat",
    stream: bool = False,
    tool_context: Optional[Any] = None
) -> str:
    """
    A2A客户端工具函数

    Args:
        prompt: 要发送的提示消息
        model: 模型名称
        stream: 是否使用流式响应
        tool_context: 工具上下文（可选）

    Returns:
        JSON格式的响应字符串
    """
    return await _a2a_tool.execute(
        prompt=prompt,
        model=model,
        stream=stream,
        tool_context=tool_context
    )


if __name__ == "__main__":
    # 测试A2A客户端工具
    import asyncio

    async def test_a2a():
        result = await a2a_client(prompt="Hello, A2A!")
        print(result)

    asyncio.run(test_a2a())
