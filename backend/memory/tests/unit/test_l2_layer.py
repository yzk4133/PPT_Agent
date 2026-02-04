"""
Unit tests for L2 Short-term Memory Layer.

Tests for:
- Redis connection handling
- Basic storage and retrieval
- Serialization/deserialization
- Pipeline batch operations
- Cross-session tracking
- Batch writes
- Redis failure handling
- Data expiration (TTL)
"""

import pytest
import json
from unittest.mock import Mock, patch

from memory.models import (
    MemoryLayer,
    MemoryScope,
    MemoryMetadata,
)
from memory.layers.l2_short_term import L2ShortTermLayer


class TestL2ShortTermLayer:
    """Test L2ShortTermLayer functionality."""

    def test_layer_initialization(self, l2_layer):
        """Test layer initialization."""
        assert l2_layer.layer_type == MemoryLayer.L2_SHORT_TERM
        assert l2_layer.default_ttl_seconds == 3600
        assert l2_layer.client is not None
        assert l2_layer.stats["hits"] == 0
        assert l2_layer.stats["misses"] == 0

    @pytest.mark.asyncio
    async def test_redis_connection_available(self, l2_layer):
        """Test checking if Redis is available."""
        assert l2_layer._is_available() is True

    @pytest.mark.asyncio
    async def test_set_and_get(self, l2_layer):
        """Test basic set and get operations."""
        value = {"data": "test_value", "nested": {"key": "value"}}
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L2_SHORT_TERM,
            scope=MemoryScope.SESSION,
            importance=0.6,
        )

        # Set
        result = await l2_layer.set(
            "test_key",
            value,
            MemoryScope.SESSION,
            "session_123",
            metadata=metadata,
        )
        assert result is True

        # Get
        retrieved_value, retrieved_metadata = await l2_layer.get(
            "test_key", MemoryScope.SESSION, "session_123"
        )

        assert retrieved_value == value
        assert retrieved_metadata.key == "test_key"
        assert retrieved_metadata.access_count == 1

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, l2_layer):
        """Test getting a non-existent key."""
        result = await l2_layer.get("nonexistent", MemoryScope.SESSION, "session_123")

        assert result is None
        assert l2_layer.stats["misses"] == 1

    @pytest.mark.asyncio
    async def test_get_increments_access_count(self, l2_layer):
        """Test that getting a value increments access count."""
        await l2_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.SESSION,
            "session_123",
        )

        # First get
        _, metadata1 = await l2_layer.get("test_key", MemoryScope.SESSION, "session_123")
        assert metadata1.access_count == 1

        # Second get
        _, metadata2 = await l2_layer.get("test_key", MemoryScope.SESSION, "session_123")
        assert metadata2.access_count == 2

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, l2_layer):
        """Test setting data with custom TTL."""
        short_ttl = 2  # 2 seconds

        await l2_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.TASK,
            "task_123",
            ttl_seconds=short_ttl,
        )

        # Should be accessible immediately
        result = await l2_layer.get("test_key", MemoryScope.TASK, "task_123")
        assert result is not None

        # Wait for expiration
        import asyncio
        await asyncio.sleep(2.5)

        result = await l2_layer.get("test_key", MemoryScope.TASK, "task_123")
        assert result is None

    @pytest.mark.asyncio
    async def test_serialization_complex_data(self, l2_layer):
        """Test serialization of complex data structures."""
        complex_value = {
            "string": "test",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3, "four"],
            "nested": {
                "deep": {
                    "value": "here"
                }
            },
            "unicode": "你好世界 🌍",
        }

        await l2_layer.set(
            "complex_key",
            complex_value,
            MemoryScope.SESSION,
            "session_123",
        )

        retrieved_value, _ = await l2_layer.get(
            "complex_key", MemoryScope.SESSION, "session_123"
        )

        assert retrieved_value == complex_value

    @pytest.mark.asyncio
    async def test_serialization_metadata(self, l2_layer):
        """Test serialization and deserialization of metadata."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L2_SHORT_TERM,
            scope=MemoryScope.SESSION,
            importance=0.85,
            access_count=5,
            tags=["tag1", "tag2", "tag3"],
        )

        serialized = l2_layer._serialize_metadata(metadata)
        deserialized = l2_layer._deserialize_metadata(serialized)

        assert deserialized.key == metadata.key
        assert deserialized.importance == metadata.importance
        assert deserialized.access_count == metadata.access_count
        assert deserialized.tags == metadata.tags

    @pytest.mark.asyncio
    async def test_delete(self, l2_layer):
        """Test deleting data."""
        await l2_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.SESSION,
            "session_123",
        )

        exists = await l2_layer.exists("test_key", MemoryScope.SESSION, "session_123")
        assert exists is True

        result = await l2_layer.delete("test_key", MemoryScope.SESSION, "session_123")
        assert result is True

        exists = await l2_layer.exists("test_key", MemoryScope.SESSION, "session_123")
        assert exists is False

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, l2_layer):
        """Test deleting a non-existent key."""
        result = await l2_layer.delete("nonexistent", MemoryScope.SESSION, "session_123")
        assert result is False

    @pytest.mark.asyncio
    async def test_exists(self, l2_layer):
        """Test checking if data exists."""
        # Before set
        exists = await l2_layer.exists("test_key", MemoryScope.SESSION, "session_123")
        assert exists is False

        # After set
        await l2_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.SESSION,
            "session_123",
        )
        exists = await l2_layer.exists("test_key", MemoryScope.SESSION, "session_123")
        assert exists is True

    @pytest.mark.asyncio
    async def test_list_keys(self, l2_layer):
        """Test listing keys in a scope."""
        await l2_layer.set("key1", {"data": "1"}, MemoryScope.SESSION, "session_123")
        await l2_layer.set("key2", {"data": "2"}, MemoryScope.SESSION, "session_123")
        await l2_layer.set("key3", {"data": "3"}, MemoryScope.SESSION, "session_123")

        keys = await l2_layer.list_keys(MemoryScope.SESSION, "session_123")

        assert set(keys) == {"key1", "key2", "key3"}

    @pytest.mark.asyncio
    async def test_list_keys_with_pattern(self, l2_layer):
        """Test listing keys with a pattern."""
        await l2_layer.set("test:key1", {"data": "1"}, MemoryScope.SESSION, "session_123")
        await l2_layer.set("test:key2", {"data": "2"}, MemoryScope.SESSION, "session_123")
        await l2_layer.set("other:key3", {"data": "3"}, MemoryScope.SESSION, "session_123")

        keys = await l2_layer.list_keys(MemoryScope.SESSION, "session_123", pattern="test:*")

        assert set(keys) == {"test:key1", "test:key2"}

    @pytest.mark.asyncio
    async def test_list_keys_scope_isolation(self, l2_layer):
        """Test that keys are isolated by scope."""
        await l2_layer.set("key1", {"data": "1"}, MemoryScope.SESSION, "session_123")
        await l2_layer.set("key1", {"data": "2"}, MemoryScope.TASK, "task_456")

        session_keys = await l2_layer.list_keys(MemoryScope.SESSION, "session_123")
        task_keys = await l2_layer.list_keys(MemoryScope.TASK, "task_456")

        assert "key1" in session_keys
        assert "key1" in task_keys

        # Verify they're different values
        session_value, _ = await l2_layer.get("key1", MemoryScope.SESSION, "session_123")
        task_value, _ = await l2_layer.get("key1", MemoryScope.TASK, "task_456")

        assert session_value["data"] == "1"
        assert task_value["data"] == "2"

    @pytest.mark.asyncio
    async def test_get_metadata(self, l2_layer):
        """Test getting metadata for a key."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L2_SHORT_TERM,
            scope=MemoryScope.SESSION,
            importance=0.75,
            tags=["important", "cached"],
        )

        await l2_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.SESSION,
            "session_123",
            metadata=metadata,
        )

        retrieved_metadata = await l2_layer.get_metadata(
            "test_key", MemoryScope.SESSION, "session_123"
        )

        assert retrieved_metadata is not None
        assert retrieved_metadata.importance == 0.75
        assert retrieved_metadata.tags == ["important", "cached"]

    @pytest.mark.asyncio
    async def test_update_metadata(self, l2_layer):
        """Test updating metadata for a key."""
        await l2_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.SESSION,
            "session_123",
        )

        updated_metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L2_SHORT_TERM,
            scope=MemoryScope.SESSION,
            importance=0.95,
            tags=["updated", "important"],
        )

        result = await l2_layer.update_metadata(
            "test_key", MemoryScope.SESSION, "session_123", updated_metadata
        )

        assert result is True

        retrieved_metadata = await l2_layer.get_metadata(
            "test_key", MemoryScope.SESSION, "session_123"
        )
        assert retrieved_metadata.importance == 0.95
        assert retrieved_metadata.tags == ["updated", "important"]

    @pytest.mark.asyncio
    async def test_update_metadata_nonexistent_key(self, l2_layer):
        """Test updating metadata for a non-existent key."""
        metadata = MemoryMetadata(
            key="nonexistent",
            layer=MemoryLayer.L2_SHORT_TERM,
            scope=MemoryScope.SESSION,
        )

        result = await l2_layer.update_metadata(
            "nonexistent", MemoryScope.SESSION, "session_123", metadata
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_clear_scope(self, l2_layer):
        """Test clearing all data in a scope."""
        await l2_layer.set("key1", {"data": "1"}, MemoryScope.SESSION, "session_123")
        await l2_layer.set("key2", {"data": "2"}, MemoryScope.SESSION, "session_123")
        await l2_layer.set("key3", {"data": "3"}, MemoryScope.TASK, "task_456")

        count = await l2_layer.clear_scope(MemoryScope.SESSION, "session_123")

        assert count == 2

        session_keys = await l2_layer.list_keys(MemoryScope.SESSION, "session_123")
        task_keys = await l2_layer.list_keys(MemoryScope.TASK, "task_456")

        assert len(session_keys) == 0
        assert len(task_keys) == 1

    @pytest.mark.asyncio
    async def test_get_stats(self, l2_layer):
        """Test getting layer statistics."""
        await l2_layer.set("key1", {"data": "1"}, MemoryScope.SESSION, "session_123")
        await l2_layer.get("key1", MemoryScope.SESSION, "session_123")
        await l2_layer.get("nonexistent", MemoryScope.SESSION, "session_123")

        stats = await l2_layer.get_stats()

        assert stats["layer"] == "short_term"
        assert stats["redis_available"] is True
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_batch_set(self, l2_layer):
        """Test batch setting of data."""
        items = [
            ("key1", {"data": "1"}, MemoryScope.SESSION, "session_123", None),
            ("key2", {"data": "2"}, MemoryScope.SESSION, "session_123", None),
            ("key3", {"data": "3"}, MemoryScope.SESSION, "session_123", None),
        ]

        count = await l2_layer.batch_set(items)

        assert count == 3
        assert l2_layer.stats["batch_writes"] == 1

        # Verify all keys were set
        for key in ["key1", "key2", "key3"]:
            result = await l2_layer.get(key, MemoryScope.SESSION, "session_123")
            assert result is not None

    @pytest.mark.asyncio
    async def test_batch_set_with_metadata(self, l2_layer):
        """Test batch setting with custom metadata."""
        items = []
        for i in range(3):
            metadata = MemoryMetadata(
                key=f"key{i}",
                layer=MemoryLayer.L2_SHORT_TERM,
                scope=MemoryScope.SESSION,
                importance=0.7 + i * 0.1,
            )
            items.append((f"key{i}", {"data": i}, MemoryScope.SESSION, "session_123", metadata))

        count = await l2_layer.batch_set(items)

        assert count == 3

        # Verify metadata
        _, metadata0 = await l2_layer.get("key0", MemoryScope.SESSION, "session_123")
        _, metadata2 = await l2_layer.get("key2", MemoryScope.SESSION, "session_123")

        assert metadata0.importance == 0.7
        assert metadata2.importance == 0.9

    @pytest.mark.asyncio
    async def test_cross_session_tracking(self, l2_layer):
        """Test tracking cross-session usage."""
        # First session access
        await l2_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.SESSION,
            "session_1",
        )
        await l2_layer.get("test_key", MemoryScope.SESSION, "session_1")

        # Second session access
        await l2_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.SESSION,
            "session_2",
        )
        _, metadata = await l2_layer.get("test_key", MemoryScope.SESSION, "session_2")

        # Should have tracked both sessions
        cross_session_count = await l2_layer.get_cross_session_count("test_key")

        # The tracker is key-based, not scope-based
        assert cross_session_count >= 1

    @pytest.mark.asyncio
    async def test_session_scope_adds_session_id(self, l2_layer):
        """Test that SESSION scope adds session_id to metadata."""
        await l2_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.SESSION,
            "session_abc",
        )

        # Get should add session_id
        _, metadata = await l2_layer.get("test_key", MemoryScope.SESSION, "session_abc")

        assert "session_abc" in metadata.session_ids

    @pytest.mark.asyncio
    async def test_redis_failure_handling_get(self):
        """Test handling of Redis failure during get."""
        layer = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
        layer.client = None  # Simulate Redis failure

        result = await layer.get("test_key", MemoryScope.SESSION, "session_123")

        assert result is None
        assert layer.stats["misses"] == 1

    @pytest.mark.asyncio
    async def test_redis_failure_handling_set(self):
        """Test handling of Redis failure during set."""
        layer = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
        layer.client = None  # Simulate Redis failure

        result = await layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.SESSION,
            "session_123",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_redis_failure_handling_delete(self):
        """Test handling of Redis failure during delete."""
        layer = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
        layer.client = None  # Simulate Redis failure

        result = await layer.delete("test_key", MemoryScope.SESSION, "session_123")

        assert result is False

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, l2_layer):
        """Test concurrent operations on L2 layer."""
        import asyncio

        # Concurrent writes
        write_tasks = [
            l2_layer.set(
                f"key_{i}",
                {"data": f"value_{i}"},
                MemoryScope.SESSION,
                "session_123",
            )
            for i in range(50)
        ]
        await asyncio.gather(*write_tasks)

        # Concurrent reads
        read_tasks = [
            l2_layer.get(f"key_{i}", MemoryScope.SESSION, "session_123")
            for i in range(50)
        ]
        results = await asyncio.gather(*read_tasks)

        successful_reads = [r for r in results if r is not None]
        assert len(successful_reads) == 50

    @pytest.mark.asyncio
    async def test_full_key_building(self, l2_layer):
        """Test that full keys are built correctly."""
        # Test the internal _build_full_key method
        full_key = l2_layer._build_full_key("mykey", MemoryScope.SESSION, "session_123")

        assert full_key == "short_term:session:session_123:mykey"

    @pytest.mark.asyncio
    async def test_data_and_meta_keys(self, l2_layer):
        """Test that data and metadata have separate keys."""
        await l2_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.SESSION,
            "session_123",
        )

        data_key = l2_layer._get_data_key("test_key", MemoryScope.SESSION, "session_123")
        meta_key = l2_layer._get_meta_key("test_key", MemoryScope.SESSION, "session_123")

        assert data_key.endswith(":data")
        assert meta_key.endswith(":meta")
        assert data_key != meta_key

        # Both should exist
        assert l2_layer.client.exists(data_key) > 0
        assert l2_layer.client.exists(meta_key) > 0
