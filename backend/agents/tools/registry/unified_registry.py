"""
Unified Tool and Skill Registry

This module provides a centralized registry for both tools and skills,
merging the functionality of tool_registry.py and skill_registry.py.
"""

from typing import Dict, List, Any, Callable, Optional, Type
from dataclasses import dataclass
from enum import Enum
import os
import json
from pathlib import Path


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


class UnifiedToolRegistry:
    """
    Unified Registry for both tools and skills.

    Merges functionality from tool_registry.py and skill_registry.py
    to provide a single source of truth for all agent-callable tools.
    """

    def __init__(self):
        """初始化统一工具注册中心"""
        self._tools: Dict[str, ToolRegistration] = {}
        self._categories: Dict[ToolCategory, List[str]] = {
            category: [] for category in ToolCategory
        }
        self._skill_wrappers: Dict[str, Any] = {}  # For skill framework integration

    def register(
        self,
        metadata: ToolMetadata,
        tool_func: Optional[Callable] = None,
        tool_class: Optional[Type] = None
    ) -> None:
        """
        注册工具或技能

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

    def register_skill_wrapper(self, wrapper: Any) -> None:
        """
        Register a skill wrapper from the skills framework.

        Args:
            wrapper: SkillWrapper instance from skills framework
        """
        skill_id = wrapper.skill_metadata.skill_id

        # Check for duplicates
        if skill_id in self._skill_wrappers:
            print(f"Warning: Skill {skill_id} already registered, skipping")
            return

        # Register skill
        self._skill_wrappers[skill_id] = wrapper

        # Also register as a tool for unified access
        self.register(
            metadata=ToolMetadata(
                name=skill_id,
                category=ToolCategory.UTILITY,
                description=wrapper.skill_metadata.description,
                version=wrapper.skill_metadata.version,
                author=wrapper.skill_metadata.author or "",
            ),
            tool_class=wrapper
        )

        print(f"Registered skill as tool: {skill_id} ({wrapper.skill_metadata.name})")

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

        # Also remove from skills if present
        if tool_name in self._skill_wrappers:
            del self._skill_wrappers[tool_name]

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

    def get_skill_wrapper(self, skill_id: str) -> Optional[Any]:
        """
        Get a skill wrapper by ID.

        Args:
            skill_id: The skill identifier

        Returns:
            SkillWrapper or None if not found
        """
        return self._skill_wrappers.get(skill_id)

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

    def get_all_skills(self) -> Dict[str, Any]:
        """Get all registered skill wrappers"""
        return self._skill_wrappers.copy()

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
        enabled_only: bool = False,
        include_skills: bool = True
    ) -> List[str]:
        """
        列出工具名称

        Args:
            category: 工具类别（可选）
            enabled_only: 是否只列出启用的工具
            include_skills: 是否包含技能

        Returns:
            工具名称列表
        """
        if category:
            tools = self.get_tools_by_category(category)
        else:
            tools = list(self._tools.values())

        if enabled_only:
            tools = [t for t in tools if t.metadata.enabled]

        result = [t.metadata.name for t in tools]

        # Add skills if requested
        if include_skills:
            result.extend(list(self._skill_wrappers.keys()))

        return list(set(result))  # Remove duplicates

    def get_tool_count(self) -> int:
        """
        获取工具总数

        Returns:
            工具总数
        """
        return len(self._tools)

    def get_skill_count(self) -> int:
        """
        Get total skill count

        Returns:
            Number of registered skills
        """
        return len(self._skill_wrappers)

    def get_adk_tools(
        self,
        categories: Optional[List[ToolCategory]] = None,
        tool_names: Optional[List[str]] = None,
        include_skills: bool = True,
    ) -> List[Any]:
        """
        Get ADK tools matching the given criteria.

        Args:
            categories: Filter by categories
            tool_names: Specific tool names to include
            include_skills: Whether to include skills

        Returns:
            List of tools ready for use with Agent
        """
        tools = []

        # Get matching tools
        if tool_names:
            registrations = [self._tools[name] for name in tool_names if name in self._tools]
        elif categories:
            registrations = []
            for category in categories:
                registrations.extend(self.get_tools_by_category(category))
        else:
            registrations = list(self._tools.values())

        # Extract tool functions and classes
        for registration in registrations:
            if registration.tool_func:
                tools.append(registration.tool_func)
            elif registration.tool_class:
                tools.append(registration.tool_class)

        # Add skills if requested
        if include_skills:
            for wrapper in self._skill_wrappers.values():
                try:
                    skill_tools = wrapper.get_adk_tools()
                    tools.extend(skill_tools)
                except Exception as e:
                    print(f"Warning: Failed to get tools for skill: {e}")

        return tools

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        return {
            "total_tools": len(self._tools),
            "total_skills": len(self._skill_wrappers),
            "enabled_tools": sum(1 for t in self._tools.values() if t.metadata.enabled),
            "categories": {cat.value: len(names) for cat, names in self._categories.items()},
        }


# Global registry instance
_global_registry: Optional[UnifiedToolRegistry] = None


def get_unified_registry() -> UnifiedToolRegistry:
    """
    获取全局统一工具注册中心实例

    Returns:
        UnifiedToolRegistry实例
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = UnifiedToolRegistry()
        # Auto-register built-in tools
        _register_builtin_tools(_global_registry)
    return _global_registry


def _register_builtin_tools(registry: UnifiedToolRegistry) -> None:
    """
    注册内置工具

    Args:
        registry: 工具注册中心
    """
    try:
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
    except ImportError as e:
        print(f"Warning: Could not import built-in tools: {e}")


# Convenience functions
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
    registry = get_unified_registry()
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
    return get_unified_registry().get_tool(tool_name)


def list_all_tools(enabled_only: bool = False) -> List[str]:
    """
    列出所有工具的便捷函数

    Args:
        enabled_only: 是否只列出启用的工具

    Returns:
        工具名称列表
    """
    return get_unified_registry().list_tools(enabled_only=enabled_only)


if __name__ == "__main__":
    # 测试代码
    registry = get_unified_registry()

    print(f"已注册工具总数: {registry.get_tool_count()}")
    print(f"已注册技能总数: {registry.get_skill_count()}")
    print(f"所有工具: {registry.list_tools()}")
    print(f"搜索工具: {registry.list_tools(category=ToolCategory.SEARCH)}")
    print(f"媒体工具: {registry.list_tools(category=ToolCategory.MEDIA)}")
    print(f"统计信息: {registry.get_stats()}")
