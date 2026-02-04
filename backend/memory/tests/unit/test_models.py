"""
Unit tests for Memory data models.

Tests for:
- MemoryMetadata
- MemoryLayer enum
- MemoryScope enum
- PromotionReason enum
- PromotionTracker
"""

import pytest
from datetime import datetime, timedelta

from memory.models import (
    MemoryLayer,
    MemoryScope,
    MemoryMetadata,
    PromotionReason,
    PromotionTracker,
)


class TestMemoryMetadata:
    """Test MemoryMetadata class."""

    def test_metadata_creation(self):
        """Test metadata creation with default values."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
        )

        assert metadata.key == "test_key"
        assert metadata.layer == MemoryLayer.L1_TRANSIENT
        assert metadata.scope == MemoryScope.SESSION
        assert metadata.importance == 0.5
        assert metadata.access_count == 0
        assert metadata.session_ids == []
        assert metadata.tags == []
        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.last_accessed, datetime)

    def test_metadata_creation_with_custom_values(self):
        """Test metadata creation with custom values."""
        created_at = datetime.now() - timedelta(hours=1)
        last_accessed = datetime.now()

        metadata = MemoryMetadata(
            key="custom_key",
            layer=MemoryLayer.L2_SHORT_TERM,
            scope=MemoryScope.USER,
            created_at=created_at,
            importance=0.8,
            access_count=10,
            last_accessed=last_accessed,
            session_ids=["session1", "session2"],
            tags=["important", "cached"],
        )

        assert metadata.key == "custom_key"
        assert metadata.layer == MemoryLayer.L2_SHORT_TERM
        assert metadata.scope == MemoryScope.USER
        assert metadata.importance == 0.8
        assert metadata.access_count == 10
        assert metadata.session_ids == ["session1", "session2"]
        assert metadata.tags == ["important", "cached"]
        assert metadata.created_at == created_at
        assert metadata.last_accessed == last_accessed

    def test_importance_clamping_high(self):
        """Test that importance values above 1.0 are clamped to 1.0."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            importance=1.5,
        )

        assert metadata.importance == 1.0

    def test_importance_clamping_low(self):
        """Test that importance values below 0.0 are clamped to 0.0."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            importance=-0.5,
        )

        assert metadata.importance == 0.0

    def test_importance_boundary_values(self):
        """Test that boundary values (0.0 and 1.0) are preserved."""
        metadata1 = MemoryMetadata(
            key="test1",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            importance=0.0,
        )
        metadata2 = MemoryMetadata(
            key="test2",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            importance=1.0,
        )

        assert metadata1.importance == 0.0
        assert metadata2.importance == 1.0

    def test_increment_access(self):
        """Test increment_access method."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            access_count=5,
        )

        original_count = metadata.access_count
        original_last_accessed = metadata.last_accessed

        metadata.increment_access()

        assert metadata.access_count == original_count + 1
        assert metadata.last_accessed > original_last_accessed

    def test_increment_access_multiple_times(self):
        """Test multiple increments."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            access_count=0,
        )

        for i in range(1, 6):
            metadata.increment_access()
            assert metadata.access_count == i

    def test_add_session_id_new(self):
        """Test adding a new session ID."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
        )

        metadata.add_session_id("session_123")

        assert "session_123" in metadata.session_ids
        assert len(metadata.session_ids) == 1

    def test_add_session_id_duplicate(self):
        """Test that duplicate session IDs are not added."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
            session_ids=["session_123"],
        )

        metadata.add_session_id("session_123")

        assert metadata.session_ids.count("session_123") == 1
        assert len(metadata.session_ids) == 1

    def test_add_multiple_session_ids(self):
        """Test adding multiple unique session IDs."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
        )

        session_ids = ["session_1", "session_2", "session_3"]
        for sid in session_ids:
            metadata.add_session_id(sid)

        assert len(metadata.session_ids) == 3
        for sid in session_ids:
            assert sid in metadata.session_ids

    def test_should_promote_to_l2_by_access_count(self):
        """Test L2 promotion by access count threshold."""
        # Below threshold
        metadata1 = MemoryMetadata(
            key="test1",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            access_count=2,
            importance=0.5,
        )
        assert not metadata1.should_promote_to_l2()

        # At threshold
        metadata2 = MemoryMetadata(
            key="test2",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            access_count=3,
            importance=0.5,
        )
        assert metadata2.should_promote_to_l2()

        # Above threshold
        metadata3 = MemoryMetadata(
            key="test3",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            access_count=10,
            importance=0.5,
        )
        assert metadata3.should_promote_to_l2()

    def test_should_promote_to_l2_by_importance(self):
        """Test L2 promotion by importance threshold."""
        # Below threshold
        metadata1 = MemoryMetadata(
            key="test1",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            access_count=0,
            importance=0.6,
        )
        assert not metadata1.should_promote_to_l2()

        # At threshold
        metadata2 = MemoryMetadata(
            key="test2",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            access_count=0,
            importance=0.7,
        )
        assert metadata2.should_promote_to_l2()

        # Above threshold
        metadata3 = MemoryMetadata(
            key="test3",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            access_count=0,
            importance=1.0,
        )
        assert metadata3.should_promote_to_l2()

    def test_should_promote_to_l2_combined_conditions(self):
        """Test L2 promotion with combined conditions."""
        # Both conditions met
        metadata = MemoryMetadata(
            key="test",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            access_count=5,
            importance=0.9,
        )
        assert metadata.should_promote_to_l2()

    def test_should_promote_to_l3_by_session_count(self):
        """Test L3 promotion by session count."""
        # Below threshold
        metadata1 = MemoryMetadata(
            key="test1",
            layer=MemoryLayer.L2_SHORT_TERM,
            scope=MemoryScope.SESSION,
            session_ids=["session1"],
        )
        assert not metadata1.should_promote_to_l3()

        # At threshold
        metadata2 = MemoryMetadata(
            key="test2",
            layer=MemoryLayer.L2_SHORT_TERM,
            scope=MemoryScope.SESSION,
            session_ids=["session1", "session2"],
        )
        assert metadata2.should_promote_to_l3()

        # Above threshold
        metadata3 = MemoryMetadata(
            key="test3",
            layer=MemoryLayer.L2_SHORT_TERM,
            scope=MemoryScope.SESSION,
            session_ids=["s1", "s2", "s3"],
        )
        assert metadata3.should_promote_to_l3()

    def test_to_dict(self):
        """Test metadata serialization to dictionary."""
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        last_accessed = datetime(2024, 1, 2, 12, 0, 0)

        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.SESSION,
            created_at=created_at,
            importance=0.75,
            access_count=10,
            last_accessed=last_accessed,
            session_ids=["session1", "session2"],
            tags=["tag1", "tag2"],
        )

        result = metadata.to_dict()

        assert result["key"] == "test_key"
        assert result["layer"] == "transient"
        assert result["scope"] == "session"
        assert result["created_at"] == created_at.isoformat()
        assert result["importance"] == 0.75
        assert result["access_count"] == 10
        assert result["last_accessed"] == last_accessed.isoformat()
        assert result["session_ids"] == ["session1", "session2"]
        assert result["tags"] == ["tag1", "tag2"]

    def test_to_dict_empty_collections(self):
        """Test to_dict with empty session_ids and tags."""
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
        )

        result = metadata.to_dict()

        assert result["session_ids"] == []
        assert result["tags"] == []


