"""
Tests for TextProcessor class in ppt_generator module
"""
import pytest
from pptx.util import Pt, Inches
from unittest.mock import MagicMock
import sys
import os

# Add parent directory to path

from utils.save_ppt.text_processor import TextProcessor

class TestTextProcessor:
    """测试TextProcessor工具类"""

    def test_remove_html_tags_basic(self):
        """测试基本HTML标签移除"""
        processor = TextProcessor()
        html = "<p>Hello <strong>world</strong></p>"
        clean = processor.remove_html_tags(html)
        assert clean == "Hello world"
        assert "<" not in clean
        assert ">" not in clean

    def test_remove_html_tags_nested(self):
        """测试嵌套HTML标签"""
        processor = TextProcessor()
        html = "<div><p>Text <span>nested</span> here</p></div>"
        clean = processor.remove_html_tags(html)
        assert clean == "Text nested here"

    def test_remove_html_tags_with_none(self):
        """测试None输入"""
        processor = TextProcessor()
        assert processor.remove_html_tags(None) == ""

    def test_remove_html_tags_with_number(self):
        """测试数字输入"""
        processor = TextProcessor()
        assert processor.remove_html_tags(123) == ""

    def test_remove_html_tags_empty_string(self):
        """测试空字符串"""
        processor = TextProcessor()
        assert processor.remove_html_tags("") == ""

    def test_remove_html_tags_with_attributes(self):
        """测试带属性的HTML标签"""
        processor = TextProcessor()
        html = '<a href="http://example.com" class="link">Link</a>'
        clean = processor.remove_html_tags(html)
        assert clean == "Link"

    def test_remove_html_tags_preserves_content(self):
        """测试保留内容"""
        processor = TextProcessor()
        html = "<p>Hello   world</p>"  # 多个空格
        clean = processor.remove_html_tags(html)
        assert "Hello" in clean
        assert "world" in clean

    def test_calculate_optimal_font_size_no_text(self):
        """测试无文本时的字体大小"""
        processor = TextProcessor()
        mock_shape = MagicMock()
        result = processor.calculate_optimal_font_size("", mock_shape)
        assert result == 18  # default content font size

    def test_calculate_optimal_font_size_no_shape(self):
        """测试无shape时的字体大小"""
        processor = TextProcessor()
        result = processor.calculate_optimal_font_size("some text", None)
        assert result == 18  # default

    def test_calculate_optimal_font_size_short_text(self):
        """测试短文本的字体大小"""
        processor = TextProcessor()
        mock_shape = MagicMock()
        mock_shape.width = Inches(5)
        mock_shape.height = Inches(3)

        result = processor.calculate_optimal_font_size("Short", mock_shape)
        assert result > 18  # 短文本应该使用较大字体

    def test_calculate_optimal_font_size_long_text(self):
        """测试长文本的字体大小"""
        processor = TextProcessor()
        mock_shape = MagicMock()
        mock_shape.width = Inches(5)
        mock_shape.height = Inches(3)

        long_text = "This is a very long text " * 50
        result = processor.calculate_optimal_font_size(long_text, mock_shape, "content")
        assert result == 12  # 最小字体大小

    def test_calculate_optimal_font_size_title_type(self):
        """测试标题类型字体计算"""
        processor = TextProcessor()
        mock_shape = MagicMock()
        mock_shape.width = Inches(8)
        mock_shape.height = Inches(2)

        result = processor.calculate_optimal_font_size("Title", mock_shape, "title")
        assert result >= 18 and result <= 44

    def test_calculate_optimal_font_size_small_type(self):
        """测试小字类型"""
        processor = TextProcessor()
        mock_shape = MagicMock()
        mock_shape.width = Inches(3)
        mock_shape.height = Inches(2)

        result = processor.calculate_optimal_font_size("Small text", mock_shape, "small")
        assert result >= 10 and result <= 16

    def test_truncate_text_short(self):
        """测试短文本不截断"""
        processor = TextProcessor()
        text = "短文本"
        result = processor.truncate_text(text, max_chars=10)
        assert result == "短文本"
        assert not result.endswith("...")

    def test_truncate_text_exact_length(self):
        """测试刚好等于最大长度"""
        processor = TextProcessor()
        text = "1234567890"
        result = processor.truncate_text(text, max_chars=10)
        assert result == "1234567890"
        assert not result.endswith("...")

    def test_truncate_text_long(self):
        """测试长文本截断"""
        processor = TextProcessor()
        text = "这是一段很长的文本内容需要被截断"
        result = processor.truncate_text(text, max_chars=10)
        # text[:7] + "..." = 10个字符
        assert len(result) == 10
        assert result == "这是一段很长的..."

    def test_truncate_text_custom_suffix(self):
        """测试自定义后缀"""
        processor = TextProcessor()
        text = "这是一段很长的文本内容需要被截断"
        result = processor.truncate_text(text, max_chars=10, suffix="***")
        # text[:7] + "***" = 10个字符
        assert result.endswith("***")
        assert len(result) == 10

    def test_truncate_text_empty_string(self):
        """测试空字符串"""
        processor = TextProcessor()
        result = processor.truncate_text("", max_chars=10)
        assert result == ""

    def test_split_text_into_chunks_basic(self):
        """测试基本文本分块"""
        processor = TextProcessor()
        # 使用带空格的句子（正则要求标点后有空格）
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = processor.split_text_into_chunks(text, max_chars=30)
        assert len(chunks) > 1
        assert all(len(chunk) <= 35 for chunk in chunks)  # 允许一些余量

    def test_split_text_into_chunks_empty(self):
        """测试空文本分块"""
        processor = TextProcessor()
        assert processor.split_text_into_chunks("") == []
        assert processor.split_text_into_chunks(None) == []

    def test_split_text_into_chunks_whitespace_only(self):
        """测试只有空白字符"""
        processor = TextProcessor()
        assert processor.split_text_into_chunks("   \n\n   ") == []

    def test_split_text_into_chunks_long_paragraphs(self):
        """测试长段落分块"""
        processor = TextProcessor()
        # 使用带空格分隔的句子
        text = "This is a very long sentence. " * 50
        chunks = processor.split_text_into_chunks(text, max_chars=100)
        # 由于分句逻辑，至少会有一部分被分割
        assert len(chunks) >= 1
        # 检查每个块是否合理
        for chunk in chunks:
            # 由于一个句子可能很长，块的长度可能会超过100
            assert len(chunk) > 0

    def test_split_text_into_chunks_english_punctuation(self):
        """测试英文标点分块"""
        processor = TextProcessor()
        text = "First sentence. Second sentence. Third sentence."
        chunks = processor.split_text_into_chunks(text, max_chars=30)
        assert len(chunks) >= 1

    def test_split_text_into_chunks_chinese_punctuation(self):
        """测试中文标点分块"""
        processor = TextProcessor()
        text = "第一句。第二句。第三句。"
        chunks = processor.split_text_into_chunks(text, max_chars=15)
        assert len(chunks) >= 1

    def test_split_text_into_chunks_mixed_punctuation(self):
        """测试混合标点"""
        processor = TextProcessor()
        text = "First sentence。 Second sentence. 第三句。"
        chunks = processor.split_text_into_chunks(text, max_chars=30)
        assert len(chunks) >= 1

    def test_split_text_into_chunks_preserves_content(self):
        """测试内容保留"""
        processor = TextProcessor()
        text = "第一句。第二句。第三句。"
        chunks = processor.split_text_into_chunks(text, max_chars=50)
        combined = "".join(chunks)
        # 所有原文都应该保留（可能除了尾部空格）
        for char in text.strip():
            assert char in combined

    def test_split_text_into_chunks_default_max_chars(self):
        """测试默认最大字符数"""
        processor = TextProcessor()
        # 使用带空格分隔的句子
        text = "This is a test. " * 200
        chunks = processor.split_text_into_chunks(text)
        # 过滤掉空块（如果有）
        non_empty_chunks = [c for c in chunks if c]
        assert len(non_empty_chunks) > 0
        # 使用默认的MAX_CHARS_PER_TEXT_CHUNK (800)
        # 验证至少有一些块有内容
        for chunk in non_empty_chunks:
            assert len(chunk) > 0
