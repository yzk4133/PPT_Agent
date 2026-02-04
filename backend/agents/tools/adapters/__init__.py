"""
Adapters Module

Provides adapters for converting between different tool formats.
"""

from .mcp_to_adk_adapter import (
    MCPAgentTool,
    mcp_to_agent_tool,
    mcp_to_agent_tools_batch
)

__all__ = [
    "MCPAgentTool",
    "mcp_to_agent_tool",
    "mcp_to_agent_tools_batch"
]
