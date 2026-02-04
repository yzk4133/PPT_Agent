#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skill Framework - Skill Registry Module

This module provides the central registry for managing all Skills.
It handles discovery, registration, and retrieval of Skills.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Type

from google.adk.tools import BaseTool
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset

from .skill_metadata import SkillMetadata, SkillCategory, MarkdownSkillMetadata
from .skill_wrapper import SkillWrapper, McpSkillAdapter
from .skill_loaders import CompositeSkillLoader

class SkillRegistry:
    """
    Central registry for managing all Skills.

    The registry is responsible for:
    - Auto-discovering and loading Skills
    - Maintaining skill metadata
    - Converting Skills to ADK tools
    - Providing search and filter capabilities
    """

    _instance: Optional["SkillRegistry"] = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one registry exists"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: Optional[str] = None, auto_load: bool = True):
        """
        Initialize the Skill Registry.

        Args:
            config_path: Path to skill_config.json
            auto_load: Whether to auto-discover and load skills on init
        """
        if self._initialized:
            return

        self._skills: Dict[str, SkillWrapper] = {}  # skill_id -> SkillWrapper (executable)
        self._descriptive_skills: Dict[str, MarkdownSkillMetadata] = {}  # skill_id -> MarkdownSkillMetadata
        self._mcp_tools: List[McpSkillAdapter] = []  # MCP tool adapters
        self._category_index: Dict[SkillCategory, List[str]] = {}  # category -> [skill_ids]
        self._tag_index: Dict[str, List[str]] = {}  # tag -> [skill_ids]

        # Load configuration
        self.config = self._load_config(config_path)

        # Initialize loader
        self.loader = CompositeSkillLoader(self.config)

        # Auto-load if enabled
        if auto_load and self.config.get("auto_discovery", True):
            self.discover_skills()

        self._initialized = True

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            "skill_directories": ["backend/skills"],
            "config_directory": "backend/skills/configs",
            "auto_discovery": True,
            "cache_enabled": True,
        }

        if config_path is None:
            # Try default location
            config_path = "backend/skill_config.json"

        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Failed to load skill config from {config_path}: {e}")

        return default_config

    def discover_skills(self) -> Dict[str, int]:
        """
        Auto-discover and load all Skills from configured directories.

        Returns:
            Dictionary with counts of loaded skills
        """
        loaded = self.loader.load_all()

        executable_count = 0
        descriptive_count = 0

        # Register executable skills
        for wrapper in loaded.get("executable", []):
            self.register_skill_wrapper(wrapper)
            executable_count += 1

        # Register descriptive skills
        for metadata in loaded.get("descriptive", []):
            self.register_markdown_skill(metadata)
            descriptive_count += 1

        return {
            "executable": executable_count,
            "descriptive": descriptive_count,
            "total": executable_count + descriptive_count,
        }

    def register_skill_wrapper(self, wrapper: SkillWrapper) -> None:
        """
        Register a SkillWrapper.

        Args:
            wrapper: SkillWrapper instance to register
        """
        skill_id = wrapper.skill_metadata.skill_id

        # Check for duplicates
        if skill_id in self._skills:
            print(f"Warning: Skill {skill_id} already registered, skipping")
            return

        # Register
        self._skills[skill_id] = wrapper

        # Update indexes
        category = wrapper.skill_metadata.category
        if category not in self._category_index:
            self._category_index[category] = []
        self._category_index[category].append(skill_id)

        for tag in wrapper.skill_metadata.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            if skill_id not in self._tag_index[tag]:
                self._tag_index[tag].append(skill_id)

        print(f"Registered skill: {skill_id} ({wrapper.skill_metadata.name})")

    def register_skill_class(self, skill_class: Type) -> None:
        """
        Register a Skill class directly.

        The class must have the @Skill decorator.

        Args:
            skill_class: A class with __skill_metadata__ attribute
        """
        if not hasattr(skill_class, "__skill_metadata__"):
            raise ValueError(f"Class {skill_class.__name__} is not a valid Skill")

        metadata = skill_class.get_skill_metadata()
        wrapper = SkillWrapper(skill_class, metadata)
        self.register_skill_wrapper(wrapper)

    def register_markdown_skill(self, metadata: MarkdownSkillMetadata) -> None:
        """
        Register a Markdown-based descriptive skill.

        Args:
            metadata: MarkdownSkillMetadata instance
        """
        skill_id = metadata.skill_id

        # Check for duplicates
        if skill_id in self._descriptive_skills:
            print(f"Warning: Markdown skill {skill_id} already registered, skipping")
            return

        # Register
        self._descriptive_skills[skill_id] = metadata

        # Update indexes
        category = metadata.category
        if category not in self._category_index:
            self._category_index[category] = []
        if skill_id not in self._category_index[category]:
            self._category_index[category].append(skill_id)

        for tag in metadata.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            if skill_id not in self._tag_index[tag]:
                self._tag_index[tag].append(skill_id)

        print(f"Registered Markdown skill: {skill_id} ({metadata.name})")

    def get_descriptive_skill(self, skill_id: str) -> Optional[MarkdownSkillMetadata]:
        """
        Get a descriptive skill by ID.

        Args:
            skill_id: The skill identifier

        Returns:
            MarkdownSkillMetadata or None if not found
        """
        return self._descriptive_skills.get(skill_id)

    def get_descriptive_skills(
        self,
        categories: Optional[List[SkillCategory]] = None,
        tags: Optional[List[str]] = None,
        enabled_only: bool = True,
    ) -> List[MarkdownSkillMetadata]:
        """
        Get descriptive skills matching the given criteria.

        Args:
            categories: Filter by categories (any match)
            tags: Filter by tags (any match)
            enabled_only: Only return enabled skills

        Returns:
            List of MarkdownSkillMetadata instances
        """
        results = []

        for skill_id, metadata in self._descriptive_skills.items():
            # Check metadata matches
            if not metadata.matches_filter(categories, tags, enabled_only):
                continue

            results.append(metadata)

        return results

    def register_mcp_tool(self, mcp_toolset: MCPToolset, category: SkillCategory = SkillCategory.EXTERNAL) -> None:
        """
        Register an MCP toolset.

        Args:
            mcp_toolset: MCPToolset instance
            category: Category to assign to the MCP tool
        """
        adapter = McpSkillAdapter(mcp_toolset, category)
        self._mcp_tools.append(adapter)

    def get_skill(self, skill_id: str) -> Optional[SkillWrapper]:
        """
        Get a skill by ID.

        Args:
            skill_id: The skill identifier

        Returns:
            SkillWrapper or None if not found
        """
        return self._skills.get(skill_id)

    def get_all_skills(self) -> Dict[str, SkillWrapper]:
        """Get all registered skills"""
        return self._skills.copy()

    def get_skills_by_category(self, category: SkillCategory) -> List[SkillWrapper]:
        """
        Get all skills in a category.

        Args:
            category: The skill category

        Returns:
            List of SkillWrapper instances
        """
        skill_ids = self._category_index.get(category, [])
        return [self._skills[skill_id] for skill_id in skill_ids if skill_id in self._skills]

    def get_skills_by_tag(self, tag: str) -> List[SkillWrapper]:
        """
        Get all skills with a specific tag.

        Args:
            tag: The tag to search for

        Returns:
            List of SkillWrapper instances
        """
        skill_ids = self._tag_index.get(tag.lower(), [])
        return [self._skills[skill_id] for skill_id in skill_ids if skill_id in self._skills]

    def search_skills(
        self,
        categories: Optional[List[SkillCategory]] = None,
        tags: Optional[List[str]] = None,
        enabled_only: bool = True,
        keyword: Optional[str] = None,
    ) -> List[SkillWrapper]:
        """
        Search for skills matching the given criteria.

        Args:
            categories: Filter by categories (any match)
            tags: Filter by tags (any match)
            enabled_only: Only return enabled skills
            keyword: Search keyword in name/description

        Returns:
            List of matching SkillWrapper instances
        """
        results = []

        for skill_id, wrapper in self._skills.items():
            metadata = wrapper.skill_metadata

            # Check metadata matches
            if not metadata.matches_filter(categories, tags, enabled_only):
                continue

            # Check keyword search
            if keyword:
                keyword_lower = keyword.lower()
                if (
                    keyword_lower not in metadata.name.lower()
                    and keyword_lower not in metadata.description.lower()
                    and keyword_lower not in metadata.skill_id.lower()
                ):
                    continue

            results.append(wrapper)

        return results

    def get_adk_tools(
        self,
        categories: Optional[List[SkillCategory]] = None,
        tags: Optional[List[str]] = None,
        skill_ids: Optional[List[str]] = None,
        include_mcp: bool = True,
    ) -> List[Any]:
        """
        Get ADK tools matching the given criteria.

        Args:
            categories: Filter by categories
            tags: Filter by tags
            skill_ids: Specific skill IDs to include
            include_mcp: Whether to include MCP tools

        Returns:
            List of tools (async functions or BaseTool instances) ready for use with Agent
        """
        tools = []

        # Get matching skills
        if skill_ids:
            # Load specific skills
            wrappers = [self._skills[sid] for sid in skill_ids if sid in self._skills]
        else:
            # Search by criteria
            wrappers = self.search_skills(categories=categories, tags=tags, enabled_only=True)

        # Convert to ADK tools
        for wrapper in wrappers:
            try:
                skill_tools = wrapper.get_adk_tools()
                tools.extend(skill_tools)
            except Exception as e:
                print(f"Warning: Failed to get tools for {wrapper.skill_metadata.skill_id}: {e}")

        # Add MCP tools
        if include_mcp:
            for mcp_adapter in self._mcp_tools:
                try:
                    mcp_tools = mcp_adapter.get_adk_tools()
                    tools.extend(mcp_tools)
                except Exception as e:
                    print(f"Warning: Failed to get MCP tools: {e}")

        return tools

    def get_skill_info(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a skill.

        Args:
            skill_id: The skill identifier

        Returns:
            Dictionary with skill information or None
        """
        wrapper = self.get_skill(skill_id)
        if not wrapper:
            return None

        metadata = wrapper.skill_metadata
        info = metadata.to_dict()

        # Add method information
        info["methods"] = list(wrapper._discover_methods().keys())

        return info

    def list_skills(
        self,
        categories: Optional[List[SkillCategory]] = None,
        tags: Optional[List[str]] = None,
        enabled_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        List all skills matching criteria.

        Args:
            categories: Filter by categories
            tags: Filter by tags
            enabled_only: Only show enabled skills

        Returns:
            List of skill info dictionaries
        """
        wrappers = self.search_skills(
            categories=categories,
            tags=tags,
            enabled_only=enabled_only,
        )

        return [w.skill_metadata.to_dict() for w in wrappers]

    def enable_skill(self, skill_id: str) -> bool:
        """
        Enable a skill.

        Args:
            skill_id: The skill identifier

        Returns:
            True if successful, False otherwise
        """
        wrapper = self.get_skill(skill_id)
        if wrapper:
            wrapper.skill_metadata.enabled = True
            return True
        return False

    def disable_skill(self, skill_id: str) -> bool:
        """
        Disable a skill.

        Args:
            skill_id: The skill identifier

        Returns:
            True if successful, False otherwise
        """
        wrapper = self.get_skill(skill_id)
        if wrapper:
            wrapper.skill_metadata.enabled = False
            return True
        return False

    def reload(self) -> None:
        """Reload all skills from configured directories"""
        # Clear current registry
        self._skills.clear()
        self._descriptive_skills.clear()
        self._category_index.clear()
        self._tag_index.clear()

        # Reload config
        self.config = self._load_config(None)

        # Reinitialize loader
        self.loader = CompositeSkillLoader(self.config)

        # Discover skills again
        self.discover_skills()

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        return {
            "executable_skills": len(self._skills),
            "descriptive_skills": len(self._descriptive_skills),
            "total_skills": len(self._skills) + len(self._descriptive_skills),
            "enabled_executable": sum(1 for w in self._skills.values() if w.skill_metadata.enabled),
            "enabled_descriptive": sum(1 for m in self._descriptive_skills.values() if m.enabled),
            "mcp_tools": len(self._mcp_tools),
            "categories": {cat.value: len(sids) for cat, sids in self._category_index.items()},
            "total_tags": len(self._tag_index),
        }

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
            agent_name: Optional agent name (not currently used, for future mapping)
            categories: Filter by categories
            tags: Filter by tags
            skill_ids: Specific skill IDs to include

        Returns:
            Dictionary with 'executable' and 'descriptive' lists
        """
        result = {
            "executable": [],
            "descriptive": [],
        }

        # Get executable skills
        if skill_ids:
            wrappers = [self._skills[sid] for sid in skill_ids if sid in self._skills]
        else:
            wrappers = self.search_skills(
                categories=categories,
                tags=tags,
                enabled_only=True,
            )

        result["executable"] = [w.skill_metadata.to_dict() for w in wrappers]

        # Get descriptive skills
        descriptive_metadata = self.get_descriptive_skills(
            categories=categories,
            tags=tags,
            enabled_only=True,
        )

        # Filter by skill_ids if provided
        if skill_ids:
            descriptive_metadata = [m for m in descriptive_metadata if m.skill_id in skill_ids]

        result["descriptive"] = [m.to_dict() for m in descriptive_metadata]

        return result
