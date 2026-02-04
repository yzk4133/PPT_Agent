"""
MCP Tool Auto-Discovery Module

This module provides automatic discovery and registration of MCP tools.
It scans the MCP directory for BaseMCPTool subclasses and registers them.
"""

import inspect
import logging
from pathlib import Path
from typing import List, Type

logger = logging.getLogger(__name__)

def discover_mcp_tools(mcp_dir: Path = None) -> List[Type]:
    """
    自动发现MCP工具类

    Args:
        mcp_dir: MCP工具目录路径，默认为当前模块所在目录

    Returns:
        发现的工具类列表
    """
    if mcp_dir is None:
        mcp_dir = Path(__file__).parent

    tools = []
    for py_file in mcp_dir.glob("*.py"):
        if py_file.name.startswith("_"):
            continue

        try:
            module_name = f"backend.agents.tools.mcp.{py_file.stem}"
            module = __import__(module_name, fromlist=[''])

            for name, obj in inspect.getmembers(module, inspect.isclass):
                # 查找继承自BaseMCPTool的类
                from .base_mcp_tool import BaseMCPTool
                if (issubclass(obj, BaseMCPTool) and
                    obj is not BaseMCPTool and
                    obj.__module__ == module_name):
                    tools.append(obj)
                    logger.debug(f"Discovered MCP tool class: {name}")
        except Exception as e:
            logger.warning(f"Failed to import {py_file}: {e}")

    return tools

def auto_register_tools(registry=None) -> int:
    """
    自动注册所有发现的MCP工具

    Args:
        registry: 工具注册中心实例，默认为全局注册中心

    Returns:
        成功注册的工具数量
    """
    if registry is None:
        from backend.agents.tools.registry.unified_registry import get_unified_registry
        registry = get_unified_registry()

    tool_classes = discover_mcp_tools()
    registered_count = 0

    for tool_class in tool_classes:
        try:
            instance = tool_class()

            async def wrapper(**kwargs):
                return await instance.execute(**kwargs)

            from backend.agents.tools.registry.unified_registry import ToolMetadata, ToolCategory
            registry.register(
                metadata=ToolMetadata(
                    name=instance.name,
                    category=ToolCategory.UTILITY,
                    description=instance.description or f"{instance.name} tool",
                    version="1.0.0",
                    author="MultiAgentPPT"
                ),
                tool_func=wrapper
            )
            logger.info(f"Auto-registered tool: {instance.name}")
            registered_count += 1
        except Exception as e:
            logger.error(f"Failed to register {tool_class.__name__}: {e}")

    logger.info(f"Auto-registered {registered_count}/{len(tool_classes)} MCP tools")
    return registered_count

if __name__ == "__main__":
    # 测试自动发现
    logging.basicConfig(level=logging.DEBUG)

    tools = discover_mcp_tools()
    print(f"Discovered {len(tools)} MCP tool classes:")
    for tool in tools:
        print(f"  - {tool.__name__}")
