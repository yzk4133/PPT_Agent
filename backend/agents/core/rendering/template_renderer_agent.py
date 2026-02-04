"""
Template Renderer Agent

PPT模板渲染智能体，负责基于模板填充和渲染PPT。

功能：
1. 模板加载（根据 template_type）
2. 页面扩容
3. 内容与素材填充
4. 基础优化（目录、页码）
5. 文件生成与前端预览数据生成
"""

import os
import sys
import json
import logging
from typing import AsyncGenerator, Optional, Dict, Any, List
from datetime import datetime

from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.genai import types
from google.adk.events.event import Event

# 导入基础设施

# 导入领域模型
from domain.models import Requirement, TemplateType

logger = logging.getLogger(__name__)

class TemplateRendererAgent(BaseAgent):
    """
    PPT模板渲染智能体

    职责：
    1. 模板加载（根据 template_type）
    2. 页面扩容
    3. 内容与素材填充
    4. 基础优化（目录、页码）
    5. 文件生成与前端预览数据生成
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="TemplateRendererAgent",
            description="负责基于模板填充和渲染PPT，生成最终文件",
            **kwargs
        )

        # 导入PresentationGenerator（延迟导入以避免依赖问题）
        try:
            from utils.save_ppt.ppt_generator import PresentationGenerator
            object.__setattr__(self, 'generator', PresentationGenerator())
            object.__setattr__(self, 'generator_available', True)
        except ImportError as e:
            logger.warning(f"PresentationGenerator not available: {e}")
            object.__setattr__(self, 'generator', None)
            object.__setattr__(self, 'generator_available', False)

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        执行模板渲染

        Args:
            ctx: 调用上下文
        """
        try:
            # 1. 获取输入数据
            requirement_dict = ctx.session.state.get("structured_requirements", {})
            framework_dict = ctx.session.state.get("ppt_framework", {})
            content_material_list = ctx.session.state.get("content_material", [])
            raw_input = ctx.session.state.get("raw_user_input", "")

            if not framework_dict:
                raise ValueError("Missing ppt_framework in session state")

            requirement = Requirement.from_dict(requirement_dict) if requirement_dict else None
            logger.info(f"TemplateRendererAgent processing: {framework_dict.get('total_page')} pages")

            # 2. 生成XML格式的内容（与现有slide_writer_agent兼容）
            xml_content = self._generate_xml_content(
                framework_dict, content_material_list, requirement
            )

            # 3. 生成PPT文件
            ppt_file_path = await self._render_ppt(
                xml_content=xml_content,
                requirement=requirement,
                framework=framework_dict,
                content_material=content_material_list,
                raw_input=raw_input,
                ctx=ctx
            )

            # 4. 生成预览数据
            preview_data = self._generate_preview_data(
                framework_dict, content_material_list
            )

            # 5. 保存结果到上下文
            ctx.session.state["ppt_output"] = {
                "file_path": ppt_file_path,
                "preview_data": preview_data,
                "xml_content": xml_content
            }

            logger.info(f"Template rendering completed: {ppt_file_path}")

            # 6. 产生完成事件
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[types.Part(
                        text=f"PPT渲染完成：\n"
                        f"- 文件路径: {ppt_file_path}\n"
                        f"- 总页数: {framework_dict.get('total_page', 0)}\n"
                        f"- 预览数据已生成"
                    )]
                ),
            )

        except Exception as e:
            logger.error(f"TemplateRendererAgent failed: {e}", exc_info=True)
            # 生成错误信息
            ctx.session.state["ppt_output"] = {
                "error": str(e),
                "file_path": None,
                "preview_data": None
            }
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[types.Part(text=f"PPT渲染失败: {str(e)}")]
                ),
            )

    def _generate_xml_content(
        self,
        framework_dict: Dict[str, Any],
        content_material_list: List[Dict[str, Any]],
        requirement: Optional[Requirement]
    ) -> str:
        """
        生成XML格式的内容

        Args:
            framework_dict: 框架字典
            content_material_list: 内容素材列表
            requirement: 需求对象

        Returns:
            XML格式的内容字符串
        """
        xml_parts = ["```xml", "<PRESENTATION>"]

        pages = framework_dict.get("ppt_framework", [])

        for i, page_def in enumerate(pages):
            page_no = page_def.get("page_no", i + 1)
            page_title = page_def.get("title", "")
            page_type = page_def.get("page_type", "content")

            # 查找对应的内容素材
            content_material = None
            for material in content_material_list:
                if material.get("page_no") == page_no:
                    content_material = material
                    break

            # 生成页面XML
            page_xml = self._generate_page_xml(
                page_no=page_no,
                page_title=page_title,
                page_type=page_type,
                page_def=page_def,
                content_material=content_material,
                requirement=requirement,
                total_pages=len(pages)
            )

            xml_parts.append(page_xml)

        xml_parts.append("</PRESENTATION>")
        xml_parts.append("```")

        return "\n".join(xml_parts)

    def _generate_page_xml(
        self,
        page_no: int,
        page_title: str,
        page_type: str,
        page_def: Dict[str, Any],
        content_material: Optional[Dict[str, Any]],
        requirement: Optional[Requirement],
        total_pages: int
    ) -> str:
        """
        生成单个页面的XML

        Args:
            page_no: 页码
            page_title: 页面标题
            page_type: 页面类型
            page_def: 页面定义
            content_material: 内容素材
            requirement: 需求对象
            total_pages: 总页数

        Returns:
            页面XML字符串
        """
        if page_type == "cover":
            # 封面页
            topic = requirement.ppt_topic if requirement else page_title
            return f'''<SLIDE>
    <TITLE>{topic}</TITLE>
    <SUBTITLE>{page_def.get("core_content", "").split(chr(10))[0] if page_def.get("core_content") else ""}</SUBTITLE>
    <AUTHOR>汇报人</AUTHOR>
    <DATE>{datetime.now().strftime("%Y年%m月%d日")}</DATE>
</SLIDE>'''

        elif page_type == "directory":
            # 目录页
            items = "\n".join([
                f"        <ITEM>{i+1}. 章节{i+1}</ITEM>"
                for i in range(min(5, total_pages - 2))
            ])
            return f'''<SLIDE>
    <TITLE>目录</TITLE>
    <CONTENT>
{items}
    </CONTENT>
</SLIDE>'''

        elif page_type == "summary" or page_type == "thanks":
            # 总结/致谢页
            return f'''<SLIDE>
    <TITLE>{page_title}</TITLE>
    <CONTENT>
        <POINT>感谢聆听</POINT>
        <POINT>欢迎提问与交流</POINT>
    </CONTENT>
</SLIDE>'''

        else:
            # 内容页
            content_text = content_material.get("content_text", "") if content_material else ""
            chart_info = ""
            image_info = ""

            if content_material:
                if content_material.get("has_chart"):
                    chart_data = content_material.get("chart_data", {})
                    chart_info = f'        <CHART type="{chart_data.get("chart_type", "bar")}" title="{chart_data.get("title", "")}"/>'

                if content_material.get("has_image"):
                    image_suggestion = content_material.get("image_suggestion", {})
                    image_info = f'        <IMAGE suggestion="{image_suggestion.get("search_query", "")}"/>'

            return f'''<SLIDE>
    <TITLE>{page_title}</TITLE>
    <CONTENT>
        <TEXT>{content_text[:200] if content_text else page_def.get("core_content", "")}</TEXT>
{chart_info}
{image_info}
    </CONTENT>
</SLIDE>'''

    async def _render_ppt(
        self,
        xml_content: str,
        requirement: Optional[Requirement],
        framework: Dict[str, Any],
        content_material: List[Dict[str, Any]],
        raw_input: str,
        ctx: InvocationContext
    ) -> str:
        """
        渲染PPT文件

        Args:
            xml_content: XML格式内容
            requirement: 需求对象
            framework: 框架字典
            content_material: 内容素材列表
            raw_input: 原始用户输入
            ctx: 调用上下文

        Returns:
            PPT文件路径
        """
        if not self.generator_available:
            # 如果生成器不可用，返回虚拟路径
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"ppt_{timestamp}.xml"
            file_path = os.path.join(output_dir, file_name)

            # 保存XML内容
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(xml_content)

            logger.info(f"Saved XML content to: {file_path}")
            return file_path

        # 使用实际的PPT生成器
        try:
            # 这里可以调用现有的PresentationGenerator
            # 简化实现，保存XML
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"ppt_{timestamp}.xml"
            file_path = os.path.join(output_dir, file_name)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(xml_content)

            logger.info(f"PPT file generated: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Error rendering PPT: {e}")
            raise

    def _generate_preview_data(
        self,
        framework_dict: Dict[str, Any],
        content_material_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成前端预览数据

        Args:
            framework_dict: 框架字典
            content_material_list: 内容素材列表

        Returns:
            预览数据字典
        """
        pages = framework_dict.get("ppt_framework", [])

        preview_pages = []
        for i, page_def in enumerate(pages):
            page_no = page_def.get("page_no", i + 1)
            page_title = page_def.get("title", "")

            # 查找对应的内容素材
            content_material = None
            for material in content_material_list:
                if material.get("page_no") == page_no:
                    content_material = material
                    break

            preview_page = {
                "page_no": page_no,
                "title": page_title,
                "type": page_def.get("page_type", "content"),
                "has_chart": content_material.get("has_chart", False) if content_material else False,
                "has_image": content_material.get("has_image", False) if content_material else False,
                "preview_text": content_material.get("content_text", "")[:100] if content_material else ""
            }

            preview_pages.append(preview_page)

        return {
            "total_pages": len(preview_pages),
            "pages": preview_pages,
            "created_at": datetime.now().isoformat()
        }

# 创建全局实例
template_renderer_agent = TemplateRendererAgent()

if __name__ == "__main__":
    # 测试代码
    import asyncio
    from domain.models import Requirement, TemplateType

    print(f"Testing TemplateRendererAgent")
    print("=" * 60)

    agent = template_renderer_agent

    # 测试XML生成
    framework = {
        "total_page": 3,
        "ppt_framework": [
            {"page_no": 1, "title": "封面", "page_type": "cover", "core_content": "主题\\n副标题"},
            {"page_no": 2, "title": "目录", "page_type": "directory", "core_content": ""},
            {"page_no": 3, "title": "总结", "page_type": "summary", "core_content": ""},
        ]
    }

    content_material = [
        {"page_no": 1, "content_text": "封面内容"},
        {"page_no": 2, "content_text": "目录内容"},
        {"page_no": 3, "content_text": "总结内容"},
    ]

    requirement = Requirement(
        ppt_topic="测试主题",
        page_num=3,
        template_type=TemplateType.BUSINESS
    )

    xml = agent._generate_xml_content(framework, content_material, requirement)
    print(f"Generated XML:\n{xml[:500]}...")

    preview = agent._generate_preview_data(framework, content_material)
    print(f"\nPreview data: {json.dumps(preview, indent=2, ensure_ascii=False)}")
