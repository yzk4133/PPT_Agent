"""
LLM 测试 Fixtures
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, Any

@pytest.fixture
def mock_litellm_completion():
    """Mock LiteLLM completion 响应"""
    response = MagicMock()
    response.id = "test-chat-id-123"
    response.object = "chat.completion"
    response.created = 1234567890
    response.model = "deepseek-chat"
    response.choices = [
        MagicMock(
            index=0,
            message=MagicMock(
                role="assistant",
                content='{"result": "success", "answer": "42"}'
            ),
            finish_reason="stop"
        )
    ]
    response.usage = MagicMock(
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30
    )
    return response

@pytest.fixture
def mock_litellm_stream():
    """Mock LiteLLM 流式响应"""
    chunks = [
        MagicMock(choices=[MagicMock(delta=MagicMock(content='{"'))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content='result'))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content='": "'))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content='success'))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content='"}'))]),
    ]
    return chunks

@pytest.fixture
def mock_model_factory():
    """Mock 模型工厂"""
    factory = MagicMock()
    factory.create_model = MagicMock(return_value={"model": "deepseek-chat"})
    factory._model_cache = {}
    return factory

@pytest.fixture
def mock_model_instance():
    """Mock 模型实例"""
    model = AsyncMock()
    model.generate = AsyncMock(return_value="Generated response")
    model.stream = AsyncMock(return_value=["chunk1", "chunk2", "chunk3"])
    return model

@pytest.fixture
def sample_llm_config_dict():
    """示例 LLM 配置字典"""
    return {
        "provider": "deepseek",
        "model": "deepseek-chat",
        "temperature": 0.7,
        "max_tokens": 4096,
        "top_p": 0.9,
        "stream": False,
    }

@pytest.fixture
def mock_retry_config():
    """Mock 重试配置"""
    config = MagicMock()
    config.max_retries = 3
    config.base_delay = 1.0
    config.max_delay = 60.0
    config.exponential_base = 2
    config.retry_on_exceptions = (Exception,)
    return config

@pytest.fixture
def mock_cache_entry():
    """Mock 缓存条目"""
    entry = MagicMock()
    entry.key = "test_cache_key"
    entry.value = "cached_value"
    entry.ttl_seconds = 3600
    entry.created_at = 1234567890
    entry.access_count = 5
    return entry
