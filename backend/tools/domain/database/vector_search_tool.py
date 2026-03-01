"""
LangChain Native Tool: Vector Search

Semantic vector search in knowledge base using vector embeddings.
"""

import logging
from typing import Optional, Dict, List

from langchain_core.tools import StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field

from backend.tools.core.monitoring import monitor_tool
from backend.tools.application.tool_registry import get_native_registry

logger = logging.getLogger(__name__)

# Vector service cache
_vector_service = None


def _init_vector_service():
    """Initialize vector memory service"""
    global _vector_service

    if _vector_service is not None:
        return _vector_service

    try:
        from backend.memory.core.core.hierarchical_memory_manager import HierarchicalMemoryManager

        # Try to get existing instance
        try:
            _vector_service = HierarchicalMemoryManager.get_instance()
            logger.info("[vector_search] Using existing HierarchicalMemoryManager")
        except Exception:
            # Create new instance
            _vector_service = HierarchicalMemoryManager()
            logger.info("[vector_search] Created new HierarchicalMemoryManager")

    except ImportError as e:
        logger.warning(f"[vector_search] VectorMemoryService not available: {e}")
        _vector_service = None
    except Exception as e:
        logger.warning(f"[vector_search] Failed to initialize vector service: {e}")
        _vector_service = None

    return _vector_service


# Input schema
class VectorSearchInput(BaseModel):
    """Vector search input schema"""

    query: str = Field(description="Search query for semantic search")
    collection: str = Field(default="default", description="Collection name to search")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")


@monitor_tool
async def vector_search(query: str, collection: str = "default", top_k: int = 5) -> dict:
    """
    Execute semantic vector search in knowledge base

    Performs semantic search using vector embeddings to find relevant
    content from the knowledge base.

    Args:
        query: Search query text
        collection: Collection name to search
        top_k: Number of results to return (1-20)

    Returns:
        Dictionary with search results including content and scores

    Note:
        This tool requires the vector memory service to be initialized.
        The service uses embeddings to find semantically similar content.
    """
    logger.info(f"[vector_search] Searching: {query} in {collection}")

    vector_service = _init_vector_service()

    if not vector_service:
        raise RuntimeError(
            "VectorMemoryService not initialized. Check memory system configuration."
        )

    try:
        # Validate top_k
        top_k = max(1, min(top_k, 20))

        results = []

        # Try HierarchicalMemoryManager search
        if hasattr(vector_service, "search"):
            vector_results = await vector_service.search(
                query_text=query, top_k=top_k, layer="l2"  # Search in short-term memory
            )
            results = _format_hierarchical_results(vector_results)

        # Try direct vector search if available
        elif hasattr(vector_service, "vector_search"):
            vector_results = await vector_service.vector_search(
                query=query, collection=collection, top_k=top_k
            )
            results = _format_vector_results(vector_results)

        logger.info(f"[vector_search] Found {len(results)} results")

        return {"results": results, "total": len(results), "query": query, "collection": collection}

    except Exception as e:
        logger.error(f"[vector_search] Error: {e}", exc_info=True)
        raise


def _format_hierarchical_results(raw_results: List) -> List[Dict]:
    """Format results from HierarchicalMemoryManager"""
    formatted = []
    for result in raw_results:
        if isinstance(result, dict):
            formatted.append(
                {
                    "id": result.get("id", ""),
                    "content": result.get("content", result.get("text", "")),
                    "score": result.get("score", result.get("similarity", 0.0)),
                    "metadata": result.get("metadata", {}),
                }
            )
        else:
            formatted.append({"content": str(result), "score": 0.0})
    return formatted


def _format_vector_results(raw_results: List) -> List[Dict]:
    """Format results from vector search"""
    formatted = []
    for result in raw_results:
        if isinstance(result, dict):
            formatted.append(
                {
                    "id": result.get("id", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", result.get("similarity", 0.0)),
                    "metadata": result.get("metadata", {}),
                }
            )
    return formatted


# Create LangChain StructuredTool
tool = StructuredTool.from_function(
    func=vector_search,
    name="vector_search",
    description="Semantic vector search in knowledge base. Use this to find relevant content using semantic similarity.",
    args_schema=VectorSearchInput,
)

# Auto-register with global registry
registry = get_native_registry()
registry.register_tool(tool, category=registry.VECTOR)

__all__ = ["tool", "vector_search"]
