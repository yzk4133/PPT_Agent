"""
LLM Cache 测试
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from infrastructure.llm.llm_cache import (
    LLMRequestCache,
    get_global_cache,
    cached_llm_call,
    _global_cache,
)

@pytest.mark.unit
class TestLLMRequestCache:
    """测试 LLMRequestCache 类"""

    def test_cache_initialization(self):
        """测试缓存初始化"""
        cache = LLMRequestCache(default_ttl_seconds=3600, max_size=1000)

        assert cache.default_ttl_seconds == 3600
        assert cache.max_size == 1000
        assert cache._cache == {}
        assert cache._hits == 0
        assert cache._misses == 0
        assert cache._evictions == 0

    def test_generate_cache_key(self):
        """测试缓存键生成"""
        cache = LLMRequestCache()

        model = "gpt-4"
        messages = [{"role": "user", "content": "Hello"}]
        temperature = 0.7
        max_tokens = 1000

        key1 = cache.generate_cache_key(model, messages, temperature, max_tokens)
        key2 = cache.generate_cache_key(model, messages, temperature, max_tokens)

        # 相同输入应该生成相同的键
        assert key1 == key2
        assert len(key1) == 64  # SHA256 hash 长度

    def test_generate_cache_key_different_inputs(self):
        """测试不同输入生成不同键"""
        cache = LLMRequestCache()

        model = "gpt-4"
        messages = [{"role": "user", "content": "Hello"}]
        temperature = 0.7
        max_tokens = 1000

        key1 = cache.generate_cache_key(model, messages, temperature, max_tokens)
        key2 = cache.generate_cache_key(model, messages, 0.5, max_tokens)  # 不同 temperature

        assert key1 != key2

    def test_cache_set_and_get(self):
        """测试缓存设置和获取"""
        cache = LLMRequestCache()

        cache_key = "test_key_123"
        response = {"result": "success", "data": "test_data"}

        # 设置缓存
        result = cache.set(cache_key, response)
        assert result is True

        # 获取缓存
        cached_response = cache.get(cache_key)
        assert cached_response == response

    def test_cache_hit(self):
        """测试缓存命中"""
        cache = LLMRequestCache()

        cache_key = "test_key_123"
        response = {"result": "success"}

        cache.set(cache_key, response)
        result = cache.get(cache_key)

        assert result == response
        assert cache._hits == 1
        assert cache._misses == 0

    def test_cache_miss(self):
        """测试缓存未命中"""
        cache = LLMRequestCache()

        result = cache.get("non_existent_key")

        assert result is None
        assert cache._hits == 0
        assert cache._misses == 1

    def test_cache_expiration(self):
        """测试缓存过期"""
        cache = LLMRequestCache(default_ttl_seconds=1)

        cache_key = "test_key_123"
        response = {"result": "success"}

        # 设置缓存
        cache.set(cache_key, response)

        # 立即获取应该成功
        result = cache.get(cache_key)
        assert result == response

        # 等待过期
        time.sleep(2)

        # 过期后应该返回 None
        result = cache.get(cache_key)
        assert result is None
        # 过期也算 miss
        assert cache._misses == 2  # 第一次 hit + 过期后的 miss

    def test_cache_custom_ttl(self):
        """测试自定义 TTL"""
        cache = LLMRequestCache(default_ttl_seconds=3600)

        cache_key = "test_key_123"
        response = {"result": "success"}

        # 设置 1 秒过期的缓存
        cache.set(cache_key, response, ttl_seconds=1)

        # 立即获取应该成功
        result = cache.get(cache_key)
        assert result == response

        # 等待过期
        time.sleep(2)

        # 过期后应该返回 None
        result = cache.get(cache_key)
        assert result is None

    def test_cache_clear(self):
        """测试清空缓存"""
        cache = LLMRequestCache()

        # 添加多个缓存
        for i in range(5):
            cache.set(f"key_{i}", {"value": i})

        assert len(cache._cache) == 5

        # 清空缓存
        cache.clear()

        assert len(cache._cache) == 0

    def test_cleanup_expired(self):
        """测试清理过期缓存"""
        cache = LLMRequestCache()

        # 添加缓存
        cache.set("key1", {"value": 1}, ttl_seconds=1)
        cache.set("key2", {"value": 2}, ttl_seconds=3600)
        cache.set("key3", {"value": 3}, ttl_seconds=1)

        # 等待部分过期
        time.sleep(2)

        # 清理过期
        cleaned_count = cache.cleanup_expired()

        assert cleaned_count == 2
        assert len(cache._cache) == 1
        assert "key2" in cache._cache

    def test_lru_eviction(self):
        """测试 LRU 淘汰策略"""
        cache = LLMRequestCache(max_size=3)

        # 添加 3 个缓存（达到上限）
        cache.set("key1", {"value": 1})
        cache.set("key2", {"value": 2})
        cache.set("key3", {"value": 3})

        assert len(cache._cache) == 3

        # 访问 key1 和 key2，使 key3 成为 LRU
        cache.get("key1")
        cache.get("key2")

        # 添加第 4 个缓存，应该淘汰 key3
        cache.set("key4", {"value": 4})

        assert len(cache._cache) == 3
        assert "key3" not in cache._cache
        assert "key4" in cache._cache
        assert cache._evictions == 1

    def test_get_stats(self):
        """测试获取统计信息"""
        cache = LLMRequestCache(max_size=100)

        # 添加缓存
        cache.set("key1", {"value": 1})
        cache.set("key2", {"value": 2})

        # 缓存命中
        cache.get("key1")
        cache.get("key1")

        # 缓存未命中
        cache.get("key3")

        stats = cache.get_stats()

        assert stats["size"] == 2
        assert stats["max_size"] == 100
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 2 / 3
        assert stats["evictions"] == 0

    def test_reset_stats(self):
        """测试重置统计信息"""
        cache = LLMRequestCache()

        cache.set("key1", {"value": 1})
        cache.get("key1")
        cache.get("key2")

        assert cache._hits == 1
        assert cache._misses == 1

        # 重置统计
        cache.reset_stats()

        assert cache._hits == 0
        assert cache._misses == 0
        assert cache._evictions == 0

    def test_cache_hit_updates_last_accessed(self):
        """测试缓存命中更新最后访问时间"""
        cache = LLMRequestCache()

        cache.set("key1", {"value": 1})

        first_access_time = cache._cache["key1"]["last_accessed"]

        time.sleep(0.1)

        # 再次访问
        cache.get("key1")

        second_access_time = cache._cache["key1"]["last_accessed"]

        assert second_access_time > first_access_time

@pytest.mark.unit
class TestGlobalCache:
    """测试全局缓存"""

    def test_get_global_cache_singleton(self):
        """测试全局缓存单例"""
        # 重置全局变量
        import infrastructure.llm.llm_cache as cache_module
        cache_module._global_cache = None

        cache1 = get_global_cache()
        cache2 = get_global_cache()

        assert cache1 is cache2

@pytest.mark.unit
@pytest.mark.asyncio
class TestCachedLLMCall:
    """测试 LLM 调用缓存装饰器"""

    async def test_cached_llm_call_decorator_async(self):
        """测试异步函数的缓存装饰器"""
        # 重置全局缓存
        import infrastructure.llm.llm_cache as cache_module
        cache_module._global_cache = LLMRequestCache()

        call_count = []

        @cached_llm_call(ttl_seconds=60)
        async def mock_llm_call(model, messages, temperature, max_tokens):
            call_count.append(1)
            return {"response": f"Response for {model}"}

        # 第一次调用
        result1 = await mock_llm_call("gpt-4", [{"role": "user", "content": "Hello"}], 0.7, 1000)
        assert result1 == {"response": "Response for gpt-4"}
        assert len(call_count) == 1

        # 第二次调用（应该使用缓存）
        result2 = await mock_llm_call("gpt-4", [{"role": "user", "content": "Hello"}], 0.7, 1000)
        assert result2 == {"response": "Response for gpt-4"}
        assert len(call_count) == 1  # 没有增加

    async def test_cached_llm_call_decorator_sync(self):
        """测试同步函数的缓存装饰器"""
        # 重置全局缓存
        import infrastructure.llm.llm_cache as cache_module
        cache_module._global_cache = LLMRequestCache()

        call_count = []

        @cached_llm_call(ttl_seconds=60)
        def mock_llm_call_sync(model, messages, temperature, max_tokens):
            call_count.append(1)
            return {"response": f"Response for {model}"}

        # 第一次调用
        result1 = mock_llm_call_sync("gpt-4", [{"role": "user", "content": "Hello"}], 0.7, 1000)
        assert result1 == {"response": "Response for gpt-4"}
        assert len(call_count) == 1

        # 第二次调用（应该使用缓存）
        result2 = mock_llm_call_sync("gpt-4", [{"role": "user", "content": "Hello"}], 0.7, 1000)
        assert result2 == {"response": "Response for gpt-4"}
        assert len(call_count) == 1

    async def test_cached_llm_call_different_params(self):
        """测试不同参数不使用缓存"""
        # 重置全局缓存
        import infrastructure.llm.llm_cache as cache_module
        cache_module._global_cache = LLMRequestCache()

        call_count = []

        @cached_llm_call(ttl_seconds=60)
        async def mock_llm_call(model, messages, temperature, max_tokens):
            call_count.append(1)
            return {"response": f"Response for {model}"}

        # 不同参数的调用
        await mock_llm_call("gpt-4", [{"role": "user", "content": "Hello"}], 0.7, 1000)
        await mock_llm_call("gpt-4", [{"role": "user", "content": "Hi"}], 0.7, 1000)  # 不同消息
        await mock_llm_call("gpt-3.5", [{"role": "user", "content": "Hello"}], 0.7, 1000)  # 不同模型

        assert len(call_count) == 3  # 每次都调用
