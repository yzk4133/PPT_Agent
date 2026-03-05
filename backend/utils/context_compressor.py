"""
上下文压缩工具

用于压缩 PPT 生成过程中的历史上下文，减少 token 消耗
"""

import re
import logging
from typing import List, Dict, Set

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

class SlideInfo(BaseModel):
    """压缩后的单页信息"""
    page_number: int = Field(ge=1, description="页码")
    title: str = Field(min_length=1, description="页面标题")
    layout: str = Field(default="vertical", description="布局类型")
    key_points: List[str] = Field(default_factory=list, description="关键要点")
    images: List[str] = Field(default_factory=list, description="图片URL列表")
    keywords: Set[str] = Field(default_factory=set, description="关键词集合")

    @field_validator('keywords', mode='before')
    @classmethod
    def validate_keywords(cls, v):
        """验证并转换关键词"""
        if isinstance(v, list):
            return set(v)
        return v

    def to_summary(self) -> str:
        """转换为简洁的摘要文本"""
        summary = f"""
【第{self.page_number}页】{self.title}
布局: {self.layout}
要点: {', '.join(self.key_points[:3])}{'...' if len(self.key_points) > 3 else ''}
"""
        if self.images:
            summary += f"图片: {len(self.images)}张\n"
        return summary.strip()

    @classmethod
    def from_dict(cls, data: Dict) -> "SlideInfo":
        """从字典创建实例（向后兼容）"""
        keywords = data.get("keywords", set())
        if isinstance(keywords, list):
            keywords = set(keywords)

        return cls(
            page_number=data.get("page_number", 1),
            title=data.get("title", ""),
            layout=data.get("layout", "vertical"),
            key_points=data.get("key_points", []),
            images=data.get("images", []),
            keywords=keywords
        )

