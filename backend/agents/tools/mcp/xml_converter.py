#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XML to JSON Converter MCP Tool

将 XML 格式的 PPT 数据转换为 JSON 格式，方便 PPT 生成和下载。

Converted to MCP tool format - 2025-02-03
"""

import json
import logging
import os
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
import dotenv
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

from .base_mcp_tool import BaseMCPTool

dotenv.load_dotenv()

logger = logging.getLogger(__name__)

class XMLConverterTool(BaseMCPTool):
    """
    XML to JSON Converter Tool

    将 XML 格式的 PPT 数据转换为 JSON 格式，
    并调用 PPT 生成服务创建 PPT 文件。
    """

    def __init__(self):
        super().__init__(name="xml_converter")
        self.download_url = os.environ.get("DOWNLOAD_URL", "")

    async def execute(
        self,
        xml_content: str,
        title: str = "Presentation",
        references: Optional[List[Dict]] = None,
        generate_ppt: bool = False,
        tool_context: Optional[Any] = None
    ) -> str:
        """
        将 XML 格式的 PPT 内容转换为 JSON 格式

        Args:
            xml_content: XML 格式的 PPT 内容
            title: PPT 标题
            references: 参考文献列表
            generate_ppt: 是否生成 PPT 文件（需要 DOWNLOAD_URL 环境变量）
            tool_context: 工具上下文（可选）

        Returns:
            JSON 格式的转换结果
        """
        try:
            # 解析 XML 并转换为 JSON
            sections_data = self._parse_xml_content(xml_content)

            if not sections_data:
                return self._error("无法解析 XML 内容", {
                    "xml_length": len(xml_content),
                    "title": title
                })

            result = {
                "title": title,
                "sections": sections_data,
                "total_sections": len(sections_data),
                "references": references or []
            }

            # 如果需要生成 PPT 文件
            ppt_url = None
            if generate_ppt:
                if not self.download_url:
                    return self._error("未配置 DOWNLOAD_URL 环境变量", result)

                ppt_url = await self._generate_pptx_file(title, sections_data, references or [])
                if ppt_url:
                    result["ppt_url"] = ppt_url
                    result["ppt_generated"] = True
                else:
                    result["ppt_generated"] = False
                    result["ppt_error"] = "PPT 生成失败"

            return self._success(result, metadata={
                "xml_parsed": True,
                "ppt_generated": ppt_url is not None if generate_ppt else False
            })

        except Exception as e:
            logger.error(f"XML conversion failed: {e}")
            return self._error(f"转换失败: {str(e)}", {
                "title": title,
                "xml_length": len(xml_content) if xml_content else 0
            })

    def _parse_xml_content(self, xml_content: str) -> List[Dict[str, Any]]:
        """
        解析 XML 内容并返回 JSON 格式的 sections 列表

        Args:
            xml_content: XML 格式的字符串

        Returns:
            sections 列表
        """
        try:
            # 清理 XML 内容
            cleaned_xml = self._clean_xml(xml_content)

            # 解析 XML
            soup = BeautifulSoup(cleaned_xml, "xml")
            clean_xml_str = str(soup)

            parser = ET.XMLParser()
            root = ET.fromstring(clean_xml_str, parser=parser)

            # 解析所有 SECTION
            sections = root.findall("SECTION")
            sections_data = [self._parse_section(sec) for sec in sections]

            logger.info(f"Parsed {len(sections_data)} sections from XML")
            return sections_data

        except Exception as e:
            logger.error(f"XML parsing error: {e}")
            return []

    def _clean_xml(self, xml_content: str) -> str:
        """清理 XML 内容，移除多余的分隔符和注释"""
        # 移除 Markdown XML block 分隔符
        start_delimiter = "```xml\n"
        end_delimiter = "```"
        if xml_content.startswith(start_delimiter):
            xml_content = xml_content[len(start_delimiter):]
        if xml_content.endswith(end_delimiter):
            xml_content = xml_content[:-len(end_delimiter)]

        # 移除 XML 注释行
        xml_content = re.sub(r'<!--.*?-->\n?', '', xml_content)

        return xml_content.strip()

    def _parse_section(self, section) -> Dict[str, Any]:
        """解析单个 SECTION 元素"""
        result = {
            "id": str(uuid.uuid4()),
            "content": [],
            "rootImage": None,
            "layoutType": section.attrib.get("layout", "vertical"),
            "alignment": "center"
        }

        # H1 标题
        h1 = section.find("H1")
        if h1 is not None and h1.text:
            result["content"].append({
                "type": "h1",
                "children": [{"text": h1.text.strip()}]
            })

        # 结构体标签
        structured_tags = ["BULLETS", "COLUMNS", "STAIRCASE", "TIMELINE"]
        for tag in structured_tags:
            node = section.find(tag)
            if node is not None:
                bullets = []
                for div in node.findall("DIV"):
                    bullets.append(self._parse_div(div))
                result["content"].append({
                    "type": "bullets",
                    "children": bullets
                })

        # 图片
        img = section.find("IMG")
        if img is not None:
            result["rootImage"] = {
                "url": img.attrib.get("src", ""),
                "query": "",
                "background": img.attrib.get("background", "false").lower() == "true",
                "alt": img.attrib.get("alt", "")
            }

        return result

    def _parse_div(self, div) -> Dict[str, Any]:
        """解析 DIV 元素"""
        children = []
        for elem in div:
            if elem.tag == "H3" and elem.text:
                children.append({
                    "type": "h3",
                    "children": [{"text": elem.text.strip()}]
                })
            elif elem.tag == "P" and elem.text:
                children.append({
                    "type": "p",
                    "children": [{"text": elem.text.strip()}]
                })
        return {
            "type": "bullet",
            "children": children
        }

    async def _generate_pptx_file(
        self,
        title: str,
        sections: List[Dict],
        references: List[Dict]
    ) -> Optional[str]:
        """
        调用 PPT 生成服务生成 PPT 文件

        Args:
            title: PPT 标题
            sections: sections 列表
            references: 参考文献列表

        Returns:
            PPT 文件下载 URL，失败返回 None
        """
        try:
            front_data = {
                "title": title,
                "sections": sections,
                "references": references
            }

            response = requests.post(
                f"{self.download_url}/generate-ppt",
                json=front_data,
                timeout=120
            )

            logger.info(f"PPT generation status: {response.status_code}")

            if response.status_code == 200:
                response_json = response.json()
                if "ppt_url" in response_json and response_json["ppt_url"].endswith(".pptx"):
                    ppt_url = response_json["ppt_url"]
                    logger.info(f"PPT generated successfully: {ppt_url}")
                    return ppt_url
                else:
                    logger.error(f"Invalid response: {response_json}")
                    return None
            else:
                logger.error(f"PPT generation failed with status {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"PPT generation error: {e}")
            return None

    async def parse_trunk_data(
        self,
        trunk_list: List[Dict],
        title: str = "Presentation"
    ) -> str:
        """
        解析 trunk 数据（Agent 输出流）并转换为 JSON 格式

        Args:
            trunk_list: Agent 输出的 trunk 列表
            title: PPT 标题

        Returns:
            JSON 格式的结果
        """
        try:
            # 用于存储每个页码对应的XML内容
            page_xml_map = {}
            overall_start_xml = ""
            overall_end_xml = ""
            latest_references = []

            # 正则表达式匹配 page_number
            page_number_pattern = re.compile(
                r'<SECTION[^>]+page_number\s*=\s*["\']?(\d+)["\']?[^>]*>'
            )

            for one in trunk_list:
                # 提取 XML 文本内容
                content_parts = one.get("text", {}).get("result", {}).get("status", {}) \
                    .get("message", {}).get("parts", [])
                if not content_parts:
                    continue

                text_content = content_parts[0].get("text", "")

                # 清理 XML
                text_content = self._clean_xml(text_content)

                # 更新 references
                metadata = one.get("text", {}).get("result", {}).get("status", {}) \
                    .get("message", {}).get("metadata", {})
                if "references" in metadata:
                    latest_references = metadata["references"]

                # 匹配 page_number
                match = page_number_pattern.search(text_content)

                if match:
                    page_number = int(match.group(1))
                    page_xml_map[page_number] = text_content.strip()
                elif text_content.strip() == '<PRESENTATION>':
                    overall_start_xml = text_content.strip()
                elif text_content.strip() == '</PRESENTATION>':
                    overall_end_xml = text_content.strip()

            # 拼接完整的 XML 内容
            final_xml_parts = []
            if overall_start_xml:
                final_xml_parts.append(overall_start_xml)

            sorted_page_numbers = sorted(page_xml_map.keys())
            for page_num in sorted_page_numbers:
                final_xml_parts.append(page_xml_map[page_num])

            if overall_end_xml:
                final_xml_parts.append(overall_end_xml)

            ppt_content = "\n".join(final_xml_parts)

            # 解析并转换为 JSON
            sections_data = self._parse_xml_content(ppt_content)

            result = {
                "title": title,
                "sections": sections_data,
                "total_sections": len(sections_data),
                "references": latest_references
            }

            return self._success(result)

        except Exception as e:
            logger.error(f"Trunk data parsing failed: {e}")
            return self._error(f"解析失败: {str(e)}", {
                "title": title,
                "trunk_count": len(trunk_list)
            })

# 创建全局实例
_xml_converter_tool = XMLConverterTool()

# 导出函数式接口（与 agents 工具兼容）
async def xml_converter(
    xml_content: str,
    title: str = "Presentation",
    references: Optional[List[Dict]] = None,
    generate_ppt: bool = False,
    tool_context: Optional[Any] = None
) -> str:
    """
    将 XML 格式的 PPT 内容转换为 JSON 格式

    Args:
        xml_content: XML 格式的 PPT 内容
        title: PPT 标题
        references: 参考文献列表
        generate_ppt: 是否生成 PPT 文件
        tool_context: 工具上下文（可选）

    Returns:
        JSON 格式的转换结果
    """
    return await _xml_converter_tool.execute(
        xml_content=xml_content,
        title=title,
        references=references,
        generate_ppt=generate_ppt,
        tool_context=tool_context
    )

async def parse_xml_to_json(
    xml_content: str,
    title: str = "Presentation"
) -> Dict[str, Any]:
    """
    便捷函数：将 XML 转换为 JSON 字典

    Args:
        xml_content: XML 格式的字符串
        title: PPT 标题

    Returns:
        转换后的字典
    """
    result = await xml_converter(xml_content=xml_content, title=title)
    data = json.loads(result)
    if data.get("success"):
        return data["result"]
    return {}

async def parse_trunk_data(
    trunk_list: List[Dict],
    title: str = "Presentation"
) -> str:
    """
    便捷函数：解析 trunk 数据并转换为 JSON

    Args:
        trunk_list: Agent 输出的 trunk 列表
        title: PPT 标题

    Returns:
        JSON 格式的结果
    """
    return await _xml_converter_tool.parse_trunk_data(trunk_list, title)

if __name__ == "__main__":
    # 测试代码
    async def test():
        # 测试 XML 转换
        test_xml = """
        <PRESENTATION>
        <SECTION page_number="1" layout="vertical">
            <H1>测试标题</H1>
            <BULLETS>
                <DIV>
                    <H3>要点1</H3>
                    <P>内容1</P>
                </DIV>
            </BULLETS>
        </SECTION>
        </PRESENTATION>
        """

        result = await xml_converter(
            xml_content=test_xml,
            title="测试PPT"
        )
        print(json.dumps(json.loads(result), ensure_ascii=False, indent=2))

    import asyncio
    asyncio.run(test())
