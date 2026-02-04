"""
Tests for PresentationGenerator class in ppt_generator module
"""
import pytest
from unittest.mock import MagicMock, patch, Mock
import tempfile
import os
import sys

# Add parent directory to path

from utils.save_ppt.ppt_generator import PresentationGenerator, SlideConfig

@pytest.fixture
def mock_template():
    """创建临时模板文件"""
    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    try:
        os.unlink(temp_path)
    except:
        pass

@pytest.fixture
def mock_presentation():
    """Mock Presentation对象"""
    pres = MagicMock()
    pres.slide_width = 9144000
    pres.slide_height = 6858000
    pres.slide_layouts = [MagicMock(name=f"layout{i}") for i in range(31)]
    pres.slides = MagicMock()
    pres.slides.__len__ = MagicMock(return_value=0)
    return pres

@pytest.fixture
def mock_slide():
    """Mock Slide对象"""
    slide = MagicMock()

    # 创建文本形状工厂函数
    def create_text_shape(shape_id, name):
        shape = MagicMock()
        shape.shape_id = shape_id
        shape.has_text_frame = True
        shape.name = name
        shape.is_placeholder = False
        shape.text = ""

        text_frame = MagicMock()
        text_frame.word_wrap = True
        text_frame.auto_size = 1
        text_frame.vertical_anchor = 3
        text_frame.margin_left = 0.1
        text_frame.margin_right = 0.1
        text_frame.margin_top = 0.05
        text_frame.margin_bottom = 0.05
        text_frame.paragraphs = [MagicMock()]

        p = text_frame.paragraphs[0]
        p.alignment = 0
        p.font = MagicMock()
        p.font.size = 18

        shape.text_frame = text_frame
        return shape

    # 创建多个形状
    slide.shapes = [
        create_text_shape(2, "Title"),
        create_text_shape(3, "Content"),
        create_text_shape(4, "Content2"),
        create_text_shape(9, "Date")
    ]

    slide.slide_layout = MagicMock()
    slide.slide_layout.name = "Test Layout"
    slide.slide_layout.index = lambda: 0

    return slide

