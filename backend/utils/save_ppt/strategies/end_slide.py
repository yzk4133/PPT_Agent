"""
结束页生成策略
"""

from .base import SlideStrategy

class EndSlideStrategy(SlideStrategy):
    """结束页生成策略"""

    def create_slide(self):
        """创建结束页"""
        self.slide_counter += 1
        print(f"\n{'#'*80}")
        print(f"# 创建第 {self.slide_counter} 页: 结束页")
        print(f"{'#'*80}")

        slide_layout = self._get_slide_layout("END_PAGE")
        slide = self.presentation.slides.add_slide(slide_layout)

        # 记录所有形状信息
        self._log_slide_shapes(slide, "结束页")

        print(f"✓ 结束页创建完成")
