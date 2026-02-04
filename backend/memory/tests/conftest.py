"""
Pytest configuration and shared fixtures for Memory layer tests.
"""

import sys
import os

# Add backend directory to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import Mock, AsyncMock
from fakeredis import FakeStrictRedis

# Now import from memory module
from memory.models import (
    MemoryLayer,
    MemoryScope,
    MemoryMetadata,
    PromotionReason,
)
from memory.layers.l1_transient import L1TransientLayer
from memory.layers.l2_short_term import L2ShortTermLayer
from memory.promotion import (
    PromotionConfig,
    ActiveScopeTracker,
    PromotionRuleEngine,
)


# ============================================================================
# Test Fixtures - Memory Layers
# ============================================================================

@pytest.fixture
async def l1_layer() -> AsyncGenerator[L1TransientLayer, None]:
    """Create a mock L1 transient layer with small capacity for testing."""
    layer = L1TransientLayer(capacity=100, default_ttl_seconds=300)
    await layer.start_cleanup_task()
    yield layer
    await layer.stop_cleanup_task()


@pytest.fixture
def l2_layer():
    """Create a mock L2 short-term layer using fakeredis."""
    layer = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
    layer.client = FakeStrictRedis(decode_responses=False)
    return layer


@pytest.fixture
def mock_l2_layer():
    """Create a fully mocked L2 layer for isolated testing."""
    layer = Mock(spec=L2ShortTermLayer)
    layer.layer_type = MemoryLayer.L2_SHORT_TERM
    layer.get = AsyncMock()
    layer.set = AsyncMock(return_value=True)
    layer.delete = AsyncMock(return_value=True)
    layer.exists = AsyncMock(return_value=False)
    return layer


@pytest.fixture
def mock_l3_layer():
    """Create a fully mocked L3 layer for isolated testing."""
    from memory.layers.l3_longterm import L3LongtermLayer
    layer = Mock(spec=L3LongtermLayer)
    layer.layer_type = MemoryLayer.L3_LONG_TERM
    layer.get = AsyncMock(return_value=None)
    layer.set = AsyncMock(return_value=True)
    return layer


# ============================================================================
# Simple test data
# ============================================================================

@pytest.fixture
def sample_metadata():
    """Create sample memory metadata."""
    return MemoryMetadata(
        key="test_key",
        layer=MemoryLayer.L1_TRANSIENT,
        scope=MemoryScope.SESSION,
        importance=0.5,
        access_count=0,
    )


@pytest.fixture
def sample_value():
    """Create sample data value."""
    return {
        "type": "test_data",
        "content": "Sample content for testing",
        "metadata": {"version": 1.0},
    }
