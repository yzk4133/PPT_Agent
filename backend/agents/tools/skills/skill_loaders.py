#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skill Framework - Skill Loaders Module

This module provides loaders for different skill definition formats:
- Python classes with @Skill decorator
- JSON configuration files
- YAML configuration files
"""

import os
import sys
import importlib
import importlib.util
import inspect
import json
from pathlib import Path
from typing import List, Dict, Any, Type, Optional

from .skill_metadata import SkillMetadata, SkillCategory, MarkdownSkillMetadata
from .skill_wrapper import SkillWrapper


class PythonSkillLoader:
    """
    Loader for Python-based Skills using the @Skill decorator.

    This loader discovers and imports Python modules with Skill classes.
    """

    def __init__(self, skill_directories: List[str]):
        """
        Initialize the Python skill loader.

        Args:
            skill_directories: List of directories to search for skills
        """
        self.skill_directories = skill_directories
        self._loaded_modules: Dict[str, Any] = {}

    def _add_to_path(self, directory: str):
        """Add a directory to Python path if not already present"""
        abs_path = os.path.abspath(directory)
        if abs_path not in sys.path:
            sys.path.insert(0, abs_path)

    def discover_modules(self) -> List[Path]:
        """
        Discover all Python modules in skill directories.

        Returns:
            List of Path objects for discovered modules
        """
        modules = []

        for directory in self.skill_directories:
            if not os.path.exists(directory):
                continue

            # Add to path
            self._add_to_path(directory)

            # Walk through directory
            for root, dirs, files in os.walk(directory):
                # Skip __pycache__ and hidden directories
                dirs[:] = [d for d in dirs if not d.startswith("_") and not d.startswith(".")]

                for file in files:
                    if file.endswith(".py") and not file.startswith("_"):
                        module_path = Path(root) / file
                        modules.append(module_path)

        return modules

    def load_from_file(self, file_path: Path) -> List[Type]:
        """
        Load Skill classes from a Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            List of Skill classes found in the file
        """
        skill_classes = []

        try:
            # Load module dynamically
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            if spec is None or spec.loader is None:
                return skill_classes

            module = importlib.util.module_from_spec(spec)
            sys.modules[file_path.stem] = module
            spec.loader.exec_module(module)

            # Cache the module
            self._loaded_modules[file_path.stem] = module

            # Find classes with __skill_metadata__
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if hasattr(obj, "__skill_metadata__"):
                    # Skip imported classes (not defined in this module)
                    if obj.__module__ == file_path.stem:
                        skill_classes.append(obj)

        except Exception as e:
            print(f"Warning: Failed to load skills from {file_path}: {e}")

        return skill_classes

    def load_from_module(self, module_path: str) -> List[Type]:
        """
        Load Skill classes from a module path (e.g., "skills.document.search").

        Args:
            module_path: Dot-notation module path

        Returns:
            List of Skill classes found in the module
        """
        skill_classes = []

        try:
            module = importlib.import_module(module_path)

            # Find classes with __skill_metadata__
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if hasattr(obj, "__skill_metadata__"):
                    skill_classes.append(obj)

        except Exception as e:
            print(f"Warning: Failed to load module {module_path}: {e}")

        return skill_classes

    def load_all(self) -> List[SkillWrapper]:
        """
        Discover and load all Skills from configured directories.

        Returns:
            List of SkillWrapper instances
        """
        wrappers = []

        modules = self.discover_modules()
        for module_path in modules:
            skill_classes = self.load_from_file(module_path)

            for skill_class in skill_classes:
                metadata = skill_class.get_skill_metadata()
                wrapper = SkillWrapper(skill_class, metadata)
                wrappers.append(wrapper)

        return wrappers


class JsonSkillLoader:
    """
    Loader for JSON-based Skill definitions.

    JSON skills are defined in configuration files that reference
    a Python class or function to execute.
    """

    def __init__(self, config_directory: str):
        """
        Initialize the JSON skill loader.

        Args:
            config_directory: Directory containing JSON skill configs
        """
        self.config_directory = config_directory

    def discover_configs(self) -> List[Path]:
        """Discover all JSON config files in the directory"""
        configs = []

        if not os.path.exists(self.config_directory):
            return configs

        for file in os.listdir(self.config_directory):
            if file.endswith(".json"):
                configs.append(Path(self.config_directory) / file)

        return configs

    def load_from_file(self, file_path: Path) -> Optional[SkillMetadata]:
        """
        Load skill metadata from a JSON file.

        Args:
            file_path: Path to the JSON config file

        Returns:
            SkillMetadata instance or None if failed
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return SkillMetadata.from_dict(data)

        except Exception as e:
            print(f"Warning: Failed to load JSON config {file_path}: {e}")
            return None

    def load_skill_class(self, config: Dict[str, Any]) -> Optional[Type]:
        """
        Load the actual Python class from entry_point in config.

        Args:
            config: Dictionary containing entry_point key

        Returns:
            The loaded class or None
        """
        entry_point = config.get("entry_point")
        if not entry_point:
            return None

        try:
            # Parse entry point (e.g., "skills.search:WebSearchSkill")
            if ":" in entry_point:
                module_path, class_name = entry_point.split(":")
                module = importlib.import_module(module_path)
                return getattr(module, class_name)
            else:
                # Just import module
                return importlib.import_module(entry_point)

        except Exception as e:
            print(f"Warning: Failed to load entry point {entry_point}: {e}")
            return None

    def load_all(self) -> List[SkillWrapper]:
        """
        Load all Skills from JSON configs.

        Returns:
            List of SkillWrapper instances
        """
        wrappers = []

        configs = self.discover_configs()
        for config_path in configs:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Load metadata
            metadata = SkillMetadata.from_dict(data)

            # Load actual class
            skill_class = self.load_skill_class(data)
            if skill_class:
                wrapper = SkillWrapper(skill_class, metadata)
                wrappers.append(wrapper)

        return wrappers


