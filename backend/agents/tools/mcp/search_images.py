#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MCP Tool: Search Images

Implements image search functionality using Unsplash API.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path

import httpx

from .base_mcp_tool import BaseMCPTool


# Configuration
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
UNSPLASH_API = "https://api.unsplash.com/search/photos"
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
PEXELS_API = "https://api.pexels.com/v1/search"

# Cache configuration
CACHE_DIR = Path(os.getenv("MCP_CACHE_DIR", "./data/mcp_cache"))
CACHE_ENABLED = os.getenv("MCP_CACHE_ENABLED", "true").lower() == "true"

logger = logging.getLogger(__name__)


class SearchImagesTool(BaseMCPTool):
    """Image search tool using Unsplash and Pexels APIs"""

    def __init__(self):
        super().__init__(
            name="search_images",
            description="Search for images using Unsplash API"
        )
        self.unsplash_key = UNSPLASH_ACCESS_KEY
        self.pexels_key = PEXELS_API_KEY
        self.cache_dir = CACHE_DIR
        self.cache_enabled = CACHE_ENABLED

    async def execute(
        self,
        query: str,
        num_results: int = 5,
        orientation: str = "landscape",
        size: str = "large",
        color: str = "any",
        source: str = "unsplash",
        tool_context: Optional[Any] = None
    ) -> str:
        """
        Search for images

        Args:
            query: Search query
            num_results: Number of results to return (default: 5, max: 10)
            orientation: Image orientation (landscape, portrait, squarish)
            size: Image size (small, medium, large, original)
            color: Color filter (any, black_white, black, white, yellow, orange, red, purple, green, blue)
            source: Image source (unsplash, pexels)
            tool_context: Optional tool context

        Returns:
            JSON string with image results
        """
        logger.info(f"[search_images] Searching: {query}")

        # Validate num_results
        num_results = max(1, min(num_results, 10))

        try:
            if source == "unsplash":
                if not self.unsplash_key:
                    return self._error(
                        message="UNSPLASH_ACCESS_KEY not configured",
                        code="MISSING_API_KEY"
                    )
                images = await self._search_unsplash(query, num_results, orientation, size, color)
            elif source == "pexels":
                if not self.pexels_key:
                    return self._error(
                        message="PEXELS_API_KEY not configured",
                        code="MISSING_API_KEY"
                    )
                images = await self._search_pexels(query, num_results, orientation)
            else:
                return self._error(
                    message=f"Unsupported image source: {source}",
                    code="UNSUPPORTED_SOURCE"
                )

            metadata = {
                "total_results": len(images),
                "query": query,
                "source": source
            }

            return self._success({"images": images}, metadata=metadata)

        except Exception as e:
            logger.error(f"Image search error: {e}", exc_info=True)
            return self._error(
                message=str(e),
                code="SEARCH_ERROR",
                details={"query": query, "source": source}
            )

    async def _search_unsplash(
        self,
        query: str,
        num_results: int,
        orientation: str,
        size: str,
        color: str
    ) -> list:
        """Search using Unsplash API"""
        params = {
            "query": query,
            "per_page": num_results,
            "orientation": orientation,
        }

        # Add color filter if specified
        if color and color != "any":
            # Map color names to Unsplash color values
            color_map = {
                "black_white": "black_and_white",
                "black": "black",
                "white": "white",
                "yellow": "yellow",
                "orange": "orange",
                "red": "red",
                "purple": "purple",
                "green": "green",
                "blue": "blue"
            }
            if color in color_map:
                params["color"] = color_map[color]

        headers = {
            "Authorization": f"Client-ID {self.unsplash_key}"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                UNSPLASH_API,
                headers=headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()

        # Parse results
        images = []
        for photo in data.get("results", []):
            urls = photo.get("urls", {})

            images.append({
                "url": urls.get(size, urls.get("regular", "")),
                "thumbnail": urls.get("thumb", urls.get("small", "")),
                "description": photo.get("description") or photo.get("alt_description", ""),
                "photographer": photo["user"].get("name", ""),
                "photographer_url": photo["user"].get("links", {}).get("html", ""),
                "width": photo.get("width"),
                "height": photo.get("height"),
                "source": "unsplash",
                "id": photo.get("id")
            })

        return images

    async def _search_pexels(
        self,
        query: str,
        num_results: int,
        orientation: str
    ) -> list:
        """Search using Pexels API"""
        params = {
            "query": query,
            "per_page": num_results,
        }

        # Map orientation to Pexels format
        if orientation == "portrait":
            params["orientation"] = "portrait"
        elif orientation == "landscape":
            params["orientation"] = "landscape"
        elif orientation == "squarish":
            params["orientation"] = "square"

        headers = {
            "Authorization": self.pexels_key
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                PEXELS_API,
                headers=headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()

        # Parse results
        images = []
        for photo in data.get("photos", []):
            # Get the appropriate size
            src = photo.get("src", {})

            images.append({
                "url": src.get("large2x", src.get("large", "")),
                "thumbnail": src.get("small", src.get("medium", "")),
                "description": photo.get("alt", ""),
                "photographer": photo.get("photographer", ""),
                "photographer_url": photo.get("photographer_url", ""),
                "width": photo.get("width"),
                "height": photo.get("height"),
                "source": "pexels",
                "id": photo.get("id")
            })

        return images


# Global instance
_tool_instance = None


def get_tool() -> SearchImagesTool:
    """Get or create the search images tool instance"""
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = SearchImagesTool()
    return _tool_instance


async def search_images(
    query: str,
    num_results: int = 5,
    orientation: str = "landscape",
    size: str = "large",
    color: str = "any",
    source: str = "unsplash",
    tool_context: Optional[Any] = None
) -> str:
    """
    Search for images

    Args:
        query: Search query
        num_results: Number of results to return (default: 5, max: 10)
        orientation: Image orientation (landscape, portrait, squarish)
        size: Image size (small, medium, large, original)
        color: Color filter (any, black_white, black, white, yellow, orange, red, purple, green, blue)
        source: Image source (unsplash, pexels)
        tool_context: Optional tool context

    Returns:
        JSON string with image results
    """
    tool = get_tool()
    return await tool.execute(
        query=query,
        num_results=num_results,
        orientation=orientation,
        size=size,
        color=color,
        source=source,
        tool_context=tool_context
    )
