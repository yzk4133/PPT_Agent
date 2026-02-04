"""
图片页生成策略
"""

import logging
from typing import Dict, Optional
from io import BytesIO

import requests
from PIL import Image

from .base import SlideStrategy
from ..config import SlideConfig

logger = logging.getLogger(__name__)

class ImageSlideStrategy(SlideStrategy):
    """图片页生成策略"""

    def _is_valid_image_url(self, url: str) -> bool:
        """检查图片URL是否有效"""
        if not isinstance(url, str):
            return False
        is_valid = any(url.startswith(prefix) for prefix in self.config.VALID_IMAGE_URL_PREFIXES)
        logger.debug(f"图片URL验证: {url} -> {'有效' if is_valid else '无效'}")
        return is_valid

    def _download_image(self, image_url: str) -> Optional[BytesIO]:
        """下载图片"""
        if not self._is_valid_image_url(image_url):
            logger.warning(f"无效的图片URL: {image_url}")
            return None

        try:
            print(f"开始下载图片: {image_url}")
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            print(f"✓ 成功下载图片，大小: {len(response.content)} 字节")
            return BytesIO(response.content)
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ 下载图片失败 {image_url}: {e}")
            return None

    def _insert_image_into_placeholder(self, slide, img_stream: BytesIO, placeholder_shape_id: int):
        """将图片插入占位符"""
        logger.debug(f"尝试将图片插入占位符 {placeholder_shape_id}")

        placeholder_shape = None
        for shape in slide.shapes:
            if shape.shape_id == placeholder_shape_id:
                placeholder_shape = shape
                print(f"✓ 找到图片占位符 {placeholder_shape_id} (名称: {shape.name})")
                break

        if not placeholder_shape:
            logger.error(f"✗ 未找到图片占位符 {placeholder_shape_id}")
            available_ids = [s.shape_id for s in slide.shapes]
            logger.error(f"  可用的形状ID: {available_ids}")
            return None

        try:
            img = Image.open(img_stream)
            img_width, img_height = img.size
            logger.debug(f"图片尺寸: {img_width} x {img_height}")

            placeholder_width = placeholder_shape.width
            placeholder_height = placeholder_shape.height

            # 计算缩放比例
            width_ratio = placeholder_width / img_width
            height_ratio = placeholder_height / img_height
            scaling_factor = min(width_ratio, height_ratio)

            pic_width = int(img_width * scaling_factor)
            pic_height = int(img_height * scaling_factor)

            # 居中位置
            left = placeholder_shape.left + (placeholder_width - pic_width) / 2
            top = placeholder_shape.top + (placeholder_height - pic_height) / 2

            img_stream.seek(0)
            added_picture = slide.shapes.add_picture(img_stream, left, top, pic_width, pic_height)
            print(f"✓ 图片已插入，缩放后尺寸: {pic_width/914400:.2f} x {pic_height/914400:.2f} 英寸")

            # 移除占位符
            sp = placeholder_shape._element
            sp.getparent().remove(sp)

            return added_picture
        except Exception as e:
            logger.error(f"✗ 插入图片失败: {e}")
            return None

    def create_slide(self, image_data: Dict, section_title: str = "图表"):
        """创建图片幻灯片"""
        self.slide_counter += 1
        image_url = image_data.get("url", "")
        description = image_data.get("alt", "")
        image_title = section_title

        print(f"\n{'#'*80}")
        print(f"# 创建第 {self.slide_counter} 页: 图片页")
        print(f"# 标题: {image_title}")
        print(f"# 图片URL: {image_url}")
        print(f"# 是否有描述: {'是' if description else '否'}")
        print(f"{'#'*80}")

        img_stream = self._download_image(image_url)
        if not img_stream:
            logger.warning(f"跳过图片幻灯片: {image_url}")
            return

        try:
            img = Image.open(img_stream)
            img_width, img_height = img.size
            print(f"图片尺寸: {img_width} x {img_height}")
        except Exception as e:
            logger.error(f"打开图片失败 {image_url}: {e}")
            return

        description = self.text_processor.remove_html_tags(description)

        # 选择布局
        if description:
            if img_width > img_height:
                layout_key = "IMAGE_TITLE_AND_DESCRIPTION_WIDE"
                print("使用横向图片布局（带描述）")
            else:
                layout_key = "IMAGE_TITLE_AND_DESCRIPTION_TALL"
                print("使用纵向图片布局（带描述）")
        else:
            layout_key = "IMAGE_ONLY"
            print("使用纯图片布局")

        slide_layout = self._get_slide_layout(layout_key)
        slide = self.presentation.slides.add_slide(slide_layout)

        # 记录所有形状信息
        self._log_slide_shapes(slide, "图片页")

        self._insert_image_into_placeholder(slide, img_stream, self.config.SHAPE_IDS["IMAGE_PLACEHOLDER"])
        self._add_text_with_auto_fit(
            slide,
            self.config.SHAPE_IDS["IMAGE_TITLE"],
            image_title,
            font_type="title",
            is_title_page=False
        )

        if description:
            self._add_text_with_auto_fit(
                slide,
                self.config.SHAPE_IDS["IMAGE_DESCRIPTION"],
                description,
                font_type="content"
            )

        self._fill_empty_placeholders(slide)
        print(f"✓ 图片页创建完成")
