"""
Agent Cache 测试
"""

import pytest
import time
import threading
from infrastructure.cache.agent_cache import (
    CacheEntry,
    CacheStats,
    AgentCache,
    get_agent_cache,
    reset_agent_cache,
    _global_cache,
    cached,
)

@pytest.mark.unit
class TestCacheEntry:
    """测试 CacheEntry 类"""

    def test_cache_entry_creation(self):
        """测试缓存条目创建"""
        from datetime import datetime

        now = datetime.now()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now,
            accessed_at=now,
            access_count=0,
            ttl_seconds=3600,
            size_bytes=100,
        )

        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.ttl_seconds == 3600
        assert entry.size_bytes == 100
        assert entry.access_count == 0

    def test_is_expired_with_ttl(self):
        """测试带 TTL 的过期检查"""
        from datetime import datetime, timedelta

        now = datetime.now()

        # 未过期
        entry = CacheEntry(
            key="test_key",
            value="value",
            created_at=now,
            accessed_at=now,
            ttl_seconds=3600,
        )
        assert entry.is_expired() is False

        # 已过期
        entry = CacheEntry(
            key="test_key",
            value="value",
            created_at=now - timedelta(seconds=3700),
            accessed_at=now,
            ttl_seconds=3600,
        )
        assert entry.is_expired() is True

    def test_is_expired_without_ttl(self):
        """测试不带 TTL 的过期检查"""
        from datetime import datetime

        now = datetime.now()
        entry = CacheEntry(
            key="test_key",
            value="value",
            created_at=now,
            accessed_at=now,
            ttl_seconds=None,  # 永不过期
        )

        assert entry.is_expired() is False

    def test_touch(self):
        """测试更新访问信息"""
        from datetime import datetime

        now = datetime.now()
        entry = CacheEntry(
            key="test_key",
            value="value",
            created_at=now,
            accessed_at=now,
            access_count=0,
        )

        time.sleep(0.1)
        entry.touch()

        assert entry.access_count == 1
        assert entry.accessed_at > now

    def test_to_dict(self):
        """测试转换为字典"""
        from datetime import datetime

        now = datetime.now()
        entry = CacheEntry(
            key="test_key_with_very_long_name_that_should_be_truncated",
            value="value",
            created_at=now,
            accessed_at=now,
            ttl_seconds=3600,
            size_bytes=1024,
        )

        result = entry.to_dict()

        assert "key" in result
        assert "created_at" in result
        assert "accessed_at" in result
        assert "access_count" in result
        assert "ttl_seconds" in result
        assert "size_bytes" in result
        assert "expired" in result
        assert len(result["key"]) <= 53  # 应该被截断

@pytest.mark.unit
class TestCacheStats:
    """测试 CacheStats 类"""

    def test_cache_stats_defaults(self):
        """测试缓存统计默认值"""
        stats = CacheStats()

        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.total_entries == 0
        assert stats.total_size_bytes == 0

    def test_total_requests_property(self):
        """测试总请求数属性"""
        stats = CacheStats(hits=7, misses=3)

        assert stats.total_requests == 10

    def test_hit_rate_property(self):
        """测试命中率属性"""
        stats = CacheStats(hits=7, misses=3)

        assert stats.hit_rate == 0.7

    def test_hit_rate_no_requests(self):
        """测试无请求时的命中率"""
        stats = CacheStats()

        assert stats.hit_rate == 0.0

    def test_to_dict(self):
        """测试转换为字典"""
        stats = CacheStats(
            hits=70,
            misses=30,
            evictions=5,
            total_entries=20,
            total_size_bytes=2048000,
        )

        result = stats.to_dict()

        assert result["hits"] == 70
        assert result["misses"] == 30
        assert result["evictions"] == 5
        assert result["total_requests"] == 100
        assert result["hit_rate"] == 70.0
        assert result["miss_rate"] == 30.0
        assert result["total_size_mb"] == 1.95

