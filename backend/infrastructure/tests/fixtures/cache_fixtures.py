"""
缓存测试 Fixtures
"""

import pytest
import time
from typing import Any, Dict
from dataclasses import dataclass

@dataclass
class MockCacheStats:
    """Mock 缓存统计信息"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size_bytes: int = 0
    entry_count: int = 0

@pytest.fixture
def sample_cache_data():
    """示例缓存数据"""
    return {
        "agent_result": {"status": "success", "data": "test_data"},
        "llm_response": {"text": "This is a test response", "tokens": 100},
        "checkpoint": {"step": 5, "state": {"x": 1, "y": 2}},
    }

@pytest.fixture
def sample_cache_entries():
    """示例缓存条目"""
    return [
        {"key": "key1", "value": "value1", "size": 100, "ttl": 3600},
        {"key": "key2", "value": "value2", "size": 200, "ttl": 7200},
        {"key": "key3", "value": "value3", "size": 150, "ttl": 1800},
    ]

@pytest.fixture
def mock_cache_stats():
    """Mock 缓存统计"""
    return MockCacheStats(
        hits=100,
        misses=20,
        evictions=5,
        size_bytes=10240,
        entry_count=50
    )

@pytest.fixture
def cache_config():
    """缓存配置"""
    config = {
        "max_size_mb": 1.0,
        "max_entries": 1000,
        "default_ttl_seconds": 3600,
        "enable_lru": True,
        "enable_stats": True,
    }
    return config

@pytest.fixture
def time_mock():
    """时间 Mock"""
    import time as time_module

    class TimeMock:
        def __init__(self):
            self.current_time = time_module.time()

        def time(self):
            return self.current_time

        def sleep(self, seconds):
            self.current_time += seconds

        def advance(self, seconds):
            self.current_time += seconds

    return TimeMock()
