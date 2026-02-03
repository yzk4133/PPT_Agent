"""
L2 短期内存层 (Short-term Memory Layer)

特性：
- Redis存储，快速访问
- 会话级生命周期 (hours级别, 默认1小时)
- session_id作用域隔离
- 批量写入机制，减少网络往返
- 提升规则：跨会话使用≥2次 → 自动提升到L3
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from redis import Redis
from redis.exceptions import RedisError
import os

from ..models import (
    BaseMemoryLayer,
    MemoryLayer,
    MemoryScope,
    MemoryMetadata,
    PromotionReason,
)

logger = logging.getLogger(__name__)


class L2ShortTermLayer(BaseMemoryLayer):
    """L2 短期内存层 - Redis存储"""

    def __init__(
        self, redis_url: Optional[str] = None, default_ttl_seconds: int = 3600  # 1小时
    ):
        super().__init__(MemoryLayer.L2_SHORT_TERM)
        self.default_ttl_seconds = default_ttl_seconds

        # 初始化Redis连接
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")

        try:
            self.client = Redis.from_url(
                redis_url,
                decode_responses=False,  # 使用bytes模式，手动控制序列化
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            self.client.ping()
            logger.info(f"L2 Layer Redis connected")
        except RedisError as e:
            logger.error(f"L2 Layer Redis connection failed: {e}")
            self.client = None

        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "batch_writes": 0,
        }

        # 跨会话使用追踪 (key -> set of session_ids)
        self._cross_session_tracker_key = "l2:cross_session_tracker"

    def _is_available(self) -> bool:
        """检查Redis是否可用"""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except RedisError:
            return False

    def _serialize_value(self, value: Any) -> bytes:
        """序列化数据值"""
        return json.dumps(value, ensure_ascii=False).encode("utf-8")

    def _deserialize_value(self, data: bytes) -> Any:
        """反序列化数据值"""
        return json.loads(data.decode("utf-8"))

    def _serialize_metadata(self, metadata: MemoryMetadata) -> bytes:
        """序列化元数据"""
        return json.dumps(metadata.to_dict(), ensure_ascii=False).encode("utf-8")

    def _deserialize_metadata(self, data: bytes) -> MemoryMetadata:
        """反序列化元数据"""
        meta_dict = json.loads(data.decode("utf-8"))
        return MemoryMetadata(
            key=meta_dict["key"],
            layer=MemoryLayer(meta_dict["layer"]),
            scope=MemoryScope(meta_dict["scope"]),
            created_at=datetime.fromisoformat(meta_dict["created_at"]),
            importance=meta_dict["importance"],
            access_count=meta_dict["access_count"],
            last_accessed=datetime.fromisoformat(meta_dict["last_accessed"]),
            session_ids=meta_dict.get("session_ids", []),
            tags=meta_dict.get("tags", []),
        )

    def _get_data_key(self, key: str, scope: MemoryScope, scope_id: str) -> str:
        """获取数据存储键"""
        return f"{self._build_full_key(key, scope, scope_id)}:data"

    def _get_meta_key(self, key: str, scope: MemoryScope, scope_id: str) -> str:
        """获取元数据存储键"""
        return f"{self._build_full_key(key, scope, scope_id)}:meta"

    async def get(
        self, key: str, scope: MemoryScope, scope_id: str
    ) -> Optional[Tuple[Any, MemoryMetadata]]:
        """获取数据"""
        if not self._is_available():
            self.stats["misses"] += 1
            return None

        try:
            data_key = self._get_data_key(key, scope, scope_id)
            meta_key = self._get_meta_key(key, scope, scope_id)

            # 批量获取数据和元数据
            pipe = self.client.pipeline()
            pipe.get(data_key)
            pipe.get(meta_key)
            results = pipe.execute()

            data_bytes, meta_bytes = results

            if data_bytes is None:
                self.stats["misses"] += 1
                return None

            # 反序列化
            value = self._deserialize_value(data_bytes)

            if meta_bytes:
                metadata = self._deserialize_metadata(meta_bytes)
            else:
                # 数据存在但元数据丢失，创建默认元数据
                metadata = MemoryMetadata(
                    key=key, layer=MemoryLayer.L2_SHORT_TERM, scope=scope
                )

            # 更新访问信息
            metadata.increment_access()

            # 追踪跨会话使用
            if scope == MemoryScope.SESSION:
                metadata.add_session_id(scope_id)
                await self._track_cross_session_usage(key, scope_id)

            # 异步更新元数据（不等待结果）
            self.client.setex(
                meta_key, self.default_ttl_seconds, self._serialize_metadata(metadata)
            )

            self.stats["hits"] += 1
            return value, metadata

        except Exception as e:
            logger.error(f"L2 get error: {e}")
            self.stats["misses"] += 1
            return None

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
        if not self._is_available():
            return False

        try:
            data_key = self._get_data_key(key, scope, scope_id)
            meta_key = self._get_meta_key(key, scope, scope_id)

            # 创建或更新元数据
            if metadata is None:
                metadata = MemoryMetadata(
                    key=key, layer=MemoryLayer.L2_SHORT_TERM, scope=scope
                )

            # 设置TTL
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds

            # 序列化
            data_bytes = self._serialize_value(value)
            meta_bytes = self._serialize_metadata(metadata)

            # 批量设置
            pipe = self.client.pipeline()
            pipe.setex(data_key, ttl, data_bytes)
            pipe.setex(meta_key, ttl, meta_bytes)
            pipe.execute()

            self.stats["sets"] += 1
            return True

        except Exception as e:
            logger.error(f"L2 set error: {e}")
            return False

    async def delete(self, key: str, scope: MemoryScope, scope_id: str) -> bool:
        """删除数据"""
        if not self._is_available():
            return False

        try:
            data_key = self._get_data_key(key, scope, scope_id)
            meta_key = self._get_meta_key(key, scope, scope_id)

            pipe = self.client.pipeline()
            pipe.delete(data_key)
            pipe.delete(meta_key)
            results = pipe.execute()

            deleted = any(r > 0 for r in results)
            if deleted:
                self.stats["deletes"] += 1

            return deleted

        except Exception as e:
            logger.error(f"L2 delete error: {e}")
            return False

    async def exists(self, key: str, scope: MemoryScope, scope_id: str) -> bool:
        """检查数据是否存在"""
        if not self._is_available():
            return False

        try:
            data_key = self._get_data_key(key, scope, scope_id)
            return self.client.exists(data_key) > 0
        except Exception as e:
            logger.error(f"L2 exists error: {e}")
            return False

    async def list_keys(
        self, scope: MemoryScope, scope_id: str, pattern: Optional[str] = None
    ) -> List[str]:
        """列出符合条件的所有键"""
        if not self._is_available():
            return []

        try:
            prefix = f"{self.layer_type.value}:{scope.value}:{scope_id}:"

            if pattern:
                search_pattern = f"{prefix}{pattern}:data"
            else:
                search_pattern = f"{prefix}*:data"

            # 使用SCAN而不是KEYS（生产环境更安全）
            keys = []
            cursor = 0
            while True:
                cursor, batch = self.client.scan(
                    cursor, match=search_pattern, count=100
                )
                keys.extend(batch)
                if cursor == 0:
                    break

            # 提取原始键名
            result_keys = []
            for full_key in keys:
                full_key_str = (
                    full_key.decode("utf-8")
                    if isinstance(full_key, bytes)
                    else full_key
                )
                # 移除 ":data" 后缀
                if full_key_str.endswith(":data"):
                    full_key_str = full_key_str[:-5]
                parsed = self._parse_full_key(full_key_str)
                if parsed:
                    key, _, _ = parsed
                    result_keys.append(key)

            return result_keys

        except Exception as e:
            logger.error(f"L2 list_keys error: {e}")
            return []

    async def get_metadata(
        self, key: str, scope: MemoryScope, scope_id: str
    ) -> Optional[MemoryMetadata]:
        """获取数据的元信息"""
        if not self._is_available():
            return None

        try:
            meta_key = self._get_meta_key(key, scope, scope_id)
            meta_bytes = self.client.get(meta_key)

            if meta_bytes:
                return self._deserialize_metadata(meta_bytes)
            return None

        except Exception as e:
            logger.error(f"L2 get_metadata error: {e}")
            return None

    async def update_metadata(
        self, key: str, scope: MemoryScope, scope_id: str, metadata: MemoryMetadata
    ) -> bool:
        """更新数据的元信息"""
        if not self._is_available():
            return False

        try:
            # 检查数据是否存在
            data_key = self._get_data_key(key, scope, scope_id)
            if not self.client.exists(data_key):
                return False

            # 更新元数据
            meta_key = self._get_meta_key(key, scope, scope_id)
            ttl = self.client.ttl(data_key)
            if ttl < 0:
                ttl = self.default_ttl_seconds

            self.client.setex(meta_key, ttl, self._serialize_metadata(metadata))
            return True

        except Exception as e:
            logger.error(f"L2 update_metadata error: {e}")
            return False

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
        stats = {
            "layer": self.layer_type.value,
            "redis_available": self._is_available(),
            **self.stats,
        }

        if self._is_available():
            try:
                info = self.client.info("memory")
                stats["redis_memory_used_mb"] = info.get("used_memory", 0) / (
                    1024 * 1024
                )
                stats["redis_memory_peak_mb"] = info.get("used_memory_peak", 0) / (
                    1024 * 1024
                )
            except Exception as e:
                logger.error(f"Failed to get Redis stats: {e}")

        hit_rate = 0.0
        total_requests = self.stats["hits"] + self.stats["misses"]
        if total_requests > 0:
            hit_rate = self.stats["hits"] / total_requests
        stats["hit_rate"] = hit_rate

        return stats

    async def batch_set(
        self,
        items: List[Tuple[str, Any, MemoryScope, str, Optional[MemoryMetadata]]],
        ttl_seconds: Optional[int] = None,
    ) -> int:
        """
        批量设置数据

        Args:
            items: [(key, value, scope, scope_id, metadata), ...]
            ttl_seconds: 统一TTL

        Returns:
            成功设置的数量
        """
        if not self._is_available():
            return 0

        try:
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
            pipe = self.client.pipeline()

            for key, value, scope, scope_id, metadata in items:
                data_key = self._get_data_key(key, scope, scope_id)
                meta_key = self._get_meta_key(key, scope, scope_id)

                if metadata is None:
                    metadata = MemoryMetadata(
                        key=key, layer=MemoryLayer.L2_SHORT_TERM, scope=scope
                    )

                data_bytes = self._serialize_value(value)
                meta_bytes = self._serialize_metadata(metadata)

                pipe.setex(data_key, ttl, data_bytes)
                pipe.setex(meta_key, ttl, meta_bytes)

            pipe.execute()

            count = len(items)
            self.stats["sets"] += count
            self.stats["batch_writes"] += 1

            logger.info(f"L2 batch set: {count} items")
            return count

        except Exception as e:
            logger.error(f"L2 batch_set error: {e}")
            return 0

    async def _track_cross_session_usage(self, key: str, session_id: str):
        """追踪跨会话使用情况"""
        try:
            # 使用Redis Set追踪哪些session访问过这个key
            tracker_key = f"{self._cross_session_tracker_key}:{key}"
            self.client.sadd(tracker_key, session_id)
            self.client.expire(tracker_key, 86400)  # 24小时过期
        except Exception as e:
            logger.error(f"Failed to track cross-session usage: {e}")

    async def get_cross_session_count(self, key: str) -> int:
        """获取跨会话使用次数"""
        if not self._is_available():
            return 0

        try:
            tracker_key = f"{self._cross_session_tracker_key}:{key}"
            return self.client.scard(tracker_key)
        except Exception as e:
            logger.error(f"Failed to get cross-session count: {e}")
            return 0

    async def get_promotion_candidates(
        self, scope: MemoryScope, scope_id: str
    ) -> List[Tuple[str, Any, MemoryMetadata, PromotionReason]]:
        """
        获取应该提升到L3的数据候选

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

            # 检查提升条件：跨会话使用≥2次
            if metadata.should_promote_to_l3():
                candidates.append(
                    (key, value, metadata, PromotionReason.CROSS_SESSION_USAGE)
                )

        return candidates
