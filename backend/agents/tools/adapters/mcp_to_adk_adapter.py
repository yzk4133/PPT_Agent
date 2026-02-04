"""
MCP to ADK Adapter Module

This module provides conversion from MCP tools to Google ADK AgentTool format.
It wraps MCP tool functions into a compatible interface for use with ADK Agents.
"""

from typing import Callable, Dict, Optional, Any
import json
import logging
import inspect

logger = logging.getLogger(__name__)

class MCPAgentTool:
    """
    MCP工具到ADK AgentTool的适配器

    This class wraps an MCP tool function to provide a compatible interface
    for Google ADK's Agent system.
    """

    def __init__(self, mcp_func: Callable, name: str, description: str, schema: Dict = None):
        """
        Initialize the MCPAgentTool adapter.

        Args:
            mcp_func: The MCP tool function to wrap
            name: Tool name
            description: Tool description
            schema: Optional parameter schema
        """
        self.mcp_func = mcp_func
        self._name = name
        self._description = description
        self._schema = schema or self._infer_schema(mcp_func)

    @property
    def name(self) -> str:
        """Get tool name"""
        return self._name

    @property
    def description(self) -> str:
        """Get tool description"""
        return self._description

    async def run(self, **kwargs) -> str:
        """
        执行MCP工具

        Args:
            **kwargs: Tool parameters

        Returns:
            JSON string result from MCP tool
        """
        try:
            result = await self.mcp_func(**kwargs)
            return result
        except Exception as e:
            logger.error(f"Error executing {self.name}: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    def _infer_schema(self, func: Callable) -> Dict:
        """
        从函数签名推断参数schema

        Args:
            func: Function to inspect

        Returns:
            Parameter schema dictionary
        """
        sig = inspect.signature(func)
        parameters = {}

        for param_name, param in sig.parameters.items():
            param_type = param.annotation if param.annotation != inspect.Parameter.empty else "string"
            parameters[param_name] = {
                "type": param_type,
                "description": f"Parameter {param_name}",
                "required": param.default == inspect.Parameter.empty
            }

        return {
            "type": "object",
            "properties": parameters
        }

def mcp_to_agent_tool(
    mcp_func: Callable,
    name: str,
    description: str,
    schema: Dict = None
) -> MCPAgentTool:
    """
    将MCP函数转换为AgentTool

    Args:
        mcp_func: MCP tool function
        name: Tool name
        description: Tool description
        schema: Optional parameter schema

    Returns:
        MCPAgentTool instance compatible with ADK
    """
    return MCPAgentTool(mcp_func, name, description, schema)

def mcp_to_agent_tools_batch(
    registrations: list
) -> list:
    """
    批量转换MCP工具注册为AgentTool列表

    Args:
        registrations: List of ToolRegistration objects

    Returns:
        List of MCPAgentTool instances
    """
    tools = []
    for registration in registrations:
        if registration.tool_func:
            tools.append(mcp_to_agent_tool(
                mcp_func=registration.tool_func,
                name=registration.metadata.name,
                description=registration.metadata.description
            ))
        elif registration.tool_class:
            # For tool classes, try to use them directly
            tools.append(registration.tool_class)
    return tools

if __name__ == "__main__":
    # 测试适配器
    import asyncio

    async def sample_mcp_tool(query: str) -> str:
        """Sample MCP tool for testing"""
        return json.dumps({
            "success": True,
            "result": f"Search results for: {query}"
        })

    adapter = mcp_to_agent_tool(
        mcp_func=sample_mcp_tool,
        name="search",
        description="Search tool"
    )

    print(f"Tool name: {adapter.name}")
    print(f"Tool description: {adapter.description}")

    # Test execution
    result = asyncio.run(adapter.run(query="test query"))
    print(f"Execution result: {result}")
