"""
Generation Prompts

This module contains prompts for content generation agents.
"""
from .content_material_prompt import XML_PPT_AGENT_NEXT_PAGE_PROMPT
from .slide_writer_prompt import CHECKER_AGENT_PROMPT, SLIDE_ENHANCEMENT_PROMPT

__all__ = [
    "XML_PPT_AGENT_NEXT_PAGE_PROMPT",
    "CHECKER_AGENT_PROMPT",
    "SLIDE_ENHANCEMENT_PROMPT",
]
