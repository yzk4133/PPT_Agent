"""
Content State Domain Model

Domain model for the content generation stage state.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ContentMaterialState:
    """
    单个页面内容素材

    表示单个页面的内容素材状态。

    Attributes:
        page_no: 页码
        page_title: 页面标题
        page_type: 页面类型
        content_text: 文字内容
        chart_data: 图表数据
        has_chart: 是否有图表
        image_suggestion: 配图建议
        has_image: 是否有配图
    """

    page_no: int
    page_title: str
    page_type: str = "content"
    content_text: str = ""
    chart_data: Optional[Dict[str, Any]] = None
    has_chart: bool = False
    image_suggestion: Optional[Dict[str, str]] = None
    has_image: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "page_no": self.page_no,
            "page_title": self.page_title,
            "page_type": self.page_type,
            "content_text": self.content_text,
            "chart_data": self.chart_data,
            "has_chart": self.has_chart,
            "image_suggestion": self.image_suggestion,
            "has_image": self.has_image
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentMaterialState":
        """从字典创建"""
        return cls(
            page_no=data.get("page_no", 1),
            page_title=data.get("page_title", ""),
            page_type=data.get("page_type", "content"),
            content_text=data.get("content_text", ""),
            chart_data=data.get("chart_data"),
            has_chart=data.get("has_chart", False),
            image_suggestion=data.get("image_suggestion"),
            has_image=data.get("has_image", False)
        )


@dataclass
class ContentState:
    """
    内容生成阶段后的状态

    表示内容生成阶段完成后的结构化状态。

    Attributes:
        materials: 内容素材列表
        total_generated: 已生成的页面数
    """

    materials: List[ContentMaterialState] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content_material": [m.to_dict() for m in self.materials],
            "total_generated": len(self.materials)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentState":
        """从字典创建"""
        materials_data = data.get("content_material", [])
        materials = [ContentMaterialState.from_dict(m) for m in materials_data]

        return cls(materials=materials)

    def add_material(self, material: ContentMaterialState) -> None:
        """添加内容素材"""
        self.materials.append(material)

    def get_material_for_page(self, page_no: int) -> Optional[ContentMaterialState]:
        """获取指定页码的内容素材"""
        for material in self.materials:
            if material.page_no == page_no:
                return material
        return None

    @property
    def total_generated(self) -> int:
        """已生成的页面数"""
        return len(self.materials)

    @property
    def pages_with_charts(self) -> int:
        """包含图表的页面数"""
        return sum(1 for m in self.materials if m.has_chart)

    @property
    def pages_with_images(self) -> int:
        """包含配图的页面数"""
        return sum(1 for m in self.materials if m.has_image)


if __name__ == "__main__":
    # 测试代码
    material1 = ContentMaterialState(
        page_no=1,
        page_title="封面",
        page_type="cover",
        content_text="主题: AI技术介绍",
        has_image=True
    )

    material2 = ContentMaterialState(
        page_no=2,
        page_title="核心数据",
        page_type="content",
        content_text="以下是关键数据...",
        chart_data={"type": "bar", "data": [1, 2, 3]},
        has_chart=True
    )

    content_state = ContentState(materials=[material1, material2])

    print("ContentState Test:")
    print(f"Total generated: {content_state.total_generated}")
    print(f"Pages with charts: {content_state.pages_with_charts}")
    print(f"Pages with images: {content_state.pages_with_images}")

    page_1_material = content_state.get_material_for_page(1)
    print(f"Page 1 material: {page_1_material.page_title}")

    dict_data = content_state.to_dict()
    restored = ContentState.from_dict(dict_data)
    print(f"Restored: {restored.total_generated} materials")
