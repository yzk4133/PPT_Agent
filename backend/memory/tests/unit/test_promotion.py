"""
Unit tests for Promotion Engine.

Tests for:
- Active scope tracking
- Scope TTL cleanup
- L1→L2 promotion rules
- L2→L3 promotion rules
- Data migration
- Promotion event logging
- Migration statistics
- Max candidates limit
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from memory.models import (
    MemoryLayer,
    MemoryScope,
    MemoryMetadata,
    PromotionReason,
)
from memory.promotion import (
    PromotionConfig,
    ActiveScopeTracker,
    PromotionRuleEngine,
    DataMigrator,
    PromotionEventLogger,
    PromotionEngine,
    MigrationResult,
)


class TestPromotionConfig:
    """Test PromotionConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PromotionConfig()

        assert config.PROMOTE_L1_ACCESS_COUNT == 3
        assert config.PROMOTE_L1_IMPORTANCE == 0.7
        assert config.PROMOTE_L2_SESSION_COUNT == 2
        assert config.MAX_PROMOTIONS_PER_RUN == 50
        assert config.MAX_CANDIDATES_PER_BATCH == 100

    def test_custom_config(self):
        """Test custom configuration values."""
        config = PromotionConfig()
        config.PROMOTE_L1_ACCESS_COUNT = 2
        config.PROMOTE_L1_IMPORTANCE = 0.6
        config.PROMOTE_L2_SESSION_COUNT = 1

        assert config.PROMOTE_L1_ACCESS_COUNT == 2
        assert config.PROMOTE_L1_IMPORTANCE == 0.6
        assert config.PROMOTE_L2_SESSION_COUNT == 1


class TestActiveScopeTracker:
    """Test ActiveScopeTracker."""

    @pytest.mark.asyncio
    async def test_initialization(self, active_scope_tracker):
        """Test tracker initialization."""
        assert active_scope_tracker.ttl_seconds == 3600
        assert len(active_scope_tracker._active_scopes) == 0

    @pytest.mark.asyncio
    async def test_mark_active(self, active_scope_tracker):
        """Test marking a scope as active."""
        await active_scope_tracker.mark_active(MemoryScope.SESSION, "session_123")

        is_active = await active_scope_tracker.is_active(MemoryScope.SESSION, "session_123")
        assert is_active is True

    @pytest.mark.asyncio
    async def test_mark_multiple_active(self, active_scope_tracker):
        """Test marking multiple scopes as active."""
        await active_scope_tracker.mark_active(MemoryScope.SESSION, "session_1")
        await active_scope_tracker.mark_active(MemoryScope.TASK, "task_2")
        await active_scope_tracker.mark_active(MemoryScope.AGENT, "agent_3")

        stats = await active_scope_tracker.get_stats()
        assert stats["total_active_scopes"] == 3

    @pytest.mark.asyncio
    async def test_is_active_nonexistent(self, active_scope_tracker):
        """Test checking if non-existent scope is active."""
        is_active = await active_scope_tracker.is_active(MemoryScope.SESSION, "nonexistent")
        assert is_active is False

    @pytest.mark.asyncio
    async def test_is_active_expired(self):
        """Test that expired scopes are not active."""
        # Create tracker with short TTL
        tracker = ActiveScopeTracker(ttl_seconds=1)

        await tracker.mark_active(MemoryScope.SESSION, "session_123")

        # Should be active immediately
        assert await tracker.is_active(MemoryScope.SESSION, "session_123") is True

        # Wait for expiration
        import asyncio
        await asyncio.sleep(1.5)

        # Should be inactive now
        assert await tracker.is_active(MemoryScope.SESSION, "session_123") is False

    @pytest.mark.asyncio
    async def test_get_active_scopes(self, active_scope_tracker):
        """Test getting all active scopes."""
        await active_scope_tracker.mark_active(MemoryScope.SESSION, "session_1")
        await active_scope_tracker.mark_active(MemoryScope.TASK, "task_2")
        await active_scope_tracker.mark_active(MemoryScope.AGENT, "agent_3")

        active_scopes = await active_scope_tracker.get_active_scopes()

        assert len(active_scopes) == 3
        assert (MemoryScope.SESSION, "session_1") in active_scopes
        assert (MemoryScope.TASK, "task_2") in active_scopes
        assert (MemoryScope.AGENT, "agent_3") in active_scopes

    @pytest.mark.asyncio
    async def test_get_active_scopes_filters_expired(self):
        """Test that get_active_scopes filters out expired scopes."""
        tracker = ActiveScopeTracker(ttl_seconds=1)

        await tracker.mark_active(MemoryScope.SESSION, "session_1")
        await tracker.mark_active(MemoryScope.TASK, "task_2")

        import asyncio
        await asyncio.sleep(1.5)

        # Mark another scope as active (should be the only one)
        await tracker.mark_active(MemoryScope.AGENT, "agent_3")

        active_scopes = await tracker.get_active_scopes()

        assert len(active_scopes) == 1
        assert active_scopes[0] == (MemoryScope.AGENT, "agent_3")

    @pytest.mark.asyncio
    async def test_cleanup_inactive(self):
        """Test cleanup of inactive scopes."""
        tracker = ActiveScopeTracker(ttl_seconds=1)

        await tracker.mark_active(MemoryScope.SESSION, "session_1")
        await tracker.mark_active(MemoryScope.TASK, "task_2")

        # Wait for expiration
        import asyncio
        await asyncio.sleep(1.5)

        await tracker.cleanup_inactive()

        stats = await tracker.get_stats()
        assert stats["total_active_scopes"] == 0

    @pytest.mark.asyncio
    async def test_mark_active_updates_timestamp(self):
        """Test that marking active updates the timestamp."""
        tracker = ActiveScopeTracker(ttl_seconds=2)

        await tracker.mark_active(MemoryScope.SESSION, "session_123")

        import asyncio
        await asyncio.sleep(1)

        # Mark as active again, should reset TTL
        await tracker.mark_active(MemoryScope.SESSION, "session_123")

        await asyncio.sleep(1.5)

        # Should still be active
        assert await tracker.is_active(MemoryScope.SESSION, "session_123") is True


