#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MCP Tool: Vector Search

Wrapper around VectorMemoryService for semantic search.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List

from .base_mcp_tool import BaseMCPTool


logger = logging.getLogger(__name__)


class VectorSearchTool(BaseMCPTool):
    """Vector search tool wrapping VectorMemoryService"""

    def __init__(self):
        super().__init__(
            name="vector_search",
            description="Semantic vector search in knowledge base"
        )
        self.vector_service = None
        self._init_vector_service()

    def _init_vector_service(self):
        """Initialize vector memory service"""
        try:
            from backend.memory.core.core.hierarchical_memory_manager import HierarchicalMemoryManager
            from backend.memory.core.core.l2_short_term_layer import ShortTermMemoryLayer

            # Try to get existing instance
            try:
                self.vector_service = HierarchicalMemoryManager.get_instance()
                logger.info("VectorSearch: Using existing HierarchicalMemoryManager")
            except Exception:
                # Create new instance
                self.vector_service = HierarchicalMemoryManager()
                logger.info("VectorSearch: Created new HierarchicalMemoryManager")

        except ImportError as e:
            logger.warning(f"VectorMemoryService not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to initialize vector service: {e}")

    async def execute(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None,
        tool_context: Optional[Any] = None
    ) -> str:
        """
        Execute vector search

        Args:
            query: Search query
            collection: Collection name
            top_k: Number of results to return
            filter_metadata: Optional metadata filter
            tool_context: Optional tool context

        Returns:
            JSON string with search results
        """
        logger.info(f"[vector_search] Searching: {query} in {collection}")

        if not self.vector_service:
            return self._error(
                message="VectorMemoryService not initialized",
                code="SERVICE_UNAVAILABLE"
            )

        try:
            # Try different search methods based on available service
            results = []

            # Try HierarchicalMemoryManager search
            if hasattr(self.vector_service, 'search'):
                vector_results = await self.vector_service.search(
                    query_text=query,
                    top_k=top_k,
                    layer="l2"  # Search in short-term memory
                )
                results = self._format_hierarchical_results(vector_results)

            # Try direct vector search if available
            elif hasattr(self.vector_service, 'vector_search'):
                vector_results = await self.vector_service.vector_search(
                    query=query,
                    collection=collection,
                    top_k=top_k,
                    filter_metadata=filter_metadata
                )
                results = self._format_vector_results(vector_results)

            metadata = {
                "query": query,
                "collection": collection,
                "total_results": len(results)
            }

            return self._success({"results": results}, metadata=metadata)

        except Exception as e:
            logger.error(f"Vector search error: {e}", exc_info=True)
            return self._error(
                message=str(e),
                code="SEARCH_ERROR",
                details={"query": query, "collection": collection}
            )

    def _format_hierarchical_results(self, raw_results: List) -> List[Dict]:
        """Format results from HierarchicalMemoryManager"""
        formatted = []
        for result in raw_results:
            if isinstance(result, dict):
                formatted.append({
                    "id": result.get("id", ""),
                    "content": result.get("content", result.get("text", "")),
                    "score": result.get("score", result.get("similarity", 0.0)),
                    "metadata": result.get("metadata", {})
                })
            else:
                formatted.append({
                    "content": str(result),
                    "score": 0.0
                })
        return formatted

    def _format_vector_results(self, raw_results: List) -> List[Dict]:
        """Format results from vector search"""
        formatted = []
        for result in raw_results:
            if isinstance(result, dict):
                formatted.append({
                    "id": result.get("id", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", result.get("similarity", 0.0)),
                    "metadata": result.get("metadata", {})
                })
        return formatted

    async def add_documents(
        self,
        documents: List[Dict],
        collection: str = "default"
    ) -> str:
        """
        Add documents to vector store

        Args:
            documents: List of documents with content and metadata
            collection: Collection name

        Returns:
            JSON string with result
        """
        logger.info(f"[vector_search] Adding {len(documents)} documents to {collection}")

        if not self.vector_service:
            return self._error(
                message="VectorMemoryService not initialized",
                code="SERVICE_UNAVAILABLE"
            )

        try:
            added_count = 0

            for doc in documents:
                content = doc.get("content", "")
                metadata = doc.get("metadata", {})

                if not content:
                    continue

                # Try different add methods
                if hasattr(self.vector_service, 'add'):
                    await self.vector_service.add(
                        text=content,
                        metadata=metadata,
                        layer="l2"
                    )
                    added_count += 1
                elif hasattr(self.vector_service, 'add_document'):
                    await self.vector_service.add_document(
                        document=content,
                        collection=collection,
                        metadata=metadata
                    )
                    added_count += 1

            return self._success({
                "added_count": added_count,
                "collection": collection
            })

        except Exception as e:
            logger.error(f"Add documents error: {e}", exc_info=True)
            return self._error(
                message=str(e),
                code="ADD_ERROR",
                details={"collection": collection}
            )


# Global instance
_tool_instance = None


def get_tool() -> VectorSearchTool:
    """Get or create the vector search tool instance"""
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = VectorSearchTool()
    return _tool_instance


async def vector_search(
    query: str,
    collection: str = "default",
    top_k: int = 5,
    filter_metadata: Optional[Dict] = None,
    tool_context: Optional[Any] = None
) -> str:
    """
    Execute vector search

    Args:
        query: Search query
        collection: Collection name
        top_k: Number of results to return
        filter_metadata: Optional metadata filter
        tool_context: Optional tool context

    Returns:
        JSON string with search results
    """
    tool = get_tool()
    return await tool.execute(
        query=query,
        collection=collection,
        top_k=top_k,
        filter_metadata=filter_metadata,
        tool_context=tool_context
    )