class TestPresentationGenerator:
    """测试PresentationGenerator类"""

    @patch('utils.save_ppt.ppt_generator.Presentation')
    def test_init_with_template(self, mock_ppt_class, mock_presentation, mock_template):
        """测试使用模板初始化"""
        mock_ppt_class.return_value = mock_presentation

        generator = PresentationGenerator(template_file_name=mock_template)

        assert generator.presentation is not None
        assert generator.config is not None
        assert isinstance(generator.config, SlideConfig)
        assert generator.slide_counter == 0
        assert "title" in generator.strategies
        assert "content" in generator.strategies
        assert "toc" in generator.strategies
        assert "image" in generator.strategies
        assert "subsection" in generator.strategies
        assert "references" in generator.strategies
        assert "end" in generator.strategies

    @patch('utils.save_ppt.ppt_generator.Presentation')
    def test_init_missing_template(self, mock_ppt_class):
        """测试模板文件不存在"""
        mock_ppt_class.side_effect = FileNotFoundError("Template not found")

        with pytest.raises(FileNotFoundError):
            PresentationGenerator(template_file_name="nonexistent.pptx")

    def test_parse_content_blocks_with_h1(self):
        """测试解析H1标题"""
        content_blocks = [
            {"type": "h1", "children": [{"text": "测试标题"}]},
            {"type": "p", "children": [{"text": "段落内容"}]}
        ]

        with patch('utils.save_ppt.ppt_generator.Presentation'):
            generator = PresentationGenerator()
            title, main_text, bullets = generator._parse_content_blocks(content_blocks)

            assert title == "测试标题"
            assert "段落内容" in main_text

    def test_parse_content_blocks_with_bullets(self):
        """测试解析项目列表"""
        content_blocks = [
            {"type": "h1", "children": [{"text": "标题"}]},
            {"type": "bullets", "children": [
                {"type": "bullet", "children": [
                    {"type": "h3", "children": [{"text": "要点1"}]},
                    {"type": "p", "children": [{"text": "详情1"}]}
                ]},
                {"type": "bullet", "children": [
                    {"type": "h3", "children": [{"text": "要点2"}]},
                    {"type": "p", "children": [{"text": "详情2"}]}
                ]}
            ]}
        ]

        with patch('utils.save_ppt.ppt_generator.Presentation'):
            generator = PresentationGenerator()
            title, main_text, bullets = generator._parse_content_blocks(content_blocks)

            assert title == "标题"
            assert len(bullets) == 2
            assert bullets[0]["summary"] == "要点1"
            assert bullets[0]["detail"] == "详情1"

    def test_parse_content_blocks_mixed(self):
        """测试混合内容"""
        content_blocks = [
            {"type": "h1", "children": [{"text": "标题"}]},
            {"type": "p", "children": [{"text": "段落1"}]},
            {"type": "p", "children": [{"text": "段落2"}]},
            {"type": "bullets", "children": [
                {"type": "bullet", "children": [
                    {"type": "h3", "children": [{"text": "要点1"}]},
                    {"type": "p", "children": [{"text": "详情1"}]}
                ]}
            ]}
        ]

        with patch('utils.save_ppt.ppt_generator.Presentation'):
            generator = PresentationGenerator()
            title, main_text, bullets = generator._parse_content_blocks(content_blocks)

            assert "段落1" in main_text
            assert "段落2" in main_text
            assert len(bullets) == 1

    def test_format_bullet_points_as_text(self):
        """测试bullet points格式化"""
        with patch('utils.save_ppt.ppt_generator.Presentation'):
            generator = PresentationGenerator()

            bullets = [
                {"summary": "要点1", "detail": "详情1"},
                {"summary": "要点2", "detail": "详情2"},
                {"summary": "", "detail": "只有详情"}
            ]

            result = generator._format_bullet_points_as_text(bullets)

            assert "1. 要点1" in result
            assert "详情1" in result
            assert "2. 要点2" in result
            assert "详情2" in result

    @patch('utils.save_ppt.ppt_generator.Presentation')
    def test_generate_presentation_invalid_input(self, mock_ppt_class):
        """测试无效输入"""
        mock_pres = MagicMock()
        mock_ppt_class.return_value = mock_pres
        mock_pres.slide_layouts = [MagicMock() for _ in range(31)]

        generator = PresentationGenerator()

        # 无效输入
        result = generator.generate_presentation("not a dict")
        assert result is None

        result = generator.generate_presentation(None)
        assert result is None

    @patch('utils.save_ppt.ppt_generator.Presentation')
    def test_generate_presentation_with_title(self, mock_ppt_class, mock_slide):
        """测试生成带标题的演示文稿"""
        mock_pres = MagicMock()
        mock_ppt_class.return_value = mock_pres
        mock_pres.slide_layouts = [MagicMock(name=f"layout{i}") for i in range(31)]
        mock_pres.slides = MagicMock()
        mock_pres.slides.__len__ = MagicMock(return_value=0)

        json_data = {
            "title": "测试演示文稿",
            "sections": [
                {
                    "id": "section1",
                    "content": [
                        {"type": "h1", "children": [{"text": "第一章"}]},
                        {"type": "p", "children": [{"text": "内容1"}]}
                    ]
                }
            ],
            "references": []
        }

        with patch.object(mock_pres.slides, 'add_slide', return_value=mock_slide):
            with patch.object(mock_pres, 'save'):
                generator = PresentationGenerator()

                # Mock策略
                for strategy_name, strategy in generator.strategies.items():
                    strategy.create_slide = MagicMock()

                result = generator.generate_presentation(json_data)

                # 应该调用标题页策略
                generator.strategies["title"].create_slide.assert_called()
                generator.strategies["end"].create_slide.assert_called()

    @patch('utils.save_ppt.ppt_generator.Presentation')
    def test_generate_presentation_empty_sections(self, mock_ppt_class):
        """测试空章节"""
        mock_pres = MagicMock()
        mock_ppt_class.return_value = mock_pres
        mock_pres.slide_layouts = [MagicMock() for _ in range(31)]

        json_data = {
            "title": "测试",
            "sections": [],
            "references": []
        }

        with patch.object(mock_pres, 'save'):
            generator = PresentationGenerator()

            for strategy_name, strategy in generator.strategies.items():
                strategy.create_slide = MagicMock()

            result = generator.generate_presentation(json_data)

            # 应该至少创建标题页和结束页
            generator.strategies["title"].create_slide.assert_called()
            generator.strategies["end"].create_slide.assert_called()

    @patch('utils.save_ppt.ppt_generator.Presentation')
    def test_generate_presentation_with_references(self, mock_ppt_class, mock_slide):
        """测试带参考文献的演示文稿"""
        mock_pres = MagicMock()
        mock_ppt_class.return_value = mock_pres
        mock_pres.slide_layouts = [MagicMock(name=f"layout{i}") for i in range(31)]
        mock_pres.slides = MagicMock()
        mock_pres.slides.__len__ = MagicMock(return_value=0)

        json_data = {
            "title": "测试",
            "sections": [],
            "references": ["参考文献1", "参考文献2", "参考文献3"]
        }

        with patch.object(mock_pres.slides, 'add_slide', return_value=mock_slide):
            with patch.object(mock_pres, 'save'):
                generator = PresentationGenerator()

                for strategy_name, strategy in generator.strategies.items():
                    strategy.create_slide = MagicMock()

                result = generator.generate_presentation(json_data)

                # 应该调用参考文献策略
                generator.strategies["references"].create_slide.assert_called_once()

    @patch('utils.save_ppt.ppt_generator.Presentation')
    def test_generate_presentation_file_saving(self, mock_ppt_class, mock_slide):
        """测试文件保存"""
        mock_pres = MagicMock()
        mock_ppt_class.return_value = mock_pres
        mock_pres.slide_layouts = [MagicMock(name=f"layout{i}") for i in range(31)]
        mock_pres.slides = MagicMock()
        mock_pres.slides.__len__ = MagicMock(return_value=0)

        json_data = {
            "title": "测试演示文稿",
            "sections": [],
            "references": []
        }

        with patch.object(mock_pres.slides, 'add_slide', return_value=mock_slide):
            with patch('builtins.open', create=True) as mock_open:
                with patch.object(mock_pres, 'save') as mock_save:
                    generator = PresentationGenerator()

                    for strategy_name, strategy in generator.strategies.items():
                        strategy.create_slide = MagicMock()

                    result = generator.generate_presentation(json_data)

                    # 验证save被调用
                    mock_save.assert_called_once()
                    assert result is not None

