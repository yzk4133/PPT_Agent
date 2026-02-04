"""
Slide Domain Model

幻灯片领域模型，用于表示PPT中的单个幻灯片。
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class SlideLayout(str, Enum):
    """幻灯片布局类型"""
    VERTICAL = "vertical"
    LEFT = "left"
    RIGHT = "right"
    # 可以扩展更多布局类型

class SlideComponentType(str, Enum):
    """幻灯片组件类型"""
    BULLETS = "BULLETS"
    COLUMNS = "COLUMNS"
    ICONS = "ICONS"
    CYCLE = "CYCLE"
    ARROWS = "ARROWS"
    TIMELINE = "TIMELINE"
    PYRAMID = "PYRAMID"
    STAIRCASE = "STAIRCASE"
    CHART = "CHART"

@dataclass
class Image:
    """
    图片模型

    Attributes:
        src: 图片URL
        alt: 图片描述
        background: 是否为背景图
    """

    src: str
    alt: str = ""
    background: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "src": self.src,
            "alt": self.alt,
            "background": self.background
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Image":
        return cls(
            src=data.get("src", ""),
            alt=data.get("alt", ""),
            background=data.get("background", False)
        )

@dataclass
class Slide:
    """
    幻灯片模型

    表示PPT中的单个幻灯片。

    Attributes:
        page_number: 页码（从1开始）
        title: 幻灯片标题
        layout: 布局类型
        component_type: 组件类型
        content: 幻灯片内容（XML格式）
        images: 图片列表
        key_points: 关键要点
        metadata: 额外的元数据
        created_at: 创建时间
    """

    page_number: int
    title: str
    layout: SlideLayout = SlideLayout.VERTICAL
    component_type: SlideComponentType = SlideComponentType.BULLETS
    content: str = ""
    images: List[Image] = field(default_factory=list)
    key_points: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_xml(self) -> str:
        """
        转换为XML格式

        Returns:
            XML格式的幻灯片内容
        """
        images_xml = ""
        for img in self.images:
            background_attr = " background='true'" if img.background else ""
            images_xml += f'  <IMG src="{img.src}" alt="{img.alt}"{background_attr} />\n'

        key_points_xml = ""
        for point in self.key_points:
            key_points_xml += f"  <P>{point}</P>\n"

        return f"""<!-- 第{self.page_number}页开始-->
<SECTION layout="{self.layout.value}" page_number="{self.page_number}">
  <H1>{self.title}</H1>

  {key_points_xml if key_points_xml else '<!-- 内容组件 -->'}

{images_xml if images_xml else '<!-- 无图片 -->'}
</SECTION>
<!-- 第{self.page_number}页结束-->
"""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "page_number": self.page_number,
            "title": self.title,
            "layout": self.layout.value if isinstance(self.layout, SlideLayout) else self.layout,
            "component_type": self.component_type.value if isinstance(self.component_type, SlideComponentType) else self.component_type,
            "content": self.content,
            "images": [img.to_dict() for img in self.images],
            "key_points": self.key_points,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Slide":
        """从字典创建实例"""
        layout_str = data.get("layout", "vertical")
        layout = SlideLayout(layout_str) if isinstance(layout_str, str) else layout_str

        component_str = data.get("component_type", "BULLETS")
        component_type = SlideComponentType(component_str) if isinstance(component_str, str) else component_str

        images = [Image.from_dict(img) for img in data.get("images", [])]

        return cls(
            page_number=data.get("page_number", 1),
            title=data.get("title", ""),
            layout=layout,
            component_type=component_type,
            content=data.get("content", ""),
            images=images,
            key_points=data.get("key_points", []),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        )

    @classmethod
    def from_xml(cls, xml_content: str, page_number: int) -> "Slide":
        """
        从XML内容解析创建Slide实例

        Args:
            xml_content: XML格式的幻灯片内容
            page_number: 页码

        Returns:
            Slide实例
        """
        import re

        # 提取标题
        title_match = re.search(r'<H1>(.*?)</H1>', xml_content, re.DOTALL)
        title = title_match.group(1).strip() if title_match else f"第{page_number}页"

        # 提取布局
        layout_match = re.search(r'<SECTION[^>]*layout="([^"]+)"', xml_content)
        layout_str = layout_match.group(1) if layout_match else "vertical"
        layout = SlideLayout(layout_str) if layout_str in [e.value for e in SlideLayout] else SlideLayout.VERTICAL

        # 提取图片
        images = []
        for img_match in re.finditer(r'<IMG[^>]*src="([^"]+)"[^>]*alt="([^"]*)"[^>]*background="([^"]*)"', xml_content):
            images.append(Image(
                src=img_match.group(1),
                alt=img_match.group(2),
                background=img_match.group(3) == "true"
            ))

        return cls(
            page_number=page_number,
            title=title,
            layout=layout,
            content=xml_content,
            images=images
        )

    def __str__(self) -> str:
        return f"Slide(page={self.page_number}, title='{self.title}', layout={self.layout.value})"

@dataclass
class SlideList:
    """
    幻灯片列表模型

    包含多个幻灯片的集合。

    Attributes:
        slides: 幻灯片列表
        total_count: 总幻灯片数
        metadata: 额外的元数据
    """

    slides: List[Slide] = field(default_factory=list)
    total_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        if self.total_count == 0:
            self.total_count = len(self.slides)

    def add_slide(self, slide: Slide) -> None:
        """添加幻灯片"""
        self.slides.append(slide)
        self.total_count += 1

    def get_slide_by_page_number(self, page_number: int) -> Optional[Slide]:
        """根据页码获取幻灯片"""
        for slide in self.slides:
            if slide.page_number == page_number:
                return slide
        return None

    def to_presentation_xml(self) -> str:
        """
        转换为完整的PPT XML格式

        Returns:
            完整的PPT XML内容
        """
        xml_parts = ["```xml", "<PRESENTATION>"]
        for slide in self.slides:
            xml_parts.append(slide.content)
        xml_parts.append("</PRESENTATION>```")
        return "\n".join(xml_parts)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "slides": [slide.to_dict() for slide in self.slides],
            "total_count": self.total_count,
            "metadata": self.metadata
        }

if __name__ == "__main__":
    # 测试代码
    slide = Slide(
        page_number=1,
        title="人工智能概述",
        layout=SlideLayout.VERTICAL,
        key_points=["什么是AI", "AI的应用", "未来展望"]
    )
    print(slide)
    print(slide.to_xml())
