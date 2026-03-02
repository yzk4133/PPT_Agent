"""
内容生成工作流程 Skill

为 ContentAgent 提供结构化的内容生成工作流程
"""

import json
import logging
from typing import Dict, Any, List, Optional
from backend.tools.skills.base_skill import BaseSkill


logger = logging.getLogger(__name__)


class ContentGenerationSkill(BaseSkill):
    """
    内容生成工作流程 Skill

    工作流程：需求分析 → 要点提取 → 结构化 → 优化表达 → 质量检查
    """

    name = "content_generation"
    description = "结构化的内容生成工作流程：需求分析 → 要点提取 → 结构化 → 优化 → 质检"
    version = "1.0.0"
    category = "content"

    def __init__(self, llm=None):
        """初始化内容生成 Skill"""
        super().__init__(llm)

    async def execute(
        self,
        topic: str,
        research_data: Optional[Dict[str, Any]] = None,
        audience: str = "general",
        page_type: str = "content",
        num_points: int = 5,
        max_iterations: int = 3,
    ) -> str:
        """
        执行内容生成工作流程

        Args:
            topic: 页面主题
            research_data: 研究资料（来自 ResearchAgent）
            audience: 目标受众 (expert/general/student)
            page_type: 页面类型 (content/cover/summary)
            num_points: 要点数量
            max_iterations: 最大优化迭代次数

        Returns:
            str: 格式化的内容字符串
        """
        try:
            logger.info(f"[ContentSkill] 开始生成内容: {topic}")

            # 步骤 1: 分析需求
            requirement = await self._analyze_requirement(topic, audience, page_type)
            logger.info(f"[ContentSkill] 需求分析: 受众={audience}, 类型={page_type}")

            # 步骤 2: 提取要点
            key_points = await self._extract_key_points(
                topic, research_data, requirement, num_points
            )
            logger.info(f"[ContentSkill] 提取 {len(key_points)} 个要点")

            # 步骤 3: 结构化内容
            structured_content = await self._structure_content(
                topic, key_points, page_type, requirement
            )

            # 步骤 4: 优化表达（迭代）
            optimized_content = await self._optimize_content(
                structured_content, requirement, max_iterations
            )
            logger.info(f"[ContentSkill] 内容优化完成")

            # 步骤 5: 质量检查
            quality_result = await self._quality_check(optimized_content, requirement)

            # 格式化为字符串
            title = optimized_content.get("title", topic)
            lines = [f"标题: {title}"]

            if "subtitle" in optimized_content:
                lines.append(f"副标题: {optimized_content['subtitle']}")

            key_points = optimized_content.get("key_points", [])
            if key_points:
                lines.append(f"要点: {', '.join(key_points)}")

            lines.append(f"质量分数: {quality_result['score']:.2f}")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"[ContentSkill] 执行失败: {e}", exc_info=True)
            return f"错误：{str(e)}"

    async def _analyze_requirement(
        self, topic: str, audience: str, page_type: str
    ) -> Dict[str, Any]:
        """
        步骤 1: 分析需求

        Returns:
            {
                "objective": "页面目标",
                "audience_level": "expert/general/student",
                "tone": "专业/轻松/严谨",
                "style_guide": "风格指南",
                "key_points_count": 3-5
            }
        """
        # 根据受众确定语气
        tone_map = {"expert": "专业、严谨", "general": "轻松、易懂", "student": "循序渐进、详细"}

        # 根据页面类型确定结构
        structure_map = {
            "cover": {"key_points_count": 1, "needs_subtitle": True},
            "content": {"key_points_count": 5, "needs_subtitle": True},
            "summary": {"key_points_count": 3, "needs_subtitle": False},
        }

        return {
            "objective": f"向{audience}介绍 {topic}",
            "audience_level": audience,
            "tone": tone_map.get(audience, "轻松"),
            "page_type": page_type,
            "key_points_count": structure_map.get(page_type, {}).get("key_points_count", 5),
            "needs_subtitle": structure_map.get(page_type, {}).get("needs_subtitle", True),
        }

    async def _extract_key_points(
        self,
        topic: str,
        research_data: Optional[Dict[str, Any]],
        requirement: Dict[str, Any],
        num_points: int,
    ) -> List[str]:
        """
        步骤 2: 提取要点

        Args:
            topic: 主题
            research_data: 研究资料
            requirement: 需求分析结果
            num_points: 要点数量

        Returns:
            要点列表
        """
        if not self.llm:
            # 简单实现：从研究资料中提取
            if research_data and research_data.get("synthesis"):
                return [f"要点{i+1}" for i in range(num_points)]
            return [f"要点{i+1}" for i in range(num_points)]

        # 准备上下文
        context = f"""
        主题：{topic}
        受众：{requirement['audience_level']}
        语气：{requirement['tone']}
        """

        if research_data:
            context += f"\n\n研究资料：\n{research_data.get('synthesis', '无')}"

        prompt = f"""
        从以下信息中提取 {num_points} 个关键要点，用于幻灯片展示：

        {context}

        要求：
        1. 每个要点一句话（10-20字）
        2. 保持平行结构（都是动词开头，或都是名词开头）
        3. 按重要性排序
        4. 适合 {requirement['audience_level']} 受众理解
        5. 语气{requirement['tone']}

        返回 JSON 数组格式：["要点1", "要点2", ...]
        """

        try:
            result = await self.llm.ainvoke(prompt)
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]

            points = json.loads(result)
            return points[:num_points]

        except Exception as e:
            logger.warning(f"[ContentSkill] 要点提取失败: {e}")
            return [f"要点{i+1}" for i in range(num_points)]

    async def _structure_content(
        self, topic: str, key_points: List[str], page_type: str, requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        步骤 3: 结构化内容

        Returns:
            {
                "title": "标题",
                "subtitle": "副标题（可选）",
                "key_points": ["要点1", "要点2"],
                "supporting_details": [
                    {"point": "要点1", "detail": "详细说明"}
                ]
            }
        """
        if not self.llm:
            # 简单实现
            content = {"title": topic, "key_points": key_points}
            if requirement.get("needs_subtitle"):
                content["subtitle"] = f"关于{topic}的介绍"
            return content

        # 生成标题
        prompt_title = f"""
        为以下幻灯片生成一个简洁有力的标题：

        主题：{topic}
        受众：{requirement['audience_level']}
        页面类型：{page_type}

        要求：
        1. 简洁（5-15字）
        2. 吸引人
        3. 符合{requirement['tone']}语气
        4. 避免使用"关于"、"介绍"等套话

        只返回标题，不要其他内容。
        """

        try:
            title = await self.llm.ainvoke(prompt_title)
            title = title.strip().strip("\"'")

            content = {"title": title, "key_points": key_points}

            # 生成副标题（如果需要）
            if requirement.get("needs_subtitle"):
                prompt_subtitle = f"""
                为以下幻灯片生成副标题：

                主标题：{title}
                主题：{topic}

                要求：
                1. 补充说明主标题
                2. 简洁（10-20字）
                3. 引人入胜

                只返回副标题。
                """

                subtitle = await self.llm.ainvoke(prompt_subtitle)
                content["subtitle"] = subtitle.strip().strip("\"'")

            # 生成支撑细节
            if page_type == "content":
                supporting_details = []
                for point in key_points[:3]:
                    prompt_detail = f"""
                    为以下要点提供支撑细节（一句话）：

                    要点：{point}
                    主题：{topic}

                    要求：
                    1. 补充说明或举例
                    2. 一句话（20-30字）
                    3. 具体而非抽象

                    只返回细节内容。
                    """

                    detail = await self.llm.ainvoke(prompt_detail)
                    supporting_details.append(
                        {"point": point, "detail": detail.strip().strip("\"'")}
                    )

                content["supporting_details"] = supporting_details

            return content

        except Exception as e:
            logger.warning(f"[ContentSkill] 结构化失败: {e}")
            return {"title": topic, "key_points": key_points}

    async def _optimize_content(
        self, content: Dict[str, Any], requirement: Dict[str, Any], max_iterations: int
    ) -> Dict[str, Any]:
        """
        步骤 4: 优化表达（迭代）
        """
        if not self.llm:
            return content

        current_content = content

        for iteration in range(max_iterations):
            # 质量检查
            quality = await self._quality_check(current_content, requirement)

            if quality["score"] >= 0.8:
                logger.info(f"[ContentSkill] 第 {iteration+1} 轮优化通过，分数: {quality['score']}")
                break

            # 找出失败的项目
            failed_items = [name for name, passed in quality["checks"].items() if not passed]

            logger.info(f"[ContentSkill] 第 {iteration+1} 轮优化，修复: {failed_items}")

            # 优化
            current_content = await self._apply_optimization(
                current_content, failed_items, requirement
            )

        return current_content

    async def _apply_optimization(
        self, content: Dict[str, Any], failed_items: List[str], requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """应用优化"""
        # 简化实现：只优化标题长度
        if "title_length" in failed_items and self.llm:
            prompt = f"""
            优化以下标题，使其长度在 5-20 字之间：

            原标题：{content['title']}

            只返回优化后的标题。
            """
            try:
                new_title = await self.llm.ainvoke(prompt)
                content["title"] = new_title.strip().strip("\"'")
            except:
                pass

        return content

    async def _quality_check(
        self, content: Dict[str, Any], requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        步骤 5: 质量检查

        Returns:
            {
                "score": 0.85,
                "checks": {
                    "has_title": true,
                    "has_key_points": true,
                    "title_length": true,
                    "points_parallel": false,
                    ...
                },
                "passed": true
            }
        """
        checks = {}

        # 基本检查
        checks["has_title"] = bool(content.get("title"))
        checks["has_key_points"] = len(content.get("key_points", [])) >= 3

        # 标题长度检查
        title = content.get("title", "")
        checks["title_length"] = 5 <= len(title) <= 20

        # 要点数量检查
        key_points = content.get("key_points", [])
        expected_count = requirement.get("key_points_count", 5)
        checks["key_points_count"] = len(key_points) >= expected_count - 1

        # 要点长度检查
        checks["points_length_ok"] = all(len(p) <= 50 for p in key_points)

        # 计算分数
        score = sum(checks.values()) / len(checks)

        return {"score": score, "checks": checks, "passed": score >= 0.8}


class ContentOptimizationSkill(BaseSkill):
    """
    内容优化 Skill（内容生成工作流的子技能）
    """

    name = "content_optimization"
    description = "优化已生成内容的表达"
    version = "1.0.0"
    category = "content"

    async def execute(self, content: Dict[str, Any], optimization_goals: List[str] = None) -> str:
        """优化内容"""
        # 简化实现：返回 JSON 字符串
        import json

        return json.dumps(content, ensure_ascii=False)


class ContentQualityCheckSkill(BaseSkill):
    """
    质量检查 Skill（独立使用）
    """

    name = "content_quality_check"
    description = "检查内容质量并给出评分"
    version = "1.0.0"
    category = "content"

    async def execute(self, content: Dict[str, Any], requirement: Dict[str, Any] = None) -> str:
        """质量检查"""
        checks = {
            "has_title": bool(content.get("title")),
            "has_key_points": len(content.get("key_points", [])) >= 3,
            "title_length": 5 <= len(content.get("title", "")) <= 20,
        }

        score = sum(checks.values()) / len(checks)

        # 返回评分和建议
        result = f"质量分数: {score:.2f}\n"
        result += f"通过: {'是' if score >= 0.8 else '否'}\n"

        failed_items = [name for name, passed in checks.items() if not passed]
        if failed_items:
            result += f"未通过项: {', '.join(failed_items)}"

        return result


# ============================================================================
# LangChain Tool 包装器
# ============================================================================

from langchain_core.tools import StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field


class ContentGenerationInput(BaseModel):
    """内容生成输入参数"""

    topic: str = Field(..., description="页面主题")
    audience: str = Field(default="general", description="目标受众 (expert/general/student)")
    page_type: str = Field(default="content", description="页面类型 (content/cover/summary)")
    num_points: int = Field(default=5, description="要点数量")


class ContentQualityCheckInput(BaseModel):
    """内容质量检查输入参数"""

    content: Dict[str, Any] = Field(..., description="内容字典")
    requirement: Dict[str, Any] = Field(default=None, description="需求字典（可选）")


# 创建 LangChain Tools
content_generation_tool = StructuredTool.from_function(
    func=ContentGenerationSkill().execute,
    name="content_generation",
    description="结构化的内容生成工作流程：需求分析 → 要点提取 → 结构化 → 优化 → 质检",
    args_schema=ContentGenerationInput,
)

content_optimization_tool = StructuredTool.from_function(
    func=ContentOptimizationSkill().execute,
    name="content_optimization",
    description="优化已生成内容的表达",
    args_schema=type(
        "ContentOptimizationInput",
        (BaseModel,),
        {
            "content": (Dict[str, Any], Field(..., description="内容字典")),
            "optimization_goals": (List[str], Field(default=None, description="优化目标")),
        },
    ),
)

content_quality_check_tool = StructuredTool.from_function(
    func=ContentQualityCheckSkill().execute,
    name="content_quality_check",
    description="检查内容质量并给出评分",
    args_schema=ContentQualityCheckInput,
)
