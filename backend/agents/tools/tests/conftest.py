"""
Shared fixtures for Tools layer tests.
"""
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch
import pytest
import pytest_asyncio
from datetime import datetime

# Mock Google ADK framework before importing any tools modules
@pytest.fixture(autouse=True)
def mock_google_adk(monkeypatch):
    """Mock Google ADK framework imports."""
    mock_adk = MagicMock()
    mock_tools = MagicMock()

    # Create mock classes
    mock_agent_tool = MagicMock()
    mock_agent_tool.AgentTool = type('AgentTool', (), {})
    mock_tool_context = MagicMock()
    mock_function_calling = MagicMock()

    mock_tools.agent_tool = mock_agent_tool
    mock_tools.tool_context = mock_tool_context
    mock_tools.function_calling = mock_function_calling

    monkeypatch.setitem(sys.modules, "google.adk", mock_adk)
    monkeypatch.setitem(sys.modules, "google.adk.tools", mock_tools)


@pytest.fixture
def mock_api_keys(monkeypatch):
    """Mock API keys for testing."""
    monkeypatch.setenv("BING_SEARCH_API_KEY", "test_bing_key_123")
    monkeypatch.setenv("UNSPLASH_ACCESS_KEY", "test_unsplash_key_123")
    monkeypatch.setenv("PEXELS_API_KEY", "test_pexels_key_123")
    monkeypatch.setenv("VECTOR_SEARCH_API_URL", "http://test-vector-api.example.com")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    return {
        "bing": "test_bing_key_123",
        "unsplash": "test_unsplash_key_123",
        "pexels": "test_pexels_key_123",
    }


@pytest.fixture
def mock_tool_context():
    """Mock tool context for testing."""
    context = MagicMock()
    context.agent_name = "test_agent"
    context.session_id = "test_session_123"
    context.user_id = "test_user_456"
    context.request_id = "test_request_789"
    return context


@pytest.fixture
def mock_httpx_client():
    """Mock HTTP client for API calls."""
    mock_client = AsyncMock()

    # Mock successful response
    success_response = Mock()
    success_response.status_code = 200
    success_response.json = AsyncMock(return_value={"result": "success"})
    success_response.text = '{"result": "success"}'
    success_response.raise_for_status = Mock()

    # Mock error response
    error_response = Mock()
    error_response.status_code = 500
    error_response.text = "Internal Server Error"
    error_response.raise_for_status = Mock(side_effect=Exception("HTTP 500"))

    mock_client.get.return_value = success_response
    mock_client.post.return_value = success_response

    return mock_client


@pytest.fixture
def mock_async_context_manager():
    """Create an async context manager for httpx.AsyncClient."""
    class MockAsyncContextManager:
        async def __aenter__(self):
            return AsyncMock()

        async def __aexit__(self, *args):
            pass

    return MockAsyncContextManager()


@pytest.fixture
def sample_tool_data():
    """Sample tool data for testing."""
    return {
        "query": "test search query",
        "num_results": 5,
        "url": "https://example.com",
        "topic": "test topic",
        "content": "test content",
    }


@pytest.fixture
def sample_slide_data():
    """Sample slide data for create_pptx testing."""
    return {
        "title": "Test Slide",
        "content": [{"type": "text", "text": "Sample text"}],
        "layout": "TitleOnly",
        "notes": "Speaker notes",
    }


@pytest.fixture
def sample_presentation_data():
    """Sample presentation data."""
    return {
        "title": "Test Presentation",
        "slides": [
            {
                "title": "Slide 1",
                "content": [{"type": "text", "text": "Content 1"}],
                "layout": "TitleOnly",
            },
            {
                "title": "Slide 2",
                "content": [{"type": "text", "text": "Content 2"}],
                "layout": "TitleAndBody",
            },
        ],
    }


@pytest.fixture
def tmp_path_with_files(tmp_path):
    """Create temporary path with sample files."""
    # Create a sample markdown file
    md_file = tmp_path / "sample_skill.md"
    md_file.write_text(
        """# Sample Skill

## Description
A sample skill for testing.

## Parameters
- param1: First parameter
- param2: Second parameter
"""
    )

    # Create a sample Python file
    py_file = tmp_path / "sample_skill.py"
    py_file.write_text(
        """from backend.agents.tools.skills.skill_decorator import skill

@skill(name="sample_skill", category="testing")
def sample_function(param1: str, param2: int) -> str:
    \"\"\"A sample skill function.\"\"\"
    return f"{param1}: {param2}"
"""
    )

    return tmp_path


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.exists = AsyncMock(return_value=0)
    redis.keys = AsyncMock(return_value=[])
    redis.dbsize = AsyncMock(return_value=0)
    redis.flushdb = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def mock_redis_pool(monkeypatch, mock_redis):
    """Mock Redis pool creation."""
    async def mock_create_pool(*args, **kwargs):
        return mock_redis

    monkeypatch.setattr("redis.asyncio.from_url", mock_create_pool)
    return mock_redis


@pytest.fixture
def sample_research_data():
    """Sample research data for ResearchSkill testing."""
    return {
        "topic": "Artificial Intelligence",
        "depth": "basic",
        "sources": ["source1", "source2"],
        "max_results": 3,
    }


@pytest.fixture
def sample_schedule_data():
    """Sample schedule data for SchedulerSkill testing."""
    return {
        "tasks": [
            {"id": "1", "name": "Task 1", "dependencies": []},
            {"id": "2", "name": "Task 2", "dependencies": ["1"]},
            {"id": "3", "name": "Task 3", "dependencies": ["1", "2"]},
        ],
        "max_parallel": 2,
    }


@pytest.fixture
def sample_retry_data():
    """Sample retry data for RetrySkill testing."""
    return {
        "func": AsyncMock(return_value="success"),
        "max_retries": 3,
        "base_delay": 0.1,
        "max_delay": 1.0,
    }


@pytest.fixture
def mock_vector_service():
    """Mock vector search service."""
    service = AsyncMock()
    service.search = AsyncMock(
        return_value=[
            {
                "id": "1",
                "score": 0.95,
                "metadata": {"title": "Result 1", "content": "Content 1"},
            },
            {
                "id": "2",
                "score": 0.85,
                "metadata": {"title": "Result 2", "content": "Content 2"},
            },
        ]
    )
    return service


@pytest.fixture
def mock_logger():
    """Mock logger."""
    logger = MagicMock()
    logger.info = Mock()
    logger.debug = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.exception = Mock()
    return logger


# Pytest async configuration
def pytest_configure(config):
    """Configure pytest for async tests."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as an asyncio test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )


@pytest.fixture
def event_loop_policy():
    """Event loop policy for async tests."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()
