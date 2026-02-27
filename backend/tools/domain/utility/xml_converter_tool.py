"""
LangChain Native Tool: XML Converter

Converts XML-formatted PPT data to JSON format for PPT generation.
"""

import json
import logging
import os
import re
import uuid
from typing import Optional, List, Dict

import requests
import dotenv
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from backend.tools.core.monitoring import monitor_tool
from backend.tools.application.tool_registry import get_native_registry

dotenv.load_dotenv()

logger = logging.getLogger(__name__)

# Get download URL from environment
DOWNLOAD_URL = os.environ.get("DOWNLOAD_URL", "")


# Input schema
class XmlConverterInput(BaseModel):
    """XML converter input schema"""
    xml_content: str = Field(description="XML-formatted PPT content")
    title: str = Field(default="Presentation", description="Presentation title")
    generate_ppt: bool = Field(default=False, description="Whether to generate PPT file")


@monitor_tool
async def xml_converter(
    xml_content: str,
    title: str = "Presentation",
    generate_ppt: bool = False
) -> dict:
    """
    Convert XML-formatted PPT content to JSON

    Parses XML presentation data and converts it to structured JSON format.
    Optionally generates a PPT file if DOWNLOAD_URL is configured.

    Args:
        xml_content: XML-formatted presentation content
        title: Presentation title
        generate_ppt: Whether to generate PPT file

    Returns:
        Dictionary with converted JSON data and optional PPT URL
    """
    try:
        # Parse XML and convert to JSON
        sections_data = _parse_xml_content(xml_content)

        if not sections_data:
            raise ValueError("Unable to parse XML content")

        result = {
            "title": title,
            "sections": sections_data,
            "total_sections": len(sections_data),
            "references": []
        }

        # Generate PPT if requested
        ppt_url = None
        if generate_ppt:
            if not DOWNLOAD_URL:
                raise ValueError("DOWNLOAD_URL environment variable not configured")

            ppt_url = await _generate_pptx_file(title, sections_data, [])
            if ppt_url:
                result["ppt_url"] = ppt_url
                result["ppt_generated"] = True
            else:
                result["ppt_generated"] = False
                result["ppt_error"] = "PPT generation failed"

        logger.info(f"[xml_converter] Converted {len(sections_data)} sections")
        return result

    except Exception as e:
        logger.error(f"[xml_converter] Error: {e}", exc_info=True)
        raise


def _parse_xml_content(xml_content: str) -> List[Dict]:
    """Parse XML content and return sections list"""
    try:
        # Clean XML content
        cleaned_xml = _clean_xml(xml_content)

        # Parse XML
        soup = BeautifulSoup(cleaned_xml, "xml")
        clean_xml_str = str(soup)

        parser = ET.XMLParser()
        root = ET.fromstring(clean_xml_str, parser=parser)

        # Parse all SECTION elements
        sections = root.findall("SECTION")
        sections_data = [_parse_section(sec) for sec in sections]

        logger.info(f"[xml_converter] Parsed {len(sections_data)} sections")
        return sections_data

    except Exception as e:
        logger.error(f"[xml_converter] XML parsing error: {e}")
        return []


def _clean_xml(xml_content: str) -> str:
    """Clean XML content, remove delimiters and comments"""
    # Remove Markdown XML block delimiters
    start_delimiter = "```xml\n"
    end_delimiter = "```"
    if xml_content.startswith(start_delimiter):
        xml_content = xml_content[len(start_delimiter):]
    if xml_content.endswith(end_delimiter):
        xml_content = xml_content[:-len(end_delimiter)]

    # Remove XML comments
    xml_content = re.sub(r'<!--.*?-->\n?', '', xml_content)

    return xml_content.strip()


def _parse_section(section) -> Dict:
    """Parse single SECTION element"""
    result = {
        "id": str(uuid.uuid4()),
        "content": [],
        "rootImage": None,
        "layoutType": section.attrib.get("layout", "vertical"),
        "alignment": "center"
    }

    # H1 title
    h1 = section.find("H1")
    if h1 is not None and h1.text:
        result["content"].append({
            "type": "h1",
            "children": [{"text": h1.text.strip()}]
        })

    # Structured tags
    structured_tags = ["BULLETS", "COLUMNS", "STAIRCASE", "TIMELINE"]
    for tag in structured_tags:
        node = section.find(tag)
        if node is not None:
            bullets = []
            for div in node.findall("DIV"):
                bullets.append(_parse_div(div))
            result["content"].append({
                "type": "bullets",
                "children": bullets
            })

    # Image
    img = section.find("IMG")
    if img is not None:
        result["rootImage"] = {
            "url": img.attrib.get("src", ""),
            "query": "",
            "background": img.attrib.get("background", "false").lower() == "true",
            "alt": img.attrib.get("alt", "")
        }

    return result


def _parse_div(div) -> Dict:
    """Parse DIV element"""
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
    title: str,
    sections: List[Dict],
    references: List[Dict]
) -> Optional[str]:
    """Call PPT generation service to create PPT file"""
    try:
        front_data = {
            "title": title,
            "sections": sections,
            "references": references
        }

        response = requests.post(
            f"{DOWNLOAD_URL}/generate-ppt",
            json=front_data,
            timeout=120
        )

        logger.info(f"[xml_converter] PPT generation status: {response.status_code}")

        if response.status_code == 200:
            response_json = response.json()
            if "ppt_url" in response_json and response_json["ppt_url"].endswith(".pptx"):
                ppt_url = response_json["ppt_url"]
                logger.info(f"[xml_converter] PPT generated: {ppt_url}")
                return ppt_url
            else:
                logger.error(f"[xml_converter] Invalid response: {response_json}")
                return None
        else:
            logger.error(f"[xml_converter] PPT generation failed with status {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"[xml_converter] PPT generation error: {e}")
        return None


# Create LangChain StructuredTool
tool = StructuredTool.from_function(
    func=xml_converter,
    name="xml_converter",
    description="Convert XML-formatted PPT content to JSON. Use this to parse presentation data.",
    args_schema=XmlConverterInput
)

# Auto-register with global registry
registry = get_native_registry()
registry.register_tool(tool, category=registry.UTILITY)

__all__ = ["tool", "xml_converter"]
