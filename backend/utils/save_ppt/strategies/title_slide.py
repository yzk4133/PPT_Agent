"""
标题页生成策略
"""

import datetime

from .base import SlideStrategy
from ..config import SlideConfig

class TitleSlideStrategy(SlideStrategy):
    """标题页生成策略"""

    def create_slide(self, title: str):
        self.slide_counter += 1
        print(f"\n{'#'*80}")
        print(f"# 创建第 {self.slide_counter} 页: 标题页")
        print(f"# 标题: {title}")
        print(f"{'#'*80}")

        slide_layout = self._get_slide_layout("TITLE_PAGE")
        slide = self.presentation.slides.add_slide(slide_layout)

        # 记录所有形状信息
        self._log_slide_shapes(slide, "标题页")

        # 添加标题
        self._add_text_with_auto_fit(
            slide,
            self.config.SHAPE_IDS["TITLE_PAGE_TITLE"],
            title,
            font_type="title",
            max_chars=None,
            is_title_page=True
        )

        # 添加日期
        current_date = datetime.datetime.now().strftime("%Y年%m月%d日")
        self._add_text_with_auto_fit(
            slide,
            self.config.SHAPE_IDS["TITLE_PAGE_DATE"],
            current_date,
            font_type="small"
        )

        self._fill_empty_placeholders(slide)
        print(f"✓ 标题页创建完成")
