"""
End-to-end integration tests for PPT generation
"""
import pytest
from unittest.mock import MagicMock, patch
import tempfile
import os
import sys

# Add parent directories to path

@pytest.fixture
def complete_ppt_data():
    """完整的PPT测试数据"""
    return {
        "title": "完整测试演示文稿",
        "sections": [
            {
                "id": "intro",
                "content": [
                    {"type": "h1", "children": [{"text": "引言"}]},
                    {"type": "p", "children": [{"text": "这是引言部分的详细内容，介绍整个演示文稿的主题和目的。"}]},
                    {"type": "bullets", "children": [
                        {"type": "bullet", "children": [
                            {"type": "h3", "children": [{"text": "目标1"}]},
                            {"type": "p", "children": [{"text": "详细说明目标1的具体内容"}]}
                        ]},
                        {"type": "bullet", "children": [
                            {"type": "h3", "children": [{"text": "目标2"}]},
                            {"type": "p", "children": [{"text": "详细说明目标2的具体内容"}]}
                        ]},
                        {"type": "bullet", "children": [
                            {"type": "h3", "children": [{"text": "目标3"}]},
                            {"type": "p", "children": [{"text": "详细说明目标3的具体内容"}]}
                        ]}
                    ]}
                ],
                "rootImage": {
                    "url": "http://example.com/intro.jpg",
                    "alt": "引言图片",
                    "background": False
                }
            },
            {
                "id": "chapter1",
                "content": [
                    {"type": "h1", "children": [{"text": "第一章"}]},
                    {"type": "p", "children": [{"text": "这是第一章的内容，包含了详细的论述和分析。通过这一章，读者可以了解到核心概念和理论基础。"}]},
                    {"type": "bullets", "children": [
                        {"type": "bullet", "children": [
                            {"type": "h3", "children": [{"text": "概念1"}]},
                            {"type": "p", "children": [{"text": "概念1的详细解释"}]}
                        ]},
                        {"type": "bullet", "children": [
                            {"type": "h3", "children": [{"text": "概念2"}]},
                            {"type": "p", "children": [{"text": "概念2的详细解释"}]}
                        ]},
                        {"type": "bullet", "children": [
                            {"type": "h3", "children": [{"text": "概念3"}]},
                            {"type": "p", "children": [{"text": "概念3的详细解释"}]}
                        ]}
                    ]}
                ],
                "rootImage": {
                    "url": "http://example.com/chapter1.jpg",
                    "alt": "第一章配图",
                    "background": False
                }
            },
            {
                "id": "chapter2",
                "content": [
                    {"type": "h1", "children": [{"text": "第二章"}]},
                    {"type": "p", "children": [{"text": "第一段内容"}]},
                    {"type": "p", "children": [{"text": "第二段内容"}]}
                ]
            }
        ],
        "references": [
            "参考文献1: 张三, 李四. 人工智能研究进展. 计算机学报, 2023, 46(1): 1-15.",
            "参考文献2: Wang, J., & Smith, M. Deep Learning Applications. MIT Press, 2022.",
            "参考文献3: Johnson, A. et al. Neural Networks in Practice. IEEE Transactions, 2024.",
            "参考文献4: 赵五. 机器学习算法详解. 清华大学出版社, 2021.",
            "参考文献5: Brown, L. Data Science Fundamentals. O'Reilly Media, 2023.",
            "参考文献6: 陈六. 自然语言处理技术. 电子工业出版社, 2024."
        ]
    }

