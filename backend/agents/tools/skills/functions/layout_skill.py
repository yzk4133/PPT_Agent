#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skill: Select Slide Layout

Implements the SelectSlideLayoutSkill - a decision framework for choosing
appropriate PowerPoint slide layouts based on content characteristics.
"""

import json
import logging
from typing import Optional, Dict, Any

from ..skill_decorator import Skill
from ..skill_metadata import SkillCategory


logger = logging.getLogger(__name__)


@Skill(
    name="SelectSlideLayoutSkill",
    version="1.0.0",
    category=SkillCategory.GENERATION,
    tags=["layout", "design", "slides", "visual"],
    description="Select appropriate PowerPoint slide layout based on content type",
    author="MultiAgentPPT",
    enabled=True
)
class SelectSlideLayoutSkill:
    """
    SelectSlideLayoutSkill - Layout Selection Decision Framework

    This Skill implements a decision tree for selecting the most appropriate
    PowerPoint layout based on content characteristics.

    Layout Types:
    - 0: Title
    - 1: Title and Content
    - 2: Section Header
    - 3: Two Content
    - 4: Comparison
    - 5: Title Only
    - 6: Blank
    """

    # Layout decision tree
    LAYOUT_DECISIONS = {
        "title_page": "Title",              # 0
        "section": "Section Header",        # 2
        "toc": "Title and Content",         # 1
        "quote": "Title Only",              # 5
        "chart": "Title and Content",       # 1
        "image_dominant": "Blank",          # 6
    }

    def __init__(self):
        """Initialize the layout skill"""
        self.logger = logger

    async def execute(
        self,
        content_type: str,
        has_image: bool = False,
        has_chart: bool = False,
        bullet_count: int = 3,
        tool_context: Optional[Any] = None
    ) -> str:
        """
        Select appropriate slide layout

        Args:
            content_type: Type of content (title_page, section, toc, quote, standard, etc.)
            has_image: Whether slide contains an image
            has_chart: Whether slide contains a chart
            bullet_count: Number of bullet points
            tool_context: Optional tool context

        Returns:
            JSON string with recommended layout and reasoning
        """
        self.logger.info(f"[SelectSlideLayoutSkill] Selecting layout for: {content_type}")

        try:
            # Select layout based on decision tree
            layout_name = self._select_layout(
                content_type, has_image, has_chart, bullet_count
            )

            # Get layout index
            layout_index = self._get_layout_index(layout_name)

            # Generate reasoning
            reasoning = self._explain_decision(
                content_type, has_image, has_chart, bullet_count, layout_name
            )

            result = {
                "content_type": content_type,
                "recommended_layout": layout_name,
                "layout_index": layout_index,
                "reasoning": reasoning
            }

            return json.dumps({
                "success": True,
                "result": result
            }, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Layout selection error: {e}", exc_info=True)
            return json.dumps({
                "success": False,
                "error": str(e),
                "result": None
            }, ensure_ascii=False)

    def _select_layout(
        self,
        content_type: str,
        has_image: bool,
        has_chart: bool,
        bullet_count: int
    ) -> str:
        """Select layout based on decision tree"""

        # Direct mappings
        if content_type in self.LAYOUT_DECISIONS:
            return self.LAYOUT_DECISIONS[content_type]

        # Decision logic for standard content
        if content_type == "comparison":
            return "Comparison"  # 4

        elif has_chart and has_image:
            return "Two Content"  # Chart on left, image on right

        elif has_chart:
            return "Title and Content"  # Chart is the focus

        elif has_image:
            if bullet_count > 3:
                return "Two Content"  # Text on left, image on right
            else:
                return "Title and Content"  # Image with brief text

        else:  # Text only
            if bullet_count > 5:
                return "Two Content"  # Split into two columns
            elif bullet_count == 0:
                return "Title Only"  # Just the title
            else:
                return "Title and Content"  # Standard bullet layout

    def _get_layout_index(self, layout_name: str) -> int:
        """Get PowerPoint layout index"""
        layout_map = {
            "Title": 0,
            "Title and Content": 1,
            "Section Header": 2,
            "Two Content": 3,
            "Comparison": 4,
            "Title Only": 5,
            "Blank": 6
        }
        return layout_map.get(layout_name, 1)  # Default to Title and Content

    def _explain_decision(
        self,
        content_type: str,
        has_image: bool,
        has_chart: bool,
        bullet_count: int,
        layout_name: str
    ) -> str:
        """Generate explanation for layout decision"""
        reasons = []

        if content_type == "title_page":
            reasons.append("Title page requires centered, minimal layout")
        elif content_type == "section":
            reasons.append("Section header needs emphasis on title")
        elif content_type == "toc":
            reasons.append("Table of contents needs room for list")
        elif content_type == "quote":
            reasons.append("Quote needs maximum emphasis on text")
        elif has_chart and has_image:
            reasons.append("Both chart and image present, use two-column layout")
        elif has_chart:
            reasons.append("Chart is the main focus, use standard content layout")
        elif has_image:
            if bullet_count > 3:
                reasons.append("Multiple bullets with image, use two-column layout")
            else:
                reasons.append("Brief text with image, use standard content layout")
        elif bullet_count > 5:
            reasons.append("Many bullet points, split into two columns")
        else:
            reasons.append("Standard content with bullets, use Title and Content")

        return ". ".join(reasons)

    def get_skill_metadata(self):
        """Get skill metadata"""
        from ..skill_metadata import SkillMetadata
        return SkillMetadata(
            skill_id="select_layout",
            name="SelectSlideLayoutSkill",
            version="1.0.0",
            category=SkillCategory.GENERATION,
            tags=["layout", "design", "slides", "visual"],
            description="Select appropriate PowerPoint slide layout",
            enabled=True
        )


# Convenience function
async def select_slide_layout(
    content_type: str,
    has_image: bool = False,
    has_chart: bool = False,
    bullet_count: int = 3,
    tool_context: Optional[Any] = None
) -> str:
    """
    Select appropriate slide layout

    Args:
        content_type: Type of content
        has_image: Whether slide contains an image
        has_chart: Whether slide contains a chart
        bullet_count: Number of bullet points
        tool_context: Optional tool context

    Returns:
        JSON string with recommended layout
    """
    skill = SelectSlideLayoutSkill()
    return await skill.execute(
        content_type=content_type,
        has_image=has_image,
        has_chart=has_chart,
        bullet_count=bullet_count,
        tool_context=tool_context
    )