class ContextCompressor:
    """
    上下文压缩器

    功能：
    1. 从完整的 XML 中提取关键信息
    2. 去重追踪（关键词、图片）
    3. 智能选择需要传递的历史页面
    """

    def __init__(
        self,
        max_history_slides: int = 3,
        include_all_titles: bool = True,
        track_duplicates: bool = True
    ):
        """
        Args:
            max_history_slides: 保留最近几页的完整信息（默认最近3页）
            include_all_titles: 是否包含所有页面的标题（即使超出 max_history_slides）
            track_duplicates: 是否追踪重复内容（关键词、图片）
        """
        self.max_history_slides = max_history_slides
        self.include_all_titles = include_all_titles
        self.track_duplicates = track_duplicates

        # 追踪所有历史页面（用于去重）
        self.all_slides: List[SlideInfo] = []
        self.used_keywords: Set[str] = set()
        self.used_images: Set[str] = set()

    def extract_slide_info(self, slide_xml: str, page_number: int) -> SlideInfo:
        """
        从 XML 中提取关键信息

        Args:
            slide_xml: 完整的 XML 幻灯片内容
            page_number: 页码

        Returns:
            SlideInfo: 压缩后的页面信息
        """
        # 提取标题 (H1 标签)
        title_match = re.search(r'<H1>(.*?)</H1>', slide_xml, re.DOTALL)
        title = title_match.group(1).strip() if title_match else f"第{page_number}页"

        # 提取布局 (SECTION 标签的 layout 属性)
        layout_match = re.search(r'<SECTION[^>]*layout="([^"]+)"', slide_xml)
        layout = layout_match.group(1) if layout_match else "vertical"

        # 提取要点 (BULLETS, COLUMNS, ICONS 等标签中的文本)
        key_points = self._extract_key_points(slide_xml)

        # 提取图片 (IMG 标签)
        images = self._extract_images(slide_xml)

        # 提取关键词（用于去重）
        keywords = self._extract_keywords(slide_xml, title, key_points)

        slide_info = SlideInfo(
            page_number=page_number,
            title=title,
            layout=layout,
            key_points=key_points,
            images=images,
            keywords=keywords
        )

        # 更新去重追踪
        if self.track_duplicates:
            self.used_keywords.update(keywords)
            self.used_images.update(images)

        return slide_info

    def _extract_key_points(self, slide_xml: str) -> List[str]:
        """提取关键要点"""
        points = []

        # 提取 BULLETS 中的内容
        bullets = re.findall(r'<BULLETS>.*?</BULLETS>', slide_xml, re.DOTALL)
        for bullet in bullets:
            # 提取 P 标签中的文本
            texts = re.findall(r'<P>(.*?)</P>', bullet, re.DOTALL)
            points.extend([t.strip() for t in texts if t.strip()])

        # 提取 COLUMNS 中的内容
        columns = re.findall(r'<COLUMNS>.*?</COLUMNS>', slide_xml, re.DOTALL)
        for column in columns:
            texts = re.findall(r'<P>(.*?)</P>', column, re.DOTALL)
            points.extend([t.strip() for t in texts if t.strip()])

        # 提取 H3 子标题
        h3s = re.findall(r'<H3>(.*?)</H3>', slide_xml, re.DOTALL)
        points.extend([h.strip() for h in h3s if h.strip()])

        # 如果没有找到任何内容，尝试提取所有纯文本
        if not points:
            all_text = re.sub(r'<[^>]+>', ' ', slide_xml)
            all_text = ' '.join(all_text.split())
            if all_text:
                # 截取前200个字符作为关键点
                points.append(all_text[:200] + "..." if len(all_text) > 200 else all_text)

        return points[:5]  # 最多保留5个要点

    def _extract_images(self, slide_xml: str) -> List[str]:
        """提取图片 URL"""
        imgs = re.findall(r'<IMG[^>]*src="([^"]+)"', slide_xml)
        return imgs

    def _extract_keywords(
        self,
        slide_xml: str,
        title: str,
        key_points: List[str]
    ) -> Set[str]:
        """提取关键词（用于去重检测）"""
        keywords = set()

        # 从标题中提取关键词
        title_words = re.findall(r'[\w]+', title, re.UNICODE)
        keywords.update([w.lower() for w in title_words if len(w) > 2])

        # 从要点中提取关键词
        for point in key_points:
            words = re.findall(r'[\w]+', point, re.UNICODE)
            keywords.update([w.lower() for w in words if len(w) > 2])

        # 过滤掉常见停用词
        stopwords = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
            'her', 'was', 'one', 'our', 'out', 'has', 'have', 'been', 'will',
            'with', 'this', 'that', 'from', 'they', 'would', 'there', 'their',
            '的', '了', '和', '是', '在', '有', '为', '不', '这', '个', '我',
            '他', '她', '它', '们', '中', '上', '下', '大', '小', '人'
        }
        keywords -= stopwords

        return keywords

    def compress_history(
        self,
        all_slides_xml: List[str],
        current_index: int
    ) -> str:
        """
        压缩历史上下文

        Args:
            all_slides_xml: 所有已生成页面的完整 XML 列表
            current_index: 当前正在生成的页码索引

        Returns:
            str: 压缩后的上下文字符串
        """
        # 提取所有页面信息（如果还没提取过）
        if len(self.all_slides) != len(all_slides_xml):
            self.all_slides = []
            for i, slide_xml in enumerate(all_slides_xml):
                slide_info = self.extract_slide_info(slide_xml, i + 1)
                self.all_slides.append(slide_info)

        # 构建压缩后的上下文
        compressed_parts = []

        # 1. 如果启用，先列出所有页面的标题（简洁版）
        if self.include_all_titles and len(self.all_slides) > 0:
            all_titles = "、".join([
                f"第{s.page_number}页: {s.title}"
                for s in self.all_slides
            ])
            compressed_parts.append(f"## 已生成页面总览:\n{all_titles}\n")

        # 2. 最近几页的详细信息
        recent_slides = self.all_slides[-self.max_history_slides:]
        if recent_slides:
            compressed_parts.append("## 最近几页详细内容:")
            for slide in recent_slides:
                compressed_parts.append(slide.to_summary())

        # 3. 去重警告（如果启用）
        if self.track_duplicates:
            compressed_parts.append(self._get_duplication_warning())

        return "\n\n".join(compressed_parts)

    def _get_duplication_warning(self) -> str:
        """生成去重警告信息"""
        warnings = []

        if self.used_keywords:
            warnings.append(
                f"⚠️ 已使用的关键词（请避免重复）: {', '.join(list(self.used_keywords)[:20])}"
            )

        if self.used_images:
            warnings.append(
                f"⚠️ 已使用的图片数量: {len(self.used_images)} 张"
            )

        return "\n".join(warnings) if warnings else "✅ 暂无重复内容"

    def check_duplication(self, slide_xml: str) -> Dict[str, any]:
        """
        检查当前页面是否有重复内容

        Args:
            slide_xml: 待检查的 XML 内容

        Returns:
            Dict: {
                "has_duplicate": bool,
                "duplicate_keywords": List[str],
                "duplicate_images": List[str],
                "suggestions": str
            }
        """
        # 提取当前页面的标题和关键点
        title_match = re.search(r'<H1>(.*?)</H1>', slide_xml, re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""
        key_points = self._extract_key_points(slide_xml)

        # 提取当前页面的信息
        current_keywords = self._extract_keywords(slide_xml, title, key_points)
        current_images = set(self._extract_images(slide_xml))

        # 检查重复
        duplicate_keywords = current_keywords & self.used_keywords
        duplicate_images = current_images & self.used_images

        has_duplicate = bool(duplicate_keywords or duplicate_images)

        suggestions = []
        if duplicate_keywords:
            suggestions.append(
                f"重复关键词: {', '.join(list(duplicate_keywords)[:5])}"
            )
        if duplicate_images:
            suggestions.append(
                f"重复图片: {len(duplicate_images)} 张"
            )

        return {
            "has_duplicate": has_duplicate,
            "duplicate_keywords": list(duplicate_keywords),
            "duplicate_images": list(duplicate_images),
            "suggestions": "；".join(suggestions) if suggestions else ""
        }

    def get_token_savings(self, original_length: int, compressed_length: int) -> Dict[str, any]:
        """
        计算 token 节省情况

        Args:
            original_length: 原始文本长度（字符数）
            compressed_length: 压缩后文本长度（字符数）

        Returns:
            Dict: 节省统计信息
        """
        # 粗略估算：中文字符约 1.5 tokens，英文单词约 1 token
        def estimate_tokens(text_length):
            return int(text_length * 0.7)  # 粗略估算

        original_tokens = estimate_tokens(original_length)
        compressed_tokens = estimate_tokens(compressed_length)
        saved_tokens = original_tokens - compressed_tokens
        saved_percentage = (saved_tokens / original_tokens * 100) if original_tokens > 0 else 0

        return {
            "original_chars": original_length,
            "compressed_chars": compressed_length,
            "estimated_original_tokens": original_tokens,
            "estimated_compressed_tokens": compressed_tokens,
            "estimated_saved_tokens": saved_tokens,
            "saved_percentage": round(saved_percentage, 1),
            "cost_savings_gpt4o": round(saved_tokens * 0.00001, 4),  # GPT-4o: $0.01/1M tokens
            "cost_savings_gpt4o_mini": round(saved_tokens * 0.00000015, 4)  # GPT-4o-mini: $0.15/1M tokens
        }

    def reset(self):
        """重置压缩器状态（用于新的生成任务）"""
        self.all_slides.clear()
        self.used_keywords.clear()
        self.used_images.clear()

# 便捷函数
def compress_slide_history(
    slides_xml_list: List[str],
    current_index: int,
    max_history_slides: int = 3
) -> str:
    """
    便捷函数：压缩幻灯片历史

    Args:
        slides_xml_list: 所有已生成页面的 XML 列表
        current_index: 当前页码索引
        max_history_slides: 保留最近几页的详细信息

    Returns:
        str: 压缩后的上下文
    """
    compressor = ContextCompressor(max_history_slides=max_history_slides)
    return compressor.compress_history(slides_xml_list, current_index)
