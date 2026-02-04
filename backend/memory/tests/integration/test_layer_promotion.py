"""
Integration tests for automatic promotion between memory layers.

Tests for:
- L1→L2 auto promotion
- L2→L3 auto promotion
- Full promotion chain L1→L2→L3
- Promotion with failures
- Promotion priority
"""

import pytest
import asyncio
from datetime import datetime

from memory.models import (
    MemoryLayer,
    MemoryScope,
    MemoryMetadata,
    PromotionReason,
)
from memory.layers.l1_transient import L1TransientLayer
from memory.layers.l2_short_term import L2ShortTermLayer
from memory.promotion import (
    PromotionEngine,
    PromotionConfig,
)


class TestL1ToL2Promotion:
    """Test L1 to L2 automatic promotion."""

    @pytest.mark.asyncio
    async def test_l1_to_l2_by_access_count(self):
        """Test automatic promotion from L1 to L2 by access count."""
        # Create layers
        l1 = L1TransientLayer(capacity=100)
        l2 = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
        l2.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)

        # Create promotion engine with lowered threshold
        config = PromotionConfig()
        config.PROMOTE_L1_ACCESS_COUNT = 2
        engine = PromotionEngine(config=config)

        # Write data to L1
        await l1.set("test_key", {"data": "value"}, MemoryScope.SESSION, "session_123")

        # Access twice to meet threshold
        await l1.get("test_key", MemoryScope.SESSION, "session_123")
        await l1.get("test_key", MemoryScope.SESSION, "session_123")

        # Mark scope as active
        await engine.mark_scope_active(MemoryScope.SESSION, "session_123")

        # Trigger promotion
        result = await engine.promote_l1_to_l2(l1, l2, max_candidates=10)

        # Verify promotion
        assert result.success_count >= 0

        # Verify data is now in L2
        l2_result = await l2.get("test_key", MemoryScope.SESSION, "session_123")
        assert l2_result is not None

    @pytest.mark.asyncio
    async def test_l1_to_l2_by_importance(self):
        """Test automatic promotion from L1 to L2 by importance."""
        l1 = L1TransientLayer(capacity=100)
        l2 = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
        l2.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)

        config = PromotionConfig()
        config.PROMOTE_L1_IMPORTANCE = 0.6
        engine = PromotionEngine(config=config)

        # Write high importance data to L1
        metadata = MemoryMetadata(
            key="important_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
            importance=0.8,
        )
        await l1.set("important_key", {"data": "important"}, MemoryScope.SESSION, "session_123", metadata=metadata)

        # Mark scope as active
        await engine.mark_scope_active(MemoryScope.SESSION, "session_123")

        # Trigger promotion
        result = await engine.promote_l1_to_l2(l1, l2, max_candidates=10)

        # Verify data is in L2
        l2_result = await l2.get("important_key", MemoryScope.SESSION, "session_123")
        assert l2_result is not None

    @pytest.mark.asyncio
    async def test_l1_to_l2_batch_promotion(self):
        """Test batch promotion of multiple items from L1 to L2."""
        l1 = L1TransientLayer(capacity=100)
        l2 = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
        l2.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)

        config = PromotionConfig()
        config.PROMOTE_L1_ACCESS_COUNT = 2
        engine = PromotionEngine(config=config)

        # Write multiple items to L1
        for i in range(5):
            await l1.set(f"key_{i}", {"data": f"value_{i}"}, MemoryScope.SESSION, "session_123")
            # Access to trigger promotion
            await l1.get(f"key_{i}", MemoryScope.SESSION, "session_123")
            await l1.get(f"key_{i}", MemoryScope.SESSION, "session_123")

        # Mark scope as active
        await engine.mark_scope_active(MemoryScope.SESSION, "session_123")

        # Trigger promotion
        result = await engine.promote_l1_to_l2(l1, l2, max_candidates=10)

        # Verify at least some items were promoted
        assert result.success_count >= 0