class TestPromotionRuleEngine:
    """Test PromotionRuleEngine."""

    def test_should_promote_l1_to_l2_by_access(self, promotion_rule_engine):
        """Test L1→L2 promotion by access count."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            access_count=3,
            importance=0.5,
        )

        should_promote, reason, explanation = promotion_rule_engine.should_promote_l1_to_l2(metadata)

        assert should_promote is True
        assert reason == PromotionReason.HIGH_ACCESS_FREQUENCY
        assert "access_count" in explanation

    def test_should_promote_l1_to_l2_by_importance(self, promotion_rule_engine):
        """Test L1→L2 promotion by importance."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            access_count=1,
            importance=0.7,
        )

        should_promote, reason, explanation = promotion_rule_engine.should_promote_l1_to_l2(metadata)

        assert should_promote is True
        assert reason == PromotionReason.HIGH_IMPORTANCE_SCORE
        assert "importance" in explanation

    def test_should_not_promote_l1_to_l2(self, promotion_rule_engine):
        """Test that data doesn't promote when conditions not met."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            access_count=1,
            importance=0.5,
        )

        should_promote, reason, explanation = promotion_rule_engine.should_promote_l1_to_l2(metadata)

        assert should_promote is False
        assert reason is None

    def test_should_promote_l1_with_long_lifetime(self, promotion_rule_engine):
        """Test L1→L2 promotion by long lifetime."""
        # Create metadata with age > 10 minutes
        created_at = datetime.now() - timedelta(minutes=15)
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            created_at=created_at,
            access_count=2,  # Meets threshold with age
            importance=0.5,
        )

        # Calculate age
        age_seconds = (datetime.now() - created_at).total_seconds()

        should_promote, reason, explanation = promotion_rule_engine.should_promote_l1_to_l2(
            metadata, age_seconds
        )

        assert should_promote is True
        assert reason == PromotionReason.LONG_LIFETIME

    def test_should_promote_l2_to_l3_by_cross_session(self, promotion_rule_engine):
        """Test L2→L3 promotion by cross-session usage."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L2_SHORT_TERM,
            scope=MemoryScope.SESSION,
            session_ids=["session1", "session2"],
        )

        should_promote, reason, explanation = promotion_rule_engine.should_promote_l2_to_l3(
            metadata, cross_session_count=2
        )

        assert should_promote is True
        assert reason == PromotionReason.CROSS_SESSION_USAGE

    def test_should_promote_l2_to_l3_by_high_access_and_importance(self, promotion_rule_engine):
        """Test L2→L3 promotion by high access and importance."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L2_SHORT_TERM,
            scope=MemoryScope.SESSION,
            access_count=5,
            importance=0.8,
            session_ids=["session1"],
        )

        should_promote, reason, explanation = promotion_rule_engine.should_promote_l2_to_l3(
            metadata, cross_session_count=1
        )

        assert should_promote is True
        assert reason == PromotionReason.HIGH_ACCESS_FREQUENCY

    def test_should_not_promote_l2_to_l3(self, promotion_rule_engine):
        """Test that L2 data doesn't promote when conditions not met."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L2_SHORT_TERM,
            scope=MemoryScope.SESSION,
            access_count=2,
            importance=0.5,
            session_ids=["session1"],
        )

        should_promote, reason, explanation = promotion_rule_engine.should_promote_l2_to_l3(
            metadata, cross_session_count=1
        )

        assert should_promote is False
        assert reason is None