class TestMemoryEnums:
    """Test memory-related enumerations."""

    def test_memory_layer_values(self):
        """Test MemoryLayer enum values."""
        assert MemoryLayer.L1_TRANSIENT.value == "transient"
        assert MemoryLayer.L2_SHORT_TERM.value == "short_term"
        assert MemoryLayer.L3_LONG_TERM.value == "long_term"

    def test_memory_scope_values(self):
        """Test MemoryScope enum values."""
        assert MemoryScope.TASK.value == "task"
        assert MemoryScope.SESSION.value == "session"
        assert MemoryScope.AGENT.value == "agent"
        assert MemoryScope.WORKSPACE.value == "workspace"
        assert MemoryScope.USER.value == "user"

    def test_promotion_reason_values(self):
        """Test PromotionReason enum values."""
        assert PromotionReason.HIGH_ACCESS_FREQUENCY.value == "high_access_frequency"
        assert PromotionReason.HIGH_IMPORTANCE_SCORE.value == "high_importance_score"
        assert PromotionReason.CROSS_SESSION_USAGE.value == "cross_session_usage"
        assert PromotionReason.MANUAL_PROMOTION.value == "manual_promotion"
        assert PromotionReason.LONG_LIFETIME.value == "long_lifetime"


class TestPromotionTracker:
    """Test PromotionTracker class."""

    def test_tracker_initialization(self):
        """Test tracker initialization."""
        tracker = PromotionTracker()
        assert tracker.promotion_history == {}

    def test_record_promotion(self):
        """Test recording a promotion event."""
        tracker = PromotionTracker()
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            importance=0.8,
            access_count=5,
        )

        tracker.record_promotion(
            key="test_key",
            from_layer=MemoryLayer.L1_TRANSIENT,
            to_layer=MemoryLayer.L2_SHORT_TERM,
            reason=PromotionReason.HIGH_ACCESS_FREQUENCY,
            metadata=metadata,
        )

        assert "test_key" in tracker.promotion_history
        assert len(tracker.promotion_history["test_key"]) == 1

        event = tracker.promotion_history["test_key"][0]
        assert event["from_layer"] == "transient"
        assert event["to_layer"] == "short_term"
        assert event["reason"] == "high_access_frequency"
        assert event["access_count"] == 5
        assert event["importance"] == 0.8
        assert event["session_count"] == 0

    def test_record_multiple_promotions_same_key(self):
        """Test recording multiple promotions for the same key."""
        tracker = PromotionTracker()
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
        )

        # First promotion: L1 -> L2
        tracker.record_promotion(
            key="test_key",
            from_layer=MemoryLayer.L1_TRANSIENT,
            to_layer=MemoryLayer.L2_SHORT_TERM,
            reason=PromotionReason.HIGH_ACCESS_FREQUENCY,
            metadata=metadata,
        )

        # Second promotion: L2 -> L3
        metadata.session_ids = ["session1", "session2"]
        tracker.record_promotion(
            key="test_key",
            from_layer=MemoryLayer.L2_SHORT_TERM,
            to_layer=MemoryLayer.L3_LONG_TERM,
            reason=PromotionReason.CROSS_SESSION_USAGE,
            metadata=metadata,
        )

        assert len(tracker.promotion_history["test_key"]) == 2

    def test_get_promotion_history_existing(self):
        """Test getting promotion history for an existing key."""
        tracker = PromotionTracker()
        metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
        )

        tracker.record_promotion(
            key="test_key",
            from_layer=MemoryLayer.L1_TRANSIENT,
            to_layer=MemoryLayer.L2_SHORT_TERM,
            reason=PromotionReason.HIGH_ACCESS_FREQUENCY,
            metadata=metadata,
        )

        history = tracker.get_promotion_history("test_key")

        assert len(history) == 1
        assert history[0]["from_layer"] == "transient"

    def test_get_promotion_history_nonexistent(self):
        """Test getting promotion history for a non-existent key."""
        tracker = PromotionTracker()
        history = tracker.get_promotion_history("nonexistent_key")

        assert history == []

    def test_get_stats_empty_tracker(self):
        """Test getting stats from an empty tracker."""
        tracker = PromotionTracker()
        stats = tracker.get_stats()

        assert stats["total_promotions"] == 0
        assert stats["by_reason"] == {}
        assert stats["by_layer_transition"] == {}

    def test_get_stats_with_data(self):
        """Test getting stats with recorded promotions."""
        tracker = PromotionTracker()
        metadata1 = MemoryMetadata(
            key="key1",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            importance=0.8,
        )
        metadata2 = MemoryMetadata(
            key="key2",
            layer=MemoryLayer.L1_TRANSIENT,
            scope=MemoryScope.TASK,
            access_count=5,
        )

        tracker.record_promotion(
            key="key1",
            from_layer=MemoryLayer.L1_TRANSIENT,
            to_layer=MemoryLayer.L2_SHORT_TERM,
            reason=PromotionReason.HIGH_IMPORTANCE_SCORE,
            metadata=metadata1,
        )
        tracker.record_promotion(
            key="key2",
            from_layer=MemoryLayer.L1_TRANSIENT,
            to_layer=MemoryLayer.L2_SHORT_TERM,
            reason=PromotionReason.HIGH_ACCESS_FREQUENCY,
            metadata=metadata2,
        )

        stats = tracker.get_stats()

        assert stats["total_promotions"] == 2
        assert stats["unique_keys_promoted"] == 2
        assert stats["by_reason"]["high_importance_score"] == 1
        assert stats["by_reason"]["high_access_frequency"] == 1
        assert stats["by_layer_transition"]["transient_to_short_term"] == 2
