#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MCP Tool: Web Search

Implements web search functionality using Bing Search API v7.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
import httpx

from .base_mcp_tool import BaseMCPTool


# Configuration
BING_SEARCH_API_KEY = os.getenv("BING_SEARCH_API_KEY", "")
BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"
BING_CUSTOM_SEARCH_ENDPOINT = "https://api.bing.microsoft.com/v7.0/custom/search"

logger = logging.getLogger(__name__)


class WebSearchTool(BaseMCPTool):
    """Web search tool using Bing Search API"""

    def __init__(self):
        super().__init__(
            name="web_search",
            description="Execute web search and return results"
        )
        self.api_key = BING_SEARCH_API_KEY
        self.endpoint = BING_ENDPOINT

    async def execute(
        self,
        query: str,
        num_results: int = 5,
        search_engine: str = "bing",
        language: str = "zh-CN",
        time_range: str = "any",
        tool_context: Optional[Any] = None
    ) -> str:
        """
        Execute web search

        Args:
            query: Search query
            num_results: Number of results to return (default: 5, max: 10)
            search_engine: Search engine (bing, google, duckduckgo)
            language: Search language
            time_range: Time range filter (any, day, week, month, year)
            tool_context: Optional tool context

        Returns:
            JSON string with search results
        """
        agent_name = getattr(tool_context, 'agent_name', 'unknown') if tool_context else 'unknown'
        logger.info(f"[{agent_name}] Executing web search: {query}")

        if not self.api_key:
            return self._error(
                message="BING_SEARCH_API_KEY not configured",
                code="MISSING_API_KEY"
            )

        # Validate num_results
        num_results = max(1, min(num_results, 10))

        try:
            if search_engine == "bing":
                results = await self._search_bing(query, num_results, language, time_range)
            else:
                return self._error(
                    message=f"Unsupported search engine: {search_engine}",
                    code="UNSUPPORTED_ENGINE"
                )

            # Format response
            metadata = {
                "total_results": len(results),
                "search_engine": search_engine,
                "query": query
            }

            return self._success({"results": results}, metadata=metadata)

        except Exception as e:
            logger.error(f"Web search error: {e}", exc_info=True)
            return self._error(
                message=str(e),
                code="SEARCH_ERROR",
                details={"query": query}
            )

    async def _search_bing(
        self,
        query: str,
        num_results: int,
        language: str,
        time_range: str
    ) -> list:
        """Execute search using Bing Search API v7"""
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key
        }

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
            response = await client.get(
                self.endpoint,
                headers=headers,
                params=params
            )
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
                "source": self._extract_domain(item.get("url", "")),
                "relevance_score": 0.8  # Bing doesn't provide scores
            })

        return results

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return url


# Global instance
_tool_instance = None


def get_tool() -> WebSearchTool:
    """Get or create the web search tool instance"""
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = WebSearchTool()
    return _tool_instance


async def web_search(
    query: str,
    num_results: int = 5,
    search_engine: str = "bing",
    language: str = "zh-CN",
    time_range: str = "any",
    tool_context: Optional[Any] = None
) -> str:
    """
    Execute web search

    Args:
        query: Search query
        num_results: Number of results to return (default: 5, max: 10)
        search_engine: Search engine (bing, google, duckduckgo)
        language: Search language
        time_range: Time range filter (any, day, week, month, year)
        tool_context: Optional tool context

    Returns:
        JSON string with search results
    """
    tool = get_tool()
    return await tool.execute(
        query=query,
        num_results=num_results,
        search_engine=search_engine,
        language=language,
        time_range=time_range,
        tool_context=tool_context
    )
