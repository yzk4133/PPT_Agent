"""
L1 瞬时内存层 (Transient Memory Layer)

特性：
- 纯Python字典存储，最快的访问速度
- 任务级生命周期 (seconds级别)
- LRU淘汰策略，自动清理低价值数据
- 重要性评分机制，优先保留高价值数据
- 提升规则：访问≥3次 或 重要性≥0.7 → 自动提升到L2
"""

import asyncio
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from .memory_layer_base import (
    BaseMemoryLayer,
    MemoryLayer,
    MemoryScope,
    MemoryMetadata,
    PromotionReason,
)

logger = logging.getLogger(__name__)


class LRUCache:
    """线程安全的LRU缓存实现"""

    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache: OrderedDict = OrderedDict()
        self.lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """获取数据并移动到末尾（最近使用）"""
        async with self.lock:
            if key not in self.cache:
                return None
            self.cache.move_to_end(key)
            return self.cache[key]

    async def set(self, key: str, value: Any):
        """设置数据，如果超容量则淘汰最旧的"""
        async with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value

            # LRU淘汰
            if len(self.cache) > self.capacity:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                logger.debug(f"LRU evicted key: {oldest_key}")

    async def delete(self, key: str) -> bool:
        """删除数据"""
        async with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        """检查是否存在"""
        async with self.lock:
            return key in self.cache

    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """获取所有键"""
        async with self.lock:
            if pattern is None:
                return list(self.cache.keys())
            # 简单的通配符匹配
            import fnmatch

            return [k for k in self.cache.keys() if fnmatch.fnmatch(k, pattern)]

    async def clear(self):
        """清空缓存"""
        async with self.lock:
            self.cache.clear()

    async def size(self) -> int:
        """获取当前大小"""
        async with self.lock:
            return len(self.cache)


