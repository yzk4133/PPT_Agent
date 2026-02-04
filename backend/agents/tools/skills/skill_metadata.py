#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skill Framework - Core Metadata Module

This module defines the core data structures for the Skill framework,
including skill metadata, categories, and related enums.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional

class SkillCategory(Enum):
    """Categories for organizing skills"""

    DOCUMENT = "document"
    SEARCH = "search"
    GENERATION = "generation"
    ANALYSIS = "analysis"
    EXTERNAL = "external"
    UTILITY = "utility"
    COMMUNICATION = "communication"

@dataclass
class SkillMetadata:
    """
    Metadata for a Skill.

    Attributes:
        skill_id: Unique identifier for the skill (e.g., "document_search")
        name: Display name of the skill (e.g., "DocumentSearch")
        version: Semantic version string (e.g., "1.0.0")
        category: Primary category from SkillCategory enum
        tags: List of tags for filtering and discovery
        description: Human-readable description of what the skill does
        enabled: Whether the skill is currently enabled
        author: Optional author name
        dependencies: List of skill_ids this skill depends on
        parameters: Schema for tool parameters (for documentation)
        examples: List of usage examples
    """

    skill_id: str
    name: str
    version: str
    category: SkillCategory
    tags: List[str]
    description: str
    enabled: bool = True
    author: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Validate and normalize metadata after initialization"""
        # Ensure skill_id is a valid identifier
        if not self.skill_id or not isinstance(self.skill_id, str):
            raise ValueError("skill_id must be a non-empty string")

        # Normalize tags to lowercase
        if self.tags:
            self.tags = [tag.lower().strip() for tag in self.tags if tag]
        else:
            self.tags = []

    def matches_filter(
        self,
        categories: Optional[List[SkillCategory]] = None,
        tags: Optional[List[str]] = None,
        enabled_only: bool = False
    ) -> bool:
        """
        Check if this skill matches the given filter criteria.

        Args:
            categories: List of categories to match (any)
            tags: List of tags to match (any)
            enabled_only: Only return enabled skills

        Returns:
            True if the skill matches all criteria
        """
        if enabled_only and not self.enabled:
            return False

        if categories and self.category not in categories:
            return False

        if tags:
            normalized_tags = [tag.lower() for tag in tags]
            if not any(tag in self.tags for tag in normalized_tags):
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for serialization"""
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "version": self.version,
            "category": self.category.value,
            "tags": self.tags,
            "description": self.description,
            "enabled": self.enabled,
            "author": self.author,
            "dependencies": self.dependencies,
            "parameters": self.parameters,
            "examples": self.examples,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillMetadata":
        """Create metadata from dictionary (for JSON/YAML loading)"""
        # Convert category string to enum
        category_str = data.get("category", "utility")
        try:
            category = SkillCategory(category_str)
        except ValueError:
            category = SkillCategory.UTILITY

        return cls(
            skill_id=data["skill_id"],
            name=data["name"],
            version=data.get("version", "1.0.0"),
            category=category,
            tags=data.get("tags", []),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
            author=data.get("author"),
            dependencies=data.get("dependencies", []),
            parameters=data.get("parameters", {}),
            examples=data.get("examples", []),
        )

@dataclass
class SkillMethodMetadata:
    """
    Metadata for a specific method within a Skill.

    A Skill can have multiple methods, each becoming a separate ADK tool.
    """

    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    async_method: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "examples": self.examples,
            "async_method": self.async_method,
        }

@dataclass
class MarkdownSkillMetadata(SkillMetadata):
    """
    Metadata for Markdown-based Skills (Descriptive Mode).

    This extends SkillMetadata for skills that are defined as Markdown documents.
    These skills provide knowledge and methodology that can be injected into
    the system prompt rather than being executable tools.

    Attributes:
        content: The Markdown content (body after frontmatter)
        file_path: Path to the source .md file
    """

    content: str = ""
    file_path: str = ""

    def get_content_for_prompt(self) -> str:
        """
        Get formatted content for injection into system prompt.

        Returns:
            Formatted string with skill metadata and content
        """
        tags_str = ", ".join(self.tags) if self.tags else "None"

        return f"""## {self.name}

**Description**: {self.description}
**Category**: {self.category.value}
**Tags**: {tags_str}

{self.content}"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for serialization"""
        base_dict = super().to_dict()
        base_dict.update({
            "content": self.content,
            "file_path": self.file_path,
        })
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarkdownSkillMetadata":
        """Create metadata from dictionary (for JSON/YAML loading)"""
        # Convert category string to enum
        category_str = data.get("category", "utility")
        try:
            category = SkillCategory(category_str)
        except ValueError:
            category = SkillCategory.UTILITY

        return cls(
            skill_id=data["skill_id"],
            name=data["name"],
            version=data.get("version", "1.0.0"),
            category=category,
            tags=data.get("tags", []),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
            author=data.get("author"),
            dependencies=data.get("dependencies", []),
            parameters=data.get("parameters", {}),
            examples=data.get("examples", []),
            content=data.get("content", ""),
            file_path=data.get("file_path", ""),
        )
