#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skill Framework - Skill Manager Module

This module provides the high-level API for working with Skills.
It wraps the SkillRegistry with a simpler, more developer-friendly interface.
"""

from typing import List, Dict, Any, Optional, Type, Callable

from google.adk.tools import BaseTool
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset

from ..core.skill_registry import SkillRegistry
from ..core.skill_metadata import SkillCategory, SkillMetadata, MarkdownSkillMetadata
from ..core.skill_wrapper import SkillWrapper


class SkillManager:
    """
    High-level API for managing Skills.

    This class provides a simplified interface for working with the Skill framework.
    It handles the singleton registry and provides convenient methods for common tasks.

    Usage:
        # Get or create the singleton instance
        skill_manager = SkillManager()

        # Get tools for an agent
        tools = skill_manager.get_tools_for_agent(
            agent_name="outline_agent",
            categories=[SkillCategory.DOCUMENT, SkillCategory.SEARCH]
        )

        # Create agent with tools
        agent = Agent(tools=tools, ...)
    """

    _instance: Optional["SkillManager"] = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: Optional[str] = None, auto_load: bool = True):
        """
        Initialize the Skill Manager.

        Args:
            config_path: Path to skill_config.json (optional)
            auto_load: Whether to auto-discover skills on init
        """
        if self._initialized:
            return

        self._registry = SkillRegistry(config_path=config_path, auto_load=auto_load)
        self._agent_mappings: Dict[str, Dict[str, Any]] = {}
        self._load_agent_mappings()

        self._initialized = True

    def _load_agent_mappings(self) -> None:
        """Load agent-skill mappings from configuration file"""
        import json
        import os

        mapping_path = "backend/agent_skill_mapping.json"
        if os.path.exists(mapping_path):
            try:
                with open(mapping_path, "r", encoding="utf-8") as f:
                    self._agent_mappings = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load agent mappings: {e}")

    @property
    def registry(self) -> SkillRegistry:
        """Get the underlying registry instance"""
        return self._registry

    def get_tools_for_agent(
        self,
        agent_name: Optional[str] = None,
        categories: Optional[List[SkillCategory]] = None,
        tags: Optional[List[str]] = None,
        skill_ids: Optional[List[str]] = None,
        include_mcp: bool = True,
    ) -> List[Any]:
        """
        Get ADK tools for an agent.

        This is the primary method used when creating agents.

        Args:
            agent_name: Optional agent name to load from config
            categories: List of categories to filter by
            tags: List of tags to filter by
            skill_ids: Specific skill IDs to include
            include_mcp: Whether to include MCP tools

        Returns:
            List of tools (async functions or BaseTool instances) ready for Agent

        Example:
            tools = skill_manager.get_tools_for_agent(
                agent_name="outline_agent",
                categories=[SkillCategory.DOCUMENT]
            )
        """
        # If agent_name is provided, load its configuration
        if agent_name:
            agent_config = self._agent_mappings.get(agent_name, {})
            if not categories and "categories" in agent_config:
                categories = [SkillCategory(c) for c in agent_config["categories"]]
            if not tags and "tags" in agent_config:
                tags = agent_config["tags"]
            if not skill_ids and "skill_ids" in agent_config:
                skill_ids = agent_config["skill_ids"]

        # Get tools from registry
        return self._registry.get_adk_tools(
            categories=categories,
            tags=tags,
            skill_ids=skill_ids,
            include_mcp=include_mcp,
        )

    def register_custom_skill(
        self,
        skill_class: Optional[Type] = None,
        skill_wrapper: Optional[SkillWrapper] = None,
    ) -> None:
        """
        Register a custom skill.

        Can be used as a decorator or direct method call.

        Args:
            skill_class: A class with @Skill decorator
            skill_wrapper: A SkillWrapper instance

        Example as decorator:
            @skill_manager.register_custom_skill
            class MySkill:
                ...

        Example as method call:
            skill_manager.register_custom_skill(skill_class=MySkill)
        """
        if skill_class is not None:
            self._registry.register_skill_class(skill_class)
        elif skill_wrapper is not None:
            self._registry.register_skill_wrapper(skill_wrapper)
        else:
            raise ValueError("Either skill_class or skill_wrapper must be provided")

        # Return the class if used as decorator
        return skill_class

    def register_mcp_tools(self, mcp_toolsets: List[MCPToolset], category: SkillCategory = SkillCategory.EXTERNAL) -> None:
        """
        Register MCP toolsets as skills.

        Args:
            mcp_toolsets: List of MCPToolset instances
            category: Category to assign to MCP tools

        Example:
            mcp_tools = load_mcp_tools("mcp_config.json")
            skill_manager.register_mcp_tools(mcp_tools)
        """
        for mcp_toolset in mcp_toolsets:
            self._registry.register_mcp_tool(mcp_toolset, category)

    def search_skills(
        self,
        query: Optional[str] = None,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        enabled_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Search for skills.

        Args:
            query: Keyword to search in name/description
            categories: List of category strings
            tags: List of tags to filter by
            enabled_only: Only return enabled skills

        Returns:
            List of skill info dictionaries

        Example:
            results = skill_manager.search_skills(
                query="document",
                tags=["search"]
            )
        """
        # Convert category strings to enums
        category_enums = None
        if categories:
            category_enums = []
            for cat in categories:
                try:
                    category_enums.append(SkillCategory(cat))
                except ValueError:
                    print(f"Warning: Invalid category {cat}, skipping")

        wrappers = self._registry.search_skills(
            categories=category_enums,
            tags=tags,
            enabled_only=enabled_only,
            keyword=query,
        )

        return [w.skill_metadata.to_dict() for w in wrappers]

    def get_skill_info(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a skill.

        Args:
            skill_id: The skill identifier

        Returns:
            Dictionary with skill information or None
        """
        return self._registry.get_skill_info(skill_id)

    def get_all_skills(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get all registered skills.

        Args:
            enabled_only: Only return enabled skills

        Returns:
            List of skill info dictionaries
        """
        return self._registry.list_skills(enabled_only=enabled_only)

    def get_categories(self) -> List[str]:
        """Get all available categories"""
        return [cat.value for cat in SkillCategory]

    def get_tags(self) -> List[str]:
        """Get all available tags"""
        return list(self._registry._tag_index.keys())

    def enable_skill(self, skill_id: str) -> bool:
        """
        Enable a skill.

        Args:
            skill_id: The skill identifier

        Returns:
            True if successful
        """
        return self._registry.enable_skill(skill_id)

    def disable_skill(self, skill_id: str) -> bool:
        """
        Disable a skill.

        Args:
            skill_id: The skill identifier

        Returns:
            True if successful
        """
        return self._registry.disable_skill(skill_id)

    def reload_skills(self) -> None:
        """Reload all skills from configured directories"""
        self._registry.reload()
        self._load_agent_mappings()

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about registered skills"""
        return self._registry.get_stats()

    def list_agents(self) -> List[str]:
        """Get list of configured agent names"""
        return list(self._agent_mappings.keys())

    def get_agent_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific agent"""
        return self._agent_mappings.get(agent_name)

    # ===== New Methods for Hybrid Skill System =====

    def get_descriptive_content_for_prompt(
        self,
        agent_name: Optional[str] = None,
        categories: Optional[List[SkillCategory]] = None,
        tags: Optional[List[str]] = None,
        skill_ids: Optional[List[str]] = None,
    ) -> str:
        """
        Get formatted descriptive skill content for injection into system prompt.

        Args:
            agent_name: Optional agent name to load from config
            categories: Filter by categories
            tags: Filter by tags
            skill_ids: Specific skill IDs to include

        Returns:
            Formatted string with all descriptive skill content

        Example:
            content = skill_manager.get_descriptive_content_for_prompt(
                agent_name="research_agent",
                categories=[SkillCategory.SEARCH]
            )
            instruction = "You are a research assistant.\\n\\n" + content
        """
        # Load from agent config if agent_name provided
        if agent_name:
            agent_config = self._agent_mappings.get(agent_name, {})
            if not categories and "categories" in agent_config:
                categories = [SkillCategory(c) for c in agent_config["categories"]]
            if not tags and "tags" in agent_config:
                tags = agent_config["tags"]
            if not skill_ids and "skill_ids" in agent_config:
                skill_ids = agent_config["skill_ids"]

        # Get descriptive skills
        descriptive_metadata = self._registry.get_descriptive_skills(
            categories=categories,
            tags=tags,
            enabled_only=True,
        )

        # Filter by skill_ids if provided
        if skill_ids:
            descriptive_metadata = [m for m in descriptive_metadata if m.skill_id in skill_ids]

        # Build formatted content
        if not descriptive_metadata:
            return ""

        sections = []
        for metadata in descriptive_metadata:
            sections.append(metadata.get_content_for_prompt())

        return "\n\n---\n\n".join(sections)

    def get_skills_for_agent(
        self,
        agent_name: Optional[str] = None,
        categories: Optional[List[SkillCategory]] = None,
        tags: Optional[List[str]] = None,
        skill_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get both executable and descriptive skills for an agent.

        Args:
            agent_name: Optional agent name to load from config
            categories: Filter by categories
            tags: Filter by tags
            skill_ids: Specific skill IDs to include

        Returns:
            Dictionary with 'executable' (list of skill info) and 'descriptive' (list of skill info)

        Example:
            skills = skill_manager.get_skills_for_agent(
                agent_name="research_agent",
                categories=[SkillCategory.SEARCH, SkillCategory.DOCUMENT]
            )
            executable_skills = skills['executable']
            descriptive_skills = skills['descriptive']
        """
        # Load from agent config if agent_name provided
        if agent_name:
            agent_config = self._agent_mappings.get(agent_name, {})
            if not categories and "categories" in agent_config:
                categories = [SkillCategory(c) for c in agent_config["categories"]]
            if not tags and "tags" in agent_config:
                tags = agent_config["tags"]
            if not skill_ids and "skill_ids" in agent_config:
                skill_ids = agent_config["skill_ids"]

        return self._registry.get_skills_for_agent(
            agent_name=agent_name,
            categories=categories,
            tags=tags,
            skill_ids=skill_ids,
        )

    def get_all_descriptive_skills(
        self,
        categories: Optional[List[SkillCategory]] = None,
        tags: Optional[List[str]] = None,
        enabled_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get all descriptive skills.

        Args:
            categories: Filter by categories
            tags: Filter by tags
            enabled_only: Only return enabled skills

        Returns:
            List of skill info dictionaries
        """
        metadata_list = self._registry.get_descriptive_skills(
            categories=categories,
            tags=tags,
            enabled_only=enabled_only,
        )

        return [m.to_dict() for m in metadata_list]

    def get_descriptive_skill_info(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a descriptive skill.

        Args:
            skill_id: The skill identifier

        Returns:
            Dictionary with skill information or None
        """
        metadata = self._registry.get_descriptive_skill(skill_id)
        if metadata:
            return metadata.to_dict()
        return None


# Convenience function for quick access
def get_skill_manager(config_path: Optional[str] = None, auto_load: bool = True) -> SkillManager:
    """
    Get or create the SkillManager singleton.

    Args:
        config_path: Optional path to skill_config.json
        auto_load: Whether to auto-discover skills

    Returns:
        SkillManager instance
    """
    return SkillManager(config_path=config_path, auto_load=auto_load)
