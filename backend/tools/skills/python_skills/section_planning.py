"""
章节规划 Skill

将子主题规划成逻辑章节，分配页数
"""

import json
import logging
from typing import Dict, Any, List
from backend.tools.skills.base_skill import BaseSkill


logger = logging.getLogger(__name__)


class SectionPlanningSkill(BaseSkill):
    """
    章节规划 Skill

    职责：
    - 将子主题组织成逻辑章节
    - 为每个章节分配页数
    - 规划章节顺序
    """

    name = "section_planning"
    description = "将子主题规划成逻辑章节并分配页数"
    version = "1.0.0"
    category = "framework"

    async def execute(
        self,
        subtopics: List[str],
        total_pages: int = 10,
        structure_type: str = "linear"
    ) -> str:
        """
        执行章节规划

        Args:
            subtopics: 子主题列表
                ["子主题1", "子主题2", ...]
            total_pages: 总页数
            structure_type: 结构类型
                - "linear": 线性结构（开头-中间-结尾）
                - "parallel": 并行结构（多个独立主题）
                - "hierarchical": 层级结构（总-分-总）

        Returns:
            str: JSON 格式的章节规划结果
        """
        try:
            logger.info(f"[SectionPlanning] 规划 {len(subtopics)} 个子主题到 {total_pages} 页")

            # 步骤 1: 将子主题组织成章节
            sections = await self._organize_sections(subtopics, structure_type)

            # 步骤 2: 分配页数
            sections = await self._allocate_pages(sections, total_pages)

            # 步骤 3: 生成具体页面
            sections = await self._generate_pages(sections)

            logger.info(f"[SectionPlanning] 规划完成: {len(sections)} 个章节")

            # 返回 JSON 格式
            import json
            result = {
                "sections": sections,
                "total_pages": total_pages,
                "structure_type": structure_type
            }

            return json.dumps(result, ensure_ascii=False)

        except Exception as e:
            logger.error(f"[SectionPlanning] 规划失败: {e}", exc_info=True)
            return f"错误：{str(e)}"

    async def _organize_sections(
        self,
        subtopics: List[str],
        structure_type: str
    ) -> List[Dict[str, Any]]:
        """
        将子主题组织成章节

        Args:
            subtopics: 子主题列表
            structure_type: 结构类型

        Returns:
            [
                {
                    "title": "章节标题",
                    "subtopics": ["子主题1", "子主题2"],
                    "subtopic_count": 2
                },
                ...
            ]
        """
        if not self.llm:
            # 降级：每 2-3 个子主题组成一个章节
            return self._fallback_organize(subtopics)

        if structure_type == "linear":
            return await self._organize_linear(subtopics)
        elif structure_type == "parallel":
            return await self._organize_parallel(subtopics)
        elif structure_type == "hierarchical":
            return await self._organize_hierarchical(subtopics)
        else:
            return await self._organize_linear(subtopics)

    async def _organize_linear(
        self,
        subtopics: List[str]
    ) -> List[Dict[str, Any]]:
        """
        线性组织

        结构：开头 → 展开 → 总结
        """
        prompt = f"""
        将以下子主题组织成线性结构的章节：

        子主题：{subtopics}

        要求：
        1. 按照逻辑顺序组织
        2. 每 2-3 个子主题组成一个章节
        3. 章节之间有递进关系
        4. 每个章节有明确的标题

        返回 JSON 格式：
        [
            {{"title": "章节1", "subtopics": ["子主题1", "子主题2"]}},
            {{"title": "章节2", "subtopics": ["子主题3", "子主题4"]}},
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

            return [
                {
                    "title": item["title"],
                    "subtopics": item["subtopics"],
                    "subtopic_count": len(item["subtopics"])
                }
                for item in sections_data
            ]

        except Exception as e:
            logger.warning(f"[SectionPlanning] 线性组织失败: {e}")
            return self._fallback_organize(subtopics)

    async def _organize_parallel(
        self,
        subtopics: List[str]
    ) -> List[Dict[str, Any]]:
        """
        并行组织

        结构：多个独立主题并行
        """
        # 每个子主题独立成章
        return [
            {
                "title": subtopic,
                "subtopics": [subtopic],
                "subtopic_count": 1
            }
            for subtopic in subtopics
        ]

    async def _organize_hierarchical(
        self,
        subtopics: List[str]
    ) -> List[Dict[str, Any]]:
        """
        层级组织

        结构：总 → 分 → 总
        """
        if len(subtopics) < 3:
            return await self._organize_linear(subtopics)

        # 第一个章节：总览
        sections = [
            {
                "title": "总览",
                "subtopics": [subtopics[0]],
                "subtopic_count": 1
            }
        ]

        # 中间章节：详细展开
        sections.append({
            "title": "详细展开",
            "subtopics": subtopics[1:-1],
            "subtopic_count": len(subtopics) - 2
        })

        # 最后章节：总结
        sections.append({
            "title": "总结",
            "subtopics": [subtopics[-1]],
            "subtopic_count": 1
        })

        return sections

    async def _allocate_pages(
        self,
        sections: List[Dict[str, Any]],
        total_pages: int
    ) -> List[Dict[str, Any]]:
        """
        为章节分配页数

        策略：
        - 封面/目录：1-2 页（如果还没有）
        - 开头章节：1 页
        - 中间章节：平均分配
        - 总结章节：1 页
        """
        # 减去封面和目录页
        content_pages = total_pages - 2
        if content_pages < len(sections):
            content_pages = len(sections)

        # 计算每个章节的页数
        subtopic_counts = [s["subtopic_count"] for s in sections]
        total_subtopics = sum(subtopic_counts)

        allocated_sections = []

        for i, section in enumerate(sections):
            # 按子主题数量比例分配
            if i == 0:
                # 第一章节：1 页
                page_count = 1
            elif i == len(sections) - 1:
                # 最后章节：1 页
                page_count = 1
            else:
                # 中间章节：按比例分配
                proportion = section["subtopic_count"] / total_subtopics
                page_count = max(1, int(proportion * content_pages))

            allocated_sections.append({
                **section,
                "page_count": page_count
            })

        # 调整页数，确保总和正确
        allocated_total = sum(s["page_count"] for s in allocated_sections)
        if allocated_total != content_pages:
            # 调整中间章节
            for section in allocated_sections[1:-1]:
                if allocated_total < content_pages:
                    section["page_count"] += 1
                    allocated_total += 1
                elif allocated_total > content_pages and section["page_count"] > 1:
                    section["page_count"] -= 1
                    allocated_total -= 1

        return allocated_sections

    async def _generate_pages(
        self,
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        为每个章节生成具体页面

        Returns:
            [
                {
                    "title": "章节标题",
                    "subtopics": [...],
                    "page_count": 3,
                    "page_range": [1, 3],
                    "pages": [
                        {"page_no": 1, "title": "页面标题", "type": "content"},
                        ...
                    ]
                },
                ...
            ]
        """
        current_page = 1  # 从第1页开始（封面和目录会单独处理）

        for section in sections:
            pages = []
            page_range_start = current_page

            # 为每个子主题生成页面
            for i, subtopic in enumerate(section["subtopics"]):
                # 如果章节只有1页，所有子主题合并在一页
                if section["page_count"] == 1:
                    page_title = section["title"]
                    pages.append({
                        "page_no": current_page,
                        "title": page_title,
                        "type": "content",
                        "subtopics": section["subtopics"]
                    })
                    current_page += 1
                    break

                # 如果章节有多个页，每个子主题一页
                # 计算这个子主题占几页
                subtopic_pages = max(1, section["page_count"] // len(section["subtopics"]))

                for j in range(subtopic_pages):
                    if i == 0 and j == 0:
                        page_title = section["title"]
                    else:
                        page_title = subtopic

                    pages.append({
                        "page_no": current_page,
                        "title": page_title,
                        "type": "content",
                        "subtopic": subtopic if j == 0 else f"{subtopic}（续）"
                    })
                    current_page += 1

                    if current_page > page_range_start + section["page_count"]:
                        break

                if current_page >= page_range_start + section["page_count"]:
                    break

            section["pages"] = pages
            section["page_range"] = [page_range_start, current_page - 1]

        return sections

    def _fallback_organize(
        self,
        subtopics: List[str]
    ) -> List[Dict[str, Any]]:
        """降级组织：简单的线性组织"""
        # 每 2-3 个子主题一组
        sections = []
        group_size = 3

        for i in range(0, len(subtopics), group_size):
            group = subtopics[i:i+group_size]

            # 生成章节标题
            if i == 0:
                section_title = "概述"
            elif i + group_size >= len(subtopics):
                section_title = "总结"
            else:
                section_title = f"第{i//group_size + 1}部分"

            sections.append({
                "title": section_title,
                "subtopics": group,
                "subtopic_count": len(group)
            })

        return sections


class PageDistributionSkill(BaseSkill):
    """
    页面分配 Skill（章节规划的简化版本）

    快速为子主题分配页数
    """

    name = "page_distribution"
    description = "为子主题快速分配页数"
    version = "1.0.0"
    category = "framework"

    async def execute(
        self,
        subtopics: List[str],
        total_pages: int
    ) -> Dict[str, Any]:
        """快速分配"""
        # 平均分配
        pages_per_topic = total_pages // len(subtopics)

        distribution = []
        for i, subtopic in enumerate(subtopics):
            distribution.append({
                "title": subtopic,
                "page_count": pages_per_topic,
                "page_no": i * pages_per_topic + 1
            })

        return {
            "success": True,
            "data": {
                "distribution": distribution,
                "total_pages": total_pages
            }
        }


# ============================================================================
# LangChain Tool 包装器
# ============================================================================

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class SectionPlanningInput(BaseModel):
    """章节规划输入参数"""
    subtopics: List[str] = Field(..., description="子主题列表")
    total_pages: int = Field(default=10, description="总页数")
    structure_type: str = Field(default="linear", description="结构类型 (linear/parallel/hierarchical)")


# 创建 LangChain Tool
section_planning_tool = StructuredTool.from_function(
    func=SectionPlanningSkill().execute,
    name="section_planning",
    description="将子主题规划成逻辑章节并分配页数",
    args_schema=SectionPlanningInput
)
