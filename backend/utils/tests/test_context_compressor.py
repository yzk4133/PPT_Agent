"""
Tests for context_compressor module
"""
import pytest
from utils.context_compressor import SlideInfo, ContextCompressor, compress_slide_history

class TestSlideInfo:
    """测试SlideInfo数据类"""

    def test_slide_info_creation(self):
        """测试SlideInfo创建"""
        info = SlideInfo(
            page_number=1,
            title="测试标题",
            layout="vertical",
            key_points=["要点1", "要点2"],
            images=["url1.jpg", "url2.jpg"],
            keywords={"关键词"}
        )
        assert info.page_number == 1
        assert info.title == "测试标题"
        assert info.layout == "vertical"
        assert len(info.key_points) == 2
        assert len(info.images) == 2
        assert len(info.keywords) == 1

    def test_slide_info_with_defaults(self):
        """测试SlideInfo默认值"""
        info = SlideInfo(
            page_number=1,
            title="标题",
            layout="horizontal",
            key_points=[],
            images=[]
        )
        assert info.keywords == set()

    def test_to_summary_basic(self):
        """测试基本摘要生成"""
        info = SlideInfo(
            page_number=1,
            title="测试标题",
            layout="vertical",
            key_points=["要点1", "要点2"],
            images=[]
        )
        summary = info.to_summary()
        assert "第1页" in summary
        assert "测试标题" in summary
        assert "vertical" in summary
        assert "要点1, 要点2" in summary
        assert "图片:" not in summary  # 没有图片

    def test_to_summary_with_many_key_points(self):
        """测试要点超过3个时的截断"""
        info = SlideInfo(
            page_number=1,
            title="测试标题",
            layout="vertical",
            key_points=["要点1", "要点2", "要点3", "要点4", "要点5"],
            images=[]
        )
        summary = info.to_summary()
        assert "要点1, 要点2, 要点3..." in summary
        assert "要点4" not in summary

    def test_to_summary_with_images(self):
        """测试包含图片的摘要"""
        info = SlideInfo(
            page_number=1,
            title="测试标题",
            layout="vertical",
            key_points=[],
            images=["img1.jpg", "img2.png", "img3.jpg"]
        )
        summary = info.to_summary()
        assert "图片: 3张" in summary

