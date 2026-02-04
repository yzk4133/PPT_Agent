"""
Framework State Domain Model

Domain model for the framework design stage state.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional


@dataclass
class FrameworkPageState:
    """
    单页框架状态

    表示PPT中单个页面的框架状态。

    Attributes:
        page_no: 页码
        title: 页面标题
        page_type: 页面类型
        core_content: 核心内容描述
        is_need_chart: 是否需要图表
        is_need_research: 是否需要研究资料
        is_need_image: 是否需要配图
        keywords: 关键词列表
    """

    page_no: int
    title: str
    page_type: str = "content"
    core_content: str = ""
    is_need_chart: bool = False
    is_need_research: bool = False
    is_need_image: bool = False
    keywords: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "page_no": self.page_no,
            "title": self.title,
            "page_type": self.page_type,
            "core_content": self.core_content,
            "is_need_chart": self.is_need_chart,
            "is_need_research": self.is_need_research,
            "is_need_image": self.is_need_image,
            "keywords": self.keywords
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FrameworkPageState":
        """从字典创建"""
        return cls(
            page_no=data.get("page_no", 1),
            title=data.get("title", ""),
            page_type=data.get("page_type", "content"),
            core_content=data.get("core_content", ""),
            is_need_chart=data.get("is_need_chart", False),
            is_need_research=data.get("is_need_research", False),
            is_need_image=data.get("is_need_image", False),
            keywords=data.get("keywords", [])
        )


@dataclass
class FrameworkState:
    """
    框架设计后的状态

    表示框架设计阶段完成后的结构化状态。

    Attributes:
        total_page: 总页数
        ppt_framework: 页面定义列表
        research_page_indices: 需要研究的页面索引列表
        chart_page_indices: 需要图表的页面索引列表
        framework_type: 框架类型
    """

    total_page: int
    ppt_framework: List[FrameworkPageState] = field(default_factory=list)
    research_page_indices: List[int] = field(default_factory=list)
    chart_page_indices: List[int] = field(default_factory=list)
    framework_type: str = "linear"

    def __post_init__(self):
        """初始化后处理"""
        self._update_indices()

    def _update_indices(self) -> None:
        """更新索引列表"""
        self.research_page_indices = [
            p.page_no for p in self.ppt_framework if p.is_need_research
        ]
        self.chart_page_indices = [
            p.page_no for p in self.ppt_framework if p.is_need_chart
        ]

    def add_page(self, page: FrameworkPageState) -> None:
        """添加页面"""
        page.page_no = len(self.ppt_framework) + 1
        self.ppt_framework.append(page)
        self.total_page = len(self.ppt_framework)
        self._update_indices()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_page": self.total_page,
            "ppt_framework": [p.to_dict() for p in self.ppt_framework],
            "research_page_indices": self.research_page_indices,
            "chart_page_indices": self.chart_page_indices,
            "framework_type": self.framework_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FrameworkState":
        """从字典创建"""
        pages_data = data.get("ppt_framework", [])
        pages = [FrameworkPageState.from_dict(p) for p in pages_data]

        return cls(
            total_page=data.get("total_page", len(pages)),
            ppt_framework=pages,
            research_page_indices=data.get("research_page_indices", []),
            chart_page_indices=data.get("chart_page_indices", []),
            framework_type=data.get("framework_type", "linear")
        )

    def validate(self, expected_page_num: int) -> Tuple[bool, List[str]]:
        """
        校验框架

        Args:
            expected_page_num: 预期的页数

        Returns:
            (是否有效, 错误列表)
        """
        errors = []

        if self.total_page != expected_page_num:
            errors.append(f"页数不匹配: 期望{expected_page_num}, 实际{self.total_page}")

        if len(self.ppt_framework) != self.total_page:
            errors.append(f"框架页数不一致: 声明{self.total_page}, 实际{len(self.ppt_framework)}")

        # 检查是否有需要研究但没有关键词的页面
        for page in self.ppt_framework:
            if page.is_need_research and not page.keywords:
                errors.append(f"第{page.page_no}页需要研究资料但没有提供关键词")

        return len(errors) == 0, errors

    @property
    def has_research_pages(self) -> bool:
        """是否有需要研究的页面"""
        return len(self.research_page_indices) > 0

    @property
    def has_chart_pages(self) -> bool:
        """是否有需要图表的页面"""
        return len(self.chart_page_indices) > 0


if __name__ == "__main__":
    # 测试代码
    pages = [
        FrameworkPageState(
            page_no=1,
            title="封面",
            page_type="cover",
            core_content="主题+副标题"
        ),
        FrameworkPageState(
            page_no=2,
            title="目录",
            page_type="directory",
            core_content="列出主要章节"
        ),
        FrameworkPageState(
            page_no=3,
            title="核心内容",
            page_type="content",
            core_content="主要内容",
            is_need_chart=True,
            is_need_research=True,
            keywords=["AI", "技术"]
        )
    ]

    framework = FrameworkState(total_page=3, ppt_framework=pages)

    print("FrameworkState Test:")
    print(f"Total pages: {framework.total_page}")
    print(f"Has research pages: {framework.has_research_pages}")
    print(f"Research page indices: {framework.research_page_indices}")
    print(f"Chart page indices: {framework.chart_page_indices}")

    is_valid, errors = framework.validate(3)
    print(f"Valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")

    dict_data = framework.to_dict()
    restored = FrameworkState.from_dict(dict_data)
    print(f"Restored: {restored.total_page} pages")
