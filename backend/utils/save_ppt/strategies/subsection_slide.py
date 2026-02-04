"""
子章节详情页生成策略
"""

import logging
from typing import List, Dict

from .base import SlideStrategy
from ..config import SlideConfig

logger = logging.getLogger(__name__)

class SubSectionSlideStrategy(SlideStrategy):
    """子章节详情页生成策略"""

    def create_slide(self, section_name: str, sub_section_content: List[Dict]):
        """创建子章节幻灯片"""
        num_items = len(sub_section_content)
        if num_items == 0:
            logger.debug(f"跳过空子章节: '{section_name}'")
            return

        self.slide_counter += 1
        print(f"\n{'#'*80}")
        print(f"# 创建第 {self.slide_counter} 页: 子章节页")
        print(f"# 标题: {section_name}")
        print(f"# 子项数: {num_items}")
        print(f"{'#'*80}")

        # 根据项目数选择布局
        layout_map = {
            1: "TEXT_ONLY_SMALL_TITLE",
            2: "SUBCHAPTER_2_ITEMS",
            3: "SUBCHAPTER_3_ITEMS",
            4: "SUBCHAPTER_4_ITEMS",
            5: "SUBCHAPTER_5_ITEMS",
        }

        layout_key = layout_map.get(num_items)
        if not layout_key:
            logger.warning(f"不支持 {num_items} 个项目的子章节")
            return

        print(f"使用布局: {layout_key}")

        slide_layout = self._get_slide_layout(layout_key)
        slide = self.presentation.slides.add_slide(slide_layout)

        # 记录所有形状信息
        self._log_slide_shapes(slide, "子章节页")

        self._add_text_with_auto_fit(
            slide,
            self.config.SHAPE_IDS["SUBCHAPTER_TITLE"],
            section_name,
            font_type="title",
            is_title_page=False
        )

        # 添加内容项
        if num_items == 1:
            detail = sub_section_content[0].get('detail', '')
            print(f"添加单项内容: {detail[:50]}...")
            self._add_text_with_auto_fit(
                slide,
                self.config.SHAPE_IDS["CONTENT_TEXT"],
                detail,
                font_type="content"
            )
        elif num_items == 5:
            # 5项特殊处理
            print("处理5项内容（特殊布局）")
            for i, item in enumerate(sub_section_content[:5]):
                num_id, text_id = self.config.SHAPE_IDS["SUBCHAPTER_ITEMS"][5][i]
                print(f"  项目 {i+1}: 编号形状={num_id}, 文本形状={text_id}")
                self._add_text_with_auto_fit(slide, num_id, str(i+1), font_type="small")
                combined_text = f"{item.get('summary', '')}\n{item.get('detail', '')}"
                self._add_text_with_auto_fit(slide, text_id, combined_text, font_type="content")
        else:
            # 2-4项通用处理
            shape_ids = self.config.SHAPE_IDS["SUBCHAPTER_ITEMS"][num_items]
            print(f"处理 {num_items} 项内容，形状ID: {shape_ids}")
            for i, (item, shape_id) in enumerate(zip(sub_section_content, shape_ids)):
                summary = item.get("summary", "")
                detail = item.get("detail", "")
                combined_text = f"{summary}\n{detail}" if summary else detail
                print(f"  项目 {i+1}: 形状={shape_id}, 内容长度={len(combined_text)}")
                self._add_text_with_auto_fit(slide, shape_id, combined_text, font_type="content")

        self._fill_empty_placeholders(slide)
        print(f"✓ 子章节页创建完成")
