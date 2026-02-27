"""
LangChain Native Tool: WeChat Article Search

Searches WeChat official account articles using Sogou WeChat search.
"""

import json
import logging
from typing import Literal

import requests
from lxml import html
from urllib.parse import quote
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from backend.tools.core.monitoring import monitor_tool
from backend.tools.application.tool_registry import get_native_registry

logger = logging.getLogger(__name__)


# Input schema
class WeixinSearchInput(BaseModel):
    """WeChat article search input schema"""
    query: str = Field(description="Search keywords for WeChat articles")
    num_results: int = Field(default=5, ge=1, le=20, description="Number of results to return (1-20)")
    fetch_content: bool = Field(default=True, description="Whether to fetch article content")


@monitor_tool
async def weixin_search(
    query: str,
    num_results: int = 5,
    fetch_content: bool = True
) -> dict:
    """
    Search WeChat official account articles

    Searches for articles from WeChat official accounts using Sogou WeChat search.
    Optionally fetches the full content of each article.

    Args:
        query: Search keywords
        num_results: Number of results to return (1-20)
        fetch_content: Whether to fetch article full content

    Returns:
        Dictionary with search results including article titles, URLs, and content
    """
    # Validate parameters
    num_results = max(1, min(20, int(num_results)))

    logger.info(f"[weixin_search] Searching: {query}")

    # Step 1: Sogou WeChat search
    search_results = await _sogou_weixin_search(query, num_results)

    if not search_results:
        logger.warning(f"[weixin_search] No results found for '{query}'")
        return {
            "query": query,
            "total": 0,
            "articles": [],
            "message": f"No articles found for '{query}'"
        }

    # Step 2: Fetch content if requested
    if fetch_content:
        articles = []
        for result in search_results:
            real_url = await _get_real_url(result["link"])
            if real_url:
                content = await _get_article_content(real_url, result["link"])
                articles.append({
                    "title": result["title"],
                    "publish_time": result["publish_time"],
                    "sogou_url": result["link"],
                    "real_url": real_url,
                    "content": content[:5000] + "..." if len(content) > 5000 else content
                })
            else:
                articles.append({
                    "title": result["title"],
                    "publish_time": result["publish_time"],
                    "sogou_url": result["link"],
                    "real_url": "",
                    "content": "Unable to fetch article content"
                })
    else:
        articles = [
            {
                "title": r["title"],
                "publish_time": r["publish_time"],
                "sogou_url": r["link"]
            }
            for r in search_results
        ]

    logger.info(f"[weixin_search] Found {len(articles)} articles")

    return {
        "query": query,
        "total": len(articles),
        "articles": articles,
        "fetched_content": fetch_content
    }


async def _sogou_weixin_search(query: str, num_results: int) -> list:
    """Search using Sogou WeChat search"""
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Referer": f"https://weixin.sogou.com/weixin?query={quote(query)}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    }

    params = {
        "type": "2",
        "s_from": "input",
        "query": query,
        "ie": "utf8",
        "_sug_": "n",
        "_sug_type_": "",
    }

    try:
        response = requests.get(
            "https://weixin.sogou.com/weixin",
            params=params,
            headers=headers,
            timeout=15
        )

        if response.status_code == 200:
            tree = html.fromstring(response.text)
            results = []

            elements = tree.xpath("//a[contains(@id, 'sogou_vr_11002601_title_')]")
            publish_time = tree.xpath(
                "//li[contains(@id, 'sogou_vr_11002601_box_')]/div[@class='txt-box']/div[@class='s-p']/span[@class='s2']"
            )

            for element, time_elem in zip(elements[:num_results], publish_time[:num_results]):
                title = element.text_content().strip()
                link = element.get("href")
                if link and not link.startswith("http"):
                    link = "https://weixin.sogou.com" + link
                results.append({
                    "title": title,
                    "link": link,
                    "publish_time": time_elem.text_content().strip(),
                })

            logger.info(f"[weixin_search] Sogou found {len(results)} results")
            return results
        else:
            logger.warning(f"[weixin_search] Sogou returned status {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"[weixin_search] Sogou search failed: {e}")
        return []


async def _get_real_url(sogou_url: str) -> str:
    """Get real WeChat article URL from Sogou link"""
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    try:
        response = requests.get(sogou_url, headers=headers, timeout=10)
        script_content = response.text

        # Parse JavaScript URL
        start_index = script_content.find("url += '") + len("url += '")
        url_parts = []

        while True:
            part_start = script_content.find("url += '", start_index)
            if part_start == -1:
                break
            part_end = script_content.find("'", part_start + len("url += '"))
            part = script_content[part_start + len("url += '") : part_end]
            url_parts.append(part)
            start_index = part_end + 1

        if url_parts:
            full_url = "".join(url_parts).replace("@", "")
            return "https://mp." + full_url
        return ""
    except Exception as e:
        logger.error(f"[weixin_search] Get real URL failed: {e}")
        return ""


async def _get_article_content(real_url: str, referer: str) -> str:
    """Fetch WeChat article content"""
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "referer": referer,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    try:
        response = requests.get(real_url, headers=headers, timeout=10)
        tree = html.fromstring(response.text)
        content_elements = tree.xpath("//div[@id='js_content']//text()")
        cleaned_content = [text.strip() for text in content_elements if text.strip()]
        main_content = "\n".join(cleaned_content)
        return main_content
    except Exception as e:
        logger.error(f"[weixin_search] Get article content failed: {e}")
        return f"Failed to fetch article content: {str(e)}"


# Create LangChain StructuredTool
tool = StructuredTool.from_function(
    func=weixin_search,
    name="weixin_search",
    description="Search WeChat official account articles. Use this to find articles from WeChat public accounts.",
    args_schema=WeixinSearchInput
)

# Auto-register with global registry
registry = get_native_registry()
registry.register_tool(tool, category=registry.SEARCH)

__all__ = ["tool", "weixin_search"]