class TestContextCompressorIntegration:
    """上下文压缩器集成测试"""

    def test_full_compression_workflow(self):
        """测试完整的压缩工作流"""
        from utils.context_compressor import ContextCompressor

        # 创建多个幻灯片XML
        slides = [
            '''<SECTION layout="vertical">
                <H1>第一页：引言</H1>
                <BULLETS>
                    <P>要点1：人工智能的发展历史</P>
                    <P>要点2：深度学习的突破</P>
                </BULLETS>
                <IMG src="http://example.com/img1.jpg"/>
            </SECTION>''',
            '''<SECTION layout="vertical">
                <H1>第二页：核心技术</H1>
                <BULLETS>
                    <P>要点1：神经网络架构</P>
                    <P>要点2：反向传播算法</P>
                </BULLETS>
                <IMG src="http://example.com/img2.jpg"/>
            </SECTION>''',
            '''<SECTION layout="vertical">
                <H1>第三页：应用场景</H1>
                <BULLETS>
                    <P>要点1：计算机视觉</P>
                    <P>要点2：自然语言处理</P>
                </BULLETS>
                <IMG src="http://example.com/img3.jpg"/>
            </SECTION>''',
            '''<SECTION layout="vertical">
                <H1>第四页：未来展望</H1>
                <P>人工智能将继续快速发展...</P>
            </SECTION>'''
        ]

        compressor = ContextCompressor(max_history_slides=2, include_all_titles=True)

        # 提取所有页面信息
        for i, slide_xml in enumerate(slides):
            info = compressor.extract_slide_info(slide_xml, i + 1)
            assert info.page_number == i + 1
            assert info.title is not None

        # 压缩历史
        compressed = compressor.compress_history(slides, 3)

        # 验证压缩结果
        assert "第一页：引言" in compressed
        assert "第二页：核心技术" in compressed
        assert "第三页：应用场景" in compressed
        assert "第四页：未来展望" in compressed

        # 检查重复检测
        new_slide = '''<SECTION>
            <H1>新页面</H1>
            <IMG src="http://example.com/img1.jpg"/>
        </SECTION>'''

        result = compressor.check_duplication(new_slide)
        assert result["has_duplicate"] is True
        assert "img1.jpg" in result["duplicate_images"]

class TestTextProcessorIntegration:
    """文本处理器集成测试"""

    def test_html_to_ppt_workflow(self):
        """测试从HTML到PPT的文本处理工作流"""
        from utils.save_ppt.text_processor import TextProcessor

        processor = TextProcessor()

        # 原始HTML内容
        html_content = """
        <h1>这是一级标题</h1>
        <p>这是第一段内容，包含了一些<strong>加粗</strong>文本。</p>
        <p>这是第二段内容。</p>
        <ul>
            <li>列表项1</li>
            <li>列表项2</li>
            <li>列表项3</li>
        </ul>
        """

        # 清理HTML
        clean_content = processor.remove_html_tags(html_content)
        assert "<h1>" not in clean_content
        assert "<p>" not in clean_content

        # 截断长文本
        long_text = "这是一段很长的文本。" * 100
        truncated = processor.truncate_text(long_text, max_chars=200)
        assert len(truncated) <= 203  # 200 + "..."

        # 分块
        chunks = processor.split_text_into_chunks(clean_content, max_chars=100)
        assert len(chunks) >= 1

class TestPresentationGenerationIntegration:
    """演示文稿生成集成测试"""

    @patch('utils.save_ppt.ppt_generator.Presentation')
    @patch('utils.save_ppt.ppt_generator.requests.get')
    def test_complete_ppt_generation(self, mock_requests_get, mock_ppt_class, complete_ppt_data):
        """测试完整的PPT生成流程"""
        # Mock图片下载
        mock_response = MagicMock()
        mock_response.content = b"fake image data"
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        # Mock Presentation
        mock_pres = MagicMock()
        mock_ppt_class.return_value = mock_pres
        mock_pres.slide_layouts = [MagicMock(name=f"layout{i}") for i in range(31)]
        mock_pres.slides = MagicMock()
        mock_pres.slides.__len__ = MagicMock(return_value=0)

        # Mock slide
        mock_slide = MagicMock()
        mock_slide.slide_layout = MagicMock()
        mock_slide.slide_layout.name = "Test"
        mock_slide.slide_layout.index = lambda: 0

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
            text_frame.paragraphs = [MagicMock()]
            text_frame.paragraphs[0].alignment = 0
            text_frame.paragraphs[0].font = MagicMock()
            text_frame.paragraphs[0].font.size = 18
            shape.text_frame = text_frame
            return shape

        mock_slide.shapes = [
            create_text_shape(2, "Title"),
            create_text_shape(3, "Content"),
            create_text_shape(9, "Date")
        ]

        with patch.object(mock_pres.slides, 'add_slide', return_value=mock_slide):
            from utils.save_ppt.generator import PresentationGenerator

            generator = PresentationGenerator()

            # Mock策略的create_slide方法
            for strategy_name, strategy in generator.strategies.items():
                strategy.create_slide = MagicMock()

            # 生成演示文稿
            with patch.object(mock_pres, 'save'):
                output_path = generator.generate_presentation(complete_ppt_data)

                # 验证各策略被调用
                assert generator.strategies["title"].create_slide.called
                assert generator.strategies["end"].create_slide.called

                # 验证参考文献策略被调用（有参考文献）
                assert generator.strategies["references"].create_slide.called

