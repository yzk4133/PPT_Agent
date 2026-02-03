"""
Agent Cache Mechanism

Provides intelligent caching for agent results to reduce redundant LLM calls.
Supports TTL-based expiration, thread-safe operations, and cache statistics.
"""

import hashlib
import json
import logging
import threading
import time
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict


logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """
    Cache entry with metadata.

    Attributes:
        key: Cache key
        value: Cached value
        created_at: Creation timestamp
        accessed_at: Last access timestamp
        access_count: Number of times accessed
        ttl_seconds: Time to live in seconds (None for no expiration)
        size_bytes: Approximate size in bytes
    """
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    size_bytes: int = 0

    def is_expired(self) -> bool:
        """Check if this entry has expired"""
        if self.ttl_seconds is None:
            return False
        now = datetime.now()
        age = (now - self.created_at).total_seconds()
        return age > self.ttl_seconds

    def touch(self) -> None:
        """Update access timestamp and increment count"""
        self.accessed_at = datetime.now()
        self.access_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for debugging"""
        return {
            "key": self.key[:50] + "..." if len(self.key) > 50 else self.key,
            "created_at": self.created_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat(),
            "access_count": self.access_count,
            "ttl_seconds": self.ttl_seconds,
            "size_bytes": self.size_bytes,
            "expired": self.is_expired()
        }


@dataclass
class CacheStats:
    """
    Cache statistics.

    Attributes:
        hits: Number of cache hits
        misses: Number of cache misses
        evictions: Number of evicted entries
        total_entries: Current number of entries
        total_size_bytes: Total cache size in bytes
        hit_rate: Cache hit rate (0.0 - 1.0)
    """
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_entries: int = 0
    total_size_bytes: int = 0

    @property
    def total_requests(self) -> int:
        """Total number of requests"""
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        """Cache hit rate (0.0 - 1.0)"""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "total_requests": self.total_requests,
            "total_entries": self.total_entries,
            "total_size_bytes": self.total_size_bytes,
            "total_size_mb": round(self.total_size_bytes / (1024 * 1024), 2),
            "hit_rate": round(self.hit_rate * 100, 2),
            "miss_rate": round((1 - self.hit_rate) * 100, 2)
        }


class AgentCache:
    """
    Agent cache with TTL support and statistics.

    Features:
    - Thread-safe operations
    - TTL-based expiration
    - LRU eviction when size limit is reached
    - Cache statistics tracking
    - Support for different cache key strategies
    """

    # Default TTL values (in seconds)
    DEFAULT_TTL = 3600  # 1 hour
    REQUIREMENT_TTL = 1800  # 30 minutes
    RESEARCH_TTL = 3600  # 1 hour
    FRAMEWORK_TTL = 1800  # 30 minutes
    CONTENT_TTL = 900  # 15 minutes

    def __init__(
        self,
        max_size_mb: float = 100.0,
        max_entries: int = 1000,
        enable_stats: bool = True
    ):
        """
        Initialize the agent cache.

        Args:
            max_size_mb: Maximum cache size in MB
            max_entries: Maximum number of entries
            enable_stats: Whether to track statistics
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._max_size_bytes = int(max_size_mb * 1024 * 1024)
        self._max_entries = max_entries
        self._enable_stats = enable_stats
        self._stats = CacheStats()
        self._agent_stats: Dict[str, CacheStats] = defaultdict(CacheStats)

    def get(
        self,
        agent_name: str,
        input_data: Any,
        default: Any = None
    ) -> Optional[Any]:
        """
        Get a cached value for an agent.

        Args:
            agent_name: Name of the agent
            input_data: Input data used as cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        key = self._make_key(agent_name, input_data)

        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                if self._enable_stats:
                    self._stats.misses += 1
                    self._agent_stats[agent_name].misses += 1
                logger.debug(f"Cache miss: {agent_name}:{key[:30]}...")
                return default

            if entry.is_expired():
                # Expired entry, remove it
                del self._cache[key]
                if self._enable_stats:
                    self._stats.misses += 1
                    self._agent_stats[agent_name].misses += 1
                    self._stats.total_entries = len(self._cache)
                logger.debug(f"Cache expired: {agent_name}:{key[:30]}...")
                return default

            # Cache hit
            entry.touch()
            if self._enable_stats:
                self._stats.hits += 1
                self._agent_stats[agent_name].hits += 1
            logger.debug(f"Cache hit: {agent_name}:{key[:30]}...")
            return entry.value

    def set(
        self,
        agent_name: str,
        input_data: Any,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Set a cached value for an agent.

        Args:
            agent_name: Name of the agent
            input_data: Input data used as cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (None for default)

        Returns:
            True if successfully cached
        """
        key = self._make_key(agent_name, input_data)
        now = datetime.now()

        # Determine TTL based on agent type
        if ttl_seconds is None:
            ttl_seconds = self._get_default_ttl(agent_name)

        # Calculate size
        value_size = self._estimate_size(value)

        with self._lock:
            # Check if we need to evict entries
            self._ensure_space(value_size)

            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                accessed_at=now,
                access_count=0,
                ttl_seconds=ttl_seconds,
                size_bytes=value_size
            )

            # Store entry
            self._cache[key] = entry

            if self._enable_stats:
                self._stats.total_entries = len(self._cache)
                self._stats.total_size_bytes = sum(e.size_bytes for e in self._cache.values())

            logger.debug(f"Cached: {agent_name}:{key[:30]}... (size: {value_size} bytes, TTL: {ttl_seconds}s)")
            return True

    def invalidate(self, agent_name: str, input_data: Any = None) -> int:
        """
        Invalidate cache entries.

        Args:
            agent_name: Name of the agent (or None for all)
            input_data: Specific input data to invalidate (None for all)

        Returns:
            Number of entries invalidated
        """
        with self._lock:
            if input_data is None:
                # Invalidate all entries for this agent
                prefix = f"{agent_name}:"
                keys_to_remove = [k for k in self._cache.keys() if k.startswith(prefix)]
                for key in keys_to_remove:
                    del self._cache[key]
                return len(keys_to_remove)
            else:
                # Invalidate specific entry
                key = self._make_key(agent_name, input_data)
                if key in self._cache:
                    del self._cache[key]
                    if self._enable_stats:
                        self._stats.total_entries = len(self._cache)
                        self._stats.total_size_bytes = sum(e.size_bytes for e in self._cache.values())
                    return 1
                return 0

    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            if self._enable_stats:
                self._stats.total_entries = 0
                self._stats.total_size_bytes = 0
            logger.info("Cache cleared")

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
            for key in expired_keys:
                del self._cache[key]
                if self._enable_stats:
                    self._stats.evictions += 1

            if self._enable_stats:
                self._stats.total_entries = len(self._cache)
                self._stats.total_size_bytes = sum(e.size_bytes for e in self._cache.values())

            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired entries")
            return len(expired_keys)

    def get_stats(self, agent_name: Optional[str] = None) -> CacheStats:
        """
        Get cache statistics.

        Args:
            agent_name: Specific agent name or None for global stats

        Returns:
            Cache statistics
        """
        with self._lock:
            if agent_name:
                stats = self._agent_stats.get(agent_name, CacheStats())
                # Update current counts
                agent_entries = sum(1 for k in self._cache.keys() if k.startswith(f"{agent_name}:"))
                stats.total_entries = agent_entries
                return stats
            else:
                # Return copy of global stats
                stats = CacheStats(
                    hits=self._stats.hits,
                    misses=self._stats.misses,
                    evictions=self._stats.evictions,
                    total_entries=len(self._cache),
                    total_size_bytes=sum(e.size_bytes for e in self._cache.values())
                )
                return stats

    def get_entries(self, agent_name: Optional[str] = None) -> list[CacheEntry]:
        """
        Get cache entries for debugging.

        Args:
            agent_name: Filter by agent name or None for all

        Returns:
            List of cache entries
        """
        with self._lock:
            if agent_name:
                return [v for k, v in self._cache.items() if k.startswith(f"{agent_name}:")]
            else:
                return list(self._cache.values())

    def _make_key(self, agent_name: str, input_data: Any) -> str:
        """
        Create a cache key from agent name and input data.

        Args:
            agent_name: Name of the agent
            input_data: Input data

        Returns:
            Cache key string
        """
        # Convert input to string for hashing
        if isinstance(input_data, dict):
            # Sort dict keys for consistent hashing
            normalized = json.dumps(input_data, sort_keys=True, ensure_ascii=False)
        elif isinstance(input_data, (list, tuple)):
            normalized = json.dumps(input_data, ensure_ascii=False)
        else:
            normalized = str(input_data)

        # Create hash
        hash_obj = hashlib.sha256(normalized.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()[:16]

        return f"{agent_name}:{hash_hex}"

    def _get_default_ttl(self, agent_name: str) -> int:
        """Get default TTL for an agent type"""
        if "requirement" in agent_name.lower():
            return self.REQUIREMENT_TTL
        elif "research" in agent_name.lower():
            return self.RESEARCH_TTL
        elif "framework" in agent_name.lower():
            return self.FRAMEWORK_TTL
        elif "content" in agent_name.lower():
            return self.CONTENT_TTL
        else:
            return self.DEFAULT_TTL

    def _estimate_size(self, value: Any) -> int:
        """Estimate size in bytes of a value"""
        try:
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, (dict, list)):
                return len(json.dumps(value).encode('utf-8'))
            else:
                return len(str(value).encode('utf-8'))
        except:
            return 0

    def _ensure_space(self, new_size: int) -> None:
        """
        Ensure there's space for a new entry by evicting old entries.

        Uses LRU (Least Recently Used) eviction strategy.

        Args:
            new_size: Size of the new entry in bytes
        """
        # Check entry count limit
        while len(self._cache) >= self._max_entries:
            self._evict_lru()

        # Check size limit
        current_size = sum(e.size_bytes for e in self._cache.values())
        while current_size + new_size > self._max_size_bytes:
            if not self._cache:
                break
            self._evict_lru()
            current_size = sum(e.size_bytes for e in self._cache.values())

    def _evict_lru(self) -> None:
        """Evict the least recently used entry"""
        if not self._cache:
            return

        # Find entry with oldest accessed_at
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].accessed_at)
        del self._cache[lru_key]

        if self._enable_stats:
            self._stats.evictions += 1
            self._stats.total_entries = len(self._cache)
            self._stats.total_size_bytes = sum(e.size_bytes for e in self._cache.values())

        logger.debug(f"Evicted LRU entry: {lru_key[:50]}...")