class YamlSkillLoader(JsonSkillLoader):
    """
    Loader for YAML-based Skill definitions.

    Similar to JSON loader but uses YAML format.
    """

    def load_from_file(self, file_path: Path) -> Optional[SkillMetadata]:
        """
        Load skill metadata from a YAML file.

        Args:
            file_path: Path to the YAML config file

        Returns:
            SkillMetadata instance or None if failed
        """
        try:
            import yaml

            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            return SkillMetadata.from_dict(data)

        except ImportError:
            print("Warning: PyYAML not installed, cannot load YAML configs")
            return None
        except Exception as e:
            print(f"Warning: Failed to load YAML config {file_path}: {e}")
            return None

    def discover_configs(self) -> List[Path]:
        """Discover all YAML config files in the directory"""
        configs = []

        if not os.path.exists(self.config_directory):
            return configs

        for file in os.listdir(self.config_directory):
            if file.endswith((".yaml", ".yml")):
                configs.append(Path(self.config_directory) / file)

        return configs


class MarkdownSkillLoader:
    """
    Loader for Markdown-based Skills (Descriptive Skills).

    This loader discovers and parses Markdown files with YAML frontmatter.
    Markdown skills provide knowledge and methodology that can be injected
    into system prompts rather than being executable tools.
    """

    def __init__(self, skill_directories: List[str]):
        """
        Initialize the Markdown skill loader.

        Args:
            skill_directories: List of directories to search for .md skill files
        """
        self.skill_directories = skill_directories

    def discover_files(self) -> List[Path]:
        """
        Discover all Markdown skill files in skill directories.

        Returns:
            List of Path objects for discovered .md files
        """
        files = []

        for directory in self.skill_directories:
            if not os.path.exists(directory):
                continue

            # Walk through directory
            for root, dirs, filenames in os.walk(directory):
                # Skip __pycache__ and hidden directories
                dirs[:] = [d for d in dirs if not d.startswith("_") and not d.startswith(".")]

                for filename in filenames:
                    if filename.endswith(".md"):
                        file_path = Path(root) / filename
                        files.append(file_path)

        return files

    def _parse_frontmatter(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse YAML frontmatter from a Markdown file.

        Args:
            file_path: Path to the Markdown file

        Returns:
            Dictionary with frontmatter data and content, or None if failed
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for frontmatter delimiter
            if not content.startswith("---"):
                return None

            # Find end of frontmatter
            end_idx = content.find("\n---", 4)
            if end_idx == -1:
                return None

            # Extract frontmatter YAML
            frontmatter_text = content[4:end_idx]

            # Parse YAML (using built-in yaml if available, otherwise simple parsing)
            try:
                import yaml
                frontmatter_data = yaml.safe_load(frontmatter_text)
            except ImportError:
                # Fallback: simple key-value parsing for basic frontmatter
                frontmatter_data = self._parse_simple_frontmatter(frontmatter_text)

            if frontmatter_data is None:
                return None

            # Extract content body
            body_content = content[end_idx + 4:].strip()

            return {
                "frontmatter": frontmatter_data,
                "content": body_content,
            }

        except Exception as e:
            print(f"Warning: Failed to parse frontmatter from {file_path}: {e}")
            return None

    def _parse_simple_frontmatter(self, text: str) -> Dict[str, Any]:
        """
        Simple frontmatter parser for basic YAML-like format.
        Fallback when pyyaml is not available.

        Args:
            text: Frontmatter text without delimiters

        Returns:
            Dictionary of parsed key-value pairs
        """
        data = {}
        for line in text.split("\n"):
            line = line.strip()
            if ":" in line and not line.startswith("#"):
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Handle different value types
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                elif value.startswith("[") and value.endswith("]"):
                    # Parse list
                    value = [v.strip().strip('"\'') for v in value[1:-1].split(",") if v.strip()]
                else:
                    # Remove quotes if present
                    value = value.strip('"\'')

                data[key] = value

        return data

    def load_from_file(self, file_path: Path) -> Optional[MarkdownSkillMetadata]:
        """
        Load a Markdown skill from a file.

        Args:
            file_path: Path to the Markdown file

        Returns:
            MarkdownSkillMetadata instance or None if failed
        """
        parsed = self._parse_frontmatter(file_path)
        if not parsed:
            return None

        frontmatter = parsed["frontmatter"]
        content = parsed["content"]

        # Validate required fields
        if "skill_id" not in frontmatter or "name" not in frontmatter:
            print(f"Warning: Missing required fields in {file_path}")
            return None

        # Convert category string to enum
        category_str = frontmatter.get("category", "utility")
        try:
            category = SkillCategory(category_str)
        except ValueError:
            category = SkillCategory.UTILITY
            print(f"Warning: Invalid category '{category_str}' in {file_path}, using UTILITY")

        # Normalize tags
        tags = frontmatter.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]

        # Create metadata
        return MarkdownSkillMetadata(
            skill_id=frontmatter["skill_id"],
            name=frontmatter["name"],
            version=frontmatter.get("version", "1.0.0"),
            category=category,
            tags=tags,
            description=frontmatter.get("description", ""),
            enabled=frontmatter.get("enabled", True),
            author=frontmatter.get("author"),
            dependencies=frontmatter.get("dependencies", []),
            parameters=frontmatter.get("parameters", {}),
            examples=frontmatter.get("examples", []),
            content=content,
            file_path=str(file_path),
        )

    def load_all(self) -> List[MarkdownSkillMetadata]:
        """
        Discover and load all Markdown Skills from configured directories.

        Returns:
            List of MarkdownSkillMetadata instances
        """
        metadata_list = []

        files = self.discover_files()
        for file_path in files:
            metadata = self.load_from_file(file_path)
            if metadata:
                metadata_list.append(metadata)
                print(f"Loaded Markdown skill: {metadata.skill_id} ({metadata.name})")

        return metadata_list


class CompositeSkillLoader:
    """
    Composite loader that combines all loader types.

    This is the main loader used by the SkillRegistry.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the composite loader.

        Args:
            config: Configuration dictionary with loader settings
        """
        skill_dirs = config.get("skill_directories", ["backend/skills"])

        self.python_loader = PythonSkillLoader(skill_dirs)
        self.markdown_loader = MarkdownSkillLoader(skill_dirs)

        config_dir = config.get("config_directory", "backend/skills/configs")
        self.json_loader = JsonSkillLoader(config_dir)
        self.yaml_loader = YamlSkillLoader(config_dir)

    def load_all(self) -> Dict[str, List[Any]]:
        """
        Load all Skills from all sources.

        Returns:
            Dictionary with 'executable' and 'descriptive' skill lists
        """
        result = {
            "executable": [],
            "descriptive": [],
        }

        # Load Python skills (executable)
        result["executable"].extend(self.python_loader.load_all())

        # Load JSON skills (executable)
        result["executable"].extend(self.json_loader.load_all())

        # Load YAML skills (executable)
        result["executable"].extend(self.yaml_loader.load_all())

        # Load Markdown skills (descriptive)
        result["descriptive"].extend(self.markdown_loader.load_all())

        return result
