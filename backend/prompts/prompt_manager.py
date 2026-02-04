"""
Prompt Manager

Centralized prompt management with versioning support.
Provides a single source of truth for all agent prompts.
"""

from typing import Dict, Optional
import os

class PromptManager:
    """
    Centralized prompt management with versioning.

    This class provides:
    - Version control for prompts
    - Easy access to prompts by category and version
    - Backward compatibility with hardcoded prompts
    - Template variable support
    """

    # Prompts indexed by category and version
    _prompts: Dict[str, Dict[str, str]] = {
        "planning": {
            "v1": "",  # Loaded from planning_prompts.py
            "v2": "",  # Future versions can be added
        },
        "research": {
            "v1": "",  # Loaded from research_prompts.py
        },
        "generation": {
            "v1": "",  # Loaded from generation_prompts.py
        },
    }

    # Prompt template mappings
    _template_mappings: Dict[str, str] = {}

    @classmethod
    def _load_prompts(cls) -> None:
        """Load prompts from template modules"""
        if cls._prompts["planning"]["v1"]:
            return  # Already loaded

        try:
            from .templates.planning import (
                SPLIT_TOPIC_AGENT_PROMPT,
                OUTLINE_GENERATION_PROMPT,
                REQUIREMENT_PARSER_AGENT_PROMPT,
                FRAMEWORK_DESIGNER_AGENT_PROMPT,
            )

            cls._prompts["planning"]["v1"] = SPLIT_TOPIC_AGENT_PROMPT
            cls._prompts["planning"]["outline_v1"] = OUTLINE_GENERATION_PROMPT
            cls._prompts["planning"]["requirement_parser_v1"] = REQUIREMENT_PARSER_AGENT_PROMPT
            cls._prompts["planning"]["framework_designer_v1"] = FRAMEWORK_DESIGNER_AGENT_PROMPT
        except ImportError:
            pass

        try:
            from .templates.research import (
                RESEARCH_TOPIC_AGENT_PROMPT,
                DOCUMENT_ANALYSIS_PROMPT,
            )

            cls._prompts["research"]["v1"] = RESEARCH_TOPIC_AGENT_PROMPT
            cls._prompts["research"]["document_analysis_v1"] = DOCUMENT_ANALYSIS_PROMPT
        except ImportError:
            pass

        try:
            from .templates.generation import (
                XML_PPT_AGENT_NEXT_PAGE_PROMPT,
                CHECKER_AGENT_PROMPT,
                SLIDE_ENHANCEMENT_PROMPT,
            )

            cls._prompts["generation"]["v1"] = XML_PPT_AGENT_NEXT_PAGE_PROMPT
            cls._prompts["generation"]["checker_v1"] = CHECKER_AGENT_PROMPT
            cls._prompts["generation"]["enhancement_v1"] = SLIDE_ENHANCEMENT_PROMPT
        except ImportError:
            pass

    @classmethod
    def get_prompt(
        cls,
        category: str,
        version: str = "v1",
        **kwargs
    ) -> str:
        """
        Get a prompt by category and version.

        Args:
            category: Prompt category (planning, research, generation)
            version: Prompt version (default: v1)
            **kwargs: Template variables to substitute in the prompt

        Returns:
            The prompt template with variables substituted

        Example:
            prompt = PromptManager.get_prompt(
                "planning",
                version="v1",
                outline="My outline here"
            )
        """
        cls._load_prompts()

        # Get the base prompt
        prompt_template = cls._prompts.get(category, {}).get(version, "")

        if not prompt_template:
            # Try template mapping
            key = f"{category}_{version}"
            prompt_template = cls._template_mappings.get(key, "")

        if not prompt_template:
            raise ValueError(
                f"Prompt not found: category='{category}', version='{version}'"
            )

        # Substitute template variables if provided
        if kwargs:
            try:
                prompt_template = prompt_template.format(**kwargs)
            except KeyError as e:
                raise ValueError(
                    f"Missing template variable {e} for prompt {category}:{version}"
                )

        return prompt_template

    @classmethod
    def get_split_topic_prompt(cls, **kwargs) -> str:
        """Convenience method for split topic prompt"""
        return cls.get_prompt("planning", "v1", **kwargs)

    @classmethod
    def get_requirement_parser_prompt(cls, **kwargs) -> str:
        """Convenience method for requirement parser prompt"""
        return cls.get_prompt("planning", "requirement_parser_v1", **kwargs)

    @classmethod
    def get_framework_designer_prompt(cls, **kwargs) -> str:
        """Convenience method for framework designer prompt"""
        return cls.get_prompt("planning", "framework_designer_v1", **kwargs)

    @classmethod
    def get_research_topic_prompt(cls, **kwargs) -> str:
        """Convenience method for research topic prompt"""
        return cls.get_prompt("research", "v1", **kwargs)

    @classmethod
    def get_xml_ppt_generation_prompt(cls, **kwargs) -> str:
        """Convenience method for XML PPT generation prompt"""
        return cls.get_prompt("generation", "v1", **kwargs)

    @classmethod
    def get_checker_prompt(cls, **kwargs) -> str:
        """Convenience method for checker prompt"""
        return cls.get_prompt("generation", "checker_v1", **kwargs)

    @classmethod
    def list_categories(cls) -> list[str]:
        """List all available prompt categories"""
        cls._load_prompts()
        return list(cls._prompts.keys())

    @classmethod
    def list_versions(cls, category: str) -> list[str]:
        """
        List available versions for a prompt category.

        Args:
            category: The prompt category

        Returns:
            List of version strings
        """
        cls._load_prompts()
        return list(cls._prompts.get(category, {}).keys())

    @classmethod
    def register_prompt(
        cls,
        category: str,
        version: str,
        prompt_template: str
    ) -> None:
        """
        Register a new prompt or update an existing one.

        Args:
            category: Prompt category
            version: Prompt version
            prompt_template: The prompt template string
        """
        cls._load_prompts()

        if category not in cls._prompts:
            cls._prompts[category] = {}

        cls._prompts[category][version] = prompt_template

    @classmethod
    def get_all_prompts(cls) -> Dict[str, Dict[str, str]]:
        """
        Get all registered prompts.

        Returns:
            Dictionary of all prompts indexed by category and version
        """
        cls._load_prompts()
        return cls._prompts.copy()

    @classmethod
    def validate_prompt_variables(
        cls,
        category: str,
        version: str = "v1"
    ) -> list[str]:
        """
        Extract and list template variables from a prompt.

        Args:
            category: Prompt category
            version: Prompt version

        Returns:
            List of template variable names found in the prompt
        """
        import re

        prompt = cls.get_prompt(category, version)
        # Find all {variable} patterns
        variables = re.findall(r"\{(\w+)\}", prompt)
        return list(set(variables))

