#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置类 - 幻灯片生成配置
"""

from dataclasses import dataclass

@dataclass
class SlideConfig:
    """幻灯片配置数据类"""
    SLIDE_LAYOUTS = {
        "TITLE_PAGE": 0,
        "CONTENT_TITLE_AND_TEXT": 1,
        "TABLE_OF_CONTENTS_GENERIC": 22,
        "TABLE_OF_CONTENTS_4_ITEMS_A": 23,
        "TABLE_OF_CONTENTS_4_ITEMS_B": 24,
        "TABLE_OF_CONTENTS_5_ITEMS_A": 25,
        "TABLE_OF_CONTENTS_5_ITEMS_B": 26,
        "TABLE_OF_CONTENTS_3_ITEMS": 30,
        "INFO_TITLE_AND_TEXT": 15,
        "TEXT_ONLY_SMALL_TITLE": 12,
        "IMAGE_TITLE_AND_DESCRIPTION_WIDE": 9,
        "IMAGE_TITLE_AND_DESCRIPTION_TALL": 7,
        "IMAGE_ONLY": 14,
        "REFERENCES_PAGE": 10,
        "END_PAGE": 11,
        "SUBCHAPTER_2_ITEMS": 15,
        "SUBCHAPTER_3_ITEMS": 16,
        "SUBCHAPTER_4_ITEMS": 17,
        "SUBCHAPTER_5_ITEMS": 10,
    }

    SHAPE_IDS = {
        # 标题页
        "TITLE_PAGE_TITLE": 2,
        "TITLE_PAGE_DATE": 9,

        # 目录页
        "TOC_TITLE": 1,
        "TOC_ITEMS": {1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7},

        # 内容页
        "CONTENT_TITLE": 2,
        "CONTENT_TEXT": 3,
        "CONTENT_TEXT_LAYOUT1_4": 4,

        # 图片页
        "IMAGE_PLACEHOLDER": 3,
        "IMAGE_TITLE": 2,
        "IMAGE_DESCRIPTION": 4,
        "IMAGE_DIO_LAYOUT7": 6,
        "IMAGE_DIO_LAYOUT9": 5,

        # 参考文献页
        "REFERENCES_TITLE": 2,
        "REFERENCES": [
            {"num": 3, "text": 8},
            {"num": 4, "text": 9},
            {"num": 5, "text": 10},
            {"num": 6, "text": 11},
            {"num": 7, "text": 12},
        ],

        # 子章节
        "SUBCHAPTER_TITLE": 5,
        "SUBCHAPTER_ITEMS": {
            1: [2],
            2: [2, 3],
            3: [2, 3, 4],
            4: [2, 3, 4, 5],
            5: [(3, 8), (4, 9), (5, 10), (6, 11), (7, 12)],
        }
    }

    # 文本处理常量
    MAX_CHARS_PER_TEXT_CHUNK = 800
    MAX_REFERENCES_PER_SLIDE = 5
    MAX_TOTAL_REFERENCES = 10

    # 图片URL前缀
    VALID_IMAGE_URL_PREFIXES = [
        "http",
        "https",
    ]

    # 字体大小配置
    FONT_SIZES = {
        "title": {"min": 18, "max": 44, "default": 26},
        "content": {"min": 12, "max": 24, "default": 18},
        "small": {"min": 10, "max": 16, "default": 14},
    }

    # 背景图形调整配置
    BACKGROUND_SHAPE_CONFIG = {
        "min_width": 2.5,          # 最小宽度（英寸）
        "padding": 0.8,            # 总padding（英寸）
        "vertical_tolerance": 0.5,  # 垂直位置容差（英寸）
        "height_tolerance": 0.3,    # 高度容差（英寸）
        "alignment": "center"       # 对齐方式：center, left, right
    }
