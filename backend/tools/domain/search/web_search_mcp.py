"""
MCP Web Search Tool - 通过 MCP 调用 web_search

使用 Anthropic MCP SDK 连接到 MCP Server，将 web_search 暴露为 LangChain Tool。
"""

import logging
from typing import Optional

from langchain_core.tools import StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field

logger = logging.getLogger(__name__)


class MCPWebSearchInput(BaseModel):
    """MCP Web search input schema"""

    query: str = Field(description="Search query string")
    num_results: int = Field(
        default=5, ge=1, le=10, description="Number of results to return (1-10)"
    )


# MCP Client（懒加载单例）
_mcp_client: Optional[object] = None


async def get_mcp_client():
    """
    获取 MCP Client（懒加载）

    Returns:
        MCP Client 实例

    Raises:
        Exception: 如果连接失败
    """
    global _mcp_client
    if _mcp_client is None:
        from mcp.client import Client, StdioServerParameters

        logger.info("[MCP Client] Initializing connection to MCP Server...")

        # 配置 Server 参数
        server_params = StdioServerParameters(
            command="python", args=["-m", "backend.tools.mcp.server"], env=None  # 继承当前环境变量
        )

        # 创建 Client
        _mcp_client = Client(server_params)

        try:
            # 初始化连接
            await _mcp_client.initialize()
            logger.info("[MCP Client] Connected to MCP Server successfully")
        except Exception as e:
            logger.error(f"[MCP Client] Failed to connect: {e}", exc_info=True)
            raise

    return _mcp_client


async def web_search_mcp_func(query: str, num_results: int = 5) -> str:
    """
    Web search via MCP Server

    通过 MCP 协议调用远程的 web_search 工具。

    Args:
        query: Search query string
        num_results: Number of results to return

    Returns:
        str: Search results in text format

    Raises:
        Exception: 如果 MCP 调用失败

    Example:
        >>> await web_search_mcp_func("artificial intelligence", 3)
        'Found 3 results for 'artificial intelligence':\n\n1. ...'
    """
    logger.info(f"[MCP Wrapper] Calling web_search via MCP: query={query}")

    try:
        # 获取 MCP Client
        client = await get_mcp_client()

        # 调用 MCP Server 的工具
        result = await client.call_tool(
            "web_search", {"query": query, "num_results": num_results, "language": "zh-CN"}
        )

        # MCP SDK 返回的结果格式
        # result 可能是不同类型，需要处理
        if hasattr(result, "content"):
            # ToolContent 类型
            content = result.content
            if isinstance(content, list) and len(content) > 0:
                # 取第一个 content
                return content[0].text
            return str(content)
        elif isinstance(result, dict):
            # 可能是原始结果字典
            if "content" in result:
                return str(result["content"])
            elif "results" in result:
                return str(result["results"])
        elif isinstance(result, str):
            return result
        else:
            return str(result)

    except Exception as e:
        logger.error(f"[MCP Wrapper] Error calling MCP: {e}", exc_info=True)
        raise


# 创建 Langchain Tool
web_search_mcp_tool = StructuredTool.from_function(
    func=web_search_mcp_func,
    name="web_search_mcp",
    description="Web search via MCP Server - experimental implementation",
    args_schema=MCPWebSearchInput,
)

__all__ = ["web_search_mcp_tool"]
