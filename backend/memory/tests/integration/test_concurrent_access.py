"""
Integration tests for concurrent access to memory layers.

Tests for:
- Concurrent L1 reads
- Concurrent L1 writes
- Concurrent L2 operations
- Concurrent promotion
- Race conditions in LRU
- Concurrent scope operations
"""

import pytest
import asyncio
from collections import Counter

from memory.models import MemoryScope
from memory.layers.l1_transient import L1TransientLayer
from memory.layers.l2_short_term import L2ShortTermLayer


class TestConcurrentL1Access:
    """Test concurrent access to L1 layer."""

    @pytest.mark.asyncio
    async def test_concurrent_reads(self):
        """Test concurrent reads from L1 are consistent."""
        layer = L1TransientLayer(capacity=100)

        # Write data
        await layer.set("shared_key", {"counter": 0}, MemoryScope.SESSION, "session_1")

        # Concurrent reads
        async def read_task():
            result = await layer.get("shared_key", MemoryScope.SESSION, "session_1")
            return result[0]["counter"] if result else None

        tasks = [read_task() for _ in range(100)]
        results = await asyncio.gather(*tasks)

        # All reads should succeed
        assert all(r == 0 for r in results if r is not None)

    @pytest.mark.asyncio
    async def test_concurrent_writes(self):
        """Test concurrent writes to L1 don't cause conflicts."""
        layer = L1TransientLayer(capacity=100)

        # Concurrent writes to different keys
        async def write_task(i):
            await layer.set(f"key_{i}", {"value": i}, MemoryScope.SESSION, "session_1")

        tasks = [write_task(i) for i in range(100)]
        await asyncio.gather(*tasks)

        # Verify all keys were written
        keys = await layer.list_keys(MemoryScope.SESSION, "session_1")
        assert len(keys) == 100

    @pytest.mark.asyncio
    async def test_concurrent_writes_same_key(self):
        """Test concurrent writes to same key (last write wins)."""
        layer = L1TransientLayer(capacity=100)

        # Concurrent writes to same key
        async def write_task(value):
            await layer.set("same_key", {"value": value}, MemoryScope.SESSION, "session_1")

        tasks = [write_task(i) for i in range(10)]
        await asyncio.gather(*tasks)

        # One value should exist
        result = await layer.get("same_key", MemoryScope.SESSION, "session_1")
        assert result is not None
        assert result[0]["value"] in range(10)

    @pytest.mark.asyncio
    async def test_concurrent_mixed_operations(self):
        """Test mixed concurrent reads and writes."""
        layer = L1TransientLayer(capacity=100)

        # Initialize some data
        for i in range(10):
            await layer.set(f"key_{i}", {"value": i}, MemoryScope.SESSION, "session_1")

        # Mixed operations
        async def read_task():
            keys = await layer.list_keys(MemoryScope.SESSION, "session_1")
            return len(keys)

        async def write_task(i):
            await layer.set(f"new_key_{i}", {"value": i}, MemoryScope.SESSION, "session_1")

        read_tasks = [read_task() for _ in range(50)]
        write_tasks = [write_task(i) for i in range(50)]

        all_results = await asyncio.gather(*read_tasks + write_tasks)

        # All operations should complete
        read_results = all_results[:50]
        assert all(r >= 10 for r in read_results)