class TestErrorHandlingIntegration:
    """错误处理集成测试"""

    def test_invalid_xml_handling(self):
        """测试无效XML处理"""
        from utils.context_compressor import ContextCompressor

        compressor = ContextCompressor()

        # 各种边界情况
        invalid_xmls = [
            "",  # 空字符串
            "<SECTION></SECTION>",  # 空标签
            "No tags at all",  # 无标签
            "<INVALID>Invalid tag</INVALID>",  # 无效标签
            "<<H1>>Double brackets<<</H1>>",  # 双括号
        ]

        for xml in invalid_xmls:
            try:
                info = compressor.extract_slide_info(xml, 1)
                # 应该返回一个SlideInfo对象，即使内容不完整
                assert info is not None
                assert info.page_number == 1
            except Exception as e:
                # 如果抛出异常，应该是可预期的异常
                assert not isinstance(e, (AttributeError, TypeError))

    def test_empty_sections_handling(self):
        """测试空章节处理"""
        from utils.save_ppt.ppt_generator import PresentationGenerator

        with patch('utils.save_ppt.ppt_generator.Presentation'):
            generator = PresentationGenerator()

            # 空章节
            content_blocks = []
            title, main_text, bullets = generator._parse_content_blocks(content_blocks)

            assert title == ""
            assert main_text == ""
            assert bullets == []

    def test_very_long_content_handling(self):
        """测试超长内容处理"""
        from utils.save_ppt.text_processor import TextProcessor

        processor = TextProcessor()

        # 创建超长文本
        very_long_text = "这是一个很长的句子。" * 10000

        # 分块处理
        chunks = processor.split_text_into_chunks(very_long_text, max_chars=800)

        # 验证分块结果
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 850  # 允许一些余量

class TestTokenSavingsIntegration:
    """Token节省集成测试"""

    def test_compression_savings_calculation(self):
        """测试压缩节省计算"""
        from utils.context_compressor import ContextCompressor

        # 创建大量幻灯片
        slides = []
        for i in range(20):
            slide_xml = f'''<SECTION layout="vertical">
                <H1>第{i+1}页标题</H1>
                <BULLETS>
                    <P>要点1：详细内容描述</P>
                    <P>要点2：详细内容描述</P>
                    <P>要点3：详细内容描述</P>
                    <P>要点4：详细内容描述</P>
                    <P>要点5：详细内容描述</P>
                </BULLETS>
                <IMG src="http://example.com/img{i}.jpg"/>
            </SECTION>'''
            slides.append(slide_xml)

        compressor = ContextCompressor(max_history_slides=3, include_all_titles=True)

        # 计算原始长度
        original_length = sum(len(slide) for slide in slides)

        # 压缩
        compressed = compressor.compress_history(slides, 19)
        compressed_length = len(compressed)

        # 计算节省
        savings = compressor.get_token_savings(original_length, compressed_length)

        # 验证节省结果
        assert savings["original_chars"] > 0
        assert savings["compressed_chars"] > 0
        assert savings["estimated_saved_tokens"] > 0
        assert savings["saved_percentage"] > 0
        assert savings["cost_savings_gpt4o"] > 0
        assert savings["cost_savings_gpt4o_mini"] > 0

        # 压缩后应该显著减小
        assert compressed_length < original_length
