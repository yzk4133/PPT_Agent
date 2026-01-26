"""PPT模板系统

提供预设模板和模板定制功能
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import json


class TemplateCategory(Enum):
    """模板分类"""
    BUSINESS = "business"
    EDUCATION = "education"
    CREATIVE = "creative"
    TECH = "tech"
    PERSONAL = "personal"


@dataclass
class SlideTemplate:
    """幻灯片模板"""
    layout_id: int
    name: str
    description: str
    elements: List[Dict[str, Any]]  # 元素定义
    placeholders: Dict[str, int]   # 占位符映射


@dataclass
class PresentationTemplate:
    """演示文稿模板"""
    id: str
    name: str
    category: TemplateCategory
    description: str
    slide_templates: List[SlideTemplate]
    design_scheme: Dict[str, Any]
    thumbnail: Optional[str] = None


class TemplateLibrary:
    """模板库"""

    def __init__(self):
        self.templates: Dict[str, PresentationTemplate] = {}
        self._load_builtin_templates()

    def _load_builtin_templates(self):
        """加载内置模板"""
        # 商务模板
        self.templates["business_classic"] = PresentationTemplate(
            id="business_classic",
            name="经典商务",
            category=TemplateCategory.BUSINESS,
            description="适合正式商务场合的简洁模板",
            slide_templates=[
                SlideTemplate(0, "标题页", "包含标题和副标题", [], {}),
                SlideTemplate(1, "内容页", "标题+内容", [], {}),
                SlideTemplate(2, "两栏", "左右两栏布局", [], {}),
            ],
            design_scheme={
                "colors": {
                    "primary": "#2C3E50",
                    "secondary": "#3498DB"
                },
                "fonts": {
                    "title": "Arial",
                    "body": "Calibri"
                }
            }
        )

        # 教育模板
        self.templates["education_clean"] = PresentationTemplate(
            id="education_clean",
            name="清新教育",
            category=TemplateCategory.EDUCATION,
            description="适合教学和培训的清爽模板",
            slide_templates=[
                SlideTemplate(0, "封面", "课程封面", [], {}),
                SlideTemplate(1, "目录", "章节目录", [], {}),
                SlideTemplate(2, "内容", "教学内容", [], {}),
            ],
            design_scheme={
                "colors": {
                    "primary": "#27AE60",
                    "secondary": "#F39C12"
                },
                "fonts": {
                    "title": "Verdana",
                    "body": "Arial"
                }
            }
        )

        # 科技模板
        self.templates["tech_modern"] = PresentationTemplate(
            id="tech_modern",
            name="现代科技",
            category=TemplateCategory.TECH,
            description="科技风格的现代模板",
            slide_templates=[
                SlideTemplate(0, "启动页", "深色背景", [], {}),
                SlideTemplate(1, "特性页", "功能展示", [], {}),
                SlideTemplate(2, "数据页", "数据可视化", [], {}),
            ],
            design_scheme={
                "colors": {
                    "primary": "#00D4FF",
                    "secondary": "#090979"
                },
                "fonts": {
                    "title": "Roboto",
                    "body": "Open Sans"
                }
            }
        )

    def get_template(self, template_id: str) -> Optional[PresentationTemplate]:
        """获取模板"""
        return self.templates.get(template_id)

    def list_templates(
        self,
        category: Optional[TemplateCategory] = None
    ) -> List[PresentationTemplate]:
        """列出模板

        Args:
            category: 按分类过滤（可选）

        Returns:
            模板列表
        """
        templates = list(self.templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        return templates

    def search_templates(self, keyword: str) -> List[PresentationTemplate]:
        """搜索模板"""
        keyword = keyword.lower()
        return [
            t for t in self.templates.values()
            if keyword in t.name.lower() or keyword in t.description.lower()
        ]

    def create_custom_template(
        self,
        name: str,
        category: TemplateCategory,
        base_template_id: Optional[str] = None
    ) -> PresentationTemplate:
        """创建自定义模板

        Args:
            name: 模板名称
            category: 模板分类
            base_template_id: 基础模板ID（可选，用于继承）

        Returns:
            新创建的模板
        """
        import uuid

        template_id = f"custom_{uuid.uuid4().hex[:8]}"

        if base_template_id:
            base = self.get_template(base_template_id)
            if base:
                # 复制基础模板
                template = PresentationTemplate(
                    id=template_id,
                    name=name,
                    category=category,
                    description=base.description,
                    slide_templates=base.slide_templates.copy(),
                    design_scheme=base.design_scheme.copy()
                )
            else:
                raise ValueError(f"基础模板不存在: {base_template_id}")
        else:
            # 创建空白模板
            template = PresentationTemplate(
                id=template_id,
                name=name,
                category=category,
                description="自定义模板",
                slide_templates=[],
                design_scheme={}
            )

        self.templates[template_id] = template
        return template

    def update_template(
        self,
        template_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """更新模板

        Args:
            template_id: 模板ID
            updates: 更新的字段

        Returns:
            是否成功
        """
        template = self.get_template(template_id)
        if not template:
            return False

        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)

        return True

    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        if template_id in self.templates and not template_id.startswith("custom_"):
            # 只能删除自定义模板
            return False

        return self.templates.pop(template_id, None) is not None


# 全局模板库实例
_template_library: Optional[TemplateLibrary] = None


def get_template_library() -> TemplateLibrary:
    """获取全局模板库实例"""
    global _template_library
    if _template_library is None:
        _template_library = TemplateLibrary()
    return _template_library
