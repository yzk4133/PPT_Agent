#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skill Framework - Core Module

This module exports the core components of the Skill framework.
"""

from .skill_metadata import SkillMetadata, SkillCategory, SkillMethodMetadata, MarkdownSkillMetadata
from .skill_decorator import Skill, SkillMethod
from .skill_wrapper import SkillWrapper, SkillAdapter, McpSkillAdapter
from .skill_loaders import (
    PythonSkillLoader,
    JsonSkillLoader,
    YamlSkillLoader,
    MarkdownSkillLoader,
    CompositeSkillLoader,
)
from .skill_registry import SkillRegistry

__all__ = [
    # Metadata
    "SkillMetadata",
    "SkillCategory",
    "SkillMethodMetadata",
    "MarkdownSkillMetadata",
    # Decorators
    "Skill",
    "SkillMethod",
    # Wrappers
    "SkillWrapper",
    "SkillAdapter",
    "McpSkillAdapter",
    # Loaders
    "PythonSkillLoader",
    "JsonSkillLoader",
    "YamlSkillLoader",
    "MarkdownSkillLoader",
    "CompositeSkillLoader",
    # Registry
    "SkillRegistry",
]
