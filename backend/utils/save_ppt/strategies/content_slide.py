"""
内容页生成策略
"""

import logging

from .base import SlideStrategy
from ..config import SlideConfig

logger = logging.getLogger(__name__)

class ContentSlideStrategy(SlideStrategy):
    """内容页生成策略"""

    def create_slide(self, title: str, content: str):
        if not content or not content.strip():
            logger.debug(f"跳过空内容页: '{title}'")
            return

        content_chunks = self.text_processor.split_text_into_chunks(content)
        print(f"内容被分为 {len(content_chunks)} 个块")

        for idx, chunk in enumerate(content_chunks):
            self.slide_counter += 1
            slide_title = title if idx == 0 else f"{title} (续 {idx + 1})"

            print(f"\n{'#'*80}")
            print(f"# 创建第 {self.slide_counter} 页: 内容页")
            print(f"# 标题: {slide_title}")
            print(f"# 内容长度: {len(chunk)} 字符")
            print(f"{'#'*80}")

            # 根据内容长度选择布局
            if len(chunk) < 150:
                layout_key = "TEXT_ONLY_SMALL_TITLE"
                text_shape_id = self.config.SHAPE_IDS["CONTENT_TEXT"]
                print("使用小标题布局（内容较短）")
            else:
                layout_key = "CONTENT_TITLE_AND_TEXT"
                text_shape_id = self.config.SHAPE_IDS["CONTENT_TEXT_LAYOUT1_4"]
                print("使用标准内容布局")

            slide_layout = self._get_slide_layout(layout_key)
            slide = self.presentation.slides.add_slide(slide_layout)

            # 记录所有形状信息
            self._log_slide_shapes(slide, "内容页")

            # 添加标题
            self._add_text_with_auto_fit(
                slide,
                self.config.SHAPE_IDS["CONTENT_TITLE"],
                slide_title,
                font_type="title",
                max_chars=80,
                is_title_page=False
            )

            # 添加内容
            self._add_text_with_auto_fit(
                slide,
                text_shape_id,
                chunk,
                font_type="content"
            )

            self._fill_empty_placeholders(slide)
            print(f"✓ 内容页创建完成")
