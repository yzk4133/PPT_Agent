"""
Infrastructure MCP Module

统一MCP工具加载器，从slide_outline/load_mcp迁移而来
"""

import os
import json
import sys
from typing import List, Dict, Any, Optional

# 导入Google ADK的MCP工具
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StdioServerParameters,
    StdioConnectionParams,
    SseConnectionParams
)


def load_mcp_config_from_file(config_path: str = "mcp_config.json") -> Dict[str, Any]:
    """
    从JSON文件加载MCP配置

    Args:
        config_path: 配置文件路径

    Returns:
        包含配置的字典

    Raises:
        FileNotFoundError: 文件不存在
        json.JSONDecodeError: JSON格式错误
    """
    try:
        with open(config_path, "r", encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {config_path} not found.")
        raise
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {config_path}: {e}")
        raise


def load_mcp_tools(mcp_config_path: str) -> List[MCPToolset]:
    """
    加载MCP工具

    Args:
        mcp_config_path: MCP配置文件路径

    Returns:
        MCP工具集列表

    Raises:
        AssertionError: 配置文件不存在
        ValueError: 无效的MCP配置
    """
    assert os.path.exists(mcp_config_path), f"{mcp_config_path} 配置文件不存在，请检查"

    config = load_mcp_config_from_file(mcp_config_path)
    servers_cfg = config.get("mcpServers", {})
    mcp_tools = []

    for server_name, conf in servers_cfg.items():
        if "url" in conf:  # SSE server
            client = MCPToolset(
                connection_params=SseConnectionParams(
                    url=conf["url"],
                    timeout=60
                )
            )
        elif "command" in conf:  # Local process-based server
            client = MCPToolset(
                connection_params=StdioConnectionParams(
                    timeout=60,
                    server_params=StdioServerParameters(
                        command=conf.get("command"),
                        args=conf.get("args", []),
                        env=conf.get("env", {})
                    )
                )
            )
        else:
            raise ValueError(f"无效的MCP配置: {server_name}")

        mcp_tools.append(client)

    print(f"成功加载 {len(mcp_tools)} 个MCP工具")
    return mcp_tools


def load_mcp_tools_from_config(
    config: Dict[str, Any]
) -> List[MCPToolset]:
    """
    从配置字典加载MCP工具

    Args:
        config: MCP配置字典

    Returns:
        MCP工具集列表

    Raises:
        ValueError: 无效的MCP配置
    """
    servers_cfg = config.get("mcpServers", {})
    mcp_tools = []

    for server_name, conf in servers_cfg.items():
        if "url" in conf:  # SSE server
            client = MCPToolset(
                connection_params=SseConnectionParams(
                    url=conf["url"],
                    timeout=conf.get("timeout", 60)
                )
            )
        elif "command" in conf:  # Local process-based server
            client = MCPToolset(
                connection_params=StdioConnectionParams(
                    timeout=conf.get("timeout", 60),
                    server_params=StdioServerParameters(
                        command=conf.get("command"),
                        args=conf.get("args", []),
                        env=conf.get("env", {})
                    )
                )
            )
        else:
            raise ValueError(f"无效的MCP配置: {server_name}")

        mcp_tools.append(client)

    return mcp_tools


class MCPManager:
    """
    MCP管理器

    用于管理MCP工具的加载和生命周期。
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化MCP管理器

        Args:
            config_path: MCP配置文件路径（可选）
        """
        self.config_path = config_path
        self.tools: List[MCPToolset] = []

    def load_from_file(self, config_path: str) -> None:
        """
        从文件加载MCP工具

        Args:
            config_path: 配置文件路径
        """
        self.tools = load_mcp_tools(config_path)

    def load_from_config(self, config: Dict[str, Any]) -> None:
        """
        从配置字典加载MCP工具

        Args:
            config: MCP配置字典
        """
        self.tools = load_mcp_tools_from_config(config)

    def get_tools(self) -> List[MCPToolset]:
        """
        获取已加载的MCP工具

        Returns:
            MCP工具集列表
        """
        return self.tools

    def clear(self) -> None:
        """清空已加载的MCP工具"""
        self.tools.clear()


# 全局MCP管理器实例
_mcp_manager: Optional[MCPManager] = None


def get_mcp_manager() -> MCPManager:
    """
    获取全局MCP管理器实例

    Returns:
        MCPManager实例
    """
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPManager()
    return _mcp_manager


if __name__ == "__main__":
    # 测试MCP加载
    import sys
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = "mcp_config.json"

    tools = load_mcp_tools(config_path)
    print(f"Loaded {len(tools)} MCP tools")
