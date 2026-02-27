"""
MCP Server - 提供 web_search 服务

使用 Anthropic MCP SDK 实现，通过 stdio 进行通信。

启动方式：
    python -m backend.tools.mcp.server

环境变量：
    BING_SEARCH_API_KEY: Bing Search API 密钥（必需）
"""

import asyncio
import logging
import os
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

# 配置
BING_SEARCH_API_KEY = os.getenv("BING_SEARCH_API_KEY")
BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 MCP Server
server = Server("search-server")


@server.tool("web_search")
async def web_search(
    query: str,
    num_results: int = 5,
    language: str = "zh-CN"
) -> str:
    """
    Execute web search using Bing Search API

    This tool searches the web for relevant information and returns
    formatted search results.

    Args:
        query: The search query string (e.g., "artificial intelligence")
        num_results: Number of results to return (1-10, default 5)
        language: Language code for search results (e.g., "zh-CN", "en-US")

    Returns:
        str: Formatted search results with titles, URLs, and snippets

    Raises:
        ValueError: If BING_SEARCH_API_KEY is not configured

    Examples:
        >>> await web_search("AI in healthcare", num_results=3)
        "Found 3 results for 'AI in healthcare':\n\n1. ..."
    """
    logger.info(f"[MCP Server] web_search called: query={query}, num_results={num_results}")

    # 验证 API Key
    if not BING_SEARCH_API_KEY:
        raise ValueError("BING_SEARCH_API_KEY not configured in environment")

    # 验证参数
    num_results = max(1, min(num_results, 10))

    # 准备请求
    headers = {"Ocp-Apim-Subscription-Key": BING_SEARCH_API_KEY}
    params = {
        "q": query,
        "count": num_results,
        "mkt": language,
        "safeSearch": "Moderate",
        "textFormat": "HTML",
        "textDecorations": "true"
    }

    try:
        # 执行搜索
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(BING_ENDPOINT, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        # 解析结果
        results = []
        web_pages = data.get("webPages", {}).get("value", [])

        for item in web_pages:
            results.append({
                "title": item.get("name", ""),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", ""),
                "display_url": item.get("displayUrl", ""),
                "date": item.get("date"),
                "source": _extract_domain(item.get("url", ""))
            })

        # 格式化输出
        output = f"Found {len(results)} results for '{query}':\n\n"
        for i, item in enumerate(results, 1):
            output += f"{i}. {item['title']}\n"
            output += f"   URL: {item['url']}\n"
            if item['snippet']:
                snippet = item['snippet'][:150].replace('\n', ' ')
                output += f"   {snippet}...\n\n"

        logger.info(f"[MCP Server] Returning {len(results)} results")
        return output

    except httpx.HTTPStatusError as e:
        logger.error(f"[MCP Server] HTTP error: {e}")
        raise
    except Exception as e:
        logger.error(f"[MCP Server] Error: {e}", exc_info=True)
        raise


def _extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return url


async def main():
    """启动 MCP Server"""
    logger.info("[MCP Server] Starting search server...")
    logger.info(f"[MCP Server] BING_API_KEY configured: {bool(BING_SEARCH_API_KEY)}")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
