#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
技能框架 - MCP 集成模块

此模块提供 MCP (Model Context Protocol) 工具与技能框架之间的集成，
允许现有 MCP 工具作为技能进行管理。
"""

import os
import json
from typing import List, Dict, Any, Optional, Union, Callable

from google.adk.tools import BaseTool
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StdioServerParameters,
    StdioConnectionParams,
    SseConnectionParams,
)

from ..skills.skill_metadata import SkillCategory
from ..skills.skill_wrapper import McpSkillAdapter
from ..skills.managers.skill_manager import SkillManager


def load_mcp_config_from_file(config_path: str = "mcp_config.json") -> dict:
    """
    从 JSON 文件加载 MCP 配置。

    这是一个用于加载 MCP 服务器配置的实用函数。

    Args:
        config_path: MCP 配置文件路径

    Returns:
        包含配置的字典

    Raises:
        SystemExit: 如果文件未找到或包含无效 JSON
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误: {config_path} 未找到。")
        return {}
    except json.JSONDecodeError:
        print(f"错误: {config_path} 中的 JSON 无效。")
        return {}


def load_mcp_tools(
    mcp_config_path: str,
    skill_manager: Optional[SkillManager] = None,
    auto_register: bool = True,
) -> List[MCPToolset]:
    """
    从配置文件加载 MCP 工具。

    此函数读取 MCP 配置，并为每个配置的服务器创建 MCPToolset 实例。

    Args:
        mcp_config_path: mcp_config.json 路径
        skill_manager: 可选的 SkillManager，用于注册工具
        auto_register: 是否自动注册到 SkillManager

    Returns:
        MCPToolset 实例列表

    Example:
        mcp_tools = load_mcp_tools("mcp_config.json")
        tools = [tool for mcp_tool in mcp_tools for tool in mcp_tool.get_tools()]
    """
    if not os.path.exists(mcp_config_path):
        print(f"警告: {mcp_config_path} 未找到")
        return []

    config = load_mcp_config_from_file(mcp_config_path)
    servers_cfg = config.get("mcpServers", {})
    mcp_tools = []

    for server_name, conf in servers_cfg.items():
        try:
            if "url" in conf:  # SSE server
                client = MCPToolset(
                    connection_params=SseConnectionParams(
                        url=conf["url"], timeout=conf.get("timeout", 60)
                    )
                )
            elif "command" in conf:  # Local process-based server
                client = MCPToolset(
                    connection_params=StdioConnectionParams(
                        timeout=conf.get("timeout", 60),
                        server_params=StdioServerParameters(
                            command=conf.get("command"),
                            args=conf.get("args", []),
                            env=conf.get("env", {}),
                        ),
                    )
                )
            else:
                print(f"警告: {server_name} 的 MCP 配置无效")
                continue

            mcp_tools.append(client)
            print(f"已加载 MCP 工具: {server_name}")

        except Exception as e:
            print(f"警告: 加载 MCP 工具 {server_name} 失败: {e}")

    # Auto-register with skill manager if requested
    if auto_register and skill_manager:
        skill_manager.register_mcp_tools(mcp_tools)

    print(f"从 {mcp_config_path} 加载了 {len(mcp_tools)} 个 MCP 工具")
    return mcp_tools


def mcp_tools_to_skills(
    mcp_toolsets: List[MCPToolset],
    category: SkillCategory = SkillCategory.EXTERNAL,
) -> List[McpSkillAdapter]:
    """
    将 MCP 工具集转换为技能适配器。

    此函数包装现有 MCP 工具集，使其可以与原生技能一起管理。

    Args:
        mcp_toolsets: MCPToolset 实例列表
        category: 分配给 MCP 技能的类别

    Returns:
        McpSkillAdapter 实例列表

    Example:
        mcp_tools = load_mcp_tools("mcp_config.json")
        skill_adapters = mcp_tools_to_skills(mcp_tools)
    """
    adapters = []

    for mcp_toolset in mcp_toolsets:
        adapter = McpSkillAdapter(mcp_toolset, category=category)
        adapters.append(adapter)

    return adapters


def load_all_tools(
    mcp_config_path: str = "mcp_config.json",
    skill_config_path: str = "backend/skill_config.json",
    agent_name: Optional[str] = None,
    categories: Optional[List[SkillCategory]] = None,
    tags: Optional[List[str]] = None,
    include_mcp: bool = True,
) -> List[Any]:
    """
    为代理加载所有工具（技能 + MCP 工具）。

    这是一个便利函数，加载原生技能和 MCP 工具，并将它们作为统一列表返回。

    Args:
        mcp_config_path: mcp_config.json 路径
        skill_config_path: skill_config.json 路径
        agent_name: 可选代理名称用于过滤
        categories: 可选类别过滤
        tags: 可选标签过滤
        include_mcp: 是否包含 MCP 工具

    Returns:
        工具列表（异步函数或 BaseTool 实例），可用于 Agent

    Example:
        tools = load_all_tools(
            agent_name="outline_agent",
            categories=[SkillCategory.DOCUMENT, SkillCategory.SEARCH]
        )
        agent = Agent(tools=tools, ...)
    """
    # Initialize skill manager
    skill_manager = SkillManager(config_path=skill_config_path, auto_load=True)

    # Load MCP tools if config exists
    if include_mcp and os.path.exists(mcp_config_path):
        load_mcp_tools(mcp_config_path, skill_manager=skill_manager, auto_register=True)

    # Get tools for agent
    tools = skill_manager.get_tools_for_agent(
        agent_name=agent_name,
        categories=categories,
        tags=tags,
        include_mcp=include_mcp,
    )

    return tools


def get_mcp_tool_info(mcp_toolset: MCPToolset) -> Dict[str, Any]:
    """
    获取 MCP 工具集的信息。

    Args:
        mcp_toolset: MCPToolset 实例

    Returns:
        包含工具信息的字典
    """
    info = {
        "type": "mcp",
        "class": mcp_toolset.__class__.__name__,
    }

    # Try to get additional info
    if hasattr(mcp_toolset, "connection_params"):
        conn = mcp_toolset.connection_params
        info["connection_type"] = conn.__class__.__name__

        if hasattr(conn, "url"):
            info["url"] = conn.url
        elif hasattr(conn, "server_params"):
            sp = conn.server_params
            info["command"] = sp.command
            info["args"] = sp.args

    return info


# Backward compatibility with existing load_mcp.py code
# This allows existing code to work with minimal changes
def load_mcp_tools_legacy(mcp_config_path: str = "mcp_config.json") -> List:
    """
    向后兼容函数。

    此函数镜像 slide_outline/load_mcp.py 中的原始 load_mcp_tools 函数。
    """
    assert os.path.exists(mcp_config_path), f"{mcp_config_path} 配置文件未找到"

    config = load_mcp_config_from_file(mcp_config_path)
    servers_cfg = config.get("mcpServers", {})
    mcp_tools = []

    for server_name, conf in servers_cfg.items():
        if "url" in conf:  # SSE server
            client = MCPToolset(
                connection_params=SseConnectionParams(url=conf["url"], timeout=60)
            )
        elif "command" in conf:  # Local process-based server
            client = MCPToolset(
                connection_params=StdioConnectionParams(
                    timeout=60,
                    server_params=StdioServerParameters(
                        command=conf.get("command"),
                        args=conf.get("args", []),
                        env=conf.get("env", {}),
                    ),
                )
            )
        else:
            raise ValueError(f"MCP 配置无效: {server_name}")

        mcp_tools.append(client)

    print(f"加载了 {len(mcp_tools)} 个 MCP 工具")
    return mcp_tools
