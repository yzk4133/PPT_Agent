"""
LangChain Native Tool: Search Images

Implements image search functionality using Unsplash and Pexels APIs.
"""

import os
import logging
from typing import Literal

import httpx
from langchain_core.tools import StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field

from backend.tools.core.monitoring import monitor_tool
from backend.tools.application.tool_registry import get_native_registry

# Configuration
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
UNSPLASH_API = "https://api.unsplash.com/search/photos"
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
PEXELS_API = "https://api.pexels.com/v1/search"

logger = logging.getLogger(__name__)


# Input schema
class SearchImagesInput(BaseModel):
    """Image search input schema"""

    query: str = Field(description="Search query for images")
    num_results: int = Field(
        default=5, ge=1, le=10, description="Number of images to return (1-10)"
    )
    orientation: Literal["landscape", "portrait", "squarish"] = Field(
        default="landscape", description="Image orientation"
    )
    size: Literal["small", "medium", "large", "original"] = Field(
        default="large", description="Image size"
    )
    color: Literal[
        "any", "black_white", "black", "white", "yellow", "orange", "red", "purple", "green", "blue"
    ] = Field(default="any", description="Color filter")
    source: Literal["unsplash", "pexels"] = Field(
        default="unsplash", description="Image source API"
    )


@monitor_tool
async def search_images(
    query: str,
    num_results: int = 5,
    orientation: str = "landscape",
    size: str = "large",
    color: str = "any",
    source: str = "unsplash",
) -> dict:
    """
    Search for images using Unsplash or Pexels APIs

    Finds high-quality images based on search query. Supports various
    orientations, sizes, and color filters.

    Args:
        query: Search query string
        num_results: Number of results (1-10)
        orientation: Image orientation (landscape, portrait, squarish)
        size: Image size (small, medium, large, original)
        color: Color filter
        source: Image API (unsplash or pexels)

    Returns:
        Dictionary with image results including URLs and metadata
    """
    logger.info(f"[search_images] Searching: {query}")

    # Validate num_results
    num_results = max(1, min(num_results, 10))

    try:
        if source == "unsplash":
            if not UNSPLASH_ACCESS_KEY:
                raise ValueError("UNSPLASH_ACCESS_KEY not configured")
            images = await _search_unsplash(query, num_results, orientation, size, color)
        elif source == "pexels":
            if not PEXELS_API_KEY:
                raise ValueError("PEXELS_API_KEY not configured")
            images = await _search_pexels(query, num_results, orientation)
        else:
            raise ValueError(f"Unsupported image source: {source}")

        logger.info(f"[search_images] Found {len(images)} images")
        return {"images": images, "total": len(images), "query": query, "source": source}

    except Exception as e:
        logger.error(f"[search_images] Error: {e}", exc_info=True)
        raise


async def _search_unsplash(
    query: str, num_results: int, orientation: str, size: str, color: str
) -> list:
    """Search using Unsplash API"""
    params = {
        "query": query,
        "per_page": num_results,
        "orientation": orientation,
    }

    # Add color filter if specified
    if color and color != "any":
        color_map = {
            "black_white": "black_and_white",
            "black": "black",
            "white": "white",
            "yellow": "yellow",
            "orange": "orange",
            "red": "red",
            "purple": "purple",
            "green": "green",
            "blue": "blue",
        }
        if color in color_map:
            params["color"] = color_map[color]

    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(UNSPLASH_API, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

    # Parse results
    images = []
    for photo in data.get("results", []):
        urls = photo.get("urls", {})

        images.append(
            {
                "url": urls.get(size, urls.get("regular", "")),
                "thumbnail": urls.get("thumb", urls.get("small", "")),
                "description": photo.get("description") or photo.get("alt_description", ""),
                "photographer": photo["user"].get("name", ""),
                "photographer_url": photo["user"].get("links", {}).get("html", ""),
                "width": photo.get("width"),
                "height": photo.get("height"),
                "source": "unsplash",
                "id": photo.get("id"),
            }
        )

    return images


async def _search_pexels(query: str, num_results: int, orientation: str) -> list:
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

    headers = {"Authorization": PEXELS_API_KEY}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(PEXELS_API, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

    # Parse results
    images = []
    for photo in data.get("photos", []):
        src = photo.get("src", {})

        images.append(
            {
                "url": src.get("large2x", src.get("large", "")),
                "thumbnail": src.get("small", src.get("medium", "")),
                "description": photo.get("alt", ""),
                "photographer": photo.get("photographer", ""),
                "photographer_url": photo.get("photographer_url", ""),
                "width": photo.get("width"),
                "height": photo.get("height"),
                "source": "pexels",
                "id": photo.get("id"),
            }
        )

    return images


# Create LangChain StructuredTool
tool = StructuredTool.from_function(
    func=search_images,
    name="search_images",
    description="Search for images using Unsplash or Pexels APIs. Use this to find high-quality images for presentations.",
    args_schema=SearchImagesInput,
)

# Auto-register with global registry
registry = get_native_registry()
registry.register_tool(tool, category=registry.MEDIA)

__all__ = ["tool", "search_images"]
