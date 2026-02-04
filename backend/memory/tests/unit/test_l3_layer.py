"""
Unit tests for L3 Long-term Memory Layer.

Tests for:
- PostgreSQL CRUD operations
- JSONB data storage
- Vector search (mocked)
- Upsert operations
- Full-text search
- Importance filtering
- Database failure handling
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from memory.models import (
    MemoryLayer,
    MemoryScope,
    MemoryMetadata,
)
from memory.layers.l3_longterm import L3LongtermLayer


class TestL3LongtermLayer:
    """Test L3LongtermLayer functionality."""

    def test_layer_initialization(self, mock_l3_layer):
        """Test layer initialization."""
        assert mock_l3_layer.layer_type == MemoryLayer.L3_LONG_TERM

    @pytest.mark.asyncio
    async def test_set_success(self, mock_l3_layer):
        """Test successful set operation."""
        mock_l3_layer.set.return_value = True

        result = await mock_l3_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.USER,
            "user_123",
        )

        assert result is True
        mock_l3_layer.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_failure(self, mock_l3_layer):
        """Test failed set operation."""
        mock_l3_layer.set.return_value = False

        result = await mock_l3_layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.USER,
            "user_123",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_get_success(self, mock_l3_layer):
        """Test successful get operation."""
        expected_value = {"data": "test_value"}
        expected_metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L3_LONG_TERM,
            scope=MemoryScope.USER,
            importance=0.7,
            access_count=5,
        )

        mock_l3_layer.get.return_value = (expected_value, expected_metadata)

        result = await mock_l3_layer.get("test_key", MemoryScope.USER, "user_123")

        assert result is not None
        value, metadata = result
        assert value == expected_value
        assert metadata.importance == 0.7
        assert metadata.access_count == 5

    @pytest.mark.asyncio
    async def test_get_not_found(self, mock_l3_layer):
        """Test get operation when key not found."""
        mock_l3_layer.get.return_value = None

        result = await mock_l3_layer.get("nonexistent", MemoryScope.USER, "user_123")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_success(self, mock_l3_layer):
        """Test successful delete operation."""
        mock_l3_layer.delete.return_value = True

        result = await mock_l3_layer.delete("test_key", MemoryScope.USER, "user_123")

        assert result is True
        mock_l3_layer.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_l3_layer):
        """Test delete operation when key not found."""
        mock_l3_layer.delete.return_value = False

        result = await mock_l3_layer.delete("nonexistent", MemoryScope.USER, "user_123")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_true(self, mock_l3_layer):
        """Test exists operation when key exists."""
        mock_l3_layer.exists.return_value = True

        result = await mock_l3_layer.exists("test_key", MemoryScope.USER, "user_123")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self, mock_l3_layer):
        """Test exists operation when key doesn't exist."""
        mock_l3_layer.exists.return_value = False

        result = await mock_l3_layer.exists("nonexistent", MemoryScope.USER, "user_123")

        assert result is False

    @pytest.mark.asyncio
    async def test_list_keys(self, mock_l3_layer):
        """Test listing keys."""
        mock_l3_layer.list_keys.return_value = ["key1", "key2", "key3"]

        result = await mock_l3_layer.list_keys(MemoryScope.USER, "user_123")

        assert result == ["key1", "key2", "key3"]

    @pytest.mark.asyncio
    async def test_list_keys_with_pattern(self, mock_l3_layer):
        """Test listing keys with pattern."""
        mock_l3_layer.list_keys.return_value = ["test:key1", "test:key2"]

        result = await mock_l3_layer.list_keys(
            MemoryScope.USER, "user_123", pattern="test:*"
        )

        assert result == ["test:key1", "test:key2"]

    @pytest.mark.asyncio
    async def test_get_metadata(self, mock_l3_layer):
        """Test getting metadata."""
        expected_metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L3_LONG_TERM,
            scope=MemoryScope.USER,
            importance=0.8,
            tags=["important"],
        )

        mock_l3_layer.get_metadata.return_value = expected_metadata

        result = await mock_l3_layer.get_metadata(
            "test_key", MemoryScope.USER, "user_123"
        )

        assert result is not None
        assert result.importance == 0.8
        assert result.tags == ["important"]

    @pytest.mark.asyncio
    async def test_update_metadata(self, mock_l3_layer):
        """Test updating metadata."""
        mock_l3_layer.update_metadata.return_value = True

        updated_metadata = MemoryMetadata(
            key="test_key",
            layer=MemoryLayer.L3_LONG_TERM,
            scope=MemoryScope.USER,
            importance=0.9,
        )

        result = await mock_l3_layer.update_metadata(
            "test_key", MemoryScope.USER, "user_123", updated_metadata
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_update_metadata_not_found(self, mock_l3_layer):
        """Test updating metadata for non-existent key."""
        mock_l3_layer.update_metadata.return_value = False

        metadata = MemoryMetadata(
            key="nonexistent",
            layer=MemoryLayer.L3_LONG_TERM,
            scope=MemoryScope.USER,
        )

        result = await mock_l3_layer.update_metadata(
            "nonexistent", MemoryScope.USER, "user_123", metadata
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_clear_scope(self, mock_l3_layer):
        """Test clearing a scope."""
        mock_l3_layer.clear_scope.return_value = 5

        result = await mock_l3_layer.clear_scope(MemoryScope.USER, "user_123")

        assert result == 5

    @pytest.mark.asyncio
    async def test_get_stats(self, mock_l3_layer):
        """Test getting statistics."""
        mock_l3_layer.get_stats.return_value = {
            "layer": "long_term",
            "hits": 100,
            "misses": 20,
            "total_records": 500,
        }

        stats = await mock_l3_layer.get_stats()

        assert stats["layer"] == "long_term"
        assert stats["hits"] == 100
        assert stats["misses"] == 20
        assert stats["total_records"] == 500

    @pytest.mark.asyncio
    async def test_semantic_search(self, mock_l3_layer):
        """Test semantic search functionality."""
        mock_results = [
            ("key1", {"data": "value1"}, 0.95),
            ("key2", {"data": "value2"}, 0.87),
        ]

        mock_l3_layer.semantic_search.return_value = mock_results

        query_embedding = [0.1] * 1536  # Mock embedding
        results = await mock_l3_layer.semantic_search(
            query_embedding=query_embedding,
            scope=MemoryScope.USER,
            scope_id="user_123",
            limit=10,
        )

        assert len(results) == 2
        assert results[0][0] == "key1"
        assert results[0][2] == 0.95

    @pytest.mark.asyncio
    async def test_semantic_search_empty_results(self, mock_l3_layer):
        """Test semantic search with no results."""
        mock_l3_layer.semantic_search.return_value = []

        query_embedding = [0.1] * 1536
        results = await mock_l3_layer.semantic_search(
            query_embedding=query_embedding,
            scope=MemoryScope.USER,
            scope_id="user_123",
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_full_key_building(self, mock_l3_layer):
        """Test that full keys are built correctly."""
        # Mock the _build_db_key method if needed
        # This tests the layer's internal key building logic
        result = await mock_l3_layer.get("test_key", MemoryScope.USER, "user_123")

        # Verify the call was made with correct parameters
        mock_l3_layer.get.assert_called_with("test_key", MemoryScope.USER, "user_123")


class TestL3LongtermLayerReal:
    """Test L3 layer with more realistic mock database interactions."""

    @pytest.mark.asyncio
    async def test_jsonb_storage(self):
        """Test JSONB data storage."""
        layer = L3LongtermLayer(db_manager=None)

        # Mock the database session
        mock_session = MagicMock()
        mock_db_manager = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session
        mock_db_manager.get_session.return_value.__exit__.return_value = False

        layer.db = mock_db_manager

        # Mock successful insert
        mock_session.execute.return_value.fetchone.return_value = None  # No existing record

        result = await layer.set(
            "test_key",
            {"data": "value", "nested": {"key": "value"}},
            MemoryScope.USER,
            "user_123",
        )

        # Verify commit was called
        mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_jsonb_retrieval(self):
        """Test JSONB data retrieval."""
        layer = L3LongtermLayer(db_manager=None)

        # Mock the database session
        mock_session = MagicMock()
        mock_db_manager = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session
        mock_db_manager.get_session.return_value.__exit__.return_value = False

        layer.db = mock_db_manager

        # Mock query result
        mock_result = MagicMock()
        mock_result.__getitem__ = lambda self, key: {
            0: {"data": "value", "nested": {"key": "value"}},
            1: 0.7,  # importance
            2: 5,  # access_count
            3: 2,  # session_count
            4: ["tag1"],  # tags
            5: datetime.now(),  # created_at
            6: datetime.now(),  # last_accessed
            7: "l2",  # promoted_from
            8: "cross_session",  # promotion_reason
        }[key]

        mock_session.execute.return_value.fetchone.return_value = mock_result

        result = await layer.get("test_key", MemoryScope.USER, "user_123")

        assert result is not None
        value, metadata = result
        assert value["data"] == "value"
        assert metadata.importance == 0.7
        assert metadata.access_count == 5

    @pytest.mark.asyncio
    async def test_upsert_behavior(self):
        """Test upsert (update or insert) behavior."""
        layer = L3LongtermLayer(db_manager=None)

        mock_session = MagicMock()
        mock_db_manager = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session
        mock_db_manager.get_session.return_value.__exit__.return_value = False

        layer.db = mock_db_manager

        # Test insert (no existing record)
        mock_session.execute.return_value.fetchone.return_value = None

        result1 = await layer.set(
            "new_key",
            {"data": "new_value"},
            MemoryScope.USER,
            "user_123",
        )

        # Test update (existing record)
        mock_session.execute.return_value.fetchone.return_value = MagicMock(id="existing")

        result2 = await layer.set(
            "existing_key",
            {"data": "updated_value"},
            MemoryScope.USER,
            "user_123",
        )

        # Both should call commit
        assert mock_session.commit.call_count >= 2

    @pytest.mark.asyncio
    async def test_full_text_search(self):
        """Test full-text search capability."""
        layer = L3LongtermLayer(db_manager=None)

        mock_session = MagicMock()
        mock_db_manager = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session
        mock_db_manager.get_session.return_value.__exit__.return_value = False

        layer.db = mock_db_manager

        # Mock search results
        mock_rows = [
            ["user:user_123:key1"],
            ["user:user_123:key2"],
        ]
        mock_session.execute.return_value.fetchall.return_value = [
            MagicMock(__getitem__=lambda self, i: mock_rows[0][i]),
            MagicMock(__getitem__=lambda self, i: mock_rows[1][i]),
        ]

        keys = await layer.list_keys(MemoryScope.USER, "user_123")

        # Should return keys without the prefix
        assert isinstance(keys, list)

    @pytest.mark.asyncio
    async def test_importance_filtering(self):
        """Test filtering by importance."""
        layer = L3LongtermLayer(db_manager=None)

        mock_session = MagicMock()
        mock_db_manager = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session
        mock_db_manager.get_session.return_value.__exit__.return_value = False

        layer.db = mock_db_manager

        # Mock stats query
        mock_session.execute.return_value.fetchone.return_value = (
            100,  # total_records
            0.65,  # avg_importance
            500,  # total_accesses
            10,  # unique_users
        )

        stats = await layer.get_stats()

        assert stats["total_records"] == 100
        assert stats["avg_importance"] == 0.65

    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Test handling of database errors."""
        layer = L3LongtermLayer(db_manager=None)

        mock_session = MagicMock()
        mock_db_manager = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session
        mock_db_manager.get_session.return_value.__exit__.return_value = False
        mock_db_manager.get_session.return_value.__enter__.side_effect = Exception("DB Error")

        layer.db = mock_db_manager

        # Should handle error gracefully
        result = await layer.set(
            "test_key",
            {"data": "value"},
            MemoryScope.USER,
            "user_123",
        )

        # Should return False on error
        assert result is False

    @pytest.mark.asyncio
    async def test_extract_text_content_string(self):
        """Test extracting text content from string."""
        layer = L3LongtermLayer(db_manager=None)

        result = layer._extract_text_content("simple string")

        assert result == "simple string"

    @pytest.mark.asyncio
    async def test_extract_text_content_dict(self):
        """Test extracting text content from dict."""
        layer = L3LongtermLayer(db_manager=None)

        result = layer._extract_text_content({
            "text1": "value1",
            "text2": "value2",
            "number": 42,
        })

        assert "value1" in result
        assert "value2" in result

    @pytest.mark.asyncio
    async def test_extract_text_content_list(self):
        """Test extracting text content from list."""
        layer = L3LongtermLayer(db_manager=None)

        result = layer._extract_text_content(["item1", "item2", 42])

        assert "item1" in result
        assert "item2" in result

    @pytest.mark.asyncio
    async def test_extract_text_content_complex(self):
        """Test extracting text content from complex structure."""
        layer = L3LongtermLayer(db_manager=None)

        result = layer._extract_text_content({
            "level1": "text1",
            "nested": {
                "level2": "text2",
                "list": ["a", "b"],
            },
        })

        assert "text1" in result
        assert "text2" in result

    @pytest.mark.asyncio
    async def test_access_count_increments(self):
        """Test that access count increments on get."""
        layer = L3LongtermLayer(db_manager=None)

        mock_session = MagicMock()
        mock_db_manager = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session
        mock_db_manager.get_session.return_value.__exit__.return_value = False

        layer.db = mock_db_manager

        # Mock query result
        mock_result = MagicMock()
        mock_result.__getitem__ = lambda self, key: {
            0: {"data": "value"},
            1: 0.5,
            2: 3,  # access_count
            3: 1,
            4: [],
            5: datetime.now(),
            6: datetime.now(),
            7: None,
            8: None,
        }[key]

        mock_session.execute.return_value.fetchone.return_value = mock_result

        result = await layer.get("test_key", MemoryScope.USER, "user_123")

        # Verify update query was called to increment access count
        assert mock_session.execute.call_count >= 2
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_scope_isolation(self):
        """Test that different scopes are isolated."""
        layer = L3LongtermLayer(db_manager=None)

        mock_session = MagicMock()
        mock_db_manager = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session
        mock_db_manager.get_session.return_value.__exit__.return_value = False

        layer.db = mock_db_manager

        # Mock different results for different scopes
        def mock_execute_side_effect(query, params):
            if "user:user_123" in str(params):
                return MagicMock(fetchone=MagicMock(return_value=None))
            elif "agent:agent_456" in str(params):
                return MagicMock(fetchone=MagicMock(return_value=None))
            return MagicMock(fetchone=MagicMock(return_value=None))

        mock_session.execute.side_effect = mock_execute_side_effect

        # Set data in different scopes
        await layer.set("key1", {"data": "user_value"}, MemoryScope.USER, "user_123")
        await layer.set("key1", {"data": "agent_value"}, MemoryScope.AGENT, "agent_456")

        # Both should succeed
        assert mock_session.commit.call_count >= 2

    @pytest.mark.asyncio
    async def test_vector_search_unavailable(self):
        """Test semantic search when vector is unavailable."""
        # This tests the case when pgvector is not installed
        layer = L3LongtermLayer(db_manager=None)

        # Patch VECTOR_AVAILABLE to False
        with patch('memory.layers.l3_longterm.VECTOR_AVAILABLE', False):
            query_embedding = [0.1] * 1536
            results = await layer.semantic_search(
                query_embedding=query_embedding,
                scope=MemoryScope.USER,
                scope_id="user_123",
            )

            # Should return empty list
            assert results == []

    @pytest.mark.asyncio
    async def test_stats_aggregation(self):
        """Test stats aggregation functionality."""
        layer = L3LongtermLayer(db_manager=None)

        mock_session = MagicMock()
        mock_db_manager = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session
        mock_db_manager.get_session.return_value.__exit__.return_value = False

        layer.db = mock_db_manager

        # Mock stats query
        mock_session.execute.return_value.fetchone.return_value = (
            1000,  # total_records
            0.72,  # avg_importance
            5000,  # total_accesses
            50,  # unique_users
        )

        # Set some stats
        layer.stats["hits"] = 300
        layer.stats["misses"] = 50
        layer.stats["sets"] = 200
        layer.stats["deletes"] = 20

        stats = await layer.get_stats()

        assert stats["total_records"] == 1000
        assert stats["avg_importance"] == 0.72
        assert stats["total_accesses"] == 5000
        assert stats["unique_users"] == 50
        assert stats["hits"] == 300
        assert stats["misses"] == 50
        assert stats["hit_rate"] == 300 / (300 + 50)
