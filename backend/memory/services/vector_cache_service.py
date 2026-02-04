"""
向量缓存服务 - Vector Cache Service

减少向量嵌入API调用，优化性能：

1. 缓存向量嵌入 - 避免重复计算
2. 缓存预热 - 预加载常用向量
3. 缓存失效策略 - 智能淘汰
4. 批量操作 - 提升吞吐量

使用示例：
```python
cache_service = VectorCacheService()

# 获取向量（自动缓存）
embedding = await cache_service.get_embedding("用户查询文本")

# 批量获取
embeddings = await cache_service.get_embeddings(["文本1", "文本2"])

# 预热缓存
await cache_service.warm_cache(["常用问题1", "常用问题2"])
```
"""

import asyncio
import hashlib
import json
import logging
import os
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from functools import lru_cache

# 尝试导入OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

# ============================================================================
# 配置
# ============================================================================

class VectorCacheConfig:
    """向量缓存配置"""

    # 默认TTL（秒）
    DEFAULT_TTL = 7200  # 2小时

    # 缓存容量
    MAX_CACHE_SIZE = 10000

    # 批量操作大小
    BATCH_SIZE = 100

    # OpenAI配置
    EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_DIMENSION = 1536

    # 缓存预热
    WARMUP_PRIORITY_THRESHOLD = 3  # 访问次数>=3的键标记为高优先级

# ============================================================================
# 内存缓存实现
# ============================================================================

