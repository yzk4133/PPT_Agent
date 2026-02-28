"""
模板渲染智能体 - LangChain 实现

该智能体从所有收集的内容中渲染最终的 PPT 输出。
生成 XML 格式以与原始的 slide_writer_agent 兼容。
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from ...models.state import PPTGenerationState, update_state_progress, get_framework_pages
from ...models.framework import PageType
from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)


class TemplateRendererAgent(BaseAgent):
    """
    模板渲染智能体 - 使用BaseAgent重构版本

    职责：
    1. 汇总所有阶段的数据
    2. 生成XML格式的PPT内容
    3. 生成预览数据
    4. 保存最终输出
    5. 缓存渲染结果

    特性：
    - XML格式输出，与原系统兼容
    - 生成前端预览数据
    - 支持文件保存
    - 集成记忆系统：缓存渲染结果，跟踪输出历史
    - 集成 canvas-design 和 pptx 技能用于专业视觉设计

    TODO: Phase 2 - 集成实际的PPT生成器
    """

    def __init__(
        self,
        model: Optional[ChatOpenAI] = None,
        output_dir: str = "output",
        agent_name: str = "TemplateRendererAgent",
        enable_memory: bool = True,
        use_design_skills: bool = True,  # 是否使用MD设计技能
        use_python_skills: bool = True,  # 是否使用Python技能
    ):
        """
        初始化模板渲染智能体

        Args:
            model: LangChain LLM实例（可选，主要用于内容优化）
            output_dir: 输出目录
            agent_name: Agent名称
            enable_memory: 是否启用记忆功能
            use_design_skills: 是否使用MD设计技能（canvas-design, pptx）
            use_python_skills: 是否使用Python技能（layout_selection）
        """
        # 基类会自动处理：模型创建、记忆初始化
        # 注意：这个Agent不使用chain，但我们仍然提供空的实现
        self.output_dir = output_dir

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

        # 如果启用设计技能，加载相关技能
        skills = ["canvas-design", "pptx"] if use_design_skills else None

        super().__init__(
            model=model,
            temperature=0.0,
            agent_name=agent_name,
            enable_memory=enable_memory,
            skills=skills,
        )

        # 存储设计原则用于渲染
        self._design_principles = self._extract_design_principles() if use_design_skills else {}

        # 加载 Python Skills
        self._python_skills = {}
        if use_python_skills:
            self._load_python_skills()

        logger.info(
            f"[{self.agent_name}] Initialized, output_dir: {self.output_dir}, memory={enable_memory}"
        )

    def _create_chain(self) -> Runnable:
        """
        创建处理链

        注意：渲染Agent主要使用模板，不使用LLM链
        返回一个简单的chain以符合BaseAgent接口
        """
        # 创建一个简单的占位链
        prompt = ChatPromptTemplate.from_template("Output: {input}")
        return prompt | self.model

    def _extract_design_principles(self) -> Dict[str, Any]:
        """
        从加载的技能中提取设计原则

        Returns:
            设计原则字典
        """
        principles = {}

        # 提取 canvas-design 原则
        canvas_skill = self.get_skill("canvas-design")
        if canvas_skill:
            principles["canvas"] = {
                "minimal_text": True,
                "spatial_expression": True,
                "expert_craftsmanship": True,
                "negative_space": True,
            }
            logger.info(f"[{self.agent_name}] Applied canvas-design principles")

        # 提取 pptx 原则
        pptx_skill = self.get_skill("pptx")
        if pptx_skill:
            principles["pptx"] = {
                "web_safe_fonts": True,
                "visual_hierarchy": True,
                "readability": True,
                "consistency": True,
            }
            logger.info(f"[{self.agent_name}] Applied pptx principles")

        return principles

    def _load_python_skills(self):
        """加载 Python Skills"""
        try:
            from backend.tools.skills import load_skill

            logger.info(f"[{self.agent_name}] Loading Python Skills...")

            # 加载布局选择 Skill
            self._python_skills["layout_selection"] = load_skill("layout_selection", llm=self.model)
            logger.info(f"[{self.agent_name}] Loaded layout_selection skill")

        except Exception as e:
            logger.error(f"[{self.agent_name}] Failed to load Python Skills: {e}")
            self._python_skills = {}

    async def execute_task(self, state: PPTGenerationState) -> PPTGenerationState:
        """
        执行渲染任务

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        # 获取所需数据
        framework = state.get("ppt_framework", {})
        content_materials = state.get("content_materials", [])
        requirement = state.get("structured_requirements", {})
        task_id = state.get("task_id", "unknown")

        if not framework:
            raise ValueError("Missing ppt_framework in state")

        if not content_materials:
            raise ValueError("Missing content_materials in state")

        # 渲染PPT
        ppt_output = await self.render(framework, content_materials, requirement, task_id, state)

        # 使用便捷方法记住渲染结果
        await self.save_to_cache(
            f"final_output_{task_id}", ppt_output, importance=0.9, scope="TASK", state=state
        )

        # 更新状态
        state["ppt_output"] = ppt_output
        update_state_progress(state, "template_rendering", 100)

        logger.info(f"[{self.agent_name}] Task completed: {ppt_output['file_path']}")
        return state

    async def run_node(self, state: PPTGenerationState) -> PPTGenerationState:
        """兼容工作流节点调用接口"""
        return await self.execute_task(state)

    def _generate_xml_content(
        self,
        framework: Dict[str, Any],
        content_materials: List[Dict[str, Any]],
        requirement: Dict[str, Any],
    ) -> str:
        """
        生成XML格式的内容

        Args:
            framework: 框架字典
            content_materials: 内容素材列表
            requirement: 需求字典

        Returns:
            XML格式的内容字符串
        """
        xml_parts = ["```xml", "<PRESENTATION>"]

        pages = framework.get("ppt_framework", [])

        # 创建内容映射
        content_map = {}
        for material in content_materials:
            page_no = material.get("page_no")
            if page_no:
                content_map[page_no] = material

        for i, page_def in enumerate(pages):
            page_no = page_def.get("page_no", i + 1)
            page_title = page_def.get("title", "")
            page_type = page_def.get("page_type", "content")

            # 获取对应的内容素材
            content_material = content_map.get(page_no, {})

            # 生成页面XML
            page_xml = self._generate_page_xml(
                page_no=page_no,
                page_title=page_title,
                page_type=page_type,
                page_def=page_def,
                content_material=content_material,
                requirement=requirement,
                total_pages=len(pages),
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
        content_material: Dict[str, Any],
        requirement: Dict[str, Any],
        total_pages: int,
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
            topic = requirement.get("ppt_topic", page_title)
            return f"""<SLIDE>
    <TITLE>{topic}</TITLE>
    <SUBTITLE>{page_def.get("core_content", "").split(chr(10))[0] if page_def.get("core_content") else ""}</SUBTITLE>
    <AUTHOR>汇报人</AUTHOR>
    <DATE>{datetime.now().strftime("%Y年%m月%d日")}</DATE>
</SLIDE>"""

        elif page_type == "directory":
            # 目录页
            items = "\n".join(
                [f"        <ITEM>{i+1}. 章节{i+1}</ITEM>" for i in range(min(5, total_pages - 2))]
            )
            return f"""<SLIDE>
    <TITLE>目录</TITLE>
    <CONTENT>
{items}
    </CONTENT>
</SLIDE>"""

        elif page_type in ("summary", "thanks"):
            # 总结/致谢页
            return f"""<SLIDE>
    <TITLE>{page_title}</TITLE>
    <CONTENT>
        <POINT>感谢聆听</POINT>
        <POINT>欢迎提问与交流</POINT>
    </CONTENT>
</SLIDE>"""

        else:
            # 内容页
            content_text = content_material.get("content_text", "")
            chart_info = ""
            image_info = ""
            layout_info = ""

            # 获取内容类型
            content_type = page_def.get("content_type", "text_only")
            has_chart = (
                content_material.get("has_chart", False)
                if content_material
                else page_def.get("is_need_chart", False)
            )
            has_image = (
                content_material.get("has_image", False)
                if content_material
                else page_def.get("is_need_image", False)
            )
            key_points_count = (
                len(content_material.get("key_points", [])) if content_material else 0
            )

            # 使用 layout_selection Skill 选择布局
            selected_layout = None
            layout_config = {}
            if "layout_selection" in self._python_skills:
                try:
                    # 这是一个同步方法，需要在异步上下文中正确处理
                    # 由于 layout_selection Skill 可能是异步的，我们需要使用 await
                    # 但 _generate_page_xml 是同步方法，所以我们先不在这里调用
                    # 而是标记需要在 render 时处理
                    logger.debug(
                        f"[{self.agent_name}] Layout selection available for page {page_no}"
                    )
                except Exception as e:
                    logger.warning(f"[{self.agent_name}] Layout selection error: {e}")

            # 简单的规则驱动布局选择（作为降级方案）
            layout_rules = {
                "cover": "title_center",
                "directory": "vertical_list",
                "content": {
                    "text_only": "title_with_bullet_points",
                    "text_with_chart": "title_with_left_chart",
                    "text_with_image": "title_with_right_image",
                    "text_with_both": "title_with_chart_and_image",
                },
                "summary": "title_with_bottom_summary",
            }

            # 根据页面类型和内容类型选择布局
            if page_type == "content":
                layout = layout_rules["content"].get(content_type, "title_with_bullet_points")
            elif page_type in layout_rules:
                layout = layout_rules[page_type]
            else:
                layout = "title_with_bullet_points"

            layout_info = f'        <LAYOUT type="{layout}"/>'

            if content_material:
                if content_material.get("has_chart"):
                    chart_data = content_material.get("chart_data", {})
                    chart_info = f'        <CHART type="{chart_data.get("chart_type", "bar")}" title="{chart_data.get("chart_title", "")}"/>'

                if content_material.get("has_image"):
                    image_suggestion = content_material.get("image_suggestion", {})
                    image_info = (
                        f'        <IMAGE suggestion="{image_suggestion.get("search_query", "")}"/>'
                    )

            # 限制内容长度
            display_content = (
                content_text[:200] if content_text else page_def.get("core_content", "")
            )

            return f"""<SLIDE>
    <TITLE>{page_title}</TITLE>
    <CONTENT>
        <TEXT>{display_content}</TEXT>
{chart_info}
{image_info}
    </CONTENT>
    <LAYOUTS>
{layout_info}
    </LAYOUTS>
</SLIDE>"""

    def _generate_preview_data(
        self, framework: Dict[str, Any], content_materials: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成前端预览数据

        Args:
            framework: 框架字典
            content_materials: 内容素材列表

        Returns:
            预览数据字典
        """
        pages = framework.get("ppt_framework", [])

        # 创建内容映射
        content_map = {}
        for material in content_materials:
            page_no = material.get("page_no")
            if page_no:
                content_map[page_no] = material

        preview_pages = []
        for i, page_def in enumerate(pages):
            page_no = page_def.get("page_no", i + 1)
            page_title = page_def.get("title", "")

            # 获取对应的内容素材
            content_material = content_map.get(page_no, {})

            preview_page = {
                "page_no": page_no,
                "title": page_title,
                "type": page_def.get("page_type", "content"),
                "has_chart": content_material.get("has_chart", False),
                "has_image": content_material.get("has_image", False),
                "preview_text": (
                    content_material.get("content_text", "")[:100] if content_material else ""
                ),
            }

            preview_pages.append(preview_page)

        return {
            "total_pages": len(preview_pages),
            "pages": preview_pages,
            "created_at": datetime.now().isoformat(),
        }

    def _save_output(self, xml_content: str, task_id: str) -> str:
        """
        保存输出文件

        Args:
            xml_content: XML内容
            task_id: 任务ID

        Returns:
            文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"ppt_{task_id}_{timestamp}.xml"
        file_path = os.path.join(self.output_dir, file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_content)

        logger.info(f"[{self.agent_name}] Saved XML to: {file_path}")
        return file_path

    async def render(
        self,
        framework: Dict[str, Any],
        content_materials: List[Dict[str, Any]],
        requirement: Dict[str, Any],
        task_id: str,
        state: Optional[PPTGenerationState] = None,
    ) -> Dict[str, Any]:
        """
        渲染PPT

        Args:
            framework: 框架字典
            content_materials: 内容素材列表
            requirement: 需求字典
            task_id: 任务ID
            state: 可选的状态（用于记忆上下文）

        Returns:
            输出字典，包含文件路径和预览数据
        """
        logger.info(f"[{self.agent_name}] Rendering PPT for task: {task_id}")

        # 生成缓存键
        total_pages = framework.get("total_page", 0)
        cache_key = f"render_{task_id}_{total_pages}_{len(content_materials)}"

        # 使用便捷方法检查缓存（注意：文件路径会包含时间戳，所以缓存主要用于预览数据）
        cached = await self.check_cache(cache_key, state)
        if cached and "preview_data" in cached:
            logger.info(f"[{self.agent_name}] Using cached preview data for task: {task_id}")
            # 仍然重新生成文件（因为文件名包含时间戳），但复用预览数据
            preview_data = cached["preview_data"]
        else:
            # 生成预览数据
            preview_data = self._generate_preview_data(framework, content_materials)

            # 使用便捷方法缓存预览数据
            await self.save_to_cache(
                cache_key, {"preview_data": preview_data}, importance=0.4, scope="TASK", state=state
            )

        # 生成XML内容
        xml_content = self._generate_xml_content(framework, content_materials, requirement)

        # 保存文件
        file_path = self._save_output(xml_content, task_id)

        return {
            "file_path": file_path,
            "preview_data": preview_data,
            "xml_content": xml_content,
            "total_pages": total_pages,
        }

    def get_fallback_result(self, state: PPTGenerationState) -> Optional[PPTGenerationState]:
        """降级策略"""
        task_id = state.get("task_id", "unknown")
        framework = state.get("ppt_framework", {})
        content_materials = state.get("content_materials", [])

        # 生成简单的输出
        total_pages = framework.get("total_page", len(content_materials))
        file_path = os.path.join(self.output_dir, f"ppt_{task_id}_fallback.xml")

        state["ppt_output"] = {
            "file_path": file_path,
            "preview_data": {
                "total_pages": total_pages,
                "pages": [],
                "created_at": datetime.now().isoformat(),
            },
            "xml_content": "<PRESENTATION>Fallback content</PRESENTATION>",
            "total_pages": total_pages,
        }
        update_state_progress(state, "template_rendering", 100)

        return state


# 工厂函数


def create_renderer_agent(
    model: Optional[ChatOpenAI] = None,
    output_dir: str = "output",
    enable_memory: bool = True,
) -> TemplateRendererAgent:
    """
    创建模板渲染智能体

    Args:
        model: LangChain LLM 实例
        output_dir: 输出目录
        enable_memory: 是否启用记忆功能

    Returns:
        TemplateRendererAgent 实例
    """
    return TemplateRendererAgent(model=model, output_dir=output_dir, enable_memory=enable_memory)


# 便捷函数


async def render_ppt(
    framework: Dict[str, Any],
    content_materials: List[Dict[str, Any]],
    requirement: Dict[str, Any],
    task_id: str = "output",
    output_dir: str = "output",
) -> Dict[str, Any]:
    """
    直接渲染 PPT（便捷函数）

    Args:
        framework: 框架字典
        content_materials: 内容素材列表
        requirement: 需求字典
        task_id: 任务 ID
        output_dir: 输出目录

    Returns:
        输出字典
    """
    agent = create_renderer_agent(output_dir=output_dir)
    return await agent.render(framework, content_materials, requirement, task_id)


if __name__ == "__main__":
    import asyncio

    async def test():
        # 测试渲染功能
        test_framework = {
            "total_page": 3,
            "ppt_framework": [
                {
                    "page_no": 1,
                    "title": "封面",
                    "page_type": "cover",
                    "core_content": "主题\\n副标题",
                },
                {"page_no": 2, "title": "目录", "page_type": "directory", "core_content": ""},
                {"page_no": 3, "title": "总结", "page_type": "summary", "core_content": ""},
            ],
        }

        test_content = [
            {"page_no": 1, "content_text": "封面内容", "has_chart": False, "has_image": True},
            {"page_no": 2, "content_text": "目录内容", "has_chart": False, "has_image": False},
            {"page_no": 3, "content_text": "总结内容", "has_chart": False, "has_image": False},
        ]

        test_requirement = {
            "ppt_topic": "测试主题",
            "page_num": 3,
            "template_type": "business_template",
        }

        agent = create_renderer_agent()

        result = await agent.render(test_framework, test_content, test_requirement, "test_001")

        print(f"文件已保存至: {result['file_path']}")
        print(f"总页数: {result['total_pages']}")
        print(f"预览数据: {json.dumps(result['preview_data'], indent=2, ensure_ascii=False)}")

    asyncio.run(test())
