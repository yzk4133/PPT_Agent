"""
Core Agents Module

This module contains all core agents for the new "1 Master + 5 Sub" architecture.
"""

# Planning agents (including requirements)
from agents.core.planning.topic_splitter_agent import split_topic_agent
from agents.core.planning.framework_designer_agent import framework_designer_agent, FrameworkDesignerAgent
from agents.core.planning.requirements.requirement_parser_agent import requirement_parser_agent, RequirementParserAgent

# Research agents
from agents.core.research.parallel_research_agent import parallel_search_agent
from agents.core.research.research_agent import optimized_research_agent, OptimizedResearchAgent

# Generation agents
from agents.core.generation.slide_writer_agent import ppt_generator_loop_agent
from agents.core.generation.content_material_agent import content_material_agent, ContentMaterialAgent

# Rendering agents
from agents.core.rendering.template_renderer_agent import template_renderer_agent, TemplateRendererAgent

# Quality module
from agents.core.quality.feedback_loop import (
    QualityDimension,
    QualityScore,
    QualityAssessment,
    QualityAssessor,
    RuleBasedAssessor,
    FeedbackLoopAgent,
    get_default_assessor
)

__all__ = [
    # Planning (including requirements)
    "split_topic_agent",
    "framework_designer_agent",
    "FrameworkDesignerAgent",
    "requirement_parser_agent",
    "RequirementParserAgent",

    # Research
    "parallel_search_agent",
    "optimized_research_agent",
    "OptimizedResearchAgent",

    # Generation
    "ppt_generator_loop_agent",
    "content_material_agent",
    "ContentMaterialAgent",

    # Rendering
    "template_renderer_agent",
    "TemplateRendererAgent",

    # Quality
    "QualityDimension",
    "QualityScore",
    "QualityAssessment",
    "QualityAssessor",
    "RuleBasedAssessor",
    "FeedbackLoopAgent",
    "get_default_assessor",
]
