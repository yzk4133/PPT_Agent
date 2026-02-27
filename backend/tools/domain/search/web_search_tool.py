"""
LangChain Native Tool: Web Search

Implements web search functionality using Bing Search API v7.
"""

import os
import logging
from typing import Literal
from urllib.parse import urlparse

import httpx
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from backend.tools.core.monitoring import monitor_tool
from backend.tools.application.tool_registry import get_native_registry

# Configuration
BING_SEARCH_API_KEY = os.getenv("BING_SEARCH_API_KEY", "")
BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"

logger = logging.getLogger(__name__)


# Input schema
class WebSearchInput(BaseModel):
    """Web search input schema"""
    query: str = Field(description="Search query string")
    num_results: int = Field(default=5, ge=1, le=10, description="Number of results to return (1-10)")
    language: str = Field(default="zh-CN", description="Search language code (e.g., zh-CN, en-US)")
    time_range: Literal["any", "day", "week", "month", "year"] = Field(
        default="any",
        description="Time range filter for search results"
    )


@monitor_tool
async def web_search(
    query: str,
    num_results: int = 5,
    language: str = "zh-CN",
    time_range: str = "any"
) -> dict:
    """
    Execute web search using Bing Search API

    Searches the web for relevant information and returns structured results.
    Use this tool when you need current or specific information from the internet.

    Args:
        query: The search query string
        num_results: Number of results to return (1-10)
        language: Search language code
        time_range: Time range filter (any, day, week, month, year)

    Returns:
        Dictionary with search results including title, URL, snippet
    """
    if not BING_SEARCH_API_KEY:
        raise ValueError("BING_SEARCH_API_KEY not configured in environment")

    # Validate num_results
    num_results = max(1, min(num_results, 10))

    headers = {"Ocp-Apim-Subscription-Key": BING_SEARCH_API_KEY}
    params = {
        "q": query,
        "count": num_results,
        "mkt": language,
        "safeSearch": "Moderate",
        "textFormat": "HTML",
        "textDecorations": "true"
    }

    # Add time range filter
    if time_range != "any":
        time_filter_map = {
            "day": "Day",
            "week": "Week",
            "month": "Month",
            "year": "Year"
        }
        params["freshness"] = time_filter_map.get(time_range, "Day")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(BING_ENDPOINT, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

    # Parse results
    results = []
    web_pages = data.get("webPages", {}).get("value", [])

    for item in web_pages:
        results.append({
            "title": item.get("name", ""),
            "url": item.get("url", ""),
            "snippet": item.get("snippet", ""),
            "display_url": item.get("displayUrl", ""),
            "date": item.get("date"),
            "published_date": item.get("dateLastCrawled"),
            "source": _extract_domain(item.get("url", "")),
        })

    logger.info(f"[web_search] Found {len(results)} results for '{query}'")

    return {
        "results": results,
        "total": len(results),
        "query": query
    }


def _extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return url


# Create LangChain StructuredTool
tool = StructuredTool.from_function(
    func=web_search,
    name="web_search",
    description="Execute web search using Bing Search API. Use this when you need current or specific information from the internet.",
    args_schema=WebSearchInput
)

# Auto-register with global registry
registry = get_native_registry()
registry.register_tool(tool, category=registry.SEARCH)

__all__ = ["tool", "web_search"]
