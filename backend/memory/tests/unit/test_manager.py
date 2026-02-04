"""
Unit tests for HierarchicalMemoryManager.

Tests for:
- Initialization
- Get from L1
- Get from L2 with L1 fallback
- Get from L3 with cascade
- Set with auto layer selection
- Delete from all layers
- Scope isolation
- Clear scope
- Global statistics
- Manual promotion to L3
- Batch flush L1 to L2
- Semantic search
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from memory.models import (
    MemoryLayer,
    MemoryScope,
    MemoryMetadata,
    PromotionReason,
)
from memory.manager import HierarchicalMemoryManager


class TestHierarchicalMemoryManager:
    """Test HierarchicalMemoryManager functionality."""

    def test_initialization(self):
        """Test manager initialization."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(
                l1_capacity=500,
                enable_auto_promotion=False,
            )

            assert manager.l1 is not None
            assert manager.l2 is not None
            assert manager.l3 is not None
            assert manager.enable_auto_promotion is False
            assert manager.promotion_engine is None

    def test_initialization_with_promotion(self):
        """Test manager initialization with auto-promotion enabled."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(
                l1_capacity=1000,
                enable_auto_promotion=True,
            )

            assert manager.enable_auto_promotion is True
            assert manager.promotion_engine is not None

    @pytest.mark.asyncio
    async def test_get_from_l1(self):
        """Test getting data from L1 layer."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            # Mock L1 hit
            expected_value = {"data": "test"}
            expected_metadata = MemoryMetadata(
                key="test_key",
                layer=MemoryLayer.L1_TRANSIENT,
                scope=MemoryScope.SESSION,
            )

            manager.l1.get = AsyncMock(return_value=(expected_value, expected_metadata))

            result = await manager.get("test_key", MemoryScope.SESSION, "session_123")

            assert result is not None
            value, metadata = result
            assert value == expected_value
            manager.l1.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_from_l2_with_l1_fallback(self):
        """Test getting data from L2 and writing back to L1."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            # Mock L1 miss, L2 hit
            expected_value = {"data": "test"}
            expected_metadata = MemoryMetadata(
                key="test_key",
                layer=MemoryLayer.L2_SHORT_TERM,
                scope=MemoryScope.SESSION,
            )

            manager.l1.get = AsyncMock(return_value=None)
            manager.l2.get = AsyncMock(return_value=(expected_value, expected_metadata))
            manager.l1.set = AsyncMock(return_value=True)

            result = await manager.get("test_key", MemoryScope.SESSION, "session_123")

            assert result is not None
            value, metadata = result
            assert value == expected_value

            # Verify L1 was updated
            manager.l1.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_from_l3_with_cascade(self):
        """Test getting data from L3 and cascading back to L2 and L1."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            # Mock L1 miss, L2 miss, L3 hit
            expected_value = {"data": "test"}
            expected_metadata = MemoryMetadata(
                key="test_key",
                layer=MemoryLayer.L3_LONG_TERM,
                scope=MemoryScope.USER,
            )

            manager.l1.get = AsyncMock(return_value=None)
            manager.l2.get = AsyncMock(return_value=None)
            manager.l3.get = AsyncMock(return_value=(expected_value, expected_metadata))
            manager.l2.set = AsyncMock(return_value=True)
            manager.l1.set = AsyncMock(return_value=True)

            result = await manager.get("test_key", MemoryScope.USER, "user_123")

            assert result is not None

            # Verify cascade write
            manager.l2.set.assert_called_once()
            manager.l1.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        """Test getting non-existent data."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            # Mock all layers miss
            manager.l1.get = AsyncMock(return_value=None)
            manager.l2.get = AsyncMock(return_value=None)
            manager.l3.get = AsyncMock(return_value=None)

            result = await manager.get("nonexistent", MemoryScope.SESSION, "session_123")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_without_search_all_layers(self):
        """Test getting data without searching all layers."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            manager.l1.get = AsyncMock(return_value=None)

            # Should not search L2/L3
            result = await manager.get(
                "test_key",
                MemoryScope.SESSION,
                "session_123",
                search_all_layers=False,
            )

            assert result is None
            manager.l1.get.assert_called_once()
            manager.l2.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_to_l1(self):
        """Test setting data to L1 layer."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            manager.l1.set = AsyncMock(return_value=True)

            result = await manager.set(
                "test_key",
                {"data": "value"},
                MemoryScope.TASK,
                "task_123",
                importance=0.5,
            )

            assert result is True
            manager.l1.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_to_l2_by_importance(self):
        """Test setting data to L2 based on importance."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            manager.l2.set = AsyncMock(return_value=True)

            result = await manager.set(
                "test_key",
                {"data": "value"},
                MemoryScope.TASK,
                "task_123",
                importance=0.85,  # High importance
            )

            assert result is True
            manager.l2.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_to_l2_by_scope(self):
        """Test setting data to L2 based on scope."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            manager.l2.set = AsyncMock(return_value=True)

            result = await manager.set(
                "test_key",
                {"data": "value"},
                MemoryScope.WORKSPACE,  # Workspace scope
                "workspace_123",
                importance=0.5,
            )

            assert result is True
            manager.l2.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_to_l3_direct(self):
        """Test setting data directly to L3."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            manager.l3.set = AsyncMock(return_value=True)

            result = await manager.set(
                "test_key",
                {"data": "value"},
                MemoryScope.USER,
                "user_123",
                importance=0.5,
                target_layer=MemoryLayer.L3_LONG_TERM,
            )

            assert result is True
            manager.l3.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_with_tags(self):
        """Test setting data with tags."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            manager.l1.set = AsyncMock(return_value=True)

            await manager.set(
                "test_key",
                {"data": "value"},
                MemoryScope.TASK,
                "task_123",
                tags=["important", "cached"],
            )

            # Verify tags were included in metadata
            call_args = manager.l1.set.call_args
            metadata = call_args[0][4]  # metadata is the 5th argument
            assert metadata.tags == ["important", "cached"]

    @pytest.mark.asyncio
    async def test_delete_from_l1_only(self):
        """Test deleting data from L1 only."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            manager.l1.delete = AsyncMock(return_value=True)

            result = await manager.delete(
                "test_key",
                MemoryScope.SESSION,
                "session_123",
                delete_all_layers=False,
            )

            assert result is True
            manager.l1.delete.assert_called_once()
            manager.l2.delete.assert_not_called()
            manager.l3.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_from_all_layers(self):
        """Test deleting data from all layers."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            manager.l1.delete = AsyncMock(return_value=True)
            manager.l2.delete = AsyncMock(return_value=False)
            manager.l3.delete = AsyncMock(return_value=False)

            result = await manager.delete(
                "test_key",
                MemoryScope.SESSION,
                "session_123",
                delete_all_layers=True,
            )

            assert result is True
            manager.l1.delete.assert_called_once()
            manager.l2.delete.assert_called_once()
            manager.l3.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_exists(self):
        """Test checking if data exists."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            manager.l1.exists = AsyncMock(return_value=False)
            manager.l2.exists = AsyncMock(return_value=True)
            manager.l3.exists = AsyncMock(return_value=False)

            result = await manager.exists("test_key", MemoryScope.SESSION, "session_123")

            assert result is True

    @pytest.mark.asyncio
    async def test_exists_not_found(self):
        """Test checking if data exists when it doesn't."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            manager.l1.exists = AsyncMock(return_value=False)
            manager.l2.exists = AsyncMock(return_value=False)
            manager.l3.exists = AsyncMock(return_value=False)

            result = await manager.exists("test_key", MemoryScope.SESSION, "session_123")

            assert result is False

    @pytest.mark.asyncio
    async def test_clear_scope_all_layers(self):
        """Test clearing all data in a scope from all layers."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            manager.l1.clear_scope = AsyncMock(return_value=5)
            manager.l2.clear_scope = AsyncMock(return_value=3)
            manager.l3.clear_scope = AsyncMock(return_value=2)

            result = await manager.clear_scope(MemoryScope.SESSION, "session_123")

            assert result["l1"] == 5
            assert result["l2"] == 3
            assert result["l3"] == 2

    @pytest.mark.asyncio
    async def test_clear_scope_specific_layers(self):
        """Test clearing specific layers only."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            manager.l1.clear_scope = AsyncMock(return_value=5)
            manager.l2.clear_scope = AsyncMock(return_value=3)
            manager.l3.clear_scope = AsyncMock(return_value=2)

            result = await manager.clear_scope(
                MemoryScope.SESSION,
                "session_123",
                layers=[MemoryLayer.L1_TRANSIENT, MemoryLayer.L3_LONG_TERM],
            )

            assert result["l1"] == 5
            assert "l2" not in result
            assert result["l3"] == 2

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting global statistics."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            manager.l1.get_stats = AsyncMock(return_value={
                "data_count": 10,
                "hits": 100,
                "misses": 20,
            })
            manager.l2.get_stats = AsyncMock(return_value={
                "hits": 50,
                "misses": 10,
            })
            manager.l3.get_stats = AsyncMock(return_value={
                "total_records": 5,
            })

            stats = await manager.get_stats()

            assert "l1_transient" in stats
            assert "l2_short_term" in stats
            assert "l3_long_term" in stats
            assert stats["total_data_count"] >= 0

    @pytest.mark.asyncio
    async def test_manual_promote_to_l3(self):
        """Test manually promoting data to L3."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            expected_value = {"data": "important"}
            expected_metadata = MemoryMetadata(
                key="test_key",
                layer=MemoryLayer.L1_TRANSIENT,
                scope=MemoryScope.USER,
                importance=0.6,
            )

            manager.l1.get = AsyncMock(return_value=(expected_value, expected_metadata))
            manager.l2.get = AsyncMock(return_value=None)
            manager.l3.get = AsyncMock(return_value=None)
            manager.l3.set = AsyncMock(return_value=True)

            result = await manager.promote_to_l3(
                "test_key",
                MemoryScope.USER,
                "user_123",
                reason=PromotionReason.MANUAL_PROMOTION,
            )

            assert result is True
            manager.l3.set.assert_called_once()

            # Verify importance was boosted
            call_args = manager.l3.set.call_args
            metadata = call_args[0][4]
            assert metadata.importance >= 0.8

    @pytest.mark.asyncio
    async def test_manual_promote_to_l3_not_found(self):
        """Test manually promoting non-existent data."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            manager.l1.get = AsyncMock(return_value=None)
            manager.l2.get = AsyncMock(return_value=None)
            manager.l3.get = AsyncMock(return_value=None)

            result = await manager.promote_to_l3(
                "nonexistent",
                MemoryScope.USER,
                "user_123",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_batch_flush_l1_to_l2(self):
        """Test batch flushing L1 data to L2."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            # Mock L1 batch flush
            to_flush = [
                ("key1", {"data": "1"}, MemoryMetadata(key="key1", layer=MemoryLayer.L1_TRANSIENT, scope=MemoryScope.SESSION)),
                ("key2", {"data": "2"}, MemoryMetadata(key="key2", layer=MemoryLayer.L1_TRANSIENT, scope=MemoryScope.SESSION)),
            ]
            manager.l1.batch_flush_to_l2 = AsyncMock(return_value=to_flush)

            # Mock L2 batch set
            manager.l2.batch_set = AsyncMock(return_value=2)

            count = await manager.batch_flush_l1_to_l2(MemoryScope.SESSION, "session_123")

            assert count == 2
            manager.l2.batch_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_flush_l1_to_l2_empty(self):
        """Test batch flushing when no data to flush."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            manager.l1.batch_flush_to_l2 = AsyncMock(return_value=[])

            count = await manager.batch_flush_l1_to_l2(MemoryScope.SESSION, "session_123")

            assert count == 0
            manager.l2.batch_set.assert_not_called()

    @pytest.mark.asyncio
    async def test_semantic_search(self):
        """Test semantic search functionality."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            mock_results = [
                ("key1", {"data": "value1"}, 0.95),
                ("key2", {"data": "value2"}, 0.87),
            ]
            manager.l3.semantic_search = AsyncMock(return_value=mock_results)

            query_embedding = [0.1] * 1536
            results = await manager.semantic_search(
                query_embedding=query_embedding,
                scope=MemoryScope.USER,
                scope_id="user_123",
                limit=10,
            )

            assert len(results) == 2
            assert results[0][0] == "key1"

    @pytest.mark.asyncio
    async def test_get_promotion_history(self):
        """Test getting promotion history."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=True)

            # Mock promotion engine
            manager.promotion_engine.get_promotion_history = AsyncMock(
                return_value=[
                    {"key": "test1", "from_layer": "transient", "to_layer": "short_term"},
                ]
            )

            history = await manager.get_promotion_history(limit=10)

            assert len(history) == 1
            manager.promotion_engine.get_promotion_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_promotion_history_no_engine(self):
        """Test getting promotion history when promotion engine is disabled."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            history = await manager.get_promotion_history(limit=10)

            assert history == []

    def test_determine_target_layer_by_importance(self):
        """Test determining target layer based on importance."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            # High importance -> L2
            layer = manager._determine_target_layer(0.85, MemoryScope.TASK)
            assert layer == MemoryLayer.L2_SHORT_TERM

            # Low importance -> L1
            layer = manager._determine_target_layer(0.5, MemoryScope.TASK)
            assert layer == MemoryLayer.L1_TRANSIENT

    def test_determine_target_layer_by_scope(self):
        """Test determining target layer based on scope."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            # USER scope -> L2
            layer = manager._determine_target_layer(0.5, MemoryScope.USER)
            assert layer == MemoryLayer.L2_SHORT_TERM

            # WORKSPACE scope -> L2
            layer = manager._determine_target_layer(0.5, MemoryScope.WORKSPACE)
            assert layer == MemoryLayer.L2_SHORT_TERM

            # TASK scope -> L1
            layer = manager._determine_target_layer(0.5, MemoryScope.TASK)
            assert layer == MemoryLayer.L1_TRANSIENT

    @pytest.mark.asyncio
    async def test_start_background_tasks(self):
        """Test starting background tasks."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=True)

            await manager.start_background_tasks()

            # Verify tasks were started
            assert manager._promotion_task is not None

    @pytest.mark.asyncio
    async def test_stop_background_tasks(self):
        """Test stopping background tasks."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=True)

            await manager.start_background_tasks()
            await manager.stop_background_tasks()

            # Verify tasks were stopped (task is cancelled)


class TestGlobalMemoryManager:
    """Test global memory manager functions."""

    def test_get_global_memory_manager(self):
        """Test getting global memory manager instance."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            from memory.manager import get_global_memory_manager

            manager = get_global_memory_manager()

            assert manager is not None
            assert isinstance(manager, HierarchicalMemoryManager)

    @pytest.mark.asyncio
    async def test_init_global_memory_manager(self):
        """Test initializing global memory manager."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            from memory.manager import init_global_memory_manager

            manager = await init_global_memory_manager(l1_capacity=500)

            assert manager is not None
            assert manager.l1.data_cache.capacity == 500

    @pytest.mark.asyncio
    async def test_shutdown_global_memory_manager(self):
        """Test shutting down global memory manager."""
        with patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = Mock()
            mock_l2.return_value = mock_l2_instance

            from memory.manager import init_global_memory_manager, shutdown_global_memory_manager

            manager = await init_global_memory_manager()
            await shutdown_global_memory_manager()

            # Manager should be None after shutdown
            from memory.manager import _global_memory_manager
            assert _global_memory_manager is None