# Convenience functions for backward compatibility
def get_split_topic_agent_prompt() -> str:
    """Get the split topic agent prompt (v1)"""
    return PromptManager.get_split_topic_prompt()

def get_research_topic_agent_prompt() -> str:
    """Get the research topic agent prompt (v1)"""
    return PromptManager.get_research_topic_prompt()

def get_xml_ppt_agent_prompt(**kwargs) -> str:
    """Get the XML PPT agent prompt (v1) with template variables"""
    return PromptManager.get_xml_ppt_generation_prompt(**kwargs)

def get_checker_agent_prompt(**kwargs) -> str:
    """Get the checker agent prompt (v1) with template variables"""
    return PromptManager.get_checker_prompt(**kwargs)

if __name__ == "__main__":
    # Test the prompt manager
    print("Available categories:", PromptManager.list_categories())
    print("\nPlanning versions:", PromptManager.list_versions("planning"))
    print("Research versions:", PromptManager.list_versions("research"))
    print("Generation versions:", PromptManager.list_versions("generation"))

    # Test getting prompts
    print("\n=== Split Topic Prompt ===")
    split_prompt = PromptManager.get_split_topic_prompt()
    print(split_prompt[:200] + "...")

    print("\n=== XML PPT Prompt Variables ===")
    variables = PromptManager.validate_prompt_variables("generation", "v1")
    print(f"Template variables: {variables}")
