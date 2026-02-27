"""
Pytest configuration and fixtures for LangChain agents tests
"""

import pytest
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


@pytest.fixture(scope="session")
def mock_env_vars():
    """Set up mock environment variables for testing"""
    original_env = os.environ.copy()

    # Set mock environment variables
    os.environ["OPENAI_API_KEY"] = "sk-test-key-for-testing"
    os.environ["LLM_MODEL"] = "gpt-4o-mini"
    os.environ["USE_AGENT_MEMORY"] = "false"  # Disable memory by default in tests

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def disable_memory():
    """Disable memory for specific tests"""
    import os
    os.environ["USE_AGENT_MEMORY"] = "false"
    yield
    os.environ["USE_AGENT_MEMORY"] = "true"


@pytest.fixture
def enable_memory():
    """Enable memory for specific tests"""
    import os
    os.environ["USE_AGENT_MEMORY"] = "true"
    yield
    os.environ["USE_AGENT_MEMORY"] = "false"