# Global cache instance
_global_cache: Optional[AgentCache] = None
_cache_lock = threading.Lock()


def get_agent_cache() -> AgentCache:
    """
    Get the global agent cache instance.

    Returns:
        AgentCache instance
    """
    global _global_cache
    with _cache_lock:
        if _global_cache is None:
            _global_cache = AgentCache()
        return _global_cache


def reset_agent_cache() -> AgentCache:
    """
    Reset the global agent cache with a new instance.

    Returns:
        New AgentCache instance
    """
    global _global_cache
    with _cache_lock:
        _global_cache = AgentCache()
        return _global_cache


# Decorator for automatic caching
def cached(ttl_seconds: Optional[int] = None):
    """
    Decorator for automatic caching of agent results.

    Args:
        ttl_seconds: Custom TTL in seconds

    Example:
        @cached(ttl_seconds=1800)
        async def my_agent_function(input_data):
            # Expensive computation
            return result
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get agent name from function
            agent_name = func.__name__

            # Create cache key from args
            cache_key = {"args": args, "kwargs": kwargs}

            # Try to get from cache
            cache = get_agent_cache()
            cached_result = cache.get(agent_name, cache_key)

            if cached_result is not None:
                return cached_result

            # Not in cache, compute and store
            result = await func(*args, **kwargs)
            cache.set(agent_name, cache_key, result, ttl_seconds=ttl_seconds)

            return result
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test the cache
    logging.basicConfig(level=logging.DEBUG)

    cache = AgentCache(max_size_mb=1.0, max_entries=100)

    # Test basic operations
    print("=== Testing Basic Operations ===")

    # Set and get
    cache.set("RequirementParser", {"topic": "AI PPT", "pages": 10}, {"result": "parsed"})
    result = cache.get("RequirementParser", {"topic": "AI PPT", "pages": 10})
    print(f"First get: {result}")

    # Cache hit
    result = cache.get("RequirementParser", {"topic": "AI PPT", "pages": 10})
    print(f"Second get (should be hit): {result}")

    # Cache miss
    result = cache.get("RequirementParser", {"topic": "Different", "pages": 5})
    print(f"Different input (should be miss): {result}")

    # Test statistics
    print("\n=== Statistics ===")
    stats = cache.get_stats()
    print(json.dumps(stats.to_dict(), indent=2))

    # Test different agents
    cache.set("ResearchAgent", "AI trends", {"data": "research results"})
    cache.set("FrameworkDesigner", {"topic": "AI", "pages": 15}, {"framework": "designed"})

    print("\n=== All Cache Entries ===")
    entries = cache.get_entries()
    for entry in entries[:5]:
        print(entry.to_dict())

    # Test expiration
    print("\n=== Testing Expiration ===")
    cache.set("TestAgent", "expire_me", "value", ttl_seconds=1)
    time.sleep(2)
    result = cache.get("TestAgent", "expire_me")
    print(f"Expired entry (should be None): {result}")

    # Cleanup
    print("\n=== Cleanup ===")
    cache.cleanup_expired()
    print(f"Remaining entries: {len(cache.get_entries())}")