class L1TransientLayer(BaseMemoryLayer):
    """L1 瞬时内存层"""

    def __init__(self, capacity: int = 1000, default_ttl_seconds: int = 300):  # 5分钟
        super().__init__(MemoryLayer.L1_TRANSIENT)
        self.data_cache = LRUCache(capacity)
        self.metadata_cache = LRUCache(capacity)
        self.default_ttl_seconds = default_ttl_seconds
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0,
            "promotions": 0,
        }

        # 启动后台清理任务
        self._cleanup_task = None

    async def start_cleanup_task(self):
        """启动后台过期数据清理任务"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_data())

    async def stop_cleanup_task(self):
        """停止后台清理任务"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _cleanup_expired_data(self):
        """定期清理过期数据"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                await self._remove_expired_entries()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    async def _remove_expired_entries(self):
        """移除过期的条目"""
        now = datetime.now()
        keys_to_remove = []

        # 获取所有元数据键
        metadata_keys = await self.metadata_cache.keys()

        for full_key in metadata_keys:
            metadata = await self.metadata_cache.get(full_key)
            if metadata and hasattr(metadata, "expires_at"):
                if metadata.expires_at and metadata.expires_at < now:
                    keys_to_remove.append(full_key)

        # 批量删除
        for full_key in keys_to_remove:
            await self.data_cache.delete(full_key)
            await self.metadata_cache.delete(full_key)
            self.stats["evictions"] += 1

        if keys_to_remove:
            logger.info(f"Cleaned up {len(keys_to_remove)} expired entries from L1")

    async def get(
        self, key: str, scope: MemoryScope, scope_id: str
    ) -> Optional[Tuple[Any, MemoryMetadata]]:
        """获取数据"""
        full_key = self._build_full_key(key, scope, scope_id)

        # 检查是否存在
        value = await self.data_cache.get(full_key)
        if value is None:
            self.stats["misses"] += 1
            return None

        # 获取元数据
        metadata = await self.metadata_cache.get(full_key)
        if metadata is None:
            # 数据存在但元数据丢失，创建默认元数据
            metadata = MemoryMetadata(
                key=key, layer=MemoryLayer.L1_TRANSIENT, scope=scope
            )

        # 更新访问信息
        metadata.increment_access()
        await self.metadata_cache.set(full_key, metadata)

        self.stats["hits"] += 1

        return value, metadata

    async def set(
        self,
        key: str,
        value: Any,
        scope: MemoryScope,
        scope_id: str,
        metadata: Optional[MemoryMetadata] = None,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """设置数据"""
        full_key = self._build_full_key(key, scope, scope_id)

        # 创建或更新元数据
        if metadata is None:
            metadata = MemoryMetadata(
                key=key, layer=MemoryLayer.L1_TRANSIENT, scope=scope
            )

        # 设置过期时间
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        metadata.expires_at = datetime.now() + timedelta(seconds=ttl)

        # 存储数据和元数据
        await self.data_cache.set(full_key, value)
        await self.metadata_cache.set(full_key, metadata)

        self.stats["sets"] += 1

        return True

    async def delete(self, key: str, scope: MemoryScope, scope_id: str) -> bool:
        """删除数据"""
        full_key = self._build_full_key(key, scope, scope_id)

        data_deleted = await self.data_cache.delete(full_key)
        meta_deleted = await self.metadata_cache.delete(full_key)

        if data_deleted or meta_deleted:
            self.stats["deletes"] += 1
            return True
        return False

    async def exists(self, key: str, scope: MemoryScope, scope_id: str) -> bool:
        """检查数据是否存在"""
        full_key = self._build_full_key(key, scope, scope_id)
        return await self.data_cache.exists(full_key)

    async def list_keys(
        self, scope: MemoryScope, scope_id: str, pattern: Optional[str] = None
    ) -> List[str]:
        """列出符合条件的所有键"""
        prefix = f"{self.layer_type.value}:{scope.value}:{scope_id}:"

        # 构建完整的匹配模式
        if pattern:
            full_pattern = f"{prefix}{pattern}"
        else:
            full_pattern = f"{prefix}*"

        full_keys = await self.data_cache.keys(full_pattern)

        # 提取原始键名
        keys = []
        for full_key in full_keys:
            parsed = self._parse_full_key(full_key)
            if parsed:
                key, _, _ = parsed
                keys.append(key)

        return keys

    async def get_metadata(
        self, key: str, scope: MemoryScope, scope_id: str
    ) -> Optional[MemoryMetadata]:
        """获取数据的元信息"""
        full_key = self._build_full_key(key, scope, scope_id)
        return await self.metadata_cache.get(full_key)

    async def update_metadata(
        self, key: str, scope: MemoryScope, scope_id: str, metadata: MemoryMetadata
    ) -> bool:
        """更新数据的元信息"""
        full_key = self._build_full_key(key, scope, scope_id)

        # 检查数据是否存在
        if not await self.data_cache.exists(full_key):
            return False

        await self.metadata_cache.set(full_key, metadata)
        return True

    async def clear_scope(self, scope: MemoryScope, scope_id: str) -> int:
        """清空指定作用域的所有数据"""
        keys = await self.list_keys(scope, scope_id)
        count = 0

        for key in keys:
            if await self.delete(key, scope, scope_id):
                count += 1

        return count

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        data_size = await self.data_cache.size()
        metadata_size = await self.metadata_cache.size()

        hit_rate = 0.0
        total_requests = self.stats["hits"] + self.stats["misses"]
        if total_requests > 0:
            hit_rate = self.stats["hits"] / total_requests

        return {
            "layer": self.layer_type.value,
            "data_count": data_size,
            "metadata_count": metadata_size,
            "capacity": self.data_cache.capacity,
            "hit_rate": hit_rate,
            **self.stats,
        }

    async def get_promotion_candidates(
        self, scope: MemoryScope, scope_id: str
    ) -> List[Tuple[str, Any, MemoryMetadata, PromotionReason]]:
        """
        获取应该提升到L2的数据候选

        Returns:
            [(key, value, metadata, reason), ...]
        """
        candidates = []
        keys = await self.list_keys(scope, scope_id)

        for key in keys:
            result = await self.get(key, scope, scope_id)
            if result is None:
                continue

            value, metadata = result

            # 检查提升条件
            if metadata.should_promote_to_l2():
                reason = (
                    PromotionReason.HIGH_IMPORTANCE_SCORE
                    if metadata.importance >= 0.7
                    else PromotionReason.HIGH_ACCESS_FREQUENCY
                )
                candidates.append((key, value, metadata, reason))

        return candidates

    async def batch_flush_to_l2(
        self, scope: MemoryScope, scope_id: str, min_importance: float = 0.5
    ) -> List[Tuple[str, Any, MemoryMetadata]]:
        """
        批量将高价值数据刷新到L2

        Args:
            scope: 作用域
            scope_id: 作用域ID
            min_importance: 最低重要性阈值

        Returns:
            需要刷新到L2的数据列表 [(key, value, metadata), ...]
        """
        to_flush = []
        keys = await self.list_keys(scope, scope_id)

        for key in keys:
            result = await self.get(key, scope, scope_id)
            if result is None:
                continue

            value, metadata = result

            # 筛选高价值数据
            if metadata.importance >= min_importance or metadata.access_count >= 2:
                to_flush.append((key, value, metadata))

        return to_flush
