"""
布局选择 Skill

根据页面类型和内容选择最佳布局
"""

import json
import logging
from typing import Dict, Any, List
from backend.tools.skills.base_skill import BaseSkill


logger = logging.getLogger(__name__)


class LayoutSelectionSkill(BaseSkill):
    """
    布局选择 Skill

    职责：
    - 根据页面类型选择基础布局
    - 根据内容类型调整布局细节
    - 考虑图表和图片的存在
    - 提供替代布局方案
    """

    name = "layout_selection"
    description = "根据页面类型和内容选择最佳PPT布局"
    version = "1.0.0"
    category = "rendering"

    # 布局规则库
    LAYOUT_RULES = {
        # 封面页
        "cover": "title_center",
        # 目录页
        "directory": "vertical_list",
        # 内容页（根据内容类型）
        "content": {
            "text_only": "title_with_bullet_points",
            "text_with_chart": "title_with_left_chart",
            "text_with_image": "title_with_right_image",
            "text_with_both": "title_with_chart_and_image",
        },
        # 总结页
        "summary": "title_with_bottom_summary",
        # 致谢页
        "thanks": "centered_text",
    }

    async def execute(
        self,
        page_type: str,
        content_type: str = "text_only",
        has_chart: bool = False,
        has_image: bool = False,
        key_points_count: int = 3,
    ) -> str:
        """
        执行布局选择

        Args:
            page_type: 页面类型
                - cover: 封面
                - directory: 目录
                - content: 内容页
                - summary: 总结
                - thanks: 致谢
            content_type: 内容类型
                - text_only: 纯文本
                - text_with_chart: 文本+图表
                - text_with_image: 文本+图片
                - text_with_both: 文本+图表+图片
            has_chart: 是否有图表
            has_image: 是否有图片
            key_points_count: 要点数量

        Returns:
            str: 布局选择结果字符串
        """
        try:
            logger.info(f"[LayoutSelection] 选择布局: {page_type}, {content_type}")

            # 步骤 1: 根据页面类型选择基础布局
            base_layout = self._select_base_layout(page_type)

            # 步骤 2: 根据内容类型调整
            if page_type == "content":
                layout = self._adjust_for_content(base_layout, content_type, has_chart, has_image)
            else:
                layout = base_layout

            # 步骤 3: 根据要点数量微调
            layout = self._adjust_for_points(layout, key_points_count)

            # 步骤 4: 生成配置
            config = self._generate_layout_config(layout)

            # 步骤 5: 生成替代方案
            alternatives = self._get_alternatives(layout, page_type, content_type)

            logger.info(f"[LayoutSelection] 选择布局: {layout}")

            # 格式化返回字符串
            reasoning = self._explain_reasoning(page_type, content_type, has_chart, has_image)

            result = f"布局: {layout}\n"
            result += f"原因: {reasoning}\n"
            if alternatives:
                result += f"备选方案: {', '.join(alternatives)}"

            return result

        except Exception as e:
            logger.error(f"[LayoutSelection] 选择失败: {e}", exc_info=True)
            return f"错误：{str(e)}"

    def _select_base_layout(self, page_type: str) -> str:
        """根据页面类型选择基础布局"""
        return self.LAYOUT_RULES.get(page_type, "title_with_bullet_points")

    def _adjust_for_content(
        self, base_layout: str, content_type: str, has_chart: bool, has_image: bool
    ) -> str:
        """根据内容类型调整布局"""
        # 如果指定了 content_type
        if content_type in self.LAYOUT_RULES["content"]:
            return self.LAYOUT_RULES["content"][content_type]

        # 根据 has_chart 和 has_image 自动判断
        if has_chart and has_image:
            return "title_with_chart_and_image"
        elif has_chart:
            return "title_with_left_chart"
        elif has_image:
            return "title_with_right_image"
        else:
            return "title_with_bullet_points"

    def _adjust_for_points(self, layout: str, points_count: int) -> str:
        """根据要点数量微调布局"""
        if points_count > 5:
            # 要点太多，使用两栏布局
            if layout == "title_with_bullet_points":
                return "two_column_text"
        elif points_count <= 2:
            # 要点太少，使用单栏大字
            if layout in ["title_with_bullet_points", "two_column_text"]:
                return "title_with_large_text"

        return layout

    def _generate_layout_config(self, layout: str) -> Dict[str, Any]:
        """生成布局配置"""
        configs = {
            "title_center": {
                "title_position": "center",
                "content_position": "center",
                "alignment": "center",
                "use_large_title": True,
            },
            "vertical_list": {
                "title_position": "top",
                "content_position": "left",
                "list_orientation": "vertical",
                "indentation": True,
            },
            "title_with_bullet_points": {
                "title_position": "top",
                "content_position": "left",
                "bullet_style": "disc",
                "alignment": "left",
            },
            "title_with_left_chart": {
                "title_position": "top",
                "content_position": "left",
                "chart_position": "right",
                "split_ratio": "60:40",
            },
            "title_with_right_image": {
                "title_position": "top",
                "content_position": "left",
                "image_position": "right",
                "split_ratio": "60:40",
            },
            "title_with_chart_and_image": {
                "title_position": "top",
                "content_position": "left",
                "media_position": "right",
                "media_layout": "vertical_stack",
            },
            "title_with_bottom_summary": {
                "title_position": "top",
                "content_position": "left",
                "summary_position": "bottom",
                "summary_style": "highlight",
            },
            "centered_text": {
                "title_position": "center",
                "content_position": "center",
                "alignment": "center",
                "max_width": "70%",
            },
            "two_column_text": {
                "title_position": "top",
                "content_position": "split",
                "column_count": 2,
                "split_ratio": "50:50",
            },
            "title_with_large_text": {
                "title_position": "top",
                "content_position": "center",
                "font_size": "large",
                "alignment": "center",
            },
        }

        return configs.get(layout, {})

    def _get_alternatives(
        self, selected_layout: str, page_type: str, content_type: str
    ) -> List[str]:
        """生成替代布局方案"""
        alternatives = []

        # 常见替代方案
        alternative_map = {
            "title_with_bullet_points": ["two_column_text", "title_with_large_text"],
            "title_with_left_chart": ["title_with_chart_and_image", "title_with_bullet_points"],
            "title_with_right_image": ["title_with_chart_and_image", "title_with_bullet_points"],
            "title_with_chart_and_image": ["title_with_left_chart", "title_with_right_image"],
            "two_column_text": ["title_with_bullet_points", "title_with_large_text"],
        }

        return alternative_map.get(selected_layout, ["title_with_bullet_points"])

    def _explain_reasoning(
        self, page_type: str, content_type: str, has_chart: bool, has_image: bool
    ) -> str:
        """解释选择原因"""
        reasons = []

        reasons.append(f"页面类型: {page_type}")

        if content_type:
            reasons.append(f"内容类型: {content_type}")

        if has_chart:
            reasons.append("包含图表")

        if has_image:
            reasons.append("包含图片")

        return " | ".join(reasons)


