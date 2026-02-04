#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文本处理器 - 处理PPT文本内容的工具类
"""

import re
from pptx.util import Pt, Inches
from .config import SlideConfig

class TextProcessor:
    """文本处理工具类"""

    @staticmethod
    def remove_html_tags(text: str) -> str:
        """去除HTML标签"""
        if not isinstance(text, str):
            return ""
        clean = re.sub(r'<.*?>', '', text)
        return clean.strip()

    @staticmethod
    def calculate_optimal_font_size(
        text: str,
        shape,
        font_type: str = "content"
    ) -> int:
        """根据文本长度和文本框大小计算最佳字体大小"""
        if not text or not shape:
            return SlideConfig.FONT_SIZES[font_type]["default"]

        try:
            width = shape.width
            height = shape.height
        except:
            return SlideConfig.FONT_SIZES[font_type]["default"]

        char_count = len(text)
        estimated_chars_per_line = int(width / Pt(7))
        estimated_lines = max(1, char_count / max(1, estimated_chars_per_line))
        font_config = SlideConfig.FONT_SIZES[font_type]

        if estimated_lines > 20:
            return font_config["min"]
        elif estimated_lines > 10:
            return int(font_config["min"] + (font_config["default"] - font_config["min"]) * 0.5)
        elif estimated_lines > 5:
            return font_config["default"]
        else:
            return min(font_config["max"], font_config["default"] + 4)

    @staticmethod
    def truncate_text(text: str, max_chars: int, suffix: str = "...") -> str:
        """截断过长的文本"""
        if len(text) <= max_chars:
            return text
        return text[:max_chars - len(suffix)] + suffix

    @staticmethod
    def split_text_into_chunks(
        content: str,
        max_chars: int = SlideConfig.MAX_CHARS_PER_TEXT_CHUNK
    ) -> list:
        """将长文本分割成块"""
        if not content or not content.strip():
            return []

        sentences = re.split(r'(?<=[.!?。？！]) +', content)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > max_chars and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
            else:
                current_chunk += sentence + " "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks
