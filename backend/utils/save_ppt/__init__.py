"""
PPT生成器模块

用于从JSON数据生成PowerPoint演示文稿
"""

# 配置和工具
from .config import SlideConfig
from .text_processor import TextProcessor

# 主生成器
from .generator import PresentationGenerator
from .main import start_generate_presentation

# 策略
from .strategies import (
    SlideStrategy,
    TitleSlideStrategy,
    ContentSlideStrategy,
    TableOfContentsSlideStrategy,
    ImageSlideStrategy,
    SubSectionSlideStrategy,
    ReferencesSlideStrategy,
    EndSlideStrategy,
)

__all__ = [
    # 配置和工具
    'SlideConfig',
    'TextProcessor',

    # 主生成器
    'PresentationGenerator',
    'start_generate_presentation',

    # 策略
    'SlideStrategy',
    'TitleSlideStrategy',
    'ContentSlideStrategy',
    'TableOfContentsSlideStrategy',
    'ImageSlideStrategy',
    'SubSectionSlideStrategy',
    'ReferencesSlideStrategy',
    'EndSlideStrategy',
]

# 为了向后兼容，保留对原ppt_generator的引用
try:
    from . import ppt_generator
    # 将ppt_generator中的公共接口添加到当前模块
    _ppt_generator_exports = [
        'SlideConfig',
        'TextProcessor',
        'SlideStrategy',
        'TitleSlideStrategy',
        'ContentSlideStrategy',
        'TableOfContentsSlideStrategy',
        'ImageSlideStrategy',
        'SubSectionSlideStrategy',
        'ReferencesSlideStrategy',
        'EndSlideStrategy',
        'PresentationGenerator',
        'start_generate_presentation',
    ]
    for export in _ppt_generator_exports:
        if hasattr(ppt_generator, export) and export not in __all__:
            __all__.append(export)
except ImportError:
    pass

# 别名
PPTGenerator = PresentationGenerator
get_ppt_generator = lambda: PresentationGenerator()

__all__.extend(['PPTGenerator', 'get_ppt_generator'])
