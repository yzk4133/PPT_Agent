"""
Planning Prompts

This module contains prompts for planning-related agents.
"""
from .requirement_parser_prompt import REQUIREMENT_PARSER_AGENT_PROMPT
from .framework_designer_prompt import FRAMEWORK_DESIGNER_AGENT_PROMPT
from .topic_splitter_prompt import SPLIT_TOPIC_AGENT_PROMPT, OUTLINE_GENERATION_PROMPT

__all__ = [
    "REQUIREMENT_PARSER_AGENT_PROMPT",
    "FRAMEWORK_DESIGNER_AGENT_PROMPT",
    "SPLIT_TOPIC_AGENT_PROMPT",
    "OUTLINE_GENERATION_PROMPT",
]