class LayoutRecommendationSkill(BaseSkill):
    """
    布局推荐 Skill（基于内容分析）

    分析具体内容后推荐布局
    """

    name = "layout_recommendation"
    description = "基于具体内容分析推荐最佳布局"
    version = "1.0.0"
    category = "rendering"

    async def execute(
        self, content_text: str, title: str, has_chart: bool = False, has_image: bool = False
    ) -> str:
        """
        基于内容分析推荐布局

        Args:
            content_text: 正文内容
            title: 标题
            has_chart: 是否有图表
            has_image: 是否有图片

        Returns:
            str: 布局推荐结果字符串
        """
        try:
            logger.info(f"[LayoutRecommendation] 分析内容: {title}")

            # 分析内容特征
            analysis = await self._analyze_content(content_text)

            # 根据特征推荐布局
            layout = self._recommend_by_analysis(analysis, has_chart, has_image)

            # 计算置信度
            confidence = self._calculate_confidence(analysis, layout)

            # 生成推荐理由
            reasoning = self._generate_reasoning(analysis, layout)

            return f"推荐布局: {layout}\n置信度: {confidence:.2f}\n原因: {reasoning}"

        except Exception as e:
            logger.error(f"[LayoutRecommendation] 推荐失败: {e}", exc_info=True)
            return f"错误：{str(e)}"

    async def _analyze_content(self, content_text: str) -> Dict[str, Any]:
        """分析内容特征"""
        # 计算长度
        length = len(content_text)

        # 判断文本密度（字数/行数）
        lines = [line for line in content_text.split("\n") if line.strip()]
        text_density = length / len(lines) if lines else 0

        # 检测是否有列表
        has_list = any(line.strip().startswith(("-", "*", "•")) for line in lines)

        # 检测是否有段落
        has_paragraphs = len(lines) > 3

        # 判断长度级别
        if length < 100:
            length_level = "short"
        elif length < 500:
            length_level = "medium"
        else:
            length_level = "long"

        return {
            "content_length": length_level,
            "text_density": text_density,
            "has_list": has_list,
            "has_paragraphs": has_paragraphs,
            "line_count": len(lines),
        }

    def _recommend_by_analysis(
        self, analysis: Dict[str, Any], has_chart: bool, has_image: bool
    ) -> str:
        """根据分析推荐布局"""
        # 优先级：图表/图片 > 内容特征 > 默认

        if has_chart and has_image:
            return "title_with_chart_and_image"
        elif has_chart:
            return "title_with_left_chart"
        elif has_image:
            return "title_with_right_image"
        elif analysis["has_list"]:
            # 有列表，使用要点布局
            if analysis["text_density"] > 50:
                return "two_column_text"
            else:
                return "title_with_bullet_points"
        elif analysis["has_paragraphs"]:
            # 有段落，使用文本布局
            if analysis["content_length"] == "short":
                return "title_with_large_text"
            else:
                return "title_with_bullet_points"
        else:
            return "title_with_bullet_points"

    def _calculate_confidence(self, analysis: Dict[str, Any], layout: str) -> float:
        """计算推荐置信度"""
        # 简化实现
        confidence = 0.8

        # 如果内容特征明显，提高置信度
        if analysis["has_list"]:
            confidence += 0.1

        if analysis["has_paragraphs"]:
            confidence += 0.1

        return min(confidence, 1.0)

    def _generate_reasoning(self, analysis: Dict[str, Any], layout: str) -> str:
        """生成推荐理由"""
        reasoning_parts = []

        reasoning_parts.append(f"内容长度: {analysis['content_length']}")

        if analysis["has_list"]:
            reasoning_parts.append("包含列表，使用要点布局")

        if analysis["has_paragraphs"]:
            reasoning_parts.append("包含段落，使用文本布局")

        reasoning_parts.append(f"推荐布局: {layout}")

        return " | ".join(reasoning_parts)