class TestStartGeneratePresentation:
    """测试start_generate_presentation入口函数"""

    @patch('utils.save_ppt.ppt_generator.PresentationGenerator')
    def test_start_with_dict(self, mock_gen_class):
        """测试字典输入"""
        from utils.save_ppt.ppt_generator import start_generate_presentation

        mock_gen = MagicMock()
        mock_gen_class.return_value = mock_gen
        mock_gen.generate_presentation.return_value = "output.pptx"

        json_data = {"title": "测试", "sections": [], "references": []}
        result = start_generate_presentation(json_data)

        assert result == "output.pptx"
        mock_gen.generate_presentation.assert_called_once()

    @patch('utils.save_ppt.ppt_generator.PresentationGenerator')
    def test_start_with_json_string(self, mock_gen_class):
        """测试JSON字符串输入"""
        from utils.save_ppt.ppt_generator import start_generate_presentation
        import json

        mock_gen = MagicMock()
        mock_gen_class.return_value = mock_gen
        mock_gen.generate_presentation.return_value = "output.pptx"

        json_data = {"title": "测试", "sections": [], "references": []}
        json_string = json.dumps(json_data)

        result = start_generate_presentation(json_string)

        assert result == "output.pptx"

    def test_start_with_invalid_json_string(self):
        """测试无效JSON字符串"""
        from utils.save_ppt.ppt_generator import start_generate_presentation

        result = start_generate_presentation("invalid json")
        assert result is None

    @patch('utils.save_ppt.ppt_generator.PresentationGenerator')
    def test_start_generation_failure(self, mock_gen_class):
        """测试生成失败"""
        from utils.save_ppt.ppt_generator import start_generate_presentation

        mock_gen = MagicMock()
        mock_gen_class.return_value = mock_gen
        mock_gen.generate_presentation.return_value = None

        json_data = {"title": "测试", "sections": [], "references": []}
        result = start_generate_presentation(json_data)

        assert result is None
