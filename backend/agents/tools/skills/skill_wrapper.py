#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skill Framework - Skill Wrapper Module

This module provides the adapter layer between Skills and Google ADK BaseTool.
It converts Skill classes and methods into ADK-compatible tools.
"""

import inspect
import functools
from typing import Any, Dict, List, Optional, Type, Callable

from google.adk.tools import BaseTool, ToolContext
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset

from .skill_metadata import SkillMetadata, SkillMethodMetadata, SkillCategory


class SkillAdapter:
    """
    Adapter to convert a Skill method into an ADK BaseTool.

    This class wraps a method from a Skill class and makes it compatible
    with Google ADK's tool system.
    """

    def __init__(
        self,
        skill_class: Type,
        method_name: str,
        skill_metadata: SkillMetadata,
        method_metadata: Optional[SkillMethodMetadata] = None,
    ):
        """
        Initialize the SkillAdapter.

        Args:
            skill_class: The Skill class containing the method
            method_name: Name of the method to adapt
            skill_metadata: Metadata for the parent Skill
            method_metadata: Optional metadata for the specific method
        """
        self.skill_class = skill_class
        self.method_name = method_name
        self.skill_metadata = skill_metadata
        self.method_metadata = method_metadata
        self._method = getattr(skill_class, method_name)
        self._skill_instance: Optional[Any] = None

    def _get_skill_instance(self) -> Any:
        """Get or create an instance of the Skill class"""
        if self._skill_instance is None:
            try:
                self._skill_instance = self.skill_class()
            except Exception as e:
                raise RuntimeError(
                    f"Failed to instantiate skill class {self.skill_class.__name__}: {e}"
                )
        return self._skill_instance

    async def _invoke_wrapper(self, **kwargs) -> Any:
        """
        Wrapper that invokes the skill method.

        This method extracts tool_context from kwargs if present,
        calls the skill method, and returns the result.
        """
        # Extract tool_context if present
        tool_context = kwargs.pop("tool_context", None)

        # Get skill instance
        skill_instance = self._get_skill_instance()

        # Call the method
        method = getattr(skill_instance, self.method_name)

        # Check if method is async
        if inspect.iscoroutinefunction(method):
            if tool_context is not None:
                result = await method(**kwargs, tool_context=tool_context)
            else:
                result = await method(**kwargs)
        else:
            if tool_context is not None:
                result = method(**kwargs, tool_context=tool_context)
            else:
                result = method(**kwargs)

        return result

    def get_adk_tool(self) -> Callable:
        """
        Create an ADK-compatible tool function from the skill method.

        Returns:
            An async function that can be passed to Agent
        """
        # Create tool name (combine skill_id and method name)
        tool_name = f"{self.skill_metadata.skill_id}_{self.method_name}"

        # Create description
        description = self.skill_metadata.description
        if self.method_metadata and self.method_metadata.description:
            description = self.method_metadata.description

        # Get method signature to create proper wrapper
        sig = inspect.signature(self._method)

        # Build parameter list for the wrapper
        params = []
        param_names = []
        for param_name, param in sig.parameters.items():
            param_names.append(param_name)

        # Create a wrapper function with proper signature
        async def tool_wrapper(**kwargs):
            """
            Wrapper function for the skill method.

            This function receives kwargs from ADK and forwards them to the skill method.
            """
            # Get skill instance
            skill_instance = self._get_skill_instance()

            # Get the method
            method = getattr(skill_instance, self.method_name)

            # Extract tool_context if present
            tool_context = kwargs.get("tool_context")

            # Call the method
            if inspect.iscoroutinefunction(method):
                if tool_context is not None:
                    result = await method(**kwargs)
                else:
                    result = await method(**kwargs)
            else:
                if tool_context is not None:
                    result = method(**kwargs)
                else:
                    result = method(**kwargs)

            return result

        # Set function metadata for ADK introspection
        tool_wrapper.__name__ = tool_name
        tool_wrapper.__doc__ = description
        tool_wrapper.__skill_metadata__ = self.skill_metadata
        tool_wrapper.__skill_method__ = self.method_name

        # Copy the signature from the original method
        try:
            tool_wrapper.__signature__ = sig
        except AttributeError:
            pass

        return tool_wrapper


class McpSkillAdapter:
    """
    Adapter to wrap MCP tools (MCPToolset) as Skills.

    This provides backward compatibility with existing MCP tools.
    """

    def __init__(self, mcp_toolset: MCPToolset, category: SkillCategory = SkillCategory.EXTERNAL):
        """
        Initialize the MCP Skill adapter.

        Args:
            mcp_toolset: The MCPToolset instance to wrap
            category: Category to assign to the MCP skill
        """
        self.mcp_toolset = mcp_toolset
        self.category = category

    def get_metadata(self) -> SkillMetadata:
        """Create SkillMetadata for the MCP toolset"""
        return SkillMetadata(
            skill_id=f"mcp_{id(self.mcp_toolset)}",
            name=f"MCP_{self.mcp_toolset.__class__.__name__}",
            version="1.0.0",
            category=self.category,
            tags=["mcp", "external"],
            description=f"MCP Toolset: {self.mcp_toolset.__class__.__name__}",
        )

    def get_adk_tools(self) -> List[Any]:
        """
        Get ADK tools from the MCP toolset.

        Returns:
            List of tool instances from the MCP server
        """
        # MCPToolset should provide access to its tools
        # This depends on the actual MCPToolset implementation
        try:
            # Try to get tools directly
            if hasattr(self.mcp_toolset, "get_tools"):
                return self.mcp_toolset.get_tools()
            elif hasattr(self.mcp_toolset, "tools"):
                return list(self.mcp_toolset.tools)
            else:
                # Return the toolset itself if it's already a BaseTool
                return [self.mcp_toolset]
        except Exception as e:
            print(f"Warning: Failed to get tools from MCP toolset: {e}")
            return []


class SkillWrapper:
    """
    Main wrapper class for managing Skills and converting them to ADK tools.

    This is the primary interface for working with Skills in the framework.
    """

    def __init__(self, skill_class: Type, skill_metadata: SkillMetadata):
        """
        Initialize the SkillWrapper.

        Args:
            skill_class: The Skill class to wrap
            skill_metadata: Metadata for the Skill
        """
        self.skill_class = skill_class
        self.skill_metadata = skill_metadata
        self._adapters: Dict[str, SkillAdapter] = {}

    def _discover_methods(self) -> Dict[str, Callable]:
        """
        Discover all public methods in the Skill class.

        Returns:
            Dictionary of method name to method
        """
        methods = {}

        for name in dir(self.skill_class):
            # Skip private methods
            if name.startswith("_"):
                continue

            method = getattr(self.skill_class, name)

            # Skip non-callable attributes
            if not callable(method):
                continue

            # Skip non-method functions
            if not inspect.isfunction(method) and not inspect.ismethod(method):
                continue

            # Skip the class methods we added
            if name in ["get_skill_metadata"]:
                continue

            methods[name] = method

        return methods

    def get_adk_tools(self) -> List[Callable]:
        """
        Convert all methods in the Skill to ADK tools.

        Returns:
            List of async callable functions
        """
        tools = []
        methods = self._discover_methods()

        for method_name, method in methods.items():
            # Check for method metadata
            method_metadata = None
            if hasattr(method, "__skill_method_metadata__"):
                meta = method.__skill_method_metadata__
                method_metadata = SkillMethodMetadata(
                    name=method_name,
                    description=meta.get("description", ""),
                    parameters=meta.get("parameters", {}),
                    examples=meta.get("examples", []),
                )

            # Create adapter
            adapter = SkillAdapter(
                skill_class=self.skill_class,
                method_name=method_name,
                skill_metadata=self.skill_metadata,
                method_metadata=method_metadata,
            )

            self._adapters[method_name] = adapter

            # Get ADK tool
            try:
                tool = adapter.get_adk_tool()
                tools.append(tool)
            except Exception as e:
                print(f"Warning: Failed to create tool for {method_name}: {e}")

        return tools

    def get_method_adapter(self, method_name: str) -> Optional[SkillAdapter]:
        """Get adapter for a specific method"""
        return self._adapters.get(method_name)