class TestConcurrentL2Access:
    """Test concurrent access to L2 layer."""

    @pytest.mark.asyncio
    async def test_concurrent_redis_operations(self):
        """Test concurrent Redis operations work correctly."""
        l2 = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
        l2.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)

        # Concurrent writes
        async def write_task(i):
            await l2.set(f"key_{i}", {"value": i}, MemoryScope.SESSION, "session_1")

        tasks = [write_task(i) for i in range(50)]
        await asyncio.gather(*tasks)

        # Concurrent reads
        async def read_task(i):
            result = await l2.get(f"key_{i}", MemoryScope.SESSION, "session_1")
            return result[0]["value"] if result else None

        read_tasks = [read_task(i) for i in range(50)]
        results = await asyncio.gather(*read_tasks)

        # All reads should succeed
        assert all(r == i for i, r in enumerate(results) if r is not None)

    @pytest.mark.asyncio
    async def test_concurrent_batch_operations(self):
        """Test concurrent batch operations in L2."""
        l2 = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
        l2.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)

        # Create batch items
        async def batch_task(batch_num):
            items = [
                (f"batch_{batch_num}_key_{i}", {"batch": batch_num, "i": i}, MemoryScope.SESSION, "session_1", None)
                for i in range(10)
            ]
            return await l2.batch_set(items)

        # Run concurrent batches
        tasks = [batch_task(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All batches should succeed
        assert all(r == 10 for r in results)

        # Verify total count
        keys = await l2.list_keys(MemoryScope.SESSION, "session_1")
        assert len(keys) == 100


class TestConcurrentPromotion:
    """Test concurrent promotion operations."""

    @pytest.mark.asyncio
    async def test_concurrent_l1_to_l2_promotion(self):
        """Test concurrent L1 to L2 promotions don't conflict."""
        l1 = L1TransientLayer(capacity=100)
        l2 = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
        l2.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)

        # Write data to L1
        for i in range(20):
            await l1.set(f"key_{i}", {"value": i}, MemoryScope.SESSION, "session_1")

        # Simulate concurrent promotion by manually moving items
        async def promote_task(start_idx, end_idx):
            for i in range(start_idx, end_idx):
                result = await l1.get(f"key_{i}", MemoryScope.SESSION, "session_1")
                if result:
                    value, metadata = result
                    metadata.layer = __import__('memory.models').MemoryLayer.L2_SHORT_TERM
                    await l2.set(f"key_{i}", value, MemoryScope.SESSION, "session_1", metadata=metadata)

        # Run concurrent promotions
        tasks = [
            promote_task(0, 10),
            promote_task(10, 20),
        ]
        await asyncio.gather(*tasks)

        # Verify all items in L2
        l2_keys = await l2.list_keys(MemoryScope.SESSION, "session_1")
        assert len(l2_keys) == 20


class TestLRURaceConditions:
    """Test LRU cache under concurrent access."""

    @pytest.mark.asyncio
    async def test_lru_concurrent_access(self):
        """Test LRU cache maintains consistency under concurrent access."""
        layer = L1TransientLayer(capacity=50)

        # Fill cache
        for i in range(50):
            await layer.set(f"key_{i}", {"value": i}, MemoryScope.SESSION, "session_1")

        # Concurrent access pattern
        async def access_pattern(start_idx):
            for i in range(start_idx, start_idx + 10):
                # Mix of reads and writes
                if i % 2 == 0:
                    await layer.get(f"key_{i % 50}", MemoryScope.SESSION, "session_1")
                else:
                    await layer.set(f"new_key_{i}", {"value": i}, MemoryScope.SESSION, "session_1")

        # Run concurrent access patterns
        tasks = [access_pattern(i * 10) for i in range(5)]
        await asyncio.gather(*tasks)

        # Cache should maintain consistency
        stats = await layer.get_stats()
        assert stats["data_count"] <= 50  # Should not exceed capacity

    @pytest.mark.asyncio
    async def test_lru_eviction_under_load(self):
        """Test LRU eviction works correctly under concurrent load."""
        layer = L1TransientLayer(capacity=20)

        # Write more items than capacity
        async def write_batch(start, count):
            for i in range(start, start + count):
                await layer.set(f"key_{i}", {"value": i}, MemoryScope.SESSION, "session_1")

        # Concurrent writes exceeding capacity
        tasks = [
            write_batch(0, 30),
            write_batch(30, 30),
        ]
        await asyncio.gather(*tasks)

        # LRU should maintain capacity limit
        stats = await layer.get_stats()
        assert stats["data_count"] == 20

        # Oldest items should be evicted
        exists = await layer.exists("key_0", MemoryScope.SESSION, "session_1")
        assert exists is False  # Should be evicted


class TestConcurrentScopeOperations:
    """Test concurrent operations across different scopes."""

    @pytest.mark.asyncio
    async def test_concurrent_different_scopes(self):
        """Test concurrent operations on different scopes are independent."""
        layer = L1TransientLayer(capacity=100)

        # Concurrent operations on different scopes
        async def scope_task(scope_name):
            for i in range(10):
                await layer.set(f"{scope_name}_key_{i}", {"value": i}, MemoryScope.TASK, f"{scope_name}_task")

        tasks = [scope_task(f"scope_{i}") for i in range(10)]
        await asyncio.gather(*tasks)

        # Verify each scope has its data
        for i in range(10):
            keys = await layer.list_keys(MemoryScope.TASK, f"scope_{i}_task")
            assert len(keys) == 10

    @pytest.mark.asyncio
    async def test_concurrent_scope_isolation(self):
        """Test that scopes remain isolated under concurrent access."""
        layer = L1TransientLayer(capacity=100)

        # Write to multiple scopes concurrently
        async def write_to_scope(scope_id):
            await layer.set("shared_key", {"scope": scope_id}, MemoryScope.SESSION, scope_id)

        tasks = [write_to_scope(f"session_{i}") for i in range(50)]
        await asyncio.gather(*tasks)

        # Verify isolation - each scope should have its own value
        for i in range(50):
            result = await layer.get("shared_key", MemoryScope.SESSION, f"session_{i}")
            assert result is not None
            assert result[0]["scope"] == f"session_{i}"


class TestConcurrentDeleteOperations:
    """Test concurrent delete operations."""

    @pytest.mark.asyncio
    async def test_concurrent_deletes(self):
        """Test concurrent deletes don't cause issues."""
        layer = L1TransientLayer(capacity=100)

        # Initialize data
        for i in range(50):
            await layer.set(f"key_{i}", {"value": i}, MemoryScope.SESSION, "session_1")

        # Concurrent deletes
        async def delete_task(start_idx):
            for i in range(start_idx, start_idx + 10):
                await layer.delete(f"key_{i}", MemoryScope.SESSION, "session_1")

        tasks = [delete_task(i * 10) for i in range(5)]
        await asyncio.gather(*tasks)

        # All keys should be deleted
        keys = await layer.list_keys(MemoryScope.SESSION, "session_1")
        assert len(keys) == 0

    @pytest.mark.asyncio
    async def test_concurrent_delete_and_read(self):
        """Test concurrent delete and read operations."""
        layer = L1TransientLayer(capacity=100)

        # Initialize data
        for i in range(10):
            await layer.set(f"key_{i}", {"value": i}, MemoryScope.SESSION, "session_1")

        results = []

        async def delete_task():
            for i in range(10):
                await asyncio.sleep(0.001)  # Small delay
                await layer.delete(f"key_{i}", MemoryScope.SESSION, "session_1")

        async def read_task():
            for i in range(10):
                result = await layer.get(f"key_{i}", MemoryScope.SESSION, "session_1")
                results.append(result is not None)

        # Run concurrent operations
        await asyncio.gather(delete_task(), read_task())

        # Operations should complete without error
        assert len(results) == 10


class TestConcurrentClearScope:
    """Test concurrent clear_scope operations."""

    @pytest.mark.asyncio
    async def test_concurrent_clear_different_scopes(self):
        """Test clearing different scopes concurrently."""
        layer = L1TransientLayer(capacity=100)

        # Initialize data in different scopes
        for i in range(5):
            for j in range(10):
                await layer.set(f"scope_{i}_key_{j}", {"value": j}, MemoryScope.SESSION, f"session_{i}")

        # Clear scopes concurrently
        async def clear_task(scope_id):
            return await layer.clear_scope(MemoryScope.SESSION, scope_id)

        tasks = [clear_task(f"session_{i}") for i in range(5)]
        results = await asyncio.gather(*tasks)

        # All should report clearing 10 items
        assert all(r == 10 for r in results)


class TestConcurrentStats:
    """Test concurrent statistics collection."""

    @pytest.mark.asyncio
    async def test_concurrent_stats_collection(self):
        """Test that concurrent stats collection doesn't cause issues."""
        layer = L1TransientLayer(capacity=100)

        # Write some data
        for i in range(10):
            await layer.set(f"key_{i}", {"value": i}, MemoryScope.SESSION, "session_1")

        # Concurrent stats collection
        async def stats_task():
            return await layer.get_stats()

        tasks = [stats_task() for _ in range(20)]
        results = await asyncio.gather(*tasks)

        # All stats should be consistent
        assert all(r["data_count"] == 10 for r in results)