# ============================================================================
# LangChain Tool 包装器
# ============================================================================

from langchain_core.tools import StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field


class LayoutSelectionInput(BaseModel):
    """布局选择输入参数"""

    page_type: str = Field(..., description="页面类型 (cover/directory/content/summary/thanks)")
    content_type: str = Field(default="text_only", description="内容类型")
    has_chart: bool = Field(default=False, description="是否有图表")
    has_image: bool = Field(default=False, description="是否有图片")
    key_points_count: int = Field(default=3, description="要点数量")


class LayoutRecommendationInput(BaseModel):
    """布局推荐输入参数"""

    content_text: str = Field(..., description="正文内容")
    title: str = Field(..., description="标题")
    has_chart: bool = Field(default=False, description="是否有图表")
    has_image: bool = Field(default=False, description="是否有图片")


# 创建 LangChain Tools
layout_selection_tool = StructuredTool.from_function(
    func=LayoutSelectionSkill().execute,
    name="layout_selection",
    description="根据页面类型和内容选择最佳PPT布局",
    args_schema=LayoutSelectionInput,
)

layout_recommendation_tool = StructuredTool.from_function(
    func=LayoutRecommendationSkill().execute,
    name="layout_recommendation",
    description="基于具体内容分析推荐最佳布局",
    args_schema=LayoutRecommendationInput,
)
