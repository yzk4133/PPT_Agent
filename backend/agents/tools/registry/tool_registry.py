"""
Tool Registry

工具注册中心，用于管理所有可用的工具
"""

from typing import Dict, List, Any, Callable, Optional, Type
from dataclasses import dataclass
from enum import Enum


class ToolCategory(str, Enum):
    """工具类别"""
    SEARCH = "search"
    MEDIA = "media"
    DATABASE = "database"
    VECTOR = "vector"
    UTILITY = "utility"
    MCP = "mcp"


@dataclass
class ToolMetadata:
    """
    工具元数据

    Attributes:
        name: 工具名称
        category: 工具类别
        description: 工具描述
        version: 工具版本
        author: 作者
        enabled: 是否启用
        parameters: 参数定义
    """

    name: str
    category: ToolCategory
    description: str
    version: str = "1.0.0"
    author: str = ""
    enabled: bool = True
    parameters: Dict[str, Any] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class ToolRegistration:
    """
    工具注册信息

    Attributes:
        metadata: 工具元数据
        tool_func: 工具函数
        tool_class: 工具类（可选）
    """

    metadata: ToolMetadata
    tool_func: Optional[Callable] = None
    tool_class: Optional[Type] = None


class ToolRegistry:
    """
    工具注册中心

    用于管理所有可用的工具，支持工具的注册、查询、调用等操作。
    """

    def __init__(self):
        """初始化工具注册中心"""
        self._tools: Dict[str, ToolRegistration] = {}
        self._categories: Dict[ToolCategory, List[str]] = {
            category: [] for category in ToolCategory
        }

    def register(
        self,
        metadata: ToolMetadata,
        tool_func: Optional[Callable] = None,
        tool_class: Optional[Type] = None
    ) -> None:
        """
        注册工具

        Args:
            metadata: 工具元数据
            tool_func: 工具函数
            tool_class: 工具类
        """
        registration = ToolRegistration(
            metadata=metadata,
            tool_func=tool_func,
            tool_class=tool_class
        )

        self._tools[metadata.name] = registration
        self._categories[metadata.category].append(metadata.name)

    def unregister(self, tool_name: str) -> bool:
        """
        注销工具

        Args:
            tool_name: 工具名称

        Returns:
            是否注销成功
        """
        if tool_name not in self._tools:
            return False

        registration = self._tools[tool_name]
        self._categories[registration.metadata.category].remove(tool_name)
        del self._tools[tool_name]
        return True

    def get_tool(self, tool_name: str) -> Optional[ToolRegistration]:
        """
        获取工具

        Args:
            tool_name: 工具名称

        Returns:
            工具注册信息，如果不存在则返回None
        """
        return self._tools.get(tool_name)

    def get_tools_by_category(
        self,
        category: ToolCategory
    ) -> List[ToolRegistration]:
        """
        根据类别获取工具

        Args:
            category: 工具类别

        Returns:
            工具注册信息列表
        """
        tool_names = self._categories.get(category, [])
        return [
            self._tools[name]
            for name in tool_names
            if name in self._tools
        ]

    def get_all_tools(self) -> Dict[str, ToolRegistration]:
        """
        获取所有工具

        Returns:
            所有工具的字典
        """
        return self._tools.copy()

    def get_enabled_tools(self) -> Dict[str, ToolRegistration]:
        """
        获取所有启用的工具

        Returns:
            启用工具的字典
        """
        return {
            name: registration
            for name, registration in self._tools.items()
            if registration.metadata.enabled
        }

    def enable_tool(self, tool_name: str) -> bool:
        """
        启用工具

        Args:
            tool_name: 工具名称

        Returns:
            是否成功
        """
        if tool_name not in self._tools:
            return False

        self._tools[tool_name].metadata.enabled = True
        return True

    def disable_tool(self, tool_name: str) -> bool:
        """
        禁用工具

        Args:
            tool_name: 工具名称

        Returns:
            是否成功
        """
        if tool_name not in self._tools:
            return False

        self._tools[tool_name].metadata.enabled = False
        return True

    def list_tools(
        self,
        category: Optional[ToolCategory] = None,
        enabled_only: bool = False
    ) -> List[str]:
        """
        列出工具名称

        Args:
            category: 工具类别（可选）
            enabled_only: 是否只列出启用的工具

        Returns:
            工具名称列表
        """
        if category:
            tools = self.get_tools_by_category(category)
        else:
            tools = list(self._tools.values())

        if enabled_only:
            tools = [t for t in tools if t.metadata.enabled]

        return [t.metadata.name for t in tools]

    def get_tool_count(self) -> int:
        """
        获取工具总数

        Returns:
            工具总数
        """
        return len(self._tools)


# 全局工具注册中心实例
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    获取全局工具注册中心实例

    Returns:
        ToolRegistry实例
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
        # 自动注册内置工具
        _register_builtin_tools(_global_registry)
    return _global_registry


def _register_builtin_tools(registry: ToolRegistry) -> None:
    """
    注册内置工具

    Args:
        registry: 工具注册中心
    """
    from ..search.document_search import DocumentSearch
    from ..media.image_search import SearchImage

    # 注册文档搜索工具
    registry.register(
        metadata=ToolMetadata(
            name="DocumentSearch",
            category=ToolCategory.SEARCH,
            description="根据关键词搜索文档资料",
            version="1.0.0",
            author="MultiAgentPPT"
        ),
        tool_func=DocumentSearch
    )

    # 注册图片搜索工具
    registry.register(
        metadata=ToolMetadata(
            name="SearchImage",
            category=ToolCategory.MEDIA,
            description="根据关键词搜索图片",
            version="1.0.0",
            author="MultiAgentPPT"
        ),
        tool_func=SearchImage
    )


# 便捷函数
def register_tool(
    name: str,
    category: ToolCategory,
    description: str,
    tool_func: Optional[Callable] = None,
    tool_class: Optional[Type] = None,
    **kwargs
) -> None:
    """
    注册工具的便捷函数

    Args:
        name: 工具名称
        category: 工具类别
        description: 工具描述
        tool_func: 工具函数
        tool_class: 工具类
        **kwargs: 其他元数据
    """
    registry = get_tool_registry()
    metadata = ToolMetadata(
        name=name,
        category=category,
        description=description,
        **kwargs
    )
    registry.register(metadata, tool_func, tool_class)


def get_tool(tool_name: str) -> Optional[ToolRegistration]:
    """
    获取工具的便捷函数

    Args:
        tool_name: 工具名称

    Returns:
        工具注册信息
    """
    return get_tool_registry().get_tool(tool_name)


def list_all_tools(enabled_only: bool = False) -> List[str]:
    """
    列出所有工具的便捷函数

    Args:
        enabled_only: 是否只列出启用的工具

    Returns:
        工具名称列表
    """
    return get_tool_registry().list_tools(enabled_only=enabled_only)


if __name__ == "__main__":
    # 测试代码
    registry = get_tool_registry()

    print(f"已注册工具总数: {registry.get_tool_count()}")
    print(f"所有工具: {registry.list_tools()}")
    print(f"搜索工具: {registry.list_tools(category=ToolCategory.SEARCH)}")
    print(f"媒体工具: {registry.list_tools(category=ToolCategory.MEDIA)}")
