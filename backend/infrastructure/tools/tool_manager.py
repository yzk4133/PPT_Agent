"""
统一工具管理器

支持：
- 原生 ADK 工具（AgentTool）
- MCP 工具（SSE/Stdio）
- 工具健康检查
- 工具发现和注册
- 线程安全的工具访问
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from threading import Lock
from dataclasses import dataclass
from enum import Enum

from google.adk.tools import AgentTool

from ..config.common_config import get_config


logger = logging.getLogger(__name__)


class ToolType(str, Enum):
    """工具类型"""

    NATIVE = "native"  # 原生 ADK 工具
    MCP_SSE = "mcp_sse"  # MCP SSE 工具
    MCP_STDIO = "mcp_stdio"  # MCP Stdio 工具


@dataclass
class ToolInfo:
    """工具信息"""

    name: str
    tool_type: ToolType
    tool_instance: Any
    description: Optional[str] = None
    is_healthy: bool = True
    health_check_url: Optional[str] = None


class UnifiedToolManager:
    """统一工具管理器"""

    def __init__(self):
        self.config = get_config()
        self._tools: Dict[str, ToolInfo] = {}
        self._lock = Lock()  # 线程安全锁
        self._initialized = False

    def initialize(self):
        """
        初始化工具管理器（启动时调用）

        注意：此方法确保线程安全，只在服务启动时调用一次
        """
        with self._lock:
            if self._initialized:
                logger.warning("ToolManager already initialized")
                return

            logger.info("Initializing UnifiedToolManager...")

            # 自动发现和注册工具
            self._discover_tools()

            self._initialized = True
            logger.info(f"ToolManager initialized with {len(self._tools)} tools")

    def _discover_tools(self):
        """
        自动发现可用工具

        扫描规则：
        1. backend/tools/ 目录下的 Python 文件
        2. 读取 MCP 配置文件
        """
        # TODO: 实现工具自动发现
        # 当前为占位符，后续实现时取消注释
        logger.debug("Tool discovery not implemented yet")
        pass

    def register_native_tool(
        self,
        tool: AgentTool,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """
        注册原生 ADK 工具

        Args:
            tool: AgentTool 实例
            name: 工具名称（可选，默认使用 tool.name）
            description: 工具描述
        """
        tool_name = name or getattr(tool, "name", tool.__class__.__name__)

        with self._lock:
            if tool_name in self._tools:
                logger.warning(f"Tool {tool_name} already registered, overwriting")

            self._tools[tool_name] = ToolInfo(
                name=tool_name,
                tool_type=ToolType.NATIVE,
                tool_instance=tool,
                description=description or getattr(tool, "description", None),
                is_healthy=True,
            )

            logger.info(f"Registered native tool: {tool_name}")

    def register_mcp_tool(
        self,
        name: str,
        mcp_client: Any,
        tool_type: ToolType = ToolType.MCP_SSE,
        health_check_url: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """
        注册 MCP 工具

        Args:
            name: 工具名称
            mcp_client: MCP 客户端实例
            tool_type: MCP 工具类型（SSE 或 Stdio）
            health_check_url: 健康检查 URL（仅 SSE 模式）
            description: 工具描述
        """
        with self._lock:
            if name in self._tools:
                logger.warning(f"Tool {name} already registered, overwriting")

            self._tools[name] = ToolInfo(
                name=name,
                tool_type=tool_type,
                tool_instance=mcp_client,
                description=description,
                is_healthy=True,
                health_check_url=health_check_url,
            )

            logger.info(f"Registered MCP tool: {name} ({tool_type.value})")

    def get_tool(self, name: str) -> Optional[Any]:
        """
        获取工具实例

        Args:
            name: 工具名称

        Returns:
            工具实例，不存在返回 None
        """
        with self._lock:
            tool_info = self._tools.get(name)
            if tool_info and tool_info.is_healthy:
                return tool_info.tool_instance
            elif tool_info and not tool_info.is_healthy:
                logger.warning(f"Tool {name} is unhealthy")
            return None

    def get_tools_by_type(self, tool_type: ToolType) -> List[Any]:
        """
        获取指定类型的所有工具

        Args:
            tool_type: 工具类型

        Returns:
            工具实例列表
        """
        with self._lock:
            return [
                info.tool_instance
                for info in self._tools.values()
                if info.tool_type == tool_type and info.is_healthy
            ]

    def get_all_tools(self, only_healthy: bool = True) -> List[Any]:
        """
        获取所有工具

        Args:
            only_healthy: 是否只返回健康的工具

        Returns:
            工具实例列表
        """
        with self._lock:
            if only_healthy:
                return [
                    info.tool_instance
                    for info in self._tools.values()
                    if info.is_healthy
                ]
            else:
                return [info.tool_instance for info in self._tools.values()]

    def get_tool_info(self, name: str) -> Optional[ToolInfo]:
        """
        获取工具信息

        Args:
            name: 工具名称

        Returns:
            ToolInfo 或 None
        """
        with self._lock:
            return self._tools.get(name)

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有已注册的工具

        Returns:
            工具信息字典
        """
        with self._lock:
            return {
                name: {
                    "type": info.tool_type.value,
                    "description": info.description,
                    "is_healthy": info.is_healthy,
                    "health_check_url": info.health_check_url,
                }
                for name, info in self._tools.items()
            }

    async def health_check(self, tool_name: Optional[str] = None) -> Dict[str, bool]:
        """
        健康检查

        Args:
            tool_name: 特定工具名称，None 表示检查所有

        Returns:
            工具健康状态字典 {tool_name: is_healthy}
        """
        results = {}

        tools_to_check = [tool_name] if tool_name else list(self._tools.keys())

        for name in tools_to_check:
            with self._lock:
                tool_info = self._tools.get(name)

            if not tool_info:
                results[name] = False
                continue

            # Native 工具默认健康
            if tool_info.tool_type == ToolType.NATIVE:
                results[name] = True
                continue

            # MCP SSE 工具：检查 URL
            if tool_info.tool_type == ToolType.MCP_SSE and tool_info.health_check_url:
                try:
                    import httpx

                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(tool_info.health_check_url)
                        is_healthy = response.status_code == 200
                        results[name] = is_healthy

                        # 更新健康状态
                        with self._lock:
                            self._tools[name].is_healthy = is_healthy
                except Exception as e:
                    logger.error(f"Health check failed for {name}: {e}")
                    results[name] = False
                    with self._lock:
                        self._tools[name].is_healthy = False
            else:
                # MCP Stdio 或无健康检查 URL：默认健康
                results[name] = True

        return results

    def unregister_tool(self, name: str) -> bool:
        """
        注销工具

        Args:
            name: 工具名称

        Returns:
            是否成功注销
        """
        with self._lock:
            if name in self._tools:
                del self._tools[name]
                logger.info(f"Unregistered tool: {name}")
                return True
            return False

    def clear_all_tools(self):
        """清除所有工具（谨慎使用）"""
        with self._lock:
            self._tools.clear()
            self._initialized = False
            logger.warning("All tools cleared")


