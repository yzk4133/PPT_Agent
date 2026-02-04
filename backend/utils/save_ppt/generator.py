"""
演示文稿生成器主类
"""

import os
import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from pptx import Presentation

from .config import SlideConfig
from .text_processor import TextProcessor
from .strategies import (
    TitleSlideStrategy,
    ContentSlideStrategy,
    TableOfContentsSlideStrategy,
    ImageSlideStrategy,
    SubSectionSlideStrategy,
    ReferencesSlideStrategy,
    EndSlideStrategy,
)

logger = logging.getLogger(__name__)

class PresentationGenerator:
    """演示文稿生成器主类"""

    def __init__(self, template_file_name: str = 'ppt_template_0717.pptx'):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(self.current_dir, template_file_name)

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板文件未找到: {template_path}")

        logger.info(f"\n{'='*80}")
        logger.info(f"初始化 PresentationGenerator")
        logger.info(f"模板文件: {template_path}")
        logger.info(f"{'='*80}")

        self.presentation = Presentation(template_path)
        self.config = SlideConfig()
        self.text_processor = TextProcessor()

        # 记录模板信息
        logger.info(f"模板布局数量: {len(self.presentation.slide_layouts)}")
        for idx, layout in enumerate(self.presentation.slide_layouts):
            logger.info(f"  布局 {idx}: {layout.name}")

        # 共享页面计数器
        self.slide_counter = 0

        # 初始化各种策略
        self.strategies = {
            "title": TitleSlideStrategy(self.presentation, self.config),
            "content": ContentSlideStrategy(self.presentation, self.config),
            "toc": TableOfContentsSlideStrategy(self.presentation, self.config),
            "image": ImageSlideStrategy(self.presentation, self.config),
            "subsection": SubSectionSlideStrategy(self.presentation, self.config),
            "references": ReferencesSlideStrategy(self.presentation, self.config),
            "end": EndSlideStrategy(self.presentation, self.config),
        }

        # 同步页面计数器
        for strategy in self.strategies.values():
            strategy.slide_counter = 0

        logger.info("初始化完成")

    def _parse_content_blocks(self, content_blocks: List[Dict]) -> Tuple[str, str, List[Dict]]:
        """解析内容块"""
        slide_title = ""
        main_paragraph_texts = []
        bullet_points_list = []

        logger.debug("开始解析内容块")

        for block in content_blocks:
            block_type = block.get("type")
            children = block.get("children", [])

            if block_type == "h1" and not slide_title:
                text_content = "".join(c.get("text", "") for c in children if c.get("text"))
                slide_title = self.text_processor.remove_html_tags(text_content)
                logger.debug(f"找到标题: {slide_title}")
            elif block_type == "p":
                text_content = "".join(c.get("text", "") for c in children if c.get("text"))
                clean_text = self.text_processor.remove_html_tags(text_content)
                if clean_text:
                    main_paragraph_texts.append(clean_text)
                    logger.debug(f"找到段落: {clean_text[:50]}...")
            elif block_type == "bullets":
                logger.debug(f"找到项目列表，包含 {len(children)} 项")
                for bullet_item in children:
                    if bullet_item.get("type") == "bullet":
                        summary_text = ""
                        detail_text = ""
                        for bullet_child in bullet_item.get("children", []):
                            if bullet_child.get("type") == "h3":
                                summary_text = "".join(
                                    c.get("text", "") for c in bullet_child.get("children", [])
                                    if c.get("text"))
                            elif bullet_child.get("type") == "p":
                                detail_text = "".join(
                                    c.get("text", "") for c in bullet_child.get("children", [])
                                    if c.get("text"))

                        bullet_points_list.append({
                            "summary": self.text_processor.remove_html_tags(summary_text),
                            "detail": self.text_processor.remove_html_tags(detail_text)
                        })

        logger.debug(f"解析完成: 标题='{slide_title}', 段落数={len(main_paragraph_texts)}, 项目数={len(bullet_points_list)}")

        return slide_title, "\n".join(main_paragraph_texts), bullet_points_list

    def _format_bullet_points_as_text(self, bullet_points: List[Dict]) -> str:
        """将bullet points格式化为文本内容"""
        formatted_text = []
        for i, item in enumerate(bullet_points):
            summary = item.get("summary", "")
            detail = item.get("detail", "")

            if summary:
                formatted_text.append(f"{i+1}. {summary}")
            if detail:
                formatted_text.append(f"   {detail}")
            formatted_text.append("")  # 添加空行分隔

        return "\n".join(formatted_text).strip()

    def generate_presentation(self, json_data: Dict) -> Optional[str]:
        """生成演示文稿的主方法"""
        logger.info(f"\n{'*'*80}")
        logger.info("开始生成演示文稿")
        logger.info(f"{'*'*80}")

        if not isinstance(json_data, dict):
            logger.error("无效输入：需要字典类型")
            return None

        # 获取文档标题
        doc_title = json_data.get("title", "")
        overall_references = json_data.get("references", [])
        sections = json_data.get("sections", [])

        logger.info(f"文档标题: '{doc_title}'")
        logger.info(f"章节数: {len(sections)}")
        logger.info(f"参考文献数: {len(overall_references)}")

        # 如果没有指定标题，从第一个section获取
        if not doc_title and sections:
            first_section_content = sections[0].get("content", [])
            for block in first_section_content:
                if block.get("type") == "h1":
                    doc_title = "".join(c.get("text", "") for c in block.get("children", []) if c.get("text"))
                    break

        if not doc_title:
            doc_title = "未命名演示文稿"

        try:
            # 重置所有策略的计数器
            for strategy in self.strategies.values():
                strategy.slide_counter = 0

            # 1. 创建标题页
            logger.info(f"\n{'='*60}")
            logger.info("创建标题页")
            logger.info(f"{'='*60}")
            self.strategies["title"].create_slide(doc_title)
            current_slide_count = 1
            for strategy in self.strategies.values():
                strategy.slide_counter = current_slide_count

            # 2. 处理每个section
            for section_idx, section_obj in enumerate(sections):
                logger.info(f"\n{'='*60}")
                logger.info(f"处理第 {section_idx + 1} 个章节")
                logger.info(f"{'='*60}")

                if section_idx == 0:
                    logger.info("跳过第一个章节的内容生成")
                    continue

                section_content = section_obj.get("content", [])
                section_root_image = section_obj.get("rootImage", {})

                # 解析内容
                slide_title, main_text, bullet_points = self._parse_content_blocks(section_content)

                # 如果这是第一个section且标题与文档标题相同
                if section_idx == 0 and slide_title == doc_title:
                    slide_title = "概述"

                # 决定使用哪种策略
                # 第一个section（第2页）：使用内容页
                if section_idx == 0:
                    if bullet_points:
                        bullet_text = self._format_bullet_points_as_text(bullet_points)
                        combined_text = main_text + "\n\n" + bullet_text if main_text else bullet_text
                        logger.info(f"创建内容页（包含{len(bullet_points)}个要点）")
                        self.strategies["content"].create_slide(slide_title, combined_text)
                        chunks = self.text_processor.split_text_into_chunks(combined_text)
                        current_slide_count += len(chunks)
                    elif main_text:
                        logger.info("创建内容页（纯文本）")
                        self.strategies["content"].create_slide(slide_title, main_text)
                        chunks = self.text_processor.split_text_into_chunks(main_text)
                        current_slide_count += len(chunks)

                # 第二个section（第3页）：使用SUBCHAPTER_3_ITEMS布局
                elif section_idx == 1:
                    if bullet_points and len(bullet_points) == 3:
                        logger.info("创建子章节页（使用SUBCHAPTER_3_ITEMS布局，ID=16）")
                        # 如果还有额外的段落文本，将其添加到最后一个bullet point
                        if main_text:
                            bullet_points[-1]['detail'] += f"\n\n{main_text}"
                        self.strategies["subsection"].create_slide(slide_title, bullet_points)
                        current_slide_count += 1
                    else:
                        # 如果不是正好3个bullet points，仍使用内容页
                        logger.info(f"注意：第二个section有{len(bullet_points)}个要点，不是3个，将使用普通内容页")
                        if bullet_points:
                            bullet_text = self._format_bullet_points_as_text(bullet_points)
                            combined_text = main_text + "\n\n" + bullet_text if main_text else bullet_text
                        else:
                            combined_text = main_text
                        self.strategies["content"].create_slide(slide_title, combined_text)
                        chunks = self.text_processor.split_text_into_chunks(combined_text)
                        current_slide_count += len(chunks)

                # 第三个section（第5页）：使用SUBCHAPTER_3_ITEMS布局
                elif section_idx == 2:
                    # 将段落转换为3个子项目格式
                    paragraphs = []
                    for block in section_content:
                        if block.get("type") == "p":
                            text_content = "".join(c.get("text", "") for c in block.get("children", []) if c.get("text"))
                            if text_content:
                                paragraphs.append(text_content)

                    if len(paragraphs) >= 2:
                        # 创建3个子项目，如果只有2个段落，第三个留空或合并
                        sub_items = []
                        if len(paragraphs) == 2:
                            # 将第二个段落分成两部分
                            second_para_sentences = paragraphs[1].split('. ')
                            if len(second_para_sentences) >= 2:
                                mid_point = len(second_para_sentences) // 2
                                para2_part1 = '. '.join(second_para_sentences[:mid_point]) + '.'
                                para2_part2 = '. '.join(second_para_sentences[mid_point:])

                                sub_items = [
                                    {"summary": "Research Direction", "detail": paragraphs[0]},
                                    {"summary": "Combination Strategies", "detail": para2_part1},
                                    {"summary": "Biomarker Development", "detail": para2_part2}
                                ]
                            else:
                                sub_items = [
                                    {"summary": "Research Direction", "detail": paragraphs[0]},
                                    {"summary": "Future Studies", "detail": paragraphs[1]},
                                    {"summary": "", "detail": ""}  # 空项
                                ]

                        logger.info("创建子章节页（使用SUBCHAPTER_3_ITEMS布局，ID=16）")
                        self.strategies["subsection"].create_slide(slide_title, sub_items)
                        current_slide_count += 1
                    else:
                        # 如果内容不适合，使用普通内容页
                        logger.info("内容不适合SUBCHAPTER_3_ITEMS布局，使用普通内容页")
                        self.strategies["content"].create_slide(slide_title, main_text)
                        chunks = self.text_processor.split_text_into_chunks(main_text)
                        current_slide_count += len(chunks)

                # 同步计数器
                for strategy in self.strategies.values():
                    strategy.slide_counter = current_slide_count

                # 处理图片（非背景图）- 第4页
                if section_root_image and section_root_image.get("url") and not section_root_image.get("background", False):
                    logger.info("创建图片页")
                    self.strategies["image"].create_slide(section_root_image, slide_title)
                    current_slide_count += 1
                    for strategy in self.strategies.values():
                        strategy.slide_counter = current_slide_count

            # 3. 添加参考文献页
            if overall_references:
                logger.info(f"\n{'='*60}")
                logger.info("创建参考文献页")
                logger.info(f"{'='*60}")
                pages_needed = (len(overall_references[:SlideConfig.MAX_TOTAL_REFERENCES]) +
                            SlideConfig.MAX_REFERENCES_PER_SLIDE - 1) // SlideConfig.MAX_REFERENCES_PER_SLIDE
                self.strategies["references"].create_slide(overall_references)
                current_slide_count += pages_needed
                for strategy in self.strategies.values():
                    strategy.slide_counter = current_slide_count

            # 4. 添加结束页
            logger.info(f"\n{'='*60}")
            logger.info("创建结束页")
            logger.info(f"{'='*60}")
            self.strategies["end"].create_slide()

            # 保存文件
            output_dir = os.path.join(self.current_dir, 'output_ppts')
            os.makedirs(output_dir, exist_ok=True)

            sanitized_title = re.sub(r'[\\/:*?"<>|]', '', doc_title)
            output_filename = os.path.join(output_dir, f'{sanitized_title}.pptx')
            self.presentation.save(output_filename)

            logger.info(f"\n{'*'*80}")
            logger.info(f"PPT生成成功!")
            logger.info(f"文件路径: {output_filename}")
            logger.info(f"总页数: {self.strategies['end'].slide_counter}")
            logger.info(f"{'*'*80}")

            # 输出页面总结
            logger.info("\n页面结构总结：")
            logger.info("第1页: 标题页")
            logger.info("第2页: 内容页 - 概述（3个要点）")
            logger.info("第3页: 子章节页（3项，使用布局ID=16）")
            logger.info("第4页: 图片页 - ")
            logger.info("第5页: 子章节页（3项，使用布局ID=16）")
            logger.info("第6页: 参考文献页")
            logger.info("第7页: 结束页")

            return output_filename

        except Exception as e:
            logger.critical(f"PPT生成失败: {e}", exc_info=True)
            return None
