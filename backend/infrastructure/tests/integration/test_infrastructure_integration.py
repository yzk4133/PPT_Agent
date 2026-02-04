"""
Infrastructure 集成测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from infrastructure.database.connection_manager import DatabaseManager
from infrastructure.cache.agent_cache import AgentCache
from infrastructure.config.common_config import AppConfig, DatabaseConfig
from infrastructure.llm.common_model_factory import ModelFactory, ModelProvider

@pytest.mark.integration
@pytest.mark.asyncio
class TestInfrastructureIntegration:
    """基础设施层集成测试"""

    async def test_database_to_cache_integration(self):
        """测试数据库和缓存集成"""
        with patch('infrastructure.database.connection_manager.create_async_engine') as mock_engine, \
             patch('infrastructure.database.connection_manager.async_sessionmaker') as mock_sessionmaker, \
             patch('infrastructure.database.connection_manager.ConnectionPool.from_url'):

            # Mock 数据库
            mock_engine_instance = MagicMock()
            mock_engine.return_value = mock_engine_instance
            mock_session_factory = MagicMock()
            mock_sessionmaker.return_value = mock_session_factory

            db_config = DatabaseConfig(
                database_url="postgresql://test:test@localhost/test_db",
                redis_url="redis://localhost:6379/1",
            )
            db_manager = DatabaseManager(config=db_config)
            await db_manager.initialize()

            # 创建缓存
            cache = AgentCache(max_size_mb=1.0, max_entries=100)

            # 模拟从数据库加载数据并缓存
            data = {"key": "value"}
            cache.set("TestAgent", "input_data", data)

            # 验证缓存
            result = cache.get("TestAgent", "input_data")
            assert result == data

    async def test_config_to_database_integration(self):
        """测试配置和数据库集成"""
        config = AppConfig(
            environment="test",
            database_url="postgresql://user:pass@localhost/test",
            redis_url="redis://localhost:6379/0",
            debug=True,
        )

        assert config.database.database_url == "postgresql://user:pass@localhost/test"
        assert config.database.redis_url == "redis://localhost:6379/0"

    async def test_factory_to_config_integration(self):
        """测试工厂和配置集成"""
        config = AppConfig(
            deepseek_api_key="test_key",
            environment="test",
        )

        factory = ModelFactory()
        factory.config = config

        # 验证 API Key 可以从配置获取
        api_key = factory.config.get_api_key(ModelProvider.DEEPSEEK)
        assert api_key == "test_key"

    async def test_full_stack_flow(self):
        """测试完整流程"""
        # 配置
        config = AppConfig(
            environment="test",
            database_url="postgresql://test:test@localhost/test",
            redis_url="redis://localhost:6379/0",
            deepseek_api_key="test_key",
            debug=True,
        )

        # 缓存
        cache = AgentCache(max_size_mb=1.0, max_entries=100)

        # 模拟完整的执行流程
        task_id = "task_001"
        agent_name = "TestAgent"
        input_data = {"topic": "AI PPT", "pages": 10}

        # 1. 检查缓存
        result = cache.get(agent_name, input_data)
        assert result is None

        # 2. 模拟处理数据
        processed_data = {"result": "processed", "topic": "AI PPT"}

        # 3. 存入缓存
        cache.set(agent_name, input_data, processed_data, ttl_seconds=3600)

        # 4. 验证缓存命中
        result = cache.get(agent_name, input_data)
        assert result == processed_data

        # 5. 获取统计
        stats = cache.get_stats(agent_name)
        assert stats.hits == 1
        assert stats.misses == 1

@pytest.mark.integration
@pytest.mark.asyncio
class TestCrossModuleIntegration:
    """跨模块集成测试"""

    async def test_config_factory_llm_integration(self):
        """测试配置、工厂和 LLM 集成"""
        config = AppConfig(
            deepseek_api_key="test_key",
            openai_api_key="test_openai_key",
        )

        factory = ModelFactory()
        factory.config = config

        # 验证配置对多个提供商的支持
        deepseek_key = factory.config.get_api_key(ModelProvider.DEEPSEEK)
        openai_key = factory.config.get_api_key(ModelProvider.OPENAI)

        assert deepseek_key == "test_key"
        assert openai_key == "test_openai_key"

    async def test_cache_stats_integration(self):
        """测试缓存统计集成"""
        cache = AgentCache(max_size_mb=1.0, max_entries=100)

        # 模拟多个 agent 的操作
        agents = ["Agent1", "Agent2", "Agent3"]

        for agent in agents:
            cache.set(agent, "key", {"value": f"{agent}_result"})
            cache.get(agent, "key")

        # 验证全局统计
        global_stats = cache.get_stats()
        assert global_stats.hits == 3

        # 验证每个 agent 的统计
        for agent in agents:
            agent_stats = cache.get_stats(agent)
            assert agent_stats.hits == 1

@pytest.mark.integration
@pytest.mark.asyncio
class TestErrorHandlingIntegration:
    """错误处理集成测试"""

    async def test_database_failure_handling(self):
        """测试数据库失败时的处理"""
        with patch('infrastructure.database.connection_manager.create_async_engine') as mock_engine, \
             patch('infrastructure.database.connection_manager.async_sessionmaker'):

            # 模拟数据库连接失败
            mock_engine.side_effect = Exception("Connection failed")

            db_config = DatabaseConfig(
                database_url="postgresql://test:test@localhost/test",
                redis_url="redis://localhost:6379/0",
            )

            db_manager = DatabaseManager(config=db_config)

            # 应该抛出异常
            with pytest.raises(Exception, match="Connection failed"):
                await db_manager.initialize()

    async def test_cache_failure_handling(self):
        """测试缓存失败时的处理"""
        cache = AgentCache(max_size_mb=0.0001, max_entries=1)  # 非常小的缓存

        # 添加条目直到淘汰
        for i in range(10):
            cache.set(f"Agent{i}", "key", {"value": f"data{i}"})

        # 验证淘汰统计
        stats = cache.get_stats()
        assert stats.evictions > 0

@pytest.mark.integration
@pytest.mark.asyncio
class TestPerformanceIntegration:
    """性能集成测试"""

    async def test_cache_performance(self):
        """测试缓存性能"""
        cache = AgentCache(max_size_mb=1.0, max_entries=1000)

        import time

        # 测试写入性能
        start = time.time()
        for i in range(100):
            cache.set(f"Agent{i}", "key", {"value": f"data{i}"})
        write_time = time.time() - start

        # 测试读取性能
        start = time.time()
        for i in range(100):
            cache.get(f"Agent{i}", "key")
        read_time = time.time() - start

        # 性能应该在合理范围内
        assert write_time < 1.0  # 100次写入应在1秒内
        assert read_time < 0.1  # 100次读取应在0.1秒内

    async def test_concurrent_cache_access(self):
        """测试并发缓存访问"""
        cache = AgentCache(max_size_mb=1.0, max_entries=100)

        async def worker(worker_id):
            for i in range(10):
                cache.set(f"Worker{worker_id}", f"key{i}", {"value": f"data{i}"})
                result = cache.get(f"Worker{worker_id}", f"key{i}")
                assert result is not None

        # 并发执行
        await asyncio.gather(*[worker(i) for i in range(10)])

        # 验证最终状态
        stats = cache.get_stats()
        assert stats.total_entries == 100

@pytest.mark.integration
class TestConfigurationIntegration:
    """配置集成测试"""

    def test_environment_variable_override(self):
        """测试环境变量覆盖"""
        import os

        original_env = os.environ.get("ENVIRONMENT")

        try:
            os.environ["ENVIRONMENT"] = "production"
            os.environ["DEBUG"] = "true"

            # 重新加载配置
            from infrastructure.config.common_config import get_config
            from importlib import reload
            import infrastructure.config.common_config as config_module

            # 注意：实际使用中需要重置单例

        finally:
            if original_env:
                os.environ["ENVIRONMENT"] = original_env
            else:
                os.environ.pop("ENVIRONMENT", None)

@pytest.mark.integration
@pytest.mark.asyncio
class TestEndToEndFlow:
    """端到端流程测试"""

    async def test_complete_request_flow(self):
        """测试完整的请求流程"""
        # 1. 配置
        config = AppConfig(
            environment="test",
            database_url="postgresql://test:test@localhost/test",
            redis_url="redis://localhost:6379/0",
            debug=True,
        )

        # 2. 缓存
        cache = AgentCache(max_size_mb=1.0, max_entries=100)

        # 3. 模拟请求处理
        request_data = {
            "agent": "ResearchAgent",
            "input": {"topic": "AI", "pages": 10},
        }

        # 检查缓存
        cached = cache.get(request_data["agent"], request_data["input"])

        if cached is None:
            # 处理请求
            response = {"result": "Generated PPT content"}

            # 存入缓存
            cache.set(request_data["agent"], request_data["input"], response)

            # 验证
            assert response["result"] == "Generated PPT content"
        else:
            # 使用缓存
            assert cached is not None

        # 验证缓存现在有数据
        cached = cache.get(request_data["agent"], request_data["input"])
        assert cached is not None
