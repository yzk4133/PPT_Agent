"""
目录页生成策略
"""

import logging
import random
from typing import List

from .base import SlideStrategy
from ..config import SlideConfig

logger = logging.getLogger(__name__)

class TableOfContentsSlideStrategy(SlideStrategy):
    """目录页生成策略"""

    def create_slide(self, toc_items: List[str]):
        if not toc_items:
            print("无目录项，跳过目录页")
            return

        self.slide_counter += 1
        print(f"\n{'#'*80}")
        print(f"# 创建第 {self.slide_counter} 页: 目录页")
        print(f"# 目录项数: {len(toc_items)}")
        print(f"{'#'*80}")

        # 根据项目数选择布局
        layout_map = {
            3: "TABLE_OF_CONTENTS_3_ITEMS",
            4: random.choice(["TABLE_OF_CONTENTS_4_ITEMS_A", "TABLE_OF_CONTENTS_4_ITEMS_B"]),
            5: random.choice(["TABLE_OF_CONTENTS_5_ITEMS_A", "TABLE_OF_CONTENTS_5_ITEMS_B"]),
        }

        layout_key = layout_map.get(len(toc_items), "TABLE_OF_CONTENTS_GENERIC")
        print(f"根据 {len(toc_items)} 个目录项，选择布局: {layout_key}")

        slide_layout = self._get_slide_layout(layout_key)
        slide = self.presentation.slides.add_slide(slide_layout)

        # 记录所有形状信息
        self._log_slide_shapes(slide, "目录页")

        # 添加标题
        self._add_text_with_auto_fit(
            slide,
            self.config.SHAPE_IDS["TOC_TITLE"],
            "目录",
            font_type="title",
            is_title_page=False
        )

        # 添加目录项
        toc_shape_ids = self.config.SHAPE_IDS["TOC_ITEMS"]
        for i, item in enumerate(toc_items[:6]):  # 最多6项
            if i + 1 in toc_shape_ids:
                print(f"添加目录项 {i+1}: {item}")
                self._add_text_with_auto_fit(
                    slide,
                    toc_shape_ids[i + 1],
                    item,
                    font_type="content",
                    max_chars=80
                )

        self._fill_empty_placeholders(slide)
        print(f"✓ 目录页创建完成")
