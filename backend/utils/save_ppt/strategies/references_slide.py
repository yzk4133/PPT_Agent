"""
参考文献页生成策略
"""

import logging
from typing import List

from .base import SlideStrategy
from ..config import SlideConfig

logger = logging.getLogger(__name__)

class ReferencesSlideStrategy(SlideStrategy):
    """参考文献页生成策略"""

    def _process_reference_text(self, reference_text: str) -> str:
        """处理参考文献文本"""
        if not isinstance(reference_text, str):
            return ""
        lines = reference_text.splitlines()
        processed_lines = []
        i = 0
        while i < len(lines):
            current_line = lines[i].strip()
            if len(current_line) < 15 and i + 1 < len(lines):
                current_line += " " + lines[i + 1].strip()
                i += 1
            processed_lines.append(current_line)
            i += 1
        return "\n".join(processed_lines)

    def create_slide(self, references: List[str]):
        """创建参考文献幻灯片"""
        if not references:
            print("无参考文献，跳过")
            return

        print(f"总参考文献数: {len(references)}")

        # 预处理参考文献
        processed_references = [
            self._process_reference_text(self.text_processor.remove_html_tags(ref))
            for ref in references[:self.config.MAX_TOTAL_REFERENCES]
        ]

        # 分页处理
        total_pages = (len(processed_references) + self.config.MAX_REFERENCES_PER_SLIDE - 1) // self.config.MAX_REFERENCES_PER_SLIDE

        for page_idx in range(0, len(processed_references), self.config.MAX_REFERENCES_PER_SLIDE):
            self.slide_counter += 1
            current_page = page_idx // self.config.MAX_REFERENCES_PER_SLIDE + 1

            print(f"\n{'#'*80}")
            print(f"# 创建第 {self.slide_counter} 页: 参考文献页 ({current_page}/{total_pages})")
            print(f"{'#'*80}")

            group = processed_references[page_idx:page_idx + self.config.MAX_REFERENCES_PER_SLIDE]
            slide_layout = self._get_slide_layout("REFERENCES_PAGE")
            slide = self.presentation.slides.add_slide(slide_layout)

            # 记录所有形状信息
            self._log_slide_shapes(slide, "参考文献页")

            self._add_text_with_auto_fit(
                slide,
                self.config.SHAPE_IDS["REFERENCES_TITLE"],
                "部分参考文献",
                font_type="title",
                is_title_page=False
            )

            # 添加参考文献
            for idx, ref_text in enumerate(group):
                if idx < len(self.config.SHAPE_IDS["REFERENCES"]):
                    ref_config = self.config.SHAPE_IDS["REFERENCES"][idx]
                    ref_num = page_idx + idx + 1
                    print(f"添加参考文献 {ref_num}: 编号形状={ref_config['num']}, 文本形状={ref_config['text']}")

                    self._add_text_with_auto_fit(
                        slide,
                        ref_config["num"],
                        f"{ref_num}.",
                        font_type="small"
                    )
                    self._add_text_with_auto_fit(
                        slide,
                        ref_config["text"],
                        ref_text,
                        font_type="small"
                    )

            self._fill_empty_placeholders(slide)
            print(f"✓ 参考文献页创建完成")
