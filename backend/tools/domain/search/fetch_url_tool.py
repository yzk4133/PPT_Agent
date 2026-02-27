"""
LangChain Native Tool: Fetch URL

Implements web scraping functionality to extract content from URLs.
"""

import os
import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Literal

import httpx
from bs4 import BeautifulSoup
from readability import Document
import html2text
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from backend.tools.core.monitoring import monitor_tool
from backend.tools.application.tool_registry import get_native_registry

# Cache configuration
CACHE_DIR = Path(os.getenv("MCP_CACHE_DIR", "./data/mcp_cache"))
CACHE_ENABLED = os.getenv("MCP_CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL_SECONDS = int(os.getenv("MCP_CACHE_TTL", "3600"))  # 1 hour default

logger = logging.getLogger(__name__)

# Configure html2text
h2t = html2text.HTML2Text()
h2t.ignore_links = False
h2t.ignore_images = False
h2t.body_width = 0  # Don't wrap lines


# Input schema
class FetchUrlInput(BaseModel):
    """Fetch URL input schema"""
    url: str = Field(description="The URL to fetch content from")
    timeout: int = Field(default=10, ge=1, le=30, description="Timeout in seconds")
    extract_type: Literal["full", "main_content", "article", "text_only"] = Field(
        default="main_content",
        description="Type of content extraction"
    )
    use_cache: bool = Field(default=True, description="Whether to use cache")


@monitor_tool
async def fetch_url(
    url: str,
    timeout: int = 10,
    extract_type: str = "main_content",
    use_cache: bool = True
) -> dict:
    """
    Fetch and extract content from a URL

    Retrieves web page content and extracts structured information including
    title, main content, metadata, and text. Supports multiple extraction modes.

    Args:
        url: Target URL to fetch
        timeout: Request timeout in seconds
        extract_type: Content extraction type (full, main_content, article, text_only)
        use_cache: Whether to use cached results

    Returns:
        Dictionary with extracted content and metadata
    """
    logger.info(f"[fetch_url] Fetching: {url}")

    # Check cache first
    if use_cache and CACHE_ENABLED:
        cached = await _get_from_cache(url)
        if cached:
            logger.info(f"[fetch_url] Cache hit for: {url}")
            cached["from_cache"] = True
            return cached

    try:
        # Fetch the page
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            html_content = response.text

        # Extract content based on type
        result = await _extract_content(html_content, extract_type, url)

        # Store in cache
        if use_cache and CACHE_ENABLED:
            await _save_to_cache(url, result)

        logger.info(f"[fetch_url] Successfully fetched {len(result.get('text_content', ''))} chars")
        return result

    except httpx.TimeoutException:
        raise TimeoutError(f"Request timeout after {timeout} seconds")
    except httpx.HTTPStatusError as e:
        raise ValueError(f"HTTP error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"[fetch_url] Error: {e}", exc_info=True)
        raise


async def _extract_content(html: str, extract_type: str, url: str) -> dict:
    """Extract content from HTML based on type"""
    soup = BeautifulSoup(html, 'html.parser')

    result = {
        "url": url,
        "title": "",
        "fetched_at": datetime.now().isoformat()
    }

    # Extract title
    if soup.title:
        result["title"] = soup.title.get_text().strip()

    # Extract metadata
    meta_description = soup.find("meta", attrs={"name": "description"})
    if meta_description:
        result["description"] = meta_description.get("content", "")

    # Extract author
    meta_author = soup.find("meta", attrs={"name": "author"})
    if meta_author:
        result["author"] = meta_author.get("content", "")

    # Extract based on type
    if extract_type == "full":
        result["content"] = html
        result["text_content"] = soup.get_text(separator="\n", strip=True)

    elif extract_type in ["main_content", "article"]:
        # Use readability to extract main content
        doc = Document(html)
        main_content = doc.summary()
        result["content"] = main_content
        result["text_content"] = h2t.handle(main_content)

        # Try to get lead image
        if hasattr(doc, 'main_image') and doc.main_image():
            result["lead_image_url"] = doc.main_image()

    elif extract_type == "text_only":
        result["text_content"] = h2t.handle(html)

    # Calculate word count
    if "text_content" in result:
        result["word_count"] = len(result["text_content"].split())

    return result


def _get_cache_key(url: str) -> Path:
    """Generate cache file path from URL"""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return CACHE_DIR / f"{url_hash}.json"


async def _get_from_cache(url: str) -> dict | None:
    """Get content from cache if valid"""
    cache_file = _get_cache_key(url)

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached = json.load(f)

        # Check TTL
        cached_at = datetime.fromisoformat(cached.get("fetched_at", ""))
        age = (datetime.now() - cached_at).total_seconds()

        if age > CACHE_TTL_SECONDS:
            cache_file.unlink()  # Remove expired cache
            return None

        return cached

    except Exception as e:
        logger.warning(f"[fetch_url] Cache read error: {e}")
        return None


async def _save_to_cache(url: str, data: dict):
    """Save content to cache"""
    cache_file = _get_cache_key(url)

    try:
        # Create cache directory if needed
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"[fetch_url] Cache write error: {e}")


# Create LangChain StructuredTool
tool = StructuredTool.from_function(
    func=fetch_url,
    name="fetch_url",
    description="Fetch and extract content from a URL. Use this to get the full text and metadata from web pages.",
    args_schema=FetchUrlInput
)

# Auto-register with global registry
registry = get_native_registry()
registry.register_tool(tool, category=registry.SEARCH)

__all__ = ["tool", "fetch_url"]
