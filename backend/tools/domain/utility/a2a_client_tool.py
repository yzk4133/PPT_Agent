"""
LangChain Native Tool: A2A Client

Agent-to-Agent communication client tool for inter-agent messaging.
"""

import logging
import uuid
from typing import Literal

import httpx
from langchain_core.tools import StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field

from backend.tools.core.monitoring import monitor_tool
from backend.tools.application.tool_registry import get_native_registry

logger = logging.getLogger(__name__)

# Default A2A server endpoint
A2A_ENDPOINT = "http://localhost:10011"


# Input schema
class A2AClientInput(BaseModel):
    """A2A client input schema"""

    prompt: str = Field(description="Message prompt to send to the agent")
    endpoint: str = Field(default=A2A_ENDPOINT, description="A2A server endpoint")
    stream: bool = Field(default=False, description="Whether to use streaming response")


@monitor_tool
async def a2a_client(prompt: str, endpoint: str = A2A_ENDPOINT, stream: bool = False) -> dict:
    """
    Send message to another agent via A2A (Agent-to-Agent) protocol

    Communicates with other agents using the A2A protocol for distributed
    agent coordination and collaboration.

    Args:
        prompt: Message prompt to send
        endpoint: A2A server endpoint URL
        stream: Whether to use streaming response

    Returns:
        Dictionary with agent response data

    Note:
        This tool requires an A2A server running at the specified endpoint.
        The server URL can be configured via the A2A_ENDPOINT parameter.
    """
    try:
        timeout = httpx.Timeout(30.0)

        async with httpx.AsyncClient(timeout=timeout) as httpx_client:
            # Import A2A client (lazy import to avoid dependency issues)
            try:
                from a2a.client import A2AClient
                from a2a.types import (
                    MessageSendParams,
                    SendStreamingMessageRequest,
                    SendMessageRequest,
                )
            except ImportError:
                raise ImportError("A2A package not installed. Install with: pip install a2a")

            # Initialize client
            client = await A2AClient.get_client_from_agent_card_url(httpx_client, endpoint)

            # Generate unique request ID
            request_id = uuid.uuid4().hex

            # Construct message parameters
            send_message_payload = {
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": prompt}],
                    "messageId": request_id,
                }
            }

            if stream:
                # Streaming request
                streaming_request = SendStreamingMessageRequest(
                    id=request_id, params=MessageSendParams(**send_message_payload)
                )

                responses = []
                stream_response = client.send_message_streaming(streaming_request)
                async for chunk in stream_response:
                    responses.append(chunk.model_dump(mode="json", exclude_none=True))

                logger.info(f"[a2a_client] Streaming response completed: {len(responses)} chunks")

                return {
                    "response": responses,
                    "streaming": True,
                    "endpoint": endpoint,
                    "request_id": request_id,
                }
            else:
                # Non-streaming request
                message_request = SendMessageRequest(
                    id=request_id, params=MessageSendParams(**send_message_payload)
                )

                response = client.send_message(message_request)

                logger.info(f"[a2a_client] Response received")

                return {
                    "response": response.model_dump(mode="json", exclude_none=True),
                    "streaming": False,
                    "endpoint": endpoint,
                    "request_id": request_id,
                }

    except ImportError as e:
        logger.error(f"[a2a_client] Import error: {e}")
        raise
    except Exception as e:
        logger.error(f"[a2a_client] Error: {e}", exc_info=True)
        raise


# Create LangChain StructuredTool
tool = StructuredTool.from_function(
    func=a2a_client,
    name="a2a_client",
    description="Send messages to other agents via A2A protocol. Use this for inter-agent communication.",
    args_schema=A2AClientInput,
)

# Auto-register with global registry
registry = get_native_registry()
registry.register_tool(tool, category=registry.UTILITY)

__all__ = ["tool", "a2a_client"]