@pytest.mark.unit
class TestAgentCache:
    """测试 AgentCache 类"""

    def test_cache_initialization(self):
        """测试缓存初始化"""
        cache = AgentCache(max_size_mb=10.0, max_entries=100)

        assert cache._max_size_bytes == 10 * 1024 * 1024
        assert cache._max_entries == 100
        assert cache._enable_stats is True
        assert len(cache._cache) == 0

    def test_cache_set_and_get(self):
        """测试缓存设置和获取"""
        cache = AgentCache()

        input_data = {"topic": "AI", "pages": 10}
        value = {"result": "success"}

        # 设置缓存
        cache.set("TestAgent", input_data, value)

        # 获取缓存
        result = cache.get("TestAgent", input_data)

        assert result == value

    def test_cache_hit_and_miss(self):
        """测试缓存命中和未命中"""
        cache = AgentCache()

        # 第一次获取 - miss
        result = cache.get("TestAgent", {"input": "data"})
        assert result is None

        stats = cache.get_stats("TestAgent")
        assert stats.misses == 1
        assert stats.hits == 0

        # 设置缓存
        cache.set("TestAgent", {"input": "data"}, {"result": "value"})

        # 第二次获取 - hit
        result = cache.get("TestAgent", {"input": "data"})
        assert result == {"result": "value"}

        stats = cache.get_stats("TestAgent")
        assert stats.hits == 1
        assert stats.misses == 1

    def test_cache_key_generation_dict(self):
        """测试字典输入的键生成"""
        cache = AgentCache()

        # 相同内容的字典应该生成相同的键
        input1 = {"topic": "AI", "pages": 10}
        input2 = {"pages": 10, "topic": "AI"}  # 不同顺序

        cache.set("TestAgent", input1, "value1")
        result = cache.get("TestAgent", input2)

        assert result == "value1"

    def test_cache_key_generation_string(self):
        """测试字符串输入的键生成"""
        cache = AgentCache()

        cache.set("TestAgent", "simple_string", "value")
        result = cache.get("TestAgent", "simple_string")

        assert result == "value"

    def test_cache_expiration(self):
        """测试缓存过期"""
        cache = AgentCache()

        # 设置 1 秒过期的缓存
        cache.set("TestAgent", "expire_me", "value", ttl_seconds=1)

        # 立即获取应该成功
        result = cache.get("TestAgent", "expire_me")
        assert result == "value"

        # 等待过期
        time.sleep(2)

        # 过期后应该返回 None
        result = cache.get("TestAgent", "expire_me")
        assert result is None

    def test_cache_invalidate_specific(self):
        """测试失效特定缓存条目"""
        cache = AgentCache()

        cache.set("TestAgent", "key1", "value1")
        cache.set("TestAgent", "key2", "value2")

        # 验证缓存存在
        assert cache.get("TestAgent", "key1") == "value1"

        # 失效 key1
        count = cache.invalidate("TestAgent", "key1")
        assert count == 1

        # 验证已失效
        assert cache.get("TestAgent", "key1") is None
        assert cache.get("TestAgent", "key2") == "value2"

    def test_cache_invalidate_all_for_agent(self):
        """测试失效特定 agent 的所有缓存"""
        cache = AgentCache()

        cache.set("TestAgent", "key1", "value1")
        cache.set("TestAgent", "key2", "value2")
        cache.set("OtherAgent", "key1", "value3")

        # 失效 TestAgent 的所有缓存
        count = cache.invalidate("TestAgent")
        assert count == 2

        # 验证
        assert cache.get("TestAgent", "key1") is None
        assert cache.get("TestAgent", "key2") is None
        assert cache.get("OtherAgent", "key1") == "value3"

    def test_cache_clear(self):
        """测试清空缓存"""
        cache = AgentCache()

        cache.set("Agent1", "key1", "value1")
        cache.set("Agent2", "key2", "value2")

        assert len(cache.get_entries()) == 2

        # 清空
        cache.clear()

        assert len(cache.get_entries()) == 0
        assert cache.get("Agent1", "key1") is None

    def test_cleanup_expired(self):
        """测试清理过期缓存"""
        cache = AgentCache()

        # 添加缓存
        cache.set("Agent1", "key1", "value1", ttl_seconds=1)
        cache.set("Agent2", "key2", "value2", ttl_seconds=3600)
        cache.set("Agent3", "key3", "value3", ttl_seconds=1)

        # 等待部分过期
        time.sleep(2)

        # 清理过期
        cleaned_count = cache.cleanup_expired()

        assert cleaned_count == 2
        assert len(cache.get_entries()) == 1
        assert cache.get("Agent2", "key2") == "value2"

    def test_get_stats_global(self):
        """测试获取全局统计"""
        cache = AgentCache()

        cache.set("Agent1", "key1", "value1")
        cache.set("Agent2", "key2", "value2")

        cache.get("Agent1", "key1")  # hit
        cache.get("Agent1", "key2")  # miss
        cache.get("Agent2", "key1")  # miss

        stats = cache.get_stats()

        assert stats.hits == 1
        assert stats.misses == 2
        assert stats.total_requests == 3
        assert stats.hit_rate == 1 / 3
        assert stats.total_entries == 2

    def test_get_stats_per_agent(self):
        """测试按 agent 获取统计"""
        cache = AgentCache()

        cache.set("Agent1", "key1", "value1")
        cache.set("Agent1", "key2", "value2")
        cache.set("Agent2", "key1", "value3")

        cache.get("Agent1", "key1")  # hit
        cache.get("Agent1", "key3")  # miss

        stats1 = cache.get_stats("Agent1")
        stats2 = cache.get_stats("Agent2")

        assert stats1.hits == 1
        assert stats1.misses == 1
        assert stats1.total_entries == 2

        assert stats2.hits == 0
        assert stats2.misses == 0
        assert stats2.total_entries == 1

    def test_lru_eviction_by_count(self):
        """测试基于数量的 LRU 淘汰"""
        cache = AgentCache(max_size_mb=10.0, max_entries=3)

        cache.set("Agent", "key1", "value1")
        cache.set("Agent", "key2", "value2")
        cache.set("Agent", "key3", "value3")

        assert len(cache.get_entries()) == 3

        # 访问 key1 和 key2，使 key3 成为 LRU
        cache.get("Agent", "key1")
        cache.get("Agent", "key2")

        # 添加第 4 个条目，应该淘汰 key3
        cache.set("Agent", "key4", "value4")

        assert len(cache.get_entries()) == 3
        assert cache.get("Agent", "key3") is None
        assert cache.get("Agent", "key4") == "value4"

    def test_default_ttl_by_agent_type(self):
        """测试根据 agent 类型设置默认 TTL"""
        cache = AgentCache()

        # requirement agent - 30 minutes
        cache.set("RequirementParser", "key", "value")
        entry_key = cache._make_key("RequirementParser", "key")
        entry = cache._cache[entry_key]
        assert entry.ttl_seconds == cache.REQUIREMENT_TTL

        # research agent - 1 hour
        cache.set("ResearchAgent", "key", "value")
        entry_key = cache._make_key("ResearchAgent", "key")
        entry = cache._cache[entry_key]
        assert entry.ttl_seconds == cache.RESEARCH_TTL

        # framework agent - 30 minutes
        cache.set("FrameworkDesigner", "key", "value")
        entry_key = cache._make_key("FrameworkDesigner", "key")
        entry = cache._cache[entry_key]
        assert entry.ttl_seconds == cache.FRAMEWORK_TTL

        # content agent - 15 minutes
        cache.set("ContentWriter", "key", "value")
        entry_key = cache._make_key("ContentWriter", "key")
        entry = cache._cache[entry_key]
        assert entry.ttl_seconds == cache.CONTENT_TTL

    def test_estimate_size(self):
        """测试大小估算"""
        cache = AgentCache()

        # 字符串
        size = cache._estimate_size("test string")
        assert size == len("test string".encode('utf-8'))

        # 字典
        size = cache._estimate_size({"key": "value"})
        assert size > 0

        # 列表
        size = cache._estimate_size([1, 2, 3])
        assert size > 0

    def test_thread_safety(self):
        """测试线程安全"""
        cache = AgentCache()
        results = []
        errors = []

        def worker(worker_id):
            try:
                for i in range(10):
                    cache.set(f"Agent{worker_id}", f"key{i}", f"value{worker_id}_{i}")
                    result = cache.get(f"Agent{worker_id}", f"key{i}")
                    results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(errors) == 0
        assert len(results) == 50

