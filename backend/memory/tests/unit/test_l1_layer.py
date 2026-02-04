"""
Unit tests for L1 Transient Memory Layer.

Tests for:
- Basic set and get operations
- LRU eviction mechanism
- TTL expiration
- Access count tracking
- Metadata updates
- Scope clearing
- Promotion candidate retrieval
- Batch flush to L2
- Concurrent access safety
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from memory.models import (
    MemoryLayer,
    MemoryScope,
    MemoryMetadata,
    PromotionReason,
)
from memory.layers.l1_transient import L1TransientLayer, LRUCache


class TestLRUCache:
    """Test LRUCache implementation."""

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = LRUCache(capacity=10)

        await cache.set("key1", "value1")
        value = await cache.get("key1")

        assert value == "value1"

    @pytest.mark.asyncio
    async def test_cache_get_nonexistent(self):
        """Test getting a non-existent key returns None."""
        cache = LRUCache(capacity=10)

        value = await cache.get("nonexistent")

        assert value is None

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """Test that LRU evicts the oldest item when capacity is exceeded."""
        cache = LRUCache(capacity=3)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # All keys should be present
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"
        assert await cache.get("key3") == "value3"

        # Add a fourth key, should evict key1 (oldest)
        await cache.set("key4", "value4")

        assert await cache.get("key1") is None  # Evicted
        assert await cache.get("key2") == "value2"
        assert await cache.get("key3") == "value3"
        assert await cache.get("key4") == "value4"

    @pytest.mark.asyncio
    async def test_lru_updates_on_access(self):
        """Test that accessing an item updates its position in LRU."""
        cache = LRUCache(capacity=3)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # Access key1 to make it recently used
        await cache.get("key1")

        # Add key4, should evict key2 (now oldest)
        await cache.set("key4", "value4")

        assert await cache.get("key1") == "value1"  # Still present
        assert await cache.get("key2") is None  # Evicted
        assert await cache.get("key3") == "value3"
        assert await cache.get("key4") == "value4"

    @pytest.mark.asyncio
    async def test_cache_delete(self):
        """Test deleting a key from cache."""
        cache = LRUCache(capacity=10)

        await cache.set("key1", "value1")
        assert await cache.exists("key1") is True

        result = await cache.delete("key1")
        assert result is True
        assert await cache.exists("key1") is False

    @pytest.mark.asyncio
    async def test_cache_delete_nonexistent(self):
        """Test deleting a non-existent key."""
        cache = LRUCache(capacity=10)

        result = await cache.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_cache_exists(self):
        """Test checking if a key exists."""
        cache = LRUCache(capacity=10)

        assert await cache.exists("key1") is False

        await cache.set("key1", "value1")
        assert await cache.exists("key1") is True

    @pytest.mark.asyncio
    async def test_cache_keys_no_pattern(self):
        """Test getting all keys without pattern."""
        cache = LRUCache(capacity=10)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        keys = await cache.keys()
        assert set(keys) == {"key1", "key2", "key3"}

    @pytest.mark.asyncio
    async def test_cache_keys_with_pattern(self):
        """Test getting keys with wildcard pattern."""
        cache = LRUCache(capacity=10)

        await cache.set("test: key1", "value1")
        await cache.set("test: key2", "value2")
        await cache.set("other: key3", "value3")

        keys = await cache.keys("test:*")
        assert len(keys) == 2
        assert all(k.startswith("test:") for k in keys)

    @pytest.mark.asyncio
    async def test_cache_clear(self):
        """Test clearing the entire cache."""
        cache = LRUCache(capacity=10)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        await cache.clear()

        assert await cache.size() == 0
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_cache_size(self):
        """Test getting cache size."""
        cache = LRUCache(capacity=10)

        assert await cache.size() == 0

        await cache.set("key1", "value1")
        assert await cache.size() == 1

        await cache.set("key2", "value2")
        assert await cache.size() == 2


class TestL1TransientLayer:
    """Test L1TransientLayer functionality."""

    @pytest.mark.asyncio
    async def test_layer_initialization(self, l1_layer):
        """Test layer initialization."""
        assert l1_layer.layer_type == MemoryLayer.L1_TRANSIENT
        assert l1_layer.default_ttl_seconds == 300
        assert l1_layer.data_cache.capacity == 100
        assert l1_layer.metadata_cache.capacity == 100
        assert l1_layer.stats["hits"] == 0
        assert l1_layer.stats["misses"] == 0

    @pytest.mark.asyncio
    async def test_set_and_get(self, l1_layer):
        """Test basic set and get operations."""
        value = {"data": "test_value"}
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
            importance=0.5,
        )

        # Set
        result = await l1_layer.set(
            "test_key",
            value,
            MemoryScope.SESSION,
            "session_123",
            metadata=metadata,
        )
        assert result is True

        # Get
        retrieved_value, retrieved_metadata = await l1_layer.get(
            "test_key", MemoryScope.SESSION, "session_123"
        )

        assert retrieved_value == value
        assert retrieved_metadata.key == "test_key"
        assert retrieved_metadata.access_count == 1  # Should increment on get

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, l1_layer):
        """Test getting a non-existent key."""
        result = await l1_layer.get("nonexistent", MemoryScope.SESSION, "session_123")

        assert result is None
        assert l1_layer.stats["misses"] == 1

    @pytest.mark.asyncio
    async def test_get_increments_access_count(self, l1_layer):
        """Test that getting a value increments access count."""
        await l1_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.SESSION,
            "session_123",
        )

        # First get
        _, metadata1 = await l1_layer.get("test_key", MemoryScope.SESSION, "session_123")
        assert metadata1.access_count == 1

        # Second get
        _, metadata2 = await l1_layer.get("test_key", MemoryScope.SESSION, "session_123")
        assert metadata2.access_count == 2

    @pytest.mark.asyncio
    async def test_set_with_default_metadata(self, l1_layer):
        """Test setting data without providing metadata."""
        result = await l1_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.TASK,
            "task_123",
        )

        assert result is True

        value, metadata = await l1_layer.get("test_key", MemoryScope.TASK, "task_123")
        assert value == {"data": "value"}
        assert metadata is not None
        assert metadata.importance == 0.5  # Default

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, l1_layer):
        """Test setting data with custom TTL."""
        short_ttl = 1  # 1 second

        await l1_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.TASK,
            "task_123",
            ttl_seconds=short_ttl,
        )

        # Should be accessible immediately
        result = await l1_layer.get("test_key", MemoryScope.TASK, "task_123")
        assert result is not None

        # Wait for expiration
        await asyncio.sleep(1.5)

        # Trigger cleanup
        await l1_layer._remove_expired_entries()

        # Should be expired
        result = await l1_layer.get("test_key", MemoryScope.TASK, "task_123")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, l1_layer):
        """Test deleting data."""
        await l1_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.SESSION,
            "session_123",
        )

        exists = await l1_layer.exists("test_key", MemoryScope.SESSION, "session_123")
        assert exists is True

        result = await l1_layer.delete("test_key", MemoryScope.SESSION, "session_123")
        assert result is True

        exists = await l1_layer.exists("test_key", MemoryScope.SESSION, "session_123")
        assert exists is False

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, l1_layer):
        """Test deleting a non-existent key."""
        result = await l1_layer.delete("nonexistent", MemoryScope.SESSION, "session_123")
        assert result is False

    @pytest.mark.asyncio
    async def test_exists(self, l1_layer):
        """Test checking if data exists."""
        # Before set
        exists = await l1_layer.exists("test_key", MemoryScope.SESSION, "session_123")
        assert exists is False

        # After set
        await l1_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.SESSION,
            "session_123",
        )
        exists = await l1_layer.exists("test_key", MemoryScope.SESSION, "session_123")
        assert exists is True

    @pytest.mark.asyncio
    async def test_list_keys_no_pattern(self, l1_layer):
        """Test listing all keys in a scope."""
        await l1_layer.set("key1", {"data": "1"}, MemoryScope.SESSION, "session_123")
        await l1_layer.set("key2", {"data": "2"}, MemoryScope.SESSION, "session_123")
        await l1_layer.set("key3", {"data": "3"}, MemoryScope.SESSION, "session_123")

        keys = await l1_layer.list_keys(MemoryScope.SESSION, "session_123")

        assert set(keys) == {"key1", "key2", "key3"}

    @pytest.mark.asyncio
    async def test_list_keys_with_pattern(self, l1_layer):
        """Test listing keys with a pattern."""
        await l1_layer.set("test:key1", {"data": "1"}, MemoryScope.SESSION, "session_123")
        await l1_layer.set("test:key2", {"data": "2"}, MemoryScope.SESSION, "session_123")
        await l1_layer.set("other:key3", {"data": "3"}, MemoryScope.SESSION, "session_123")

        keys = await l1_layer.list_keys(MemoryScope.SESSION, "session_123", pattern="test:*")

        assert set(keys) == {"test:key1", "test:key2"}

    @pytest.mark.asyncio
    async def test_list_keys_scope_isolation(self, l1_layer):
        """Test that keys are isolated by scope."""
        await l1_layer.set("key1", {"data": "1"}, MemoryScope.SESSION, "session_123")
        await l1_layer.set("key1", {"data": "2"}, MemoryScope.TASK, "task_456")

        session_keys = await l1_layer.list_keys(MemoryScope.SESSION, "session_123")
        task_keys = await l1_layer.list_keys(MemoryScope.TASK, "task_456")

        assert "key1" in session_keys
        assert "key1" in task_keys

        # Verify they're different values
        session_value, _ = await l1_layer.get("key1", MemoryScope.SESSION, "session_123")
        task_value, _ = await l1_layer.get("key1", MemoryScope.TASK, "task_456")

        assert session_value["data"] == "1"
        assert task_value["data"] == "2"

    @pytest.mark.asyncio
    async def test_get_metadata(self, l1_layer):
        """Test getting metadata for a key."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
            importance=0.8,
            tags=["important"],
        )

        await l1_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.SESSION,
            "session_123",
            metadata=metadata,
        )

        retrieved_metadata = await l1_layer.get_metadata(
            "test_key", MemoryScope.SESSION, "session_123"
        )

        assert retrieved_metadata is not None
        assert retrieved_metadata.importance == 0.8
        assert retrieved_metadata.tags == ["important"]

    @pytest.mark.asyncio
    async def test_update_metadata(self, l1_layer):
        """Test updating metadata for a key."""
        await l1_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.SESSION,
            "session_123",
        )

        updated_metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
            importance=0.9,
            tags=["updated"],
        )

        result = await l1_layer.update_metadata(
            "test_key", MemoryScope.SESSION, "session_123", updated_metadata
        )

        assert result is True

        retrieved_metadata = await l1_layer.get_metadata(
            "test_key", MemoryScope.SESSION, "session_123"
        )
        assert retrieved_metadata.importance == 0.9
        assert retrieved_metadata.tags == ["updated"]

    @pytest.mark.asyncio
    async def test_update_metadata_nonexistent_key(self, l1_layer):
        """Test updating metadata for a non-existent key."""
        metadata = MemoryMetadata(
            key="nonexistent",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
        )

        result = await l1_layer.update_metadata(
            "nonexistent", MemoryScope.SESSION, "session_123", metadata
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_clear_scope(self, l1_layer):
        """Test clearing all data in a scope."""
        await l1_layer.set("key1", {"data": "1"}, MemoryScope.SESSION, "session_123")
        await l1_layer.set("key2", {"data": "2"}, MemoryScope.SESSION, "session_123")
        await l1_layer.set("key3", {"data": "3"}, MemoryScope.TASK, "task_456")

        count = await l1_layer.clear_scope(MemoryScope.SESSION, "session_123")

        assert count == 2

        session_keys = await l1_layer.list_keys(MemoryScope.SESSION, "session_123")
        task_keys = await l1_layer.list_keys(MemoryScope.TASK, "task_456")

        assert len(session_keys) == 0
        assert len(task_keys) == 1

    @pytest.mark.asyncio
    async def test_get_stats(self, l1_layer):
        """Test getting layer statistics."""
        await l1_layer.set("key1", {"data": "1"}, MemoryScope.SESSION, "session_123")
        await l1_layer.get("key1", MemoryScope.SESSION, "session_123")
        await l1_layer.get("nonexistent", MemoryScope.SESSION, "session_123")

        stats = await l1_layer.get_stats()

        assert stats["layer"] == "transient"
        assert stats["data_count"] == 1
        assert stats["metadata_count"] == 1
        assert stats["capacity"] == 100
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_get_promotion_candidates_by_access(self, l1_layer):
        """Test getting promotion candidates by access count."""
        await l1_layer.set("key1", {"data": "1"}, MemoryScope.SESSION, "session_123")

        # Access 3 times to trigger promotion
        await l1_layer.get("key1", MemoryScope.SESSION, "session_123")
        await l1_layer.get("key1", MemoryScope.SESSION, "session_123")
        await l1_layer.get("key1", MemoryScope.SESSION, "session_123")

        candidates = await l1_layer.get_promotion_candidates(
            MemoryScope.SESSION, "session_123"
        )

        assert len(candidates) == 1
        key, value, metadata, reason = candidates[0]
        assert key == "key1"
        assert reason == PromotionReason.HIGH_ACCESS_FREQUENCY

    @pytest.mark.asyncio
    async def test_get_promotion_candidates_by_importance(self, l1_layer):
        """Test getting promotion candidates by importance."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
            importance=0.8,  # Above threshold
        )

        await l1_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.SESSION,
            "session_123",
            metadata=metadata,
        )

        candidates = await l1_layer.get_promotion_candidates(
            MemoryScope.SESSION, "session_123"
        )

        assert len(candidates) == 1
        key, value, metadata, reason = candidates[0]
        assert reason == PromotionReason.HIGH_IMPORTANCE_SCORE

    @pytest.mark.asyncio
    async def test_batch_flush_to_l2(self, l1_layer):
        """Test batch flush to L2."""
        await l1_layer.set("key1", {"data": "1"}, MemoryScope.SESSION, "session_123")
        await l1_layer.set("key2", {"data": "2"}, MemoryScope.SESSION, "session_123")
        await l1_layer.set("key3", {"data": "3"}, MemoryScope.SESSION, "session_123")

        # Access key1 multiple times
        await l1_layer.get("key1", MemoryScope.SESSION, "session_123")
        await l1_layer.get("key1", MemoryScope.SESSION, "session_123")

        # Set high importance on key2
        metadata = MemoryMetadata(
            key="key2",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
            importance=0.8,
        )
        await l1_layer.update_metadata(
            "key2", MemoryScope.SESSION, "session_123", metadata
        )

        to_flush = await l1_layer.batch_flush_to_l2(
            MemoryScope.SESSION, "session_123", min_importance=0.5
        )

        assert len(to_flush) == 2  # key1 (access_count >= 2) and key2 (importance >= 0.5)

    @pytest.mark.asyncio
    async def test_concurrent_access(self, l1_layer):
        """Test concurrent access to L1 layer."""
        num_writes = 100
        num_reads = 50

        # Concurrent writes
        write_tasks = [
            l1_layer.set(
                f"key_{i}",
                {"data": f"value_{i}"},
                MemoryScope.SESSION,
                "session_123",
            )
            for i in range(num_writes)
        ]
        await asyncio.gather(*write_tasks)

        # Concurrent reads
        read_tasks = [
            l1_layer.get(f"key_{i % num_writes}", MemoryScope.SESSION, "session_123")
            for i in range(num_reads)
        ]
        results = await asyncio.gather(*read_tasks)

        successful_reads = [r for r in results if r is not None]
        assert len(successful_reads) == num_reads

    @pytest.mark.asyncio
    async def test_lru_eviction_behavior(self):
        """Test that LRU eviction works correctly in full layer."""
        layer = L1TransientLayer(capacity=5)

        # Fill capacity
        for i in range(5):
            await layer.set(
                f"key_{i}",
                {"data": f"value_{i}"},
                MemoryScope.SESSION,
                "session_123",
            )

        # All keys should exist
        for i in range(5):
            exists = await layer.exists(f"key_{i}", MemoryScope.SESSION, "session_123")
            assert exists is True

        # Add one more key, should evict key_0
        await layer.set(
            "key_5",
            {"data": "value_5"},
            MemoryScope.SESSION,
            "session_123",
        )

        assert await layer.exists("key_0", MemoryScope.SESSION, "session_123") is False
        assert await layer.exists("key_5", MemoryScope.SESSION, "session_123") is True