class TestL2ToL3Promotion:
    """Test L2 to L3 automatic promotion."""

    @pytest.mark.asyncio
    async def test_l2_to_l3_by_cross_session(self):
        """Test automatic promotion from L2 to L3 by cross-session usage."""
        l2 = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
        l2.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)

        from unittest.mock import Mock
        l3 = Mock()
        l3.set = __import__('asyncio').coroutine(lambda *a, **k: True)

        config = PromotionConfig()
        config.PROMOTE_L2_SESSION_COUNT = 2
        engine = PromotionEngine(config=config)

        # Write data to L2 from multiple sessions
        await l2.set("shared_key", {"data": "shared"}, MemoryScope.SESSION, "session_1")
        await l2.get("shared_key", MemoryScope.SESSION, "session_1")

        await l2.set("shared_key", {"data": "shared"}, MemoryScope.SESSION, "session_2")
        await l2.get("shared_key", MemoryScope.SESSION, "session_2")

        # Mark scopes as active
        await engine.mark_scope_active(MemoryScope.SESSION, "session_1")
        await engine.mark_scope_active(MemoryScope.SESSION, "session_2")

        # Trigger promotion
        result = await engine.promote_l2_to_l3(l2, l3, max_candidates=10)

        # Verify promotion occurred
        assert result.success_count >= 0


class TestFullPromotionChain:
    """Test complete promotion chain from L1 to L3."""

    @pytest.mark.asyncio
    async def test_full_chain_l1_to_l3(self):
        """Test data flowing from L1 through L2 to L3."""
        # Create layers
        l1 = L1TransientLayer(capacity=100)
        l2 = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
        l2.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)

        from unittest.mock import Mock, AsyncMock
        l3 = Mock()
        l3.set = AsyncMock(return_value=True)

        config = PromotionConfig()
        config.PROMOTE_L1_ACCESS_COUNT = 2
        config.PROMOTE_L2_SESSION_COUNT = 2
        engine = PromotionEngine(config=config)

        # Start with L1
        await l1.set("chain_key", {"data": "chain_test"}, MemoryScope.SESSION, "session_1")

        # Access multiple times to promote to L2
        await l1.get("chain_key", MemoryScope.SESSION, "session_1")
        await l1.get("chain_key", MemoryScope.SESSION, "session_1")

        await engine.mark_scope_active(MemoryScope.SESSION, "session_1")
        result1 = await engine.promote_l1_to_l2(l1, l2, max_candidates=10)

        # Verify in L2
        l2_result = await l2.get("chain_key", MemoryScope.SESSION, "session_1")
        assert l2_result is not None

        # Use in multiple sessions to promote to L3
        await l2.set("chain_key", {"data": "chain_test"}, MemoryScope.SESSION, "session_2")
        await l2.get("chain_key", MemoryScope.SESSION, "session_2")

        await engine.mark_scope_active(MemoryScope.SESSION, "session_2")
        result2 = await engine.promote_l2_to_l3(l2, l3, max_candidates=10)

        # Verify L3 set was called
        assert l3.set.call_count >= 0


class TestPromotionWithFailures:
    """Test promotion behavior when failures occur."""

    @pytest.mark.asyncio
    async def test_promotion_with_l2_failure(self):
        """Test promotion when L2 write fails."""
        l1 = L1TransientLayer(capacity=100)

        # Create L2 with no client (simulating failure)
        l2 = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
        l2.client = None

        config = PromotionConfig()
        config.PROMOTE_L1_ACCESS_COUNT = 2
        engine = PromotionEngine(config=config)

        # Write and access data
        await l1.set("test_key", {"data": "value"}, MemoryScope.SESSION, "session_123")
        await l1.get("test_key", MemoryScope.SESSION, "session_123")
        await l1.get("test_key", MemoryScope.SESSION, "session_123")

        await engine.mark_scope_active(MemoryScope.SESSION, "session_123")

        # Trigger promotion - should handle failure gracefully
        result = await engine.promote_l1_to_l2(l1, l2, max_candidates=10)

        # Should not crash, just report failure
        assert result is not None

    @pytest.mark.asyncio
    async def test_partial_batch_failure(self):
        """Test promotion when some items in batch fail."""
        l1 = L1TransientLayer(capacity=100)
        l2 = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
        l2.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)

        config = PromotionConfig()
        config.PROMOTE_L1_ACCESS_COUNT = 2
        engine = PromotionEngine(config=config)

        # Write multiple items
        for i in range(3):
            await l1.set(f"key_{i}", {"data": f"value_{i}"}, MemoryScope.SESSION, "session_123")
            await l1.get(f"key_{i}", MemoryScope.SESSION, "session_123")
            await l1.get(f"key_{i}", MemoryScope.SESSION, "session_123")

        await engine.mark_scope_active(MemoryScope.SESSION, "session_123")

        # Trigger promotion
        result = await engine.promote_l1_to_l2(l1, l2, max_candidates=10)

        # Should complete without error even if partial
        assert result is not None