class TestDataMigrator:
    """Test DataMigrator."""

    @pytest.mark.asyncio
    async def test_migrate_l1_to_l2_empty_candidates(self, data_migrator):
        """Test migrating empty candidate list."""
        mock_l2 = Mock()
        mock_l2.batch_set = AsyncMock(return_value=0)

        result = await data_migrator.migrate_l1_to_l2(
            candidates=[],
            l2_layer=mock_l2,
            scope=MemoryScope.SESSION,
            scope_id="session_123",
        )

        assert result.success_count == 0
        assert result.failed_count == 0
        assert result.duration_seconds >= 0

    @pytest.mark.asyncio
    async def test_migrate_l1_to_l2_success(self, data_migrator):
        """Test successful L1 to L2 migration."""
        candidates = [
            ("key1", {"data": "1"}, MemoryMetadata(key="key1", layer=MemoryLayer.L2_SHORT_TERM, scope=MemoryScope.SESSION), PromotionReason.HIGH_ACCESS_FREQUENCY),
            ("key2", {"data": "2"}, MemoryMetadata(key="key2", layer=MemoryLayer.L2_SHORT_TERM, scope=MemoryScope.SESSION), PromotionReason.HIGH_IMPORTANCE_SCORE),
        ]

        mock_l2 = Mock()
        mock_l2.batch_set = AsyncMock(return_value=2)

        result = await data_migrator.migrate_l1_to_l2(
            candidates=candidates,
            l2_layer=mock_l2,
            scope=MemoryScope.SESSION,
            scope_id="session_123",
        )

        assert result.success_count == 2
        assert result.failed_count == 0
        mock_l2.batch_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_migrate_l1_to_l2_with_failure(self, data_migrator):
        """Test L1 to L2 migration with failures."""
        candidates = [
            ("key1", {"data": "1"}, MemoryMetadata(key="key1", layer=MemoryLayer.L2_SHORT_TERM, scope=MemoryScope.SESSION), PromotionReason.HIGH_ACCESS_FREQUENCY),
            ("key2", {"data": "2"}, MemoryMetadata(key="key2", layer=MemoryLayer.L2_SHORT_TERM, scope=MemoryScope.SESSION), PromotionReason.HIGH_IMPORTANCE_SCORE),
        ]

        mock_l2 = Mock()
        mock_l2.batch_set = AsyncMock(side_effect=Exception("Redis error"))

        result = await data_migrator.migrate_l1_to_l2(
            candidates=candidates,
            l2_layer=mock_l2,
            scope=MemoryScope.SESSION,
            scope_id="session_123",
        )

        assert result.failed_count == 2
        assert len(result.errors) == 1
        assert "Redis error" in result.errors[0]

    @pytest.mark.asyncio
    async def test_migrate_l1_to_l2_batches(self, data_migrator):
        """Test L1 to L2 migration with batching."""
        # Create 150 candidates to test batching
        candidates = [
            (f"key{i}", {"data": f"{i}"}, MemoryMetadata(key=f"key{i}", layer=MemoryLayer.L2_SHORT_TERM, scope=MemoryScope.SESSION), PromotionReason.HIGH_ACCESS_FREQUENCY)
            for i in range(150)
        ]

        mock_l2 = Mock()
        mock_l2.batch_set = AsyncMock(return_value=50)  # 50 items per batch

        result = await data_migrator.migrate_l1_to_l2(
            candidates=candidates,
            l2_layer=mock_l2,
            scope=MemoryScope.SESSION,
            scope_id="session_123",
            batch_size=50,
        )

        # Should be called 3 times (150 / 50)
        assert mock_l2.batch_set.call_count == 3
        assert result.success_count == 150

    @pytest.mark.asyncio
    async def test_migrate_l2_to_l3_success(self, data_migrator):
        """Test successful L2 to L3 migration."""
        candidates = [
            ("key1", {"data": "1"}, MemoryMetadata(key="key1", layer=MemoryLayer.L3_LONG_TERM, scope=MemoryScope.USER), PromotionReason.CROSS_SESSION_USAGE),
            ("key2", {"data": "2"}, MemoryMetadata(key="key2", layer=MemoryLayer.L3_LONG_TERM, scope=MemoryScope.USER), PromotionReason.CROSS_SESSION_USAGE),
        ]

        mock_l3 = Mock()
        mock_l3.set = AsyncMock(return_value=True)

        result = await data_migrator.migrate_l2_to_l3(
            candidates=candidates,
            l3_layer=mock_l3,
            scope=MemoryScope.USER,
            scope_id="user_123",
        )

        assert result.success_count == 2
        assert result.failed_count == 0
        assert mock_l3.set.call_count == 2

    @pytest.mark.asyncio
    async def test_migrate_l2_to_l3_with_failure(self, data_migrator):
        """Test L2 to L3 migration with failures."""
        candidates = [
            ("key1", {"data": "1"}, MemoryMetadata(key="key1", layer=MemoryLayer.L3_LONG_TERM, scope=MemoryScope.USER), PromotionReason.CROSS_SESSION_USAGE),
            ("key2", {"data": "2"}, MemoryMetadata(key="key2", layer=MemoryLayer.L3_LONG_TERM, scope=MemoryScope.USER), PromotionReason.CROSS_SESSION_USAGE),
        ]

        mock_l3 = Mock()
        mock_l3.set = AsyncMock(side_effect=[True, Exception("DB error")])

        result = await data_migrator.migrate_l2_to_l3(
            candidates=candidates,
            l3_layer=mock_l3,
            scope=MemoryScope.USER,
            scope_id="user_123",
        )

        assert result.success_count == 1
        assert result.failed_count == 1
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_migrate_l2_to_l3_increments_importance(self, data_migrator):
        """Test that L2 to L3 migration increments importance."""
        candidates = [
            ("key1", {"data": "1"}, MemoryMetadata(key="key1", layer=MemoryLayer.L3_LONG_TERM, scope=MemoryScope.USER, importance=0.5), PromotionReason.CROSS_SESSION_USAGE),
        ]

        mock_l3 = Mock()
        mock_l3.set = AsyncMock(return_value=True)

        await data_migrator.migrate_l2_to_l3(
            candidates=candidates,
            l3_layer=mock_l3,
            scope=MemoryScope.USER,
            scope_id="user_123",
        )

        # Verify that importance was boosted to at least 0.8
        call_args = mock_l3.set.call_args
        metadata = call_args[0][4]  # metadata is the 5th argument
        assert metadata.importance >= 0.8

    def test_get_migration_stats(self, data_migrator):
        """Test getting migration statistics."""
        # Initially empty
        stats = data_migrator.get_migration_stats()
        assert stats["l1_to_l2"]["total"] == 0
        assert stats["l2_to_l3"]["total"] == 0


