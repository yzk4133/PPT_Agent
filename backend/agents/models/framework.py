"""
PPT 结构框架模型

本模块定义了 PPT 框架结构的领域模型。
这些模型与原始领域模型兼容，但已适配 LangChain。
"""

from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


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


class PageDefinition(BaseModel):
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

    page_no: int = Field(ge=1, description="页码")
    title: str = Field(min_length=1, description="页面标题")
    page_type: PageType = Field(default=PageType.CONTENT, description="页面类型")
    core_content: str = Field(default="", description="核心内容描述")
    is_need_chart: bool = Field(default=False, description="是否需要图表")
    is_need_research: bool = Field(default=False, description="是否需要研究资料")
    is_need_image: bool = Field(default=False, description="是否需要配图")
    content_type: ContentType = Field(default=ContentType.TEXT_ONLY, description="内容类型")
    keywords: List[str] = Field(default_factory=list, description="关键词列表")
    estimated_word_count: int = Field(default=100, ge=0, description="预估字数")
    layout_suggestion: str = Field(default="", description="布局建议")

    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v, info):
        """验证关键词：研究页面必须有关键词"""
        if info and info.data.get('is_need_research') and not v:
            raise ValueError("研究页面必须提供关键词")
        return v

    @field_validator('page_type', 'content_type', mode='before')
    @classmethod
    def validate_enums(cls, v):
        """验证枚举值"""
        if isinstance(v, str):
            # 尝试转换为枚举
            try:
                if v in PageType.__members__:
                    return PageType(v)
                elif v in ContentType.__members__:
                    return ContentType(v)
            except (ValueError, KeyError):
                pass
        return v

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
        page_type = PageType(page_type_str) if isinstance(page_type_str, str) and page_type_str in PageType.__members__ else page_type_str
        if isinstance(page_type, str) and page_type not in PageType.__members__:
            page_type = PageType.CONTENT

        content_type_str = data.get("content_type", "text_only")
        content_type = ContentType(content_type_str) if isinstance(content_type_str, str) and content_type_str in ContentType.__members__ else content_type_str
        if isinstance(content_type, str) and content_type not in ContentType.__members__:
            content_type = ContentType.TEXT_ONLY

        return cls(
            page_no=data.get("page_no", 1),
            title=data.get("title", ""),
            page_type=page_type if isinstance(page_type, PageType) else PageType(page_type),
            core_content=data.get("core_content", ""),
            is_need_chart=data.get("is_need_chart", False),
            is_need_research=data.get("is_need_research", False),
            is_need_image=data.get("is_need_image", False),
            content_type=content_type if isinstance(content_type, ContentType) else ContentType(content_type),
            keywords=data.get("keywords", []),
            estimated_word_count=data.get("estimated_word_count", 100),
            layout_suggestion=data.get("layout_suggestion", "")
        )


class PPTFramework(BaseModel):
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

    total_page: int = Field(ge=0, description="总页数")
    pages: List[PageDefinition] = Field(default_factory=list, description="页面定义列表")
    cover_page: Optional[PageDefinition] = Field(default=None, description="封面页")
    directory_page: Optional[PageDefinition] = Field(default=None, description="目录页")
    summary_page: Optional[PageDefinition] = Field(default=None, description="总结页")
    has_research_pages: bool = Field(default=False, description="是否包含需要研究的页面")
    research_page_indices: List[int] = Field(default_factory=list, description="需要研究的页面索引列表")
    chart_page_indices: List[int] = Field(default_factory=list, description="需要图表的页面索引列表")
    image_page_indices: List[int] = Field(default_factory=list, description="需要配图的页面索引列表")
    framework_type: str = Field(default="linear", description="框架类型（线性/分支/混合）")

    @model_validator(mode='after')
    def update_indices(self):
        """自动更新索引（替代 __post_init__）"""
        self._update_indices()
        return self

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
            else:
                self.cover_page = None

            # 查找目录页
            self.directory_page = None
            for page in self.pages[1:3]:  # 目录通常在第2-3页
                if page.page_type == PageType.DIRECTORY:
                    self.directory_page = page
                    break

            # 最后一页通常是总结或致谢
            if self.pages[-1].page_type in (PageType.SUMMARY, PageType.THANKS):
                self.summary_page = self.pages[-1]
            else:
                self.summary_page = None

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
            core_content=f"主题：{topic}\n副标题\n汇报人\n日期",
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


# 使用框架的便捷函数


def create_framework_from_requirement(
    requirement: Dict[str, Any]
) -> PPTFramework:
    """
    从结构化需求创建 PPT 框架

    Args:
        requirement: 结构化需求字典

    Returns:
        PPTFramework 实例
    """
    topic = requirement.get("ppt_topic", "")
    page_num = requirement.get("page_num", 10)

    # 目前使用默认框架
    # 生产环境中应使用 LLM 生成自定义框架
    return PPTFramework.create_default(page_num=page_num, topic=topic)


def filter_pages_need_research(
    framework: PPTFramework
) -> List[PageDefinition]:
    """
    筛选需要研究的页面

    Args:
        framework: PPT 框架

    Returns:
        需要研究的页面列表
    """
    return [p for p in framework.pages if p.is_need_research]


def filter_pages_need_chart(
    framework: PPTFramework
) -> List[PageDefinition]:
    """
    筛选需要图表的页面

    Args:
        framework: PPT 框架

    Returns:
        需要图表的页面列表
    """
    return [p for p in framework.pages if p.is_need_chart]


if __name__ == "__main__":
    # 测试框架创建
    framework = PPTFramework.create_default(page_num=10, topic="人工智能介绍")
    print(f"Framework: {framework}")
    print(f"Total pages: {framework.total_page}")
    print(f"Chart pages: {framework.chart_page_indices}")

    is_valid, errors = framework.validate(10)
    print(f"Valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")

    # 从需求测试
    requirement = {
        "ppt_topic": "AI 演示文稿",
        "page_num": 5,
        "need_research": True
    }
    framework2 = create_framework_from_requirement(requirement)
    print(f"\nFramework from requirement: {framework2}")