@pytest.mark.unit
class TestGlobalCache:
    """测试全局缓存"""

    def test_get_global_cache_singleton(self):
        """测试全局缓存单例"""
        import infrastructure.cache.agent_cache as cache_module

        # 重置全局缓存
        cache_module._global_cache = None

        cache1 = get_agent_cache()
        cache2 = get_agent_cache()

        assert cache1 is cache2

    def test_reset_global_cache(self):
        """测试重置全局缓存"""
        import infrastructure.cache.agent_cache as cache_module

        cache1 = get_agent_cache()
        cache1.set("Test", "key", "value")

        cache2 = reset_agent_cache()

        assert cache2 is not cache1
        assert len(cache2.get_entries()) == 0

@pytest.mark.unit
@pytest.mark.asyncio
class TestCachedDecorator:
    """测试缓存装饰器"""

    async def test_cached_decorator(self):
        """测试缓存装饰器"""
        import infrastructure.cache.agent_cache as cache_module

        # 重置全局缓存
        cache_module._global_cache = None

        call_count = []

        @cached(ttl_seconds=60)
        async def test_function(input_data):
            call_count.append(1)
            return f"result_{input_data}"

        # 第一次调用
        result1 = await test_function("test_input")
        assert result1 == "result_test_input"
        assert len(call_count) == 1

        # 第二次调用（应该使用缓存）
        result2 = await test_function("test_input")
        assert result2 == "result_test_input"
        assert len(call_count) == 1  # 没有增加

        # 不同参数
        result3 = await test_function("other_input")
        assert result3 == "result_other_input"
        assert len(call_count) == 2