class LRUCache:
    """LRU缓存实现"""

    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, datetime] = {}
        self.access_counts: Dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        async with self._lock:
            if key not in self.cache:
                return None

            # 移动到末尾（最近使用）
            self.cache.move_to_end(key)
            self.access_counts[key] = self.access_counts.get(key, 0) + 1
            return self.cache[key]

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存值"""
        async with self._lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                # 检查容量
                if len(self.cache) >= self.capacity:
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                    self.timestamps.pop(oldest_key, None)
                    self.access_counts.pop(oldest_key, None)

            self.cache[key] = value
            self.timestamps[key] = datetime.now()

    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                self.timestamps.pop(key, None)
                self.access_counts.pop(key, None)
                return True
            return False

    async def clear(self):
        """清空缓存"""
        async with self._lock:
            self.cache.clear()
            self.timestamps.clear()
            self.access_counts.clear()

    async def size(self) -> int:
        """获取缓存大小"""
        async with self._lock:
            return len(self.cache)

    async def get_expired_keys(self, ttl_seconds: int) -> List[str]:
        """获取过期的键"""
        async with self._lock:
            now = datetime.now()
            expired = []
            for key, timestamp in self.timestamps.items():
                if (now - timestamp).total_seconds() > ttl_seconds:
                    expired.append(key)
            return expired

    async def cleanup_expired(self, ttl_seconds: int) -> int:
        """清理过期键"""
        expired_keys = await self.get_expired_keys(ttl_seconds)
        async with self._lock:
            for key in expired_keys:
                if key in self.cache:
                    del self.cache[key]
                    self.timestamps.pop(key, None)
                    self.access_counts.pop(key, None)
        return len(expired_keys)

    async def get_top_priority_keys(self, n: int = 100) -> List[str]:
        """获取访问次数最多的键"""
        async with self._lock:
            sorted_keys = sorted(
                self.access_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )
            return [key for key, _ in sorted_keys[:n]]

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        async with self._lock:
            return {
                "size": len(self.cache),
                "capacity": self.capacity,
                "usage_ratio": len(self.cache) / self.capacity if self.capacity > 0 else 0,
                "total_accesses": sum(self.access_counts.values()),
                "unique_keys": len(self.access_counts),
            }

# ============================================================================
# 向量缓存服务
# ============================================================================

class VectorCacheService:
    """
    向量缓存服务

    缓存向量嵌入，减少API调用。
    """

    def __init__(
        self,
        config: Optional[VectorCacheConfig] = None,
        redis_client=None,
    ):
        """
        初始化向量缓存服务

        Args:
            config: 缓存配置
            redis_client: Redis客户端（可选，用于分布式缓存）
        """
        self.config = config or VectorCacheConfig()
        self.memory_cache = LRUCache(capacity=self.config.MAX_CACHE_SIZE)
        self.redis = redis_client

        # OpenAI客户端
        if OPENAI_AVAILABLE:
            self.client = openai.AsyncOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
            )
        else:
            self.client = None
            logger.warning("OpenAI not available, vector cache disabled")

        # 统计信息
        self.stats = {
            "hits": 0,
            "misses": 0,
            "api_calls": 0,
            "cache_writes": 0,
        }
        self._lock = asyncio.Lock()

        # 后台清理任务
        self._cleanup_task = None

    def start_background_tasks(self):
        """启动后台任务"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_background_tasks(self):
        """停止后台任务"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _cleanup_loop(self):
        """后台清理循环"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次
                expired = await self.memory_cache.cleanup_expired(self.config.DEFAULT_TTL)
                if expired > 0:
                    logger.info(f"Cleaned up {expired} expired vector cache entries")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in vector cache cleanup: {e}")

    @staticmethod
    def _build_cache_key(text: str, model: str) -> str:
        """构建缓存键"""
        # 使用SHA256哈希避免键过长
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def get_embedding(
        self,
        text: str,
        model: Optional[str] = None,
        use_cache: bool = True,
    ) -> Optional[List[float]]:
        """
        获取文本的向量嵌入

        Args:
            text: 输入文本
            model: 嵌入模型
            use_cache: 是否使用缓存

        Returns:
            向量嵌入，失败返回None
        """
        if not self.client:
            return None

        model = model or self.config.EMBEDDING_MODEL
        cache_key = self._build_cache_key(text, model)

        # 尝试从缓存获取
        if use_cache:
            # 先查内存缓存
            cached = await self.memory_cache.get(cache_key)
            if cached is not None:
                async with self._lock:
                    self.stats["hits"] += 1
                logger.debug(f"Vector cache hit: {text[:50]}...")
                return cached

            # 再查Redis
            if self.redis:
                redis_key = f"vector_cache:{model}:{cache_key}"
                try:
                    cached_data = self.redis.get(redis_key)
                    if cached_data:
                        embedding = json.loads(cached_data)
                        # 写回内存缓存
                        await self.memory_cache.set(cache_key, embedding)
                        async with self._lock:
                            self.stats["hits"] += 1
                        logger.debug(f"Redis vector cache hit: {text[:50]}...")
                        return embedding
                except Exception as e:
                    logger.warning(f"Redis cache error: {e}")

        # 缓存未命中，调用API
        async with self._lock:
            self.stats["misses"] += 1
            self.stats["api_calls"] += 1

        try:
            response = await self.client.embeddings.create(
                model=model,
                input=text,
            )
            embedding = response.data[0].embedding

            # 写入缓存
            if use_cache:
                await self.memory_cache.set(cache_key, embedding)
                async with self._lock:
                    self.stats["cache_writes"] += 1

                # 写入Redis
                if self.redis:
                    redis_key = f"vector_cache:{model}:{cache_key}"
                    try:
                        self.redis.setex(
                            redis_key,
                            self.config.DEFAULT_TTL,
                            json.dumps(embedding),
                        )
                    except Exception as e:
                        logger.warning(f"Failed to write to Redis cache: {e}")

            return embedding

        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            return None

    async def get_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
        use_cache: bool = True,
    ) -> List[Optional[List[float]]]:
        """
        批量获取向量嵌入

        Args:
            texts: 输入文本列表
            model: 嵌入模型
            use_cache: 是否使用缓存

        Returns:
            向量嵌入列表
        """
        results = []

        for text in texts:
            embedding = await self.get_embedding(text, model, use_cache)
            results.append(embedding)

        return results

    async def warm_cache(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> int:
        """
        预热缓存

        Args:
            texts: 文本列表
            model: 嵌入模型

        Returns:
            成功预热数量
        """
        logger.info(f"Warming up vector cache with {len(texts)} texts")
        count = 0

        for text in texts:
            embedding = await self.get_embedding(text, model, use_cache=True)
            if embedding:
                count += 1

        logger.info(f"Cache warmup completed: {count}/{len(texts)} succeeded")
        return count

    async def warm_cache_by_priority(self, n: int = 100):
        """
        基于优先级预热缓存

        预热访问次数最多的N个键（需要已有缓存数据）。

        Args:
            n: 预热数量
        """
        # 这里需要从持久化存储获取高频文本
        # 简化实现，仅记录日志
        logger.info(f"Priority-based warmup requested for {n} keys")
        # 实际实现需要结合向量记忆服务

    async def invalidate(self, text: str, model: Optional[str] = None):
        """
        使缓存失效

        Args:
            text: 文本
            model: 模型
        """
        model = model or self.config.EMBEDDING_MODEL
        cache_key = self._build_cache_key(text, model)

        await self.memory_cache.delete(cache_key)

        if self.redis:
            redis_key = f"vector_cache:{model}:{cache_key}"
            try:
                self.redis.delete(redis_key)
            except Exception as e:
                logger.warning(f"Failed to invalidate Redis cache: {e}")

    async def invalidate_pattern(self, pattern: str):
        """
        批量使缓存失效

        Args:
            pattern: 键模式
        """
        # Redis模式删除
        if self.redis:
            try:
                keys = self.redis.keys(f"vector_cache:*{pattern}*")
                if keys:
                    self.redis.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} vector cache entries")
            except Exception as e:
                logger.warning(f"Failed to invalidate pattern: {e}")

    async def clear_cache(self):
        """清空所有缓存"""
        await self.memory_cache.clear()

        if self.redis:
            try:
                keys = self.redis.keys("vector_cache:*")
                if keys:
                    self.redis.delete(*keys)
                    logger.info(f"Cleared {len(keys)} Redis vector cache entries")
            except Exception as e:
                logger.warning(f"Failed to clear Redis cache: {e}")

        logger.info("Vector cache cleared")

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        cache_stats = await self.memory_cache.get_stats()

        hit_rate = 0.0
        total_accesses = self.stats["hits"] + self.stats["misses"]
        if total_accesses > 0:
            hit_rate = self.stats["hits"] / total_accesses

        return {
            "memory_cache": cache_stats,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "api_calls": self.stats["api_calls"],
            "cache_writes": self.stats["cache_writes"],
            "hit_rate": hit_rate,
            "api_calls_saved": self.stats["hits"],
        }

    async def optimize_cache(self):
        """优化缓存"""
        # 清理过期条目
        expired = await self.memory_cache.cleanup_expired(self.config.DEFAULT_TTL)

        # 如果缓存使用率过高，记录日志
        stats = await self.memory_cache.get_stats()
        if stats.get("usage_ratio", 0) > 0.9:
            logger.warning(
                f"Vector cache usage > 90%: "
                f"{stats['size']}/{stats['capacity']}"
            )

        return expired

# ============================================================================
# 全局实例
# ============================================================================

_global_vector_cache: Optional[VectorCacheService] = None

def get_vector_cache() -> VectorCacheService:
    """获取全局向量缓存服务实例"""
    global _global_vector_cache
    if _global_vector_cache is None:
        _global_vector_cache = VectorCacheService()
    return _global_vector_cache