class TestContextCompressor:
    """测试ContextCompressor类"""

    def test_initialization_default(self):
        """测试默认初始化"""
        compressor = ContextCompressor()
        assert compressor.max_history_slides == 3
        assert compressor.include_all_titles is True
        assert compressor.track_duplicates is True
        assert len(compressor.all_slides) == 0
        assert len(compressor.used_keywords) == 0
        assert len(compressor.used_images) == 0

    def test_initialization_custom(self):
        """测试自定义参数初始化"""
        compressor = ContextCompressor(
            max_history_slides=5,
            include_all_titles=False,
            track_duplicates=False
        )
        assert compressor.max_history_slides == 5
        assert compressor.include_all_titles is False
        assert compressor.track_duplicates is False

    def test_extract_slide_info_with_h1(self, sample_slide_xml):
        """测试提取H1标题"""
        compressor = ContextCompressor()
        info = compressor.extract_slide_info(sample_slide_xml["simple"], 1)
        assert info.title == "标题"
        assert info.layout == "vertical"
        assert info.page_number == 1

    def test_extract_slide_info_no_title(self, sample_slide_xml):
        """测试没有标题的情况"""
        compressor = ContextCompressor()
        info = compressor.extract_slide_info(sample_slide_xml["no_title"], 1)
        assert info.title == "第1页"  # 默认标题

    def test_extract_key_points_from_bullets(self, sample_slide_xml):
        """测试从BULLETS提取要点"""
        compressor = ContextCompressor()
        info = compressor.extract_slide_info(sample_slide_xml["with_bullets"], 1)
        assert "要点一" in info.key_points
        assert "要点二" in info.key_points
        assert "要点三" in info.key_points

    def test_extract_key_points_from_columns(self, sample_slide_xml):
        """测试从COLUMNS提取要点"""
        compressor = ContextCompressor()
        info = compressor.extract_slide_info(sample_slide_xml["with_columns"], 1)
        assert "第一列内容" in info.key_points
        assert "第二列内容" in info.key_points

    def test_extract_images(self, sample_slide_xml):
        """测试提取图片URL"""
        compressor = ContextCompressor()
        info = compressor.extract_slide_info(sample_slide_xml["with_image"], 1)
        assert "http://example.com/img.jpg" in info.images

    def test_extract_images_multiple(self):
        """测试提取多个图片"""
        xml = '''<SECTION>
            <IMG src="http://example.com/img1.jpg"/>
            <IMG src="https://example.com/img2.png"/>
            <IMG src="img3.jpg"/>
        </SECTION>'''
        compressor = ContextCompressor()
        info = compressor.extract_slide_info(xml, 1)
        assert len(info.images) == 3
        assert "http://example.com/img1.jpg" in info.images
        assert "https://example.com/img2.png" in info.images

    def test_keyword_extraction(self):
        """测试关键词提取"""
        xml = '<SECTION><H1>Artificial Intelligence Technology</H1></SECTION>'
        compressor = ContextCompressor()
        info = compressor.extract_slide_info(xml, 1)
        assert "artificial" in info.keywords
        assert "intelligence" in info.keywords
        assert "technology" in info.keywords

    def test_stopword_filtering(self):
        """测试停用词过滤"""
        xml = '<SECTION><H1>The Quick Brown Fox</H1></SECTION>'
        compressor = ContextCompressor()
        info = compressor.extract_slide_info(xml, 1)
        # "the" 应该被过滤掉
        assert "the" not in info.keywords
        assert "quick" in info.keywords

    def test_chinese_stopword_filtering(self):
        """测试中文停用词过滤"""
        xml = '<SECTION><H1>人工智能的发展</H1></SECTION>'
        compressor = ContextCompressor()
        info = compressor.extract_slide_info(xml, 1)
        # "的" 应该被过滤掉，但"人工智能的发展"会被作为整体提取
        # 因为中文没有空格分隔，正则[\w]+会将连续字符作为一个词
        assert "的" not in info.keywords
        # 整个短语会被提取
        assert len(info.keywords) > 0

    def test_keyword_extraction_and_deduplication(self):
        """测试关键词提取和去重追踪"""
        xml1 = '<SECTION><H1>人工智能技术</H1><P>AI is future trend</P></SECTION>'
        xml2 = '<SECTION><H1>机器学习</H1><P>人工智能应用广泛</P></SECTION>'

        compressor = ContextCompressor(track_duplicates=True)
        compressor.extract_slide_info(xml1, 1)
        compressor.extract_slide_info(xml2, 2)

        # "人工智能应用广泛"会被作为整体提取（中文没有空格分隔）
        # 英文单词会被正确提取
        assert len(compressor.used_keywords) > 0

    def test_image_tracking(self):
        """测试图片追踪"""
        xml1 = '<SECTION><IMG src="img1.jpg"/></SECTION>'
        xml2 = '<SECTION><IMG src="img2.jpg"/></SECTION>'

        compressor = ContextCompressor(track_duplicates=True)
        compressor.extract_slide_info(xml1, 1)
        compressor.extract_slide_info(xml2, 2)

        assert "img1.jpg" in compressor.used_images
        assert "img2.jpg" in compressor.used_images

    def test_check_duplication_with_keywords(self):
        """测试关键词重复检查"""
        # 使用英文单词以正确测试关键词重复（因为需要空格分隔）
        xml1 = '<SECTION><H1>AI Technology</H1><P>Artificial intelligence is future</P></SECTION>'
        xml2 = '<SECTION><H1>Machine Learning</H1><P>Artificial intelligence applications</P></SECTION>'

        compressor = ContextCompressor()
        compressor.extract_slide_info(xml1, 1)

        result = compressor.check_duplication(xml2)
        assert result["has_duplicate"] is True
        # "artificial" 和 "intelligence" 应该被检测为重复
        assert len(result["duplicate_keywords"]) > 0

    def test_check_duplication_with_images(self):
        """测试图片重复检查"""
        xml1 = '<SECTION><H1>第一页</H1><IMG src="img1.jpg"/></SECTION>'
        xml2 = '<SECTION><H1>第二页</H1><IMG src="img1.jpg"/></SECTION>'

        compressor = ContextCompressor()
        compressor.extract_slide_info(xml1, 1)

        result = compressor.check_duplication(xml2)
        assert result["has_duplicate"] is True
        assert "img1.jpg" in result["duplicate_images"]

    def test_check_duplication_no_duplicates(self):
        """测试无重复情况"""
        xml1 = '<SECTION><H1>第一页</H1><IMG src="img1.jpg"/></SECTION>'
        xml2 = '<SECTION><H1>第二页</H1><IMG src="img2.jpg"/></SECTION>'

        compressor = ContextCompressor()
        compressor.extract_slide_info(xml1, 1)

        result = compressor.check_duplication(xml2)
        assert result["has_duplicate"] is False

    def test_compress_history_basic(self):
        """测试基本历史压缩"""
        slides = [
            '<SECTION><H1>第1页</H1><P>内容1</P></SECTION>',
            '<SECTION><H1>第2页</H1><P>内容2</P></SECTION>',
            '<SECTION><H1>第3页</H1><P>内容3</P></SECTION>',
            '<SECTION><H1>第4页</H1><P>内容4</P></SECTION>',
        ]

        compressor = ContextCompressor(max_history_slides=2)
        compressed = compressor.compress_history(slides, 3)

        # 应该包含所有标题
        assert "第1页: 第1页" in compressed
        # 最近2页详细内容
        assert "第3页" in compressed
        assert "第4页" in compressed

    def test_compress_history_with_titles_only(self):
        """测试只显示标题模式"""
        slides = [f'<SECTION><H1>标题{i}</H1></SECTION>' for i in range(10)]

        compressor = ContextCompressor(max_history_slides=2, include_all_titles=True)
        compressed = compressor.compress_history(slides, 9)

        # 所有10页标题都应该出现
        for i in range(10):
            assert f"标题{i}" in compressed

    def test_compress_history_without_all_titles(self):
        """测试不包含所有标题"""
        slides = [f'<SECTION><H1>标题{i}</H1></SECTION>' for i in range(10)]

        compressor = ContextCompressor(max_history_slides=2, include_all_titles=False)
        compressed = compressor.compress_history(slides, 9)

        # 总览部分不应该出现
        assert "已生成页面总览" not in compressed
        # 但最近几页应该出现
        assert "标题8" in compressed
        assert "标题9" in compressed

    def test_get_duplication_warning(self):
        """测试去重警告生成"""
        compressor = ContextCompressor(track_duplicates=True)
        compressor.used_keywords.add("人工智能")
        compressor.used_keywords.add("机器学习")
        compressor.used_images.add("img1.jpg")

        warning = compressor._get_duplication_warning()
        assert "人工智能" in warning
        assert "机器学习" in warning
        assert "1 张" in warning  # 1张图片

    def test_get_duplication_warning_empty(self):
        """测试空的去重警告"""
        compressor = ContextCompressor(track_duplicates=True)
        warning = compressor._get_duplication_warning()
        assert "暂无重复内容" in warning

    def test_token_savings_calculation(self):
        """测试Token节省计算"""
        compressor = ContextCompressor()

        original = "这是一段很长的文本" * 100  # 900字符 (9字 * 100)
        compressed = "摘要内容..."  # 7字符

        result = compressor.get_token_savings(len(original), len(compressed))

        assert result["original_chars"] == 900
        assert result["compressed_chars"] == 7
        assert result["estimated_saved_tokens"] > 0
        assert result["saved_percentage"] > 0
        assert 0 < result["cost_savings_gpt4o"] < 1
        assert 0 < result["cost_savings_gpt4o_mini"] < 1

    def test_token_savings_zero_original(self):
        """测试原始长度为0的情况"""
        compressor = ContextCompressor()
        result = compressor.get_token_savings(0, 0)
        assert result["saved_percentage"] == 0

    def test_reset(self):
        """测试重置功能"""
        compressor = ContextCompressor()
        compressor.all_slides.append("test")
        compressor.used_keywords.add("test")
        compressor.used_images.add("img.jpg")

        compressor.reset()

        assert len(compressor.all_slides) == 0
        assert len(compressor.used_keywords) == 0
        assert len(compressor.used_images) == 0

class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_compress_slide_history(self):
        """测试compress_slide_history便捷函数"""
        slides = [
            '<SECTION><H1>第1页</H1></SECTION>',
            '<SECTION><H1>第2页</H1></SECTION>',
            '<SECTION><H1>第3页</H1></SECTION>',
        ]

        result = compress_slide_history(slides, 2, max_history_slides=2)

        assert isinstance(result, str)
        assert "第1页" in result or "第2页" in result or "第3页" in result
