"""
Mock tools for testing.
"""
from typing import Any, Dict
from unittest.mock import AsyncMock
from backend.agents.tools.registry.unified_registry import ToolCategory


class MockTool:
    """Mock tool class for testing."""

    def __init__(self, name: str, category: ToolCategory = ToolCategory.UTILITY):
        self.name = name
        self.category = category
        self.enabled = True
        self.call_count = 0

    async def __call__(self, *args, **kwargs) -> Dict[str, Any]:
        self.call_count += 1
        return {"result": f"MockTool {self.name} called", "count": self.call_count}


class MockMCPTool:
    """Mock MCP tool for testing."""

    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.execution_count = 0
        self.error_count = 0

    async def execute(self, **kwargs) -> Dict[str, Any]:
        self.execution_count += 1
        return {
            "success": True,
            "result": f"MockMCPTool {self.name} executed",
            "execution_count": self.execution_count,
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
        }

    def reset_stats(self):
        self.execution_count = 0
        self.error_count = 0


class MockFailingTool:
    """Mock tool that always fails for error testing."""

    def __init__(self, name: str, error_message: str = "Mock tool failed"):
        self.name = name
        self.error_message = error_message
        self.enabled = True

    async def __call__(self, *args, **kwargs) -> Dict[str, Any]:
        raise Exception(self.error_message)


class MockSlowTool:
    """Mock tool with simulated delay for performance testing."""

    import asyncio

    def __init__(self, name: str, delay: float = 0.1):
        self.name = name
        self.delay = delay
        self.enabled = True

    async def __call__(self, *args, **kwargs) -> Dict[str, Any]:
        await self.asyncio.sleep(self.delay)
        return {"result": f"MockSlowTool {self.name} completed"}


# Sample tool functions for registration testing
def sample_tool_function(query: str, num_results: int = 5) -> Dict[str, Any]:
    """Sample tool function for testing."""
    return {
        "query": query,
        "results": [f"Result {i}" for i in range(num_results)],
        "count": num_results,
    }


async def async_sample_tool_function(url: str) -> Dict[str, Any]:
    """Async sample tool function for testing."""
    return {"url": url, "content": f"Content from {url}"}


def error_tool_function() -> Dict[str, Any]:
    """Tool function that raises an error."""
    raise ValueError("This tool always fails")


# Mock tool metadata
SAMPLE_TOOL_METADATA = {
    "name": "sample_tool",
    "description": "A sample tool for testing",
    "category": ToolCategory.UTILITY,
    "parameters": {
        "query": {
            "type": "string",
            "description": "Search query",
            "required": True,
        },
        "num_results": {
            "type": "integer",
            "description": "Number of results",
            "default": 5,
        },
    },
}

SAMPLE_MCP_TOOL_METADATA = {
    "name": "sample_mcp_tool",
    "description": "A sample MCP tool",
    "category": ToolCategory.SEARCH,
    "parameters": {
        "url": {"type": "string", "description": "URL to process", "required": True}
    },
}