# 全局工具管理器实例
_tool_manager_instance: Optional[UnifiedToolManager] = None
_init_lock = Lock()


def get_tool_manager() -> UnifiedToolManager:
    """
    获取全局工具管理器实例（单例）

    注意：首次调用时会自动初始化
    """
    global _tool_manager_instance

    with _init_lock:
        if _tool_manager_instance is None:
            _tool_manager_instance = UnifiedToolManager()
            # 自动初始化（仅在首次创建时）
            if not _tool_manager_instance._initialized:
                _tool_manager_instance.initialize()

    return _tool_manager_instance


if __name__ == "__main__":
    # 测试工具管理器
    import asyncio

    logging.basicConfig(level=logging.INFO)

    manager = get_tool_manager()

    # 模拟注册工具
    class DummyTool(AgentTool):
        name = "DummyTool"
        description = "A test tool"

    manager.register_native_tool(DummyTool(), description="Test tool")

    # 列出工具
    print("\n📋 Registered tools:")
    for name, info in manager.list_tools().items():
        print(f"  - {name}: {info['type']} (healthy: {info['is_healthy']})")

    # 健康检查
    print("\n🏥 Health check:")
    health_results = asyncio.run(manager.health_check())
    for name, is_healthy in health_results.items():
        status = "✅" if is_healthy else "❌"
        print(f"  {status} {name}")
