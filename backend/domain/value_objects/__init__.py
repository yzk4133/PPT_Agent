"""
Domain Value Objects

Export all value objects from the value_objects folder.

Value objects are immutable objects defined by their attributes rather than identity.
"""

from .requirement import Requirement, RequirementAnalysis, SceneType, TemplateType
from .framework import PPTFramework, PageDefinition, PageType, ContentType, FrameworkValidation
from .research import ResearchResult, ResearchResults, ResearchStatus, Reference
from .slide import Slide, SlideList, Image, SlideLayout, SlideComponentType
from .topic import Topic, TopicList, create_topic_from_json
from .page_state import PageStatus, PageState, PageStateManager, PagePipelineConfig, PagePipelineResult

__all__ = [
    # Requirement
    "Requirement",
    "RequirementAnalysis",
    "SceneType",
    "TemplateType",
    # Framework
    "PPTFramework",
    "PageDefinition",
    "PageType",
    "ContentType",
    "FrameworkValidation",
    # Research
    "ResearchResult",
    "ResearchResults",
    "ResearchStatus",
    "Reference",
    # Slide
    "Slide",
    "SlideList",
    "Image",
    "SlideLayout",
    "SlideComponentType",
    # Topic
    "Topic",
    "TopicList",
    "create_topic_from_json",
    # Page State
    "PageStatus",
    "PageState",
    "PageStateManager",
    "PagePipelineConfig",
    "PagePipelineResult",
]
