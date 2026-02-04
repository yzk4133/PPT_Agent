#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MCP Tool: Fetch URL

Implements web scraping functionality to extract content from URLs.
Uses httpx, BeautifulSoup4, readability-lxml, and html2text.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import hashlib

import httpx
from bs4 import BeautifulSoup
from readability import Document
import html2text

from .base_mcp_tool import BaseMCPTool

# Cache configuration
CACHE_DIR = Path(os.getenv("MCP_CACHE_DIR", "./data/mcp_cache"))
CACHE_ENABLED = os.getenv("MCP_CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL_SECONDS = int(os.getenv("MCP_CACHE_TTL", "3600"))  # 1 hour default

logger = logging.getLogger(__name__)

class FetchUrlTool(BaseMCPTool):
    """URL fetching and content extraction tool"""

    def __init__(self):
        super().__init__(
            name="fetch_url",
            description="Fetch and extract content from a URL"
        )
        self.cache_dir = CACHE_DIR
        self.cache_enabled = CACHE_ENABLED
        self.cache_ttl = CACHE_TTL_SECONDS

        # Create cache directory if needed
        if self.cache_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Configure html2text
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.body_width = 0  # Don't wrap lines

    async def execute(
        self,
        url: str,
        timeout: int = 10,
        extract_type: str = "main_content",
        use_cache: bool = True,
        tool_context: Optional[Any] = None
    ) -> str:
        """
        Fetch URL content

        Args:
            url: Target URL
            timeout: Timeout in seconds
            extract_type: Content extraction type (full, main_content, article, text_only)
            use_cache: Whether to use cache
            tool_context: Optional tool context

        Returns:
            JSON string with extracted content
        """
        logger.info(f"[fetch_url] Fetching: {url}")

        # Check cache first
        if use_cache and self.cache_enabled:
            cached = await self._get_from_cache(url)
            if cached:
                logger.info(f"[fetch_url] Cache hit for: {url}")
                cached["from_cache"] = True
                return self._success(cached, metadata={"cached": True})

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
            result = await self._extract_content(html_content, extract_type, url)

            # Store in cache
            if use_cache and self.cache_enabled:
                await self._save_to_cache(url, result)

            return self._success(result, metadata={"cached": False})

        except httpx.TimeoutException:
            return self._error(
                message="Request timeout",
                code="TIMEOUT",
                details={"url": url, "timeout": timeout}
            )
        except httpx.HTTPStatusError as e:
            return self._error(
                message=f"HTTP error: {e.response.status_code}",
                code="HTTP_ERROR",
                details={"url": url, "status_code": e.response.status_code}
            )
        except Exception as e:
            logger.error(f"Fetch URL error: {e}", exc_info=True)
            return self._error(
                message=str(e),
                code="FETCH_ERROR",
                details={"url": url}
            )

    async def _extract_content(
        self,
        html: str,
        extract_type: str,
        url: str
    ) -> Dict[str, Any]:
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

        elif extract_type == "main_content" or extract_type == "article":
            # Use readability to extract main content
            doc = Document(html)
            main_content = doc.summary()
            result["content"] = main_content
            result["text_content"] = self.h2t.handle(main_content)

            # Try to get lead image
            if hasattr(doc, 'main_image') and doc.main_image():
                result["lead_image_url"] = doc.main_image()

        elif extract_type == "text_only":
            result["text_content"] = self.h2t.handle(html)

        # Calculate word count
        if "text_content" in result:
            result["word_count"] = len(result["text_content"].split())

        return result

    def _get_cache_key(self, url: str) -> Path:
        """Generate cache file path from URL"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.json"

    async def _get_from_cache(self, url: str) -> Optional[Dict]:
        """Get content from cache if valid"""
        cache_file = self._get_cache_key(url)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)

            # Check TTL
            cached_at = datetime.fromisoformat(cached.get("fetched_at", ""))
            age = (datetime.now() - cached_at).total_seconds()

            if age > self.cache_ttl:
                cache_file.unlink()  # Remove expired cache
                return None

            return cached

        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None

    async def _save_to_cache(self, url: str, data: Dict):
        """Save content to cache"""
        cache_file = self._get_cache_key(url)

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

# Global instance
_tool_instance = None

def get_tool() -> FetchUrlTool:
    """Get or create the fetch URL tool instance"""
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = FetchUrlTool()
    return _tool_instance

async def fetch_url(
    url: str,
    timeout: int = 10,
    extract_type: str = "main_content",
    use_cache: bool = True,
    tool_context: Optional[Any] = None
) -> str:
    """
    Fetch URL content

    Args:
        url: Target URL
        timeout: Timeout in seconds
        extract_type: Content extraction type (full, main_content, article, text_only)
        use_cache: Whether to use cache
        tool_context: Optional tool context

    Returns:
        JSON string with extracted content
    """
    tool = get_tool()
    return await tool.execute(
        url=url,
        timeout=timeout,
        extract_type=extract_type,
        use_cache=use_cache,
        tool_context=tool_context
    )
