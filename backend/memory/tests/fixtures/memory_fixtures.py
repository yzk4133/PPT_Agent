"""
Memory layer test fixtures.

Provides mock implementations and test data for memory layer testing.
"""

import pytest
from typing import Any, Dict, List, Tuple
from unittest.mock import Mock, AsyncMock

from memory.models import (
    MemoryLayer,
    MemoryScope,
    MemoryMetadata,
    PromotionReason,
)
from memory.layers.l1_transient import L1TransientLayer


# ============================================================================
# Mock Layer Factories
# ============================================================================

def create_mock_l1_layer(capacity: int = 1000, ttl: int = 300) -> L1TransientLayer:
    """
    Create a mock L1 layer with specified capacity and TTL.

    Args:
        capacity: Maximum number of items
        ttl: Default time-to-live in seconds

    Returns:
        Configured L1TransientLayer instance
    """
    return L1TransientLayer(capacity=capacity, default_ttl_seconds=ttl)


def create_mock_l2_layer():
    """
    Create a mock L2 layer for testing.

    Returns:
        Mocked L2ShortTermLayer with async methods
    """
    from fakeredis import FakeStrictRedis
    from memory.layers.l2_short_term import L2ShortTermLayer

    layer = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
    layer.client = FakeStrictRedis(decode_responses=False)
    return layer


def create_mock_l3_layer():
    """
    Create a mock L3 layer for testing.

    Returns:
        Mocked L3LongtermLayer with async methods
    """
    layer = Mock()
    layer.layer_type = MemoryLayer.L3_LONG_TERM
    layer.get = AsyncMock(return_value=None)
    layer.set = AsyncMock(return_value=True)
    layer.delete = AsyncMock(return_value=True)
    layer.exists = AsyncMock(return_value=False)
    layer.list_keys = AsyncMock(return_value=[])
    layer.get_metadata = AsyncMock(return_value=None)
    layer.update_metadata = AsyncMock(return_value=True)
    layer.clear_scope = AsyncMock(return_value=0)
    layer.get_stats = AsyncMock(return_value={"layer": "long_term"})
    layer.semantic_search = AsyncMock(return_value=[])
    return layer


def create_memory_manager(
    l1_capacity: int = 1000,
    enable_promotion: bool = False,
):
    """
    Create a memory manager with mock layers.

    Args:
        l1_capacity: L1 layer capacity
        enable_promotion: Whether to enable auto-promotion

    Returns:
        Mocked HierarchicalMemoryManager
    """
    manager = Mock()
    manager.l1 = create_mock_l1_layer(capacity=l1_capacity)
    manager.l2 = create_mock_l2_layer()
    manager.l3 = create_mock_l3_layer()

    # Setup async methods
    manager.get = AsyncMock()
    manager.set = AsyncMock()
    manager.delete = AsyncMock()
    manager.exists = AsyncMock()
    manager.list_keys = AsyncMock()
    manager.get_metadata = AsyncMock()
    manager.update_metadata = AsyncMock()
    manager.clear_scope = AsyncMock()
    manager.get_stats = AsyncMock()
    manager.manual_promote_to_l3 = AsyncMock()
    manager.batch_flush_l1_to_l2 = AsyncMock()
    manager.semantic_search = AsyncMock()

    return manager


# ============================================================================
# Test Data Generators
# ============================================================================

def sample_memory_data() -> Dict[str, Any]:
    """
    Generate sample memory data for testing.

    Returns:
        Dictionary with sample data structure
    """
    return {
        "type": "test_data",
        "content": "This is sample content for memory testing",
        "metadata": {
            "version": 1.0,
            "tags": ["test", "sample"],
        },
    }


def various_scoped_keys() -> List[Tuple[str, MemoryScope, str]]:
    """
    Generate test keys with various scopes.

    Returns:
        List of (key, scope, scope_id) tuples
    """
    return [
        ("task_data", MemoryScope.TASK, "task_001"),
        ("session_data", MemoryScope.SESSION, "session_001"),
        ("agent_data", MemoryScope.AGENT, "agent_001"),
        ("workspace_data", MemoryScope.WORKSPACE, "workspace_001"),
        ("user_data", MemoryScope.USER, "user_001"),
    ]


def create_test_metadata(
    key: str = "test_key",
    layer: MemoryLayer = MemoryLayer.L1_TRANSIENT,
    scope: MemoryScope = MemoryScope.SESSION,
    importance: float = 0.5,
    access_count: int = 0,
    session_ids: List[str] = None,
) -> MemoryMetadata:
    """
    Create test metadata with customizable values.

    Args:
        key: Memory key
        layer: Memory layer
        scope: Memory scope
        importance: Importance score (0-1)
        access_count: Number of accesses
        session_ids: List of session IDs

    Returns:
        MemoryMetadata instance
    """
    return MemoryMetadata(
        key=key,
        layer=layer,
        scope=scope,
        importance=importance,
        access_count=access_count,
        session_ids=session_ids or [],
    )


def create_promotion_candidate(
    key: str = "candidate_key",
    value: Any = None,
    metadata: MemoryMetadata = None,
    reason: PromotionReason = PromotionReason.HIGH_ACCESS_FREQUENCY,
) -> Tuple[str, Any, MemoryMetadata, PromotionReason]:
    """
    Create a promotion candidate tuple.

    Args:
        key: Memory key
        value: Data value
        metadata: Memory metadata
        reason: Promotion reason

    Returns:
        Tuple of (key, value, metadata, reason)
    """
    if value is None:
        value = {"data": "promotion candidate"}
    if metadata is None:
        metadata = create_test_metadata(key=key)

    return (key, value, metadata, reason)


# ============================================================================
# Data Generation Helpers
# ============================================================================

def generate_random_data(size: int = 100) -> str:
    """
    Generate random data string of specified size.

    Args:
        size: Size of the data string in bytes

    Returns:
        Random data string
    """
    import random
    import string

    return "".join(random.choices(string.ascii_letters + string.digits, k=size))


def generate_complex_data(depth: int = 3) -> Dict[str, Any]:
    """
    Generate complex nested data structure for testing serialization.

    Args:
        depth: Nesting depth

    Returns:
        Complex nested dictionary
    """
    if depth == 0:
        return {"value": generate_random_data(10)}

    return {
        "level": depth,
        "data": generate_random_data(20),
        "nested": generate_complex_data(depth - 1),
        "list": [
            generate_random_data(5),
            generate_random_data(5),
        ],
    }


# ============================================================================
# Assertion Helpers
# ============================================================================

def assert_metadata_valid(metadata: MemoryMetadata):
    """
    Assert that metadata is valid.

    Args:
        metadata: MemoryMetadata to validate

    Raises:
        AssertionError: If metadata is invalid
    """
    assert metadata.key is not None
    assert metadata.layer is not None
    assert metadata.scope is not None
    assert 0.0 <= metadata.importance <= 1.0
    assert metadata.access_count >= 0
    assert metadata.created_at is not None
    assert metadata.last_accessed is not None


def assert_promotion_result_valid(result):
    """
    Assert that promotion result is valid.

    Args:
        result: MigrationResult from promotion

    Raises:
        AssertionError: If result is invalid
    """
    assert hasattr(result, "success_count")
    assert hasattr(result, "failed_count")
    assert hasattr(result, "skipped_count")
    assert hasattr(result, "duration_seconds")
    assert result.success_count >= 0
    assert result.failed_count >= 0
    assert result.skipped_count >= 0
    assert result.duration_seconds >= 0
