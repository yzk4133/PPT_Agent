"""
框架设计工作流程 Skill

为 FrameworkAgent 提供系统化的框架设计工作流程
"""

import json
import logging
from typing import Dict, Any, List
from backend.tools.skills.base_skill import BaseSkill


logger = logging.getLogger(__name__)


class FrameworkDesignSkill(BaseSkill):
    """
    框架设计工作流程 Skill

    工作流程：需求分析 → 主题分解 → 结构设计 → 章节规划 → 流程优化
    """

    name = "framework_design"
    description = "系统化的 PPT 框架设计：需求分析 → 主题分解 → 结构设计 → 章节规划"
    version = "1.0.0"
    category = "framework"

    def __init__(self, llm=None):
        """初始化框架设计 Skill"""
        super().__init__(llm)

    async def execute(
        self,
        topic: str,
        audience: str = "general",
        depth: str = "medium",
        duration_minutes: int = 30,
        style: str = "professional",
    ) -> str:
        """
        执行框架设计工作流程

        Args:
            topic: PPT 主题
            audience: 目标受众
            depth: 深度 (shallow/medium/deep)
            duration_minutes: 预计时长（分钟）
            style: 风格 (professional/creative/academic)

        Returns:
            str: JSON 格式的框架设计结果
        """
        try:
            logger.info(f"[FrameworkSkill] 开始设计框架: {topic}")

            # 步骤 1: 需求分析
            requirement = await self._analyze_requirement(
                topic, audience, depth, duration_minutes, style
            )

            # 步骤 2: 主题分解
            subtopics = await self._decompose_topic(topic, requirement)
            logger.info(f"[FrameworkSkill] 分解为 {len(subtopics)} 个子主题")

            # 步骤 3: 结构设计
            structure = await self._design_structure(topic, subtopics, requirement)
            logger.info(f"[FrameworkSkill] 设计 {structure['total_pages']} 页结构")

            # 步骤 4: 章节规划
            sections = await self._plan_sections(structure, requirement)
            logger.info(f"[FrameworkSkill] 规划 {len(sections)} 个章节")

            # 步骤 5: 流程优化
            flow = await self._optimize_flow(sections, requirement)

            # 返回 JSON 格式的框架
            framework = {
                "title": structure.get("title", topic),
                "subtitle": structure.get("subtitle"),
                "structure": {
                    "sections": sections,
                    "total_pages": sum(s["page_count"] for s in sections),
                },
                "flow": flow,
            }

            import json

            return json.dumps(framework, ensure_ascii=False)

        except Exception as e:
            logger.error(f"[FrameworkSkill] 执行失败: {e}", exc_info=True)
            return f"错误：{str(e)}"

    async def _analyze_requirement(
        self, topic: str, audience: str, depth: str, duration_minutes: int, style: str
    ) -> Dict[str, Any]:
        """步骤 1: 需求分析"""
        # 根据时长估算页数（每页 2-3 分钟）
        min_pages = max(5, duration_minutes // 3)
        max_pages = max(8, duration_minutes // 2)

        return {
            "topic": topic,
            "audience": audience,
            "depth": depth,
            "duration_minutes": duration_minutes,
            "style": style,
            "page_count_range": (min_pages, max_pages),
        }

    async def _decompose_topic(
        self, topic: str, requirement: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """步骤 2: 主题分解"""
        if not self.llm:
            # 简单实现
            return [
                {"title": f"第一部分：{topic}概述", "subtopics": []},
                {"title": f"第二部分：核心内容", "subtopics": []},
                {"title": f"第三部分：总结", "subtopics": []},
            ]

        depth = requirement["depth"]
        num_sections = {"shallow": 3, "medium": 5, "deep": 7}.get(depth, 5)

        prompt = f"""
        将以下主题分解为 {num_sections} 个逻辑连贯的章节。

        主题：{topic}
        目标受众：{requirement['audience']}
        深度：{depth}
        风格：{requirement['style']}

        要求：
        1. 章节之间有逻辑递进关系
        2. 符合"总-分-总"或"问题-分析-解决"等经典结构
        3. 每个章节包含 2-4 个页面主题

        返回 JSON 格式：
        [
            {
                "section_title": "章节标题",
                "pages": ["页面1主题", "页面2主题", ...]
            },
            ...
        ]
        """

        try:
            result = await self.llm.ainvoke(prompt)
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]

            sections_data = json.loads(result)
            return sections_data

        except Exception as e:
            logger.warning(f"[FrameworkSkill] 主题分解失败: {e}")
            return [
                {"section_title": "概述", "pages": ["介绍"]},
                {"section_title": "正文", "pages": ["内容"]},
                {"section_title": "总结", "pages": ["总结"]},
            ]

    async def _design_structure(
        self, topic: str, subtopics: List[Dict[str, Any]], requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """步骤 3: 结构设计"""
        # 生成主标题和副标题
        if self.llm:
            prompt = f"""
            为以下 PPT 设计主标题和副标题：

            主题：{topic}
            受众：{requirement['audience']}
            风格：{requirement['style']}

            要求：
            1. 主标题简洁有力（5-15字）
            2. 副标题补充说明（10-25字）
            3. 避免"关于"、"介绍"等套话

            返回 JSON 格式：
            {
                "title": "主标题",
                "subtitle": "副标题"
            }
            """

            try:
                result = await self.llm.ainvoke(prompt)
                result = result.strip()
                if result.startswith("```"):
                    result = result.split("```")[1]
                    if result.startswith("json"):
                        result = result[4:]

                titles = json.loads(result)
                return titles
            except Exception as e:
                logger.warning(f"[FrameworkSkill] 标题生成失败: {e}")

        return {"title": topic, "subtitle": f"关于{topic}的分享"}

    async def _plan_sections(
        self, structure: Dict[str, Any], requirement: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """步骤 4: 章节规划"""
        # 这里简化实现，实际应该从 subtopics 解析
        # 先返回一个标准结构
        min_pages, max_pages = requirement["page_count_range"]

        return [
            {
                "title": "开篇",
                "page_count": 1,
                "pages": [{"title": structure.get("title", "标题"), "type": "cover"}],
            },
            {"title": "概述", "page_count": 1, "pages": [{"title": "背景介绍", "type": "content"}]},
            {
                "title": "核心内容",
                "page_count": max_pages - 4,
                "pages": [{"title": f"要点{i+1}", "type": "content"} for i in range(max_pages - 4)],
            },
            {
                "title": "总结",
                "page_count": 1,
                "pages": [{"title": "总结与展望", "type": "summary"}],
            },
        ]

    async def _optimize_flow(
        self, sections: List[Dict[str, Any]], requirement: Dict[str, Any]
    ) -> str:
        """步骤 5: 流程优化"""
        section_titles = [s["title"] for s in sections]
        return " → ".join(section_titles)


class TopicDecompositionSkill(BaseSkill):
    """
    主题分解 Skill（框架设计的子技能）
    """

    name = "topic_decomposition"
    description = "将复杂主题分解为多个子主题"
    version = "1.0.0"
    category = "framework"

    async def execute(self, topic: str, num_parts: int = 5) -> str:
        """分解主题"""
        if not self.llm:
            parts = [f"第{i+1}部分" for i in range(num_parts)]
            import json

            return json.dumps({"topic": topic, "parts": parts}, ensure_ascii=False)

        prompt = f"""
        将以下主题分解为 {num_parts} 个子主题：

        主题：{topic}

        返回 JSON 数组：["子主题1", "子主题2", ...]
        """

        try:
            result = await self.llm.ainvoke(prompt)
            parts = json.loads(result)
            import json

            return json.dumps({"topic": topic, "parts": parts}, ensure_ascii=False)
        except Exception as e:
            return f"错误：{str(e)}"


class SectionPlanningSkill(BaseSkill):
    """
    章节规划 Skill（框架设计的子技能）
    """

    name = "section_planning"
    description = "规划章节和页面分配"
    version = "1.0.0"
    category = "framework"

    async def execute(self, subtopics: List[str], total_pages: int = 10) -> str:
        """规划章节"""
        # 简化实现：平均分配
        pages_per_section = total_pages // len(subtopics)

        sections = []
        for i, subtopic in enumerate(subtopics):
            sections.append(
                {
                    "title": subtopic,
                    "page_count": pages_per_section,
                    "pages": [f"{subtopic}-要点{j+1}" for j in range(pages_per_section)],
                }
            )

        import json

        return json.dumps({"sections": sections, "total_pages": total_pages}, ensure_ascii=False)


# ============================================================================
# LangChain Tool 包装器
# ============================================================================

from langchain_core.tools import StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field


class FrameworkDesignInput(BaseModel):
    """框架设计输入参数"""

    topic: str = Field(..., description="PPT 主题")
    audience: str = Field(default="general", description="目标受众")
    depth: str = Field(default="medium", description="深度 (shallow/medium/deep)")
    duration_minutes: int = Field(default=30, description="预计时长（分钟）")
    style: str = Field(default="professional", description="风格 (professional/creative/academic)")


class TopicDecompositionInput(BaseModel):
    """主题分解输入参数"""

    topic: str = Field(..., description="主题")
    num_parts: int = Field(default=5, description="分解数量")


class SectionPlanningInput(BaseModel):
    """章节规划输入参数"""

    subtopics: List[str] = Field(..., description="子主题列表")
    total_pages: int = Field(default=10, description="总页数")


# 创建 LangChain Tools
framework_design_tool = StructuredTool.from_function(
    func=FrameworkDesignSkill().execute,
    name="framework_design",
    description="系统化的 PPT 框架设计：需求分析 → 主题分解 → 结构设计 → 章节规划",
    args_schema=FrameworkDesignInput,
)

topic_decomposition_tool = StructuredTool.from_function(
    func=TopicDecompositionSkill().execute,
    name="topic_decomposition",
    description="将复杂主题分解为多个子主题",
    args_schema=TopicDecompositionInput,
)

section_planning_tool = StructuredTool.from_function(
    func=SectionPlanningSkill().execute,
    name="section_planning",
    description="规划章节和页面分配",
    args_schema=SectionPlanningInput,
)