class TestPromotionEventLogger:
    """Test PromotionEventLogger."""

    @pytest.mark.asyncio
    async def test_log_event(self, promotion_event_logger):
        """Test logging a promotion event."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
            importance=0.8,
            access_count=5,
        )

        event_id = await promotion_event_logger.log_event(
            key="test_key",
            from_layer=MemoryLayer.L1_TRANSIENT,
            to_layer=MemoryLayer.L2_SHORT_TERM,
            reason=PromotionReason.HIGH_ACCESS_FREQUENCY,
            scope=MemoryScope.SESSION,
            scope_id="session_123",
            metadata=metadata,
            explanation="Access count >= 3",
            success=True,
        )

        assert event_id is not None
        assert len(promotion_event_logger._events) == 1

    @pytest.mark.asyncio
    async def test_log_event_with_error(self, promotion_event_logger):
        """Test logging a failed promotion event."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
        )

        event_id = await promotion_event_logger.log_event(
            key="test_key",
            from_layer=MemoryLayer.L1_TRANSIENT,
            to_layer=MemoryLayer.L2_SHORT_TERM,
            reason=PromotionReason.HIGH_ACCESS_FREQUENCY,
            scope=MemoryScope.SESSION,
            scope_id="session_123",
            metadata=metadata,
            explanation="Access count >= 3",
            success=False,
            error_message="Redis connection failed",
        )

        event = promotion_event_logger._events[0]
        assert event.success is False
        assert event.error_message == "Redis connection failed"

    @pytest.mark.asyncio
    async def test_get_events(self, promotion_event_logger):
        """Test retrieving events."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
        )

        # Log multiple events
        await promotion_event_logger.log_event(
            key="key1",
            from_layer=MemoryLayer.L1_TRANSIENT,
            to_layer=MemoryLayer.L2_SHORT_TERM,
            reason=PromotionReason.HIGH_ACCESS_FREQUENCY,
            scope=MemoryScope.SESSION,
            scope_id="session_123",
            metadata=metadata,
            explanation="Test 1",
            success=True,
        )

        await promotion_event_logger.log_event(
            key="key2",
            from_layer=MemoryLayer.L2_SHORT_TERM,
            to_layer=MemoryLayer.L3_LONG_TERM,
            reason=PromotionReason.CROSS_SESSION_USAGE,
            scope=MemoryScope.USER,
            scope_id="user_123",
            metadata=metadata,
            explanation="Test 2",
            success=True,
        )

        events = await promotion_event_logger.get_events(limit=10)

        assert len(events) == 2

    @pytest.mark.asyncio
    async def test_get_events_filtered_by_key(self, promotion_event_logger):
        """Test filtering events by key."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
        )

        await promotion_event_logger.log_event(
            key="key1",
            from_layer=MemoryLayer.L1_TRANSIENT,
            to_layer=MemoryLayer.L2_SHORT_TERM,
            reason=PromotionReason.HIGH_ACCESS_FREQUENCY,
            scope=MemoryScope.SESSION,
            scope_id="session_123",
            metadata=metadata,
            explanation="Test",
            success=True,
        )

        await promotion_event_logger.log_event(
            key="key2",
            from_layer=MemoryLayer.L1_TRANSIENT,
            to_layer=MemoryLayer.L2_SHORT_TERM,
            reason=PromotionReason.HIGH_IMPORTANCE_SCORE,
            scope=MemoryScope.SESSION,
            scope_id="session_123",
            metadata=metadata,
            explanation="Test",
            success=True,
        )

        events = await promotion_event_logger.get_events(limit=10, key="key1")

        assert len(events) == 1
        assert events[0]["key"] == "key1"

    @pytest.mark.asyncio
    async def test_get_events_filtered_by_layer(self, promotion_event_logger):
        """Test filtering events by layer transition."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
        )

        await promotion_event_logger.log_event(
            key="key1",
            from_layer=MemoryLayer.L1_TRANSIENT,
            to_layer=MemoryLayer.L2_SHORT_TERM,
            reason=PromotionReason.HIGH_ACCESS_FREQUENCY,
            scope=MemoryScope.SESSION,
            scope_id="session_123",
            metadata=metadata,
            explanation="Test",
            success=True,
        )

        await promotion_event_logger.log_event(
            key="key2",
            from_layer=MemoryLayer.L2_SHORT_TERM,
            to_layer=MemoryLayer.L3_LONG_TERM,
            reason=PromotionReason.CROSS_SESSION_USAGE,
            scope=MemoryScope.USER,
            scope_id="user_123",
            metadata=metadata,
            explanation="Test",
            success=True,
        )

        events = await promotion_event_logger.get_events(
            limit=10, from_layer=MemoryLayer.L1_TRANSIENT
        )

        assert len(events) == 1
        assert events[0]["from_layer"] == "transient"

    @pytest.mark.asyncio
    async def test_get_stats(self, promotion_event_logger):
        """Test getting event logger statistics."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
        )

        # Log some events
        await promotion_event_logger.log_event(
            key="key1",
            from_layer=MemoryLayer.L1_TRANSIENT,
            to_layer=MemoryLayer.L2_SHORT_TERM,
            reason=PromotionReason.HIGH_ACCESS_FREQUENCY,
            scope=MemoryScope.SESSION,
            scope_id="session_123",
            metadata=metadata,
            explanation="Test",
            success=True,
        )

        await promotion_event_logger.log_event(
            key="key2",
            from_layer=MemoryLayer.L1_TRANSIENT,
            to_layer=MemoryLayer.L2_SHORT_TERM,
            reason=PromotionReason.HIGH_IMPORTANCE_SCORE,
            scope=MemoryScope.SESSION,
            scope_id="session_123",
            metadata=metadata,
            explanation="Test",
            success=False,
        )

        stats = await promotion_event_logger.get_stats()

        assert stats["total_events"] == 2
        assert stats["successful"] == 1
        assert stats["failed"] == 1
        assert stats["unique_keys_promoted"] == 2

    @pytest.mark.asyncio
    async def test_clear_old_events(self, promotion_event_logger):
        """Test clearing old events."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
        )

        # Log an event
        await promotion_event_logger.log_event(
            key="key1",
            from_layer=MemoryLayer.L1_TRANSIENT,
            to_layer=MemoryLayer.L2_SHORT_TERM,
            reason=PromotionReason.HIGH_ACCESS_FREQUENCY,
            scope=MemoryScope.SESSION,
            scope_id="session_123",
            metadata=metadata,
            explanation="Test",
            success=True,
        )

        # Clear events older than 0 days (should remove all)
        await promotion_event_logger.clear_old_events(days=0)

        stats = await promotion_event_logger.get_stats()
        assert stats["total_events"] == 0

    @pytest.mark.asyncio
    async def test_max_history_limit(self):
        """Test that event history is limited to max_history."""
        logger = PromotionEventLogger(max_history=5)
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
        )

        # Log 10 events
        for i in range(10):
            await logger.log_event(
                key=f"key{i}",
                from_layer=MemoryLayer.L1_TRANSIENT,
                to_layer=MemoryLayer.L2_SHORT_TERM,
                reason=PromotionReason.HIGH_ACCESS_FREQUENCY,
                scope=MemoryScope.SESSION,
                scope_id="session_123",
                metadata=metadata,
                explanation=f"Test {i}",
                success=True,
            )

        stats = await logger.get_stats()
        # Should only keep the last 5
        assert stats["total_events"] == 5


class TestPromotionEngine:
    """Test PromotionEngine."""

    def test_initialization(self, promotion_engine):
        """Test engine initialization."""
        assert promotion_engine.config is not None
        assert promotion_engine.scope_tracker is not None
        assert promotion_engine.rule_engine is not None
        assert promotion_engine.data_migrator is not None
        assert promotion_engine.event_logger is not None

    @pytest.mark.asyncio
    async def test_mark_scope_active(self, promotion_engine):
        """Test marking a scope as active."""
        await promotion_engine.mark_scope_active(MemoryScope.SESSION, "session_123")

        is_active = await promotion_engine.scope_tracker.is_active(
            MemoryScope.SESSION, "session_123"
        )
        assert is_active is True

    @pytest.mark.asyncio
    async def test_promote_l1_to_l2_empty(self, promotion_engine, l1_layer, mock_l2_layer):
        """Test L1 to L2 promotion with no candidates."""
        result = await promotion_engine.promote_l1_to_l2(
            l1_layer=l1_layer,
            l2_layer=mock_l2_layer,
            max_candidates=10,
        )

        assert result.success_count == 0

    @pytest.mark.asyncio
    async def test_promote_l2_to_l3_empty(self, promotion_engine, l2_layer, mock_l3_layer):
        """Test L2 to L3 promotion with no candidates."""
        result = await promotion_engine.promote_l2_to_l3(
            l2_layer=l2_layer,
            l3_layer=mock_l3_layer,
            max_candidates=10,
        )

        assert result.success_count == 0

    @pytest.mark.asyncio
    async def test_get_stats(self, promotion_engine):
        """Test getting engine statistics."""
        stats = await promotion_engine.get_stats()

        assert "scope_tracker" in stats
        assert "migration" in stats
        assert "events" in stats

    @pytest.mark.asyncio
    async def test_get_promotion_history(self, promotion_engine):
        """Test getting promotion history."""
        history = await promotion_engine.get_promotion_history(limit=10)

        assert isinstance(history, list)
