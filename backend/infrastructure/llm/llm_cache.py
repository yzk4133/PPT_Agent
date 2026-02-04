"""
LLM Request Cache

提供LLM请求的缓存功能，避免重复的LLM调用，节省成本和时间。

特性：
- 基于内容hash的缓存键生成
- 可配置的TTL（生存时间）
- 缓存统计（命中率/未命中率）
- 支持同步和异步缓存操作
"""

import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

class LLMRequestCache:
    """
    LLM请求缓存类

    使用内存缓存LLM响应，避免重复调用
    """

    def __init__(self, default_ttl_seconds: int = 3600, max_size: int = 10000):
        """
        初始化缓存

        Args:
            default_ttl_seconds: 默认缓存过期时间（秒）
            max_size: 最大缓存条目数
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl_seconds = default_ttl_seconds
        self.max_size = max_size

        # 统计信息
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def generate_cache_key(
        self,
        model: str,
        messages: list,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> str:
        """
        生成缓存键

        基于LLM请求参数生成唯一的缓存键

        Args:
            model: 模型名称
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            缓存键（SHA256 hash）
        """
        # 创建规范化输入字典
        cache_input = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "kwargs": kwargs,
        }

        # 序列化为JSON字符串（排序确保一致性）
        cache_str = json.dumps(cache_input, sort_keys=True)

        # 生成SHA256 hash作为缓存键
        return hashlib.sha256(cache_str.encode()).hexdigest()

    def get(self, cache_key: str) -> Optional[Any]:
        """
        从缓存获取响应

        Args:
            cache_key: 缓存键

        Returns:
            缓存的响应，如果不存在或已过期返回None
        """
        if cache_key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[cache_key]

        # 检查是否过期
        if time.time() > entry["expires_at"]:
            # 缓存过期，删除
            del self._cache[cache_key]
            self._misses += 1
            logger.debug(f"Cache entry expired: {cache_key[:16]}...")
            return None

        self._hits += 1
        logger.debug(f"Cache hit: {cache_key[:16]}...")
        return entry["response"]

    def set(
        self,
        cache_key: str,
        response: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        将响应存入缓存

        Args:
            cache_key: 缓存键
            response: LLM响应
            ttl_seconds: 过期时间（秒），None使用默认值

        Returns:
            是否成功
        """
        # 检查缓存大小限制
        if len(self._cache) >= self.max_size:
            self._evict_lru()

        ttl = ttl_seconds or self.default_ttl_seconds
        expires_at = time.time() + ttl

        self._cache[cache_key] = {
            "response": response,
            "created_at": time.time(),
            "expires_at": expires_at,
            "ttl": ttl,
            "last_accessed": time.time(),
        }

        logger.debug(f"Cached response: {cache_key[:16]}... (TTL={ttl}s)")
        return True

    def _evict_lru(self):
        """淘汰最久未使用的缓存条目"""
        if not self._cache:
            return

        # 找到最久未访问的条目
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k]["last_accessed"])

        del self._cache[lru_key]
        self._evictions += 1
        logger.info(f"Evicted LRU cache entry: {lru_key[:16]}...")

    def clear(self):
        """清空所有缓存"""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} cache entries")

    def cleanup_expired(self):
        """清理所有已过期的缓存条目"""
        current_time = time.time()
        expired_keys = [
            k for k, v in self._cache.items()
            if current_time > v["expires_at"]
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计字典
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "evictions": self._evictions,
        }

    def reset_stats(self):
        """重置统计信息"""
        self._hits = 0
        self._misses = 0
        self._evictions = 0

# 全局缓存实例
_global_cache: Optional[LLMRequestCache] = None

def get_global_cache() -> LLMRequestCache:
    """获取全局LLM缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = LLMRequestCache()
    return _global_cache

def cached_llm_call(ttl_seconds: Optional[int] = None):
    """
    LLM调用缓存装饰器

    Args:
        ttl_seconds: 缓存过期时间（秒）

    Returns:
        装饰器函数

    Example:
        @cached_llm_call(ttl_seconds=1800)
        async def call_llm(model, messages, temperature, max_tokens):
            ...
    """
    cache = get_global_cache()

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = cache.generate_cache_key(*args, **kwargs)

            # 尝试从缓存获取
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return cached_response

            # 缓存未命中，调用LLM
            response = await func(*args, **kwargs)

            # 存入缓存
            cache.set(cache_key, response, ttl_seconds=ttl_seconds)

            return response

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = cache.generate_cache_key(*args, **kwargs)

            # 尝试从缓存获取
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return cached_response

            # 缓存未命中，调用LLM
            response = func(*args, **kwargs)

            # 存入缓存
            cache.set(cache_key, response, ttl_seconds=ttl_seconds)

            return response

        # 根据函数类型返回对应的wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

if __name__ == "__main__":
    # 测试缓存功能
    logging.basicConfig(level=logging.INFO)

    cache = LLMRequestCache(default_ttl_seconds=60)

    # 模拟LLM请求参数
    model = "gpt-4"
    messages = [{"role": "user", "content": "Hello"}]
    temperature = 0.7
    max_tokens = 1000

    # 生成缓存键
    cache_key = cache.generate_cache_key(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )

    logger.info(f"Generated cache key: {cache_key[:32]}...")

    # 测试缓存存取
    cache.set(cache_key, {"response": "Hello! How can I help you?"})
    cached_response = cache.get(cache_key)

    logger.info(f"Cached response: {cached_response}")

    # 测试缓存统计
    stats = cache.get_stats()
    logger.info(f"Cache stats: {stats}")
