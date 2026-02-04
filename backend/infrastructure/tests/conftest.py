"""
Backend Infrastructure 测试全局 Fixtures
"""

import os
import sys
import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

# 添加项目根目录到 Python 路径

# 导入所有 fixtures 子模块以使其可用
from . import fixtures
from .fixtures import database_fixtures
from .fixtures import llm_fixtures
from .fixtures import cache_fixtures

# 设置测试环境变量
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("LLM_API_KEY", "test_api_key_for_testing")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_for_jwt_must_be_32_chars_or_more")
os.environ.setdefault("DEEPSEEK_API_KEY", "test_deepseek_key")
os.environ.setdefault("OPENAI_API_KEY", "test_openai_key")

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_settings():
    """Mock 配置设置"""
    settings = MagicMock()
    settings.database_url = "postgresql+asyncpg://test:test@localhost:5432/test_db"
    settings.redis_url = "redis://localhost:6379/1"
    settings.llm_api_key = "test_api_key"
    settings.jwt_secret_key = "test_secret_key"
    settings.jwt_algorithm = "HS256"
    settings.jwt_expiration_minutes = 60
    settings.environment = "test"
    return settings

@pytest.fixture
def mock_postgres_session():
    """Mock PostgreSQL 会话"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session

@pytest.fixture
def mock_redis_client():
    """Mock Redis 客户端"""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.exists = AsyncMock(return_value=0)
    redis.expire = AsyncMock(return_value=True)
    redis.ping = AsyncMock(return_value=True)
    redis.flushdb = AsyncMock(return_value=True)
    return redis

@pytest.fixture
def mock_llm_response():
    """Mock LLM 响应"""
    response = MagicMock()
    response.text = '{"result": "success", "data": "test_data"}'
    response.content = b'{"result": "success"}'
    response.status_code = 200
    response.headers = {"content-type": "application/json"}
    return response

@pytest.fixture
def sample_agent_config():
    """示例 Agent 配置"""
    from infrastructure.config.common_config import AgentConfig, ModelProvider

    return AgentConfig(
        provider=ModelProvider.DEEPSEEK,
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=4096,
        enable_fallback=True,
        fallback_model="deepseek-lite",
    )

@pytest.fixture
def sample_app_config():
    """示例应用配置"""
    from infrastructure.config.common_config import AppConfig

    return AppConfig(
        environment="test",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test_db",
        redis_url="redis://localhost:6379/1",
        llm_api_key="test_api_key",
        jwt_secret_key="test_secret_key",
        debug=True,
    )

@pytest.fixture
async def clear_redis_cache(mock_redis_client):
    """清理 Redis 缓存"""
    yield mock_redis_client
    # 清理操作
    await mock_redis_client.flushdb()

@pytest.fixture
def temp_cache_dir(tmp_path):
    """临时缓存目录"""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir

# 异步测试辅助函数
@pytest.fixture
def async_wait():
    """异步等待辅助函数"""
    async def _wait(seconds: float = 0.1):
        await asyncio.sleep(seconds)
    return _wait
