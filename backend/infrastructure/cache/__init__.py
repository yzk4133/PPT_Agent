"""
Infrastructure Cache Module

Provides intelligent caching for agent results to reduce redundant LLM calls.
"""

from .agent_cache import (
    AgentCache,
    CacheEntry,
    CacheStats,
    get_agent_cache,
    reset_agent_cache,
    cached
)

__all__ = [
    "AgentCache",
    "CacheEntry",
    "CacheStats",
    "get_agent_cache",
    "reset_agent_cache",
    "cached",
]
