"""
PPT幻灯片生成策略模块

本模块包含所有用于生成不同类型幻灯片的策略类。
"""

from .base import SlideStrategy
from .title_slide import TitleSlideStrategy
from .content_slide import ContentSlideStrategy
from .toc_slide import TableOfContentsSlideStrategy
from .image_slide import ImageSlideStrategy
from .subsection_slide import SubSectionSlideStrategy
from .references_slide import ReferencesSlideStrategy
from .end_slide import EndSlideStrategy

__all__ = [
    'SlideStrategy',
    'TitleSlideStrategy',
    'ContentSlideStrategy',
    'TableOfContentsSlideStrategy',
    'ImageSlideStrategy',
    'SubSectionSlideStrategy',
    'ReferencesSlideStrategy',
    'EndSlideStrategy',
]
