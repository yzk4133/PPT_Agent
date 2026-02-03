"""
Cognition Prompts Module

This module provides centralized prompt management for all agents.
"""

from .prompt_manager import (
    PromptManager,
    get_split_topic_agent_prompt,
    get_research_topic_agent_prompt,
    get_xml_ppt_agent_prompt,
    get_checker_agent_prompt,
)

__all__ = [
    "PromptManager",
    "get_split_topic_agent_prompt",
    "get_research_topic_agent_prompt",
    "get_xml_ppt_agent_prompt",
    "get_checker_agent_prompt",
]
