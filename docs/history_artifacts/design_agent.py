"""设计Agent - 负责PPT的视觉设计

提供专业的视觉设计建议，确保PPT的美观性和专业性
"""

from typing import Dict, Any, List
from dataclasses import dataclass

from .agent_base import BaseAgent, AgentConfig, AgentMessage


@dataclass
class DesignScheme:
    """设计方案"""
    color_palette: Dict[str, str]  # 主色、辅助色、强调色
    fonts: Dict[str, str]          # 标题字体、正文字体
    layout_style: str              # 布局风格
    visual_elements: List[str]     # 推荐的视觉元素


class DesignAgent(BaseAgent):
    """视觉设计Agent

    职责:
    - 分析内容类型和情感基调
    - 推荐配色方案
    - 建议字体和排版
    - 提供布局建议
    """

    # 预定义的配色方案库
    COLOR_SCHEMES = {
        "business": {
            "primary": "#2C3E50",
            "secondary": "#3498DB",
            "accent": "#E74C3C",
            "background": "#ECF0F1",
            "text": "#2C3E50"
        },
        "creative": {
            "primary": "#8E44AD",
            "secondary": "#F39C12",
            "accent": "#1ABC9C",
            "background": "#FEF9E7",
            "text": "#2C3E50"
        },
        "tech": {
            "primary": "#00D4FF",
            "secondary": "#090979",
            "accent": "#00FF88",
            "background": "#0A0A0A",
            "text": "#FFFFFF"
        }
    }

    FONT_PAIRINGS = {
        "professional": {
            "title": "Arial Bold",
            "body": "Calibri"
        },
        "modern": {
            "title": "Montserrat",
            "body": "Open Sans"
        },
        "classic": {
            "title": "Georgia",
            "body": "Times New Roman"
        }
    }

    async def process(self, message: AgentMessage) -> AgentMessage:
        """处理设计请求"""
        task_type = message.content.get("task_type")

        if task_type == "analyze_content":
            return await self._analyze_content_style(message)
        elif task_type == "suggest_design":
            return await self._suggest_design(message)
        else:
            raise ValueError(f"未知的任务类型: {task_type}")

    async def _analyze_content_style(self, message: AgentMessage) -> AgentMessage:
        """分析内容风格

        分析PPT内容的情感基调、专业程度等，为设计提供依据
        """
        content = message.content.get("content", "")
        topic = message.content.get("topic", "")

        # 使用AI分析内容风格
        style_analysis = await self._analyze_with_ai(content, topic)

        return self._create_response(
            to_agent=message.from_agent,
            content={
                "task_type": "style_analyzed",
                "style_category": style_analysis["category"],
                "tone": style_analysis["tone"],
                "formality_level": style_analysis["formality"]
            }
        )

    async def _suggest_design(self, message: AgentMessage) -> AgentMessage:
        """提供设计建议

        基于内容分析和用户偏好，提供完整的设计方案
        """
        style_category = message.content.get("style_category", "business")
        user_preferences = message.content.get("preferences", {})

        # 选择配色方案
        color_scheme = self._select_color_scheme(style_category, user_preferences)

        # 选择字体组合
        fonts = self._select_fonts(style_category, user_preferences)

        # 建议布局
        layout = self._suggest_layout(style_category)

        # 推荐视觉元素
        elements = self._suggest_visual_elements(style_category)

        design_scheme = DesignScheme(
            color_palette=color_scheme,
            fonts=fonts,
            layout_style=layout,
            visual_elements=elements
        )

        return self._create_response(
            to_agent=message.from_agent,
            content={
                "task_type": "design_suggested",
                "design_scheme": design_scheme.__dict__
            }
        )

    def _select_color_scheme(self, category: str, preferences: dict) -> Dict[str, str]:
        """选择配色方案"""
        if "color_theme" in preferences:
            custom_theme = preferences["color_theme"]
            if custom_theme in self.COLOR_SCHEMES:
                return self.COLOR_SCHEMES[custom_theme]

        return self.COLOR_SCHEMES.get(category, self.COLOR_SCHEMES["business"])

    def _select_fonts(self, category: str, preferences: dict) -> Dict[str, str]:
        """选择字体组合"""
        if "font_style" in preferences:
            return self.FONT_PAIRINGS[preferences["font_style"]]

        font_map = {
            "business": "professional",
            "creative": "modern",
            "tech": "modern"
        }
        style = font_map.get(category, "professional")
        return self.FONT_PAIRINGS[style]

    def _suggest_layout(self, category: str) -> str:
        """建议布局风格"""
        layouts = {
            "business": "formal_centered",
            "creative": "dynamic_asymmetric",
            "tech": "minimalist_grid"
        }
        return layouts.get(category, "standard")

    def _suggest_visual_elements(self, category: str) -> List[str]:
        """建议视觉元素"""
        elements = {
            "business": ["图表", "图标", "时间线"],
            "creative": ["插画", "渐变", "动画"],
            "tech": ["代码片段", "架构图", "数据可视化"]
        }
        return elements.get(category, ["图标", "图表"])

    async def _analyze_with_ai(self, content: str, topic: str) -> Dict[str, Any]:
        """使用AI分析内容风格"""
        # 实际实现中会调用AI模型
        return {
            "category": "business",
            "tone": "专业",
            "formality": "高"
        }

    def _create_response(self, to_agent: str, content: Dict[str, Any]) -> AgentMessage:
        """创建响应消息"""
        return AgentMessage.create(
            from_agent=self.config.name,
            to_agent=to_agent,
            content=content
        )