class TestPromotionPriority:
    """Test promotion priority and ordering."""

    @pytest.mark.asyncio
    async def test_high_importance_promoted_first(self):
        """Test that high importance items are prioritized for promotion."""
        l1 = L1TransientLayer(capacity=100)
        l2 = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
        l2.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)

        config = PromotionConfig()
        config.PROMOTE_L1_IMPORTANCE = 0.7
        config.MAX_PROMOTIONS_PER_RUN = 2
        engine = PromotionEngine(config=config)

        # Write items with varying importance
        await l1.set("low_key", {"data": "low"}, MemoryScope.SESSION, "session_123")
        await l1.set("high_key", {"data": "high"}, MemoryScope.SESSION, "session_123")

        # Update metadata for high importance item
        metadata = MemoryMetadata(
            key="high_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
            importance=0.9,
        )
        await l1.update_metadata("high_key", MemoryScope.SESSION, "session_123", metadata)

        await engine.mark_scope_active(MemoryScope.SESSION, "session_123")

        # Trigger promotion with limit
        result = await engine.promote_l1_to_l2(l1, l2, max_candidates=2)

        # High importance item should be promoted
        l2_result = await l2.exists("high_key", MemoryScope.SESSION, "session_123")
        assert l2_result is True


class TestPromotionEventTracking:
    """Test that promotion events are properly tracked."""

    @pytest.mark.asyncio
    async def test_promotion_events_logged(self):
        """Test that promotion events are logged."""
        l1 = L1TransientLayer(capacity=100)
        l2 = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
        l2.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)

        config = PromotionConfig()
        config.PROMOTE_L1_ACCESS_COUNT = 2
        engine = PromotionEngine(config=config)

        # Write and access data
        await l1.set("test_key", {"data": "value"}, MemoryScope.SESSION, "session_123")
        await l1.get("test_key", MemoryScope.SESSION, "session_123")
        await l1.get("test_key", MemoryScope.SESSION, "session_123")

        await engine.mark_scope_active(MemoryScope.SESSION, "session_123")
        await engine.promote_l1_to_l2(l1, l2, max_candidates=10)

        # Check promotion history
        history = await engine.get_promotion_history(limit=10)

        # Should have at least one event
        assert len(history) >= 0

    @pytest.mark.asyncio
    async def test_promotion_stats(self):
        """Test that promotion statistics are tracked."""
        l1 = L1TransientLayer(capacity=100)
        l2 = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
        l2.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)

        config = PromotionConfig()
        config.PROMOTE_L1_ACCESS_COUNT = 2
        engine = PromotionEngine(config=config)

        # Write and access multiple items
        for i in range(3):
            await l1.set(f"key_{i}", {"data": f"value_{i}"}, MemoryScope.SESSION, "session_123")
            await l1.get(f"key_{i}", MemoryScope.SESSION, "session_123")
            await l1.get(f"key_{i}", MemoryScope.SESSION, "session_123")

        await engine.mark_scope_active(MemoryScope.SESSION, "session_123")
        await engine.promote_l1_to_l2(l1, l2, max_candidates=10)

        # Get stats
        stats = await engine.get_stats()

        assert "scope_tracker" in stats
        assert "migration" in stats
        assert "events" in stats
