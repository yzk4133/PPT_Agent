"""
Framework Domain Model

PPT框架领域模型，用于表示PPT的整体结构设计。
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class PageType(str, Enum):
    """页面类型"""
    COVER = "cover"                   # 封面
    DIRECTORY = "directory"            # 目录
    CONTENT = "content"                # 内容页
    CHART = "chart"                    # 图表页
    IMAGE = "image"                    # 配图页
    SUMMARY = "summary"                # 总结
    THANKS = "thanks"                  # 致谢


class ContentType(str, Enum):
    """内容类型"""
    TEXT_ONLY = "text_only"            # 纯文本
    TEXT_WITH_IMAGE = "text_with_image"  # 文字+配图
    TEXT_WITH_CHART = "text_with_chart"  # 文字+图表
    TEXT_WITH_BOTH = "text_with_both"    # 文字+图表+配图
    IMAGE_ONLY = "image_only"          # 纯配图
    CHART_ONLY = "chart_only"          # 纯图表


@dataclass
class PageDefinition:
    """
    页面定义

    表示PPT中单个页面的定义。

    Attributes:
        page_no: 页码
        title: 页面标题
        page_type: 页面类型
        core_content: 核心内容描述
        is_need_chart: 是否需要图表
        is_need_research: 是否需要研究资料
        is_need_image: 是否需要配图
        content_type: 内容类型
        keywords: 关键词列表
        estimated_word_count: 预估字数
        layout_suggestion: 布局建议
    """

    page_no: int
    title: str
    page_type: PageType = PageType.CONTENT
    core_content: str = ""
    is_need_chart: bool = False
    is_need_research: bool = False
    is_need_image: bool = False
    content_type: ContentType = ContentType.TEXT_ONLY
    keywords: List[str] = field(default_factory=list)
    estimated_word_count: int = 100
    layout_suggestion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "page_no": self.page_no,
            "title": self.title,
            "page_type": self.page_type.value if isinstance(self.page_type, PageType) else self.page_type,
            "core_content": self.core_content,
            "is_need_chart": self.is_need_chart,
            "is_need_research": self.is_need_research,
            "is_need_image": self.is_need_image,
            "content_type": self.content_type.value if isinstance(self.content_type, ContentType) else self.content_type,
            "keywords": self.keywords,
            "estimated_word_count": self.estimated_word_count,
            "layout_suggestion": self.layout_suggestion
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PageDefinition":
        """从字典创建实例"""
        page_type_str = data.get("page_type", "content")
        page_type = PageType(page_type_str) if isinstance(page_type_str, str) else page_type_str

        content_type_str = data.get("content_type", "text_only")
        content_type = ContentType(content_type_str) if isinstance(content_type_str, str) else content_type_str

        return cls(
            page_no=data.get("page_no", 1),
            title=data.get("title", ""),
            page_type=page_type,
            core_content=data.get("core_content", ""),
            is_need_chart=data.get("is_need_chart", False),
            is_need_research=data.get("is_need_research", False),
            is_need_image=data.get("is_need_image", False),
            content_type=content_type,
            keywords=data.get("keywords", []),
            estimated_word_count=data.get("estimated_word_count", 100),
            layout_suggestion=data.get("layout_suggestion", "")
        )


@dataclass
class PPTFramework:
    """
    PPT框架模型

    表示完整的PPT结构框架。

    Attributes:
        total_page: 总页数
        pages: 页面定义列表
        cover_page: 封面页
        directory_page: 目录页
        summary_page: 总结页
        has_research_pages: 是否包含需要研究的页面
        research_page_indices: 需要研究的页面索引列表
        chart_page_indices: 需要图表的页面索引列表
        image_page_indices: 需要配图的页面索引列表
        framework_type: 框架类型（线性/分支/混合）
    """

    total_page: int
    pages: List[PageDefinition] = field(default_factory=list)
    cover_page: Optional[PageDefinition] = None
    directory_page: Optional[PageDefinition] = None
    summary_page: Optional[PageDefinition] = None
    has_research_pages: bool = False
    research_page_indices: List[int] = field(default_factory=list)
    chart_page_indices: List[int] = field(default_factory=list)
    image_page_indices: List[int] = field(default_factory=list)
    framework_type: str = "linear"

    def __post_init__(self):
        """初始化后处理"""
        self._update_indices()

    def add_page(self, page: PageDefinition) -> None:
        """添加页面"""
        page.page_no = len(self.pages) + 1
        self.pages.append(page)
        self.total_page = len(self.pages)
        self._update_special_pages()
        self._update_indices()

    def insert_page(self, index: int, page: PageDefinition) -> None:
        """在指定位置插入页面"""
        self.pages.insert(index, page)
        self._renumber_pages()
        self.total_page = len(self.pages)
        self._update_special_pages()
        self._update_indices()

    def remove_page(self, page_no: int) -> Optional[PageDefinition]:
        """删除页面"""
        for i, page in enumerate(self.pages):
            if page.page_no == page_no:
                removed = self.pages.pop(i)
                self._renumber_pages()
                self.total_page = len(self.pages)
                self._update_special_pages()
                self._update_indices()
                return removed
        return None

    def _renumber_pages(self) -> None:
        """重新编号页面"""
        for i, page in enumerate(self.pages, 1):
            page.page_no = i

    def _update_special_pages(self) -> None:
        """更新特殊页面引用"""
        if self.pages:
            # 第一页通常是封面
            if self.pages[0].page_type == PageType.COVER:
                self.cover_page = self.pages[0]

            # 查找目录页
            for page in self.pages[1:3]:  # 目录通常在第2-3页
                if page.page_type == PageType.DIRECTORY:
                    self.directory_page = page
                    break

            # 最后一页通常是总结或致谢
            if self.pages[-1].page_type in (PageType.SUMMARY, PageType.THANKS):
                self.summary_page = self.pages[-1]

    def _update_indices(self) -> None:
        """更新索引列表"""
        self.research_page_indices = [
            p.page_no for p in self.pages if p.is_need_research
        ]
        self.chart_page_indices = [
            p.page_no for p in self.pages if p.is_need_chart
        ]
        self.image_page_indices = [
            p.page_no for p in self.pages if p.is_need_image
        ]
        self.has_research_pages = len(self.research_page_indices) > 0

    def get_page(self, page_no: int) -> Optional[PageDefinition]:
        """获取指定页码的页面"""
        for page in self.pages:
            if page.page_no == page_no:
                return page
        return None

    def get_pages_by_type(self, page_type: PageType) -> List[PageDefinition]:
        """根据类型获取页面列表"""
        return [p for p in self.pages if p.page_type == page_type]

    def validate(self, expected_page_num: int) -> tuple[bool, List[str]]:
        """
        校验框架

        Args:
            expected_page_num: 预期的页数

        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []

        if self.total_page != expected_page_num:
            errors.append(f"页数不匹配：期望{expected_page_num}，实际{self.total_page}")

        if not self.pages:
            errors.append("框架中没有页面")

        # 检查是否有封面
        has_cover = any(p.page_type == PageType.COVER for p in self.pages)
        if not has_cover:
            errors.append("缺少封面页")

        # 检查页码连续性
        for i, page in enumerate(self.pages):
            if page.page_no != i + 1:
                errors.append(f"页码不连续：第{i+1}个页面的page_no是{page.page_no}")

        # 检查是否有需要研究但没有关键词的页面
        for page in self.pages:
            if page.is_need_research and not page.keywords:
                errors.append(f"第{page.page_no}页需要研究资料但没有提供关键词")

        return len(errors) == 0, errors

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "total_page": self.total_page,
            "ppt_framework": [p.to_dict() for p in self.pages],
            "has_research_pages": self.has_research_pages,
            "research_page_indices": self.research_page_indices,
            "chart_page_indices": self.chart_page_indices,
            "image_page_indices": self.image_page_indices,
            "framework_type": self.framework_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PPTFramework":
        """从字典创建实例"""
        pages_data = data.get("ppt_framework", [])
        pages = [PageDefinition.from_dict(p) for p in pages_data]

        framework = cls(
            total_page=data.get("total_page", len(pages)),
            pages=pages,
            has_research_pages=data.get("has_research_pages", False),
            research_page_indices=data.get("research_page_indices", []),
            chart_page_indices=data.get("chart_page_indices", []),
            image_page_indices=data.get("image_page_indices", []),
            framework_type=data.get("framework_type", "linear")
        )

        framework._update_special_pages()
        return framework

    @classmethod
    def create_default(cls, page_num: int, topic: str = "") -> "PPTFramework":
        """
        创建默认框架

        Args:
            page_num: 页数
            topic: 主题

        Returns:
            PPTFramework实例
        """
        pages = []

        # 封面
        pages.append(PageDefinition(
            page_no=1,
            title="封面",
            page_type=PageType.COVER,
            core_content=f"主题：{topic}\\n副标题\\n汇报人\\n日期",
            is_need_chart=False,
            is_need_research=False,
            is_need_image=True,
            content_type=ContentType.TEXT_WITH_IMAGE
        ))

        # 目录
        pages.append(PageDefinition(
            page_no=2,
            title="目录",
            page_type=PageType.DIRECTORY,
            core_content="列出主要章节",
            is_need_chart=False,
            is_need_research=False,
            content_type=ContentType.TEXT_ONLY
        ))

        # 内容页
        content_pages = max(0, page_num - 3)  # 减去封面、目录、总结
        for i in range(content_pages):
            pages.append(PageDefinition(
                page_no=len(pages) + 1,
                title=f"第{i+1}部分",
                page_type=PageType.CONTENT,
                core_content=f"第{i+1}部分的核心内容",
                is_need_chart=(i % 2 == 0),  # 每隔一页需要图表
                is_need_research=False,
                content_type=ContentType.TEXT_WITH_CHART if (i % 2 == 0) else ContentType.TEXT_ONLY
            ))

        # 总结
        pages.append(PageDefinition(
            page_no=len(pages) + 1,
            title="总结",
            page_type=PageType.SUMMARY,
            core_content="总结和展望",
            is_need_chart=False,
            is_need_research=False,
            content_type=ContentType.TEXT_ONLY
        ))

        return cls(total_page=len(pages), pages=pages)

    def __str__(self) -> str:
        return f"PPTFramework(pages={self.total_page}, research_pages={len(self.research_page_indices)})"


@dataclass
class FrameworkValidation:
    """
    框架验证结果

    Attributes:
        is_valid: 是否有效
        errors: 错误列表
        warnings: 警告列表
        suggestions: 优化建议列表
    """

    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions
        }


if __name__ == "__main__":
    # 测试代码
    framework = PPTFramework.create_default(page_num=10, topic="人工智能介绍")
    print(f"Framework: {framework}")
    print(f"Total pages: {framework.total_page}")
    print(f"Chart pages: {framework.chart_page_indices}")

    is_valid, errors = framework.validate(10)
    print(f"Valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")

    print(framework.to_dict())
