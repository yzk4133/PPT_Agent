"""
内容优化 Skill

根据质量检查结果优化内容
"""

import json
import logging
from typing import Dict, Any, List
from backend.tools.skills.base_skill import BaseSkill


logger = logging.getLogger(__name__)


class ContentOptimizationSkill(BaseSkill):
    """
    内容优化 Skill

    职责：
    - 根据失败项优化内容
    - 提升内容质量分数
    - 支持迭代优化
    """

    name = "content_optimization"
    description = "根据质量检查结果优化内容，提升质量分数"
    version = "1.0.0"
    category = "content"

    async def execute(
        self,
        content: Dict[str, Any],
        failed_checks: List[str],
        requirement: Dict[str, Any] = None,
        target_score: float = 0.9,
    ) -> str:
        """
        执行内容优化

        Args:
            content: 内容字典
            failed_checks: 失败的检查项
                ["title_length", "key_points_count", ...]
            requirement: 需求字典（可选）
            target_score: 目标分数（默认 0.9）

        Returns:
            str: JSON 格式的优化后内容
        """
        try:
            logger.info(f"[ContentOptimization] 优化内容: {content.get('title', 'Unknown')}")
            logger.info(f"[ContentOptimization] 失败项: {failed_checks}")

            current = content.copy()
            improvements = []

            # 按优先级处理失败项
            for check_name in self._prioritize_checks(failed_checks):
                # 优化这个检查项
                optimized, improvement = await self._optimize_check(
                    current, check_name, requirement
                )

                if optimized is not None:
                    current = optimized
                    improvements.append(improvement)
                    logger.info(f"[ContentOptimization] 已优化: {check_name} → {improvement}")

            # 返回 JSON 格式的优化内容
            import json

            result = {
                "optimized": current,
                "improvements": improvements,
                "iterations": len(improvements),
            }

            return json.dumps(result, ensure_ascii=False)

        except Exception as e:
            logger.error(f"[ContentOptimization] 优化失败: {e}", exc_info=True)
            return f"错误：{str(e)}"

    def _prioritize_checks(self, failed_checks: List[str]) -> List[str]:
        """
        按优先级排序检查项

        优先级：
        P0: 结构性问题（has_title, has_key_points）
        P1: 标题问题（title_length）
        P2: 要点问题（key_points_count, key_points_length）
        P3: 其他问题
        """
        priority = {
            # P0: 结构
            "has_title": 0,
            "has_key_points": 0,
            "has_content": 0,
            # P1: 标题
            "title_length": 1,
            "title_attractive": 1,
            "title_not_generic": 1,
            # P2: 要点
            "key_points_count": 2,
            "key_points_length": 2,
            "key_points_parallel": 2,
            # P3: 其他
            "audience_match": 3,
            "content_length_ok": 3,
        }

        return sorted(failed_checks, key=lambda x: priority.get(x, 3))

    async def _optimize_check(
        self, content: Dict[str, Any], check_name: str, requirement: Dict[str, Any]
    ) -> tuple:
        """
        优化单个检查项

        Returns:
            (优化后的内容, 改进说明)
        """
        optimizer = getattr(self, f"_fix_{check_name}", None)

        if optimizer:
            try:
                optimized = await optimizer(content, requirement)
                improvement = self._get_improvement_text(check_name)
                return optimized, improvement
            except Exception as e:
                logger.warning(f"[ContentOptimization] 优化 {check_name} 失败: {e}")
                return None, None
        else:
            logger.warning(f"[ContentOptimization] 没有优化器: {check_name}")
            return None, None

    async def _fix_title_length(
        self, content: Dict[str, Any], requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """修复标题长度"""
        title = content.get("title", "")

        if not self.llm:
            # 简化：截断或补充
            if len(title) > 20:
                content["title"] = title[:18] + "..."
            elif len(title) < 5:
                content["title"] = title + "概述"
            return content

        prompt = f"""
        优化以下标题，使其长度在 5-20 字之间：

        原标题：{title}

        要求：
        - 保持原意
        - 简洁有力
        - 长度：5-20字

        只返回优化后的标题。
        """

        result = await self.llm.ainvoke(prompt)
        content["title"] = result.strip().strip("\"'")

        return content

    async def _fix_title_attractive(
        self, content: Dict[str, Any], requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提升标题吸引力"""
        title = content.get("title", "")

        if not self.llm:
            return content

        prompt = f"""
        提升以下标题的吸引力：

        原标题：{title}

        要求：
        - 使用疑问式、数字式或对比式
        - 避免使用"关于"、"介绍"等套话
        - 长度保持在 5-20 字

        只返回优化后的标题。
        """

        result = await self.llm.ainvoke(prompt)
        content["title"] = result.strip().strip("\"'")

        return content

    async def _fix_title_not_generic(
        self, content: Dict[str, Any], requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """去除通用性"""
        title = content.get("title", "")

        if not self.llm:
            # 简单替换
            for prefix in ["关于", "介绍"]:
                if title.startswith(prefix):
                    content["title"] = title.replace(prefix, "", 1).strip()
            return content

        prompt = f"""
        去除以下标题的通用性，使其更具体：

        原标题：{title}

        要求：
        - 去除"关于"、"介绍"等前缀
        - 使标题更具体、更有针对性

        只返回优化后的标题。
        """

        result = await self.llm.ainvoke(prompt)
        content["title"] = result.strip().strip("\"'")

        return content

    async def _fix_key_points_count(
        self, content: Dict[str, Any], requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """修复要点数量"""
        key_points = content.get("key_points", [])
        content_text = content.get("content_text", "")

        target_count = 5

        if len(key_points) < 3:
            # 需要增加要点
            if not self.llm:
                # 从正文提取
                lines = content_text.split("\n")
                for line in lines:
                    if line.strip() and len(key_points) < 3:
                        key_points.append(line.strip()[:50])
            else:
                # 使用 LLM 提取
                prompt = f"""
                从以下内容中提取 3-5 个关键要点：

                标题：{content.get('title')}
                内容：{content_text}

                要求：
                - 每个要点一句话（10-20字）
                - 按重要性排序

                返回 JSON 数组：["要点1", "要点2", ...]
                """

                result = await self.llm.ainvoke(prompt)
                result = result.strip()
                if result.startswith("```"):
                    result = result.split("```")[1]
                    if result.startswith("json"):
                        result = result[4:]

                extracted = json.loads(result)
                key_points = extracted[:5]

        elif len(key_points) > 5:
            # 需要删减要点
            key_points = key_points[:5]

        content["key_points"] = key_points

        return content

    async def _fix_key_points_length(
        self, content: Dict[str, Any], requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """修复要点长度"""
        key_points = content.get("key_points", [])

        for i, point in enumerate(key_points):
            if len(point) > 50:
                # 缩短要点
                if self.llm:
                    prompt = f"""
                    缩短以下要点，保持在 50 字以内：

                    原要点：{point}

                    要求：
                    - 保持原意
                    - 删除冗余词汇
                    - 简洁表达

                    只返回优化后的要点。
                    """

                    result = await self.llm.ainvoke(prompt)
                    key_points[i] = result.strip().strip("\"'")

                else:
                    # 截断
                    key_points[i] = point[:47] + "..."

        content["key_points"] = key_points

        return content

    async def _fix_key_points_parallel(
        self, content: Dict[str, Any], requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """修复要点平行结构"""
        key_points = content.get("key_points", [])

        if not self.llm or len(key_points) < 2:
            return content

        # 分析结构
        first_point = key_points[0]

        # 判断是动词开头还是名词开头
        if first_point.split()[0].endswith("ing"):
            structure = "动词-ing"
        elif any(first_point.startswith(p) for p in ["是", "有", "能"]):
            structure = "动词"
        else:
            structure = "名词"

        # 统一结构
        prompt = f"""
        统一以下要点的结构，使其保持平行：

        要点：{key_points}

        参考结构：{structure}

        要求：
        - 所有要点使用相同的语法结构
        - 保持原意不变

        返回 JSON 数组：["要点1", "要点2", ...]
        """

        try:
            result = await self.llm.ainvoke(prompt)
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]

            content["key_points"] = json.loads(result)

        except Exception as e:
            logger.warning(f"[ContentOptimization] 平行结构优化失败: {e}")

        return content

    async def _fix_audience_match(
        self, content: Dict[str, Any], requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """修复受众匹配"""
        audience = requirement.get("audience", "general")
        content_text = content.get("content_text", "")

        if not self.llm:
            # 简单调整长度
            if audience == "expert" and len(content_text) < 200:
                content["content_text"] = content_text + "\n\n[需要更详细的内容...]"
            elif audience == "general" and len(content_text) > 500:
                content["content_text"] = content_text[:500] + "\n\n[内容过长，已截断]"
            return content

        prompt = f"""
        调整以下内容的长度，适合 {audience} 受众：

        原内容：{content_text}

        要求：
        - 专家受众（expert）：200字以上，详细深入
        - 大众受众（general）：100-500字，适中
        - 学生受众（student）：200字以上，有示例

        返回优化后的内容。
        """

        result = await self.llm.ainvoke(prompt)
        content["content_text"] = result.strip()

        return content

    async def _fix_content_length_ok(
        self, content: Dict[str, Any], requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """修复内容长度"""
        content_text = content.get("content_text", "")

        if len(content_text) < 100:
            # 内容太短，补充
            content["content_text"] = content_text + "\n\n[此处需要补充更多详细内容...]"

        elif len(content_text) > 2000:
            # 内容太长，截断
            content["content_text"] = content_text[:2000] + "\n\n[内容过长，已截断]"

        return content

    def _get_improvement_text(self, check_name: str) -> str:
        """获取改进说明"""
        improvements = {
            "title_length": "调整标题长度到 5-20 字",
            "title_attractive": "提升标题吸引力",
            "title_not_generic": "去除通用性前缀",
            "key_points_count": "调整要点数量到 3-5 个",
            "key_points_length": "缩短过长的要点",
            "key_points_parallel": "统一要点语法结构",
            "audience_match": "调整内容长度适配受众",
            "content_length_ok": "调整内容长度到合理范围",
        }

        return improvements.get(check_name, f"优化 {check_name}")


# ============================================================================
# LangChain Tool 包装器
# ============================================================================

from langchain_core.tools import StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field


class ContentOptimizationInput(BaseModel):
    """内容优化输入参数"""

    content: Dict[str, Any] = Field(..., description="内容字典")
    failed_checks: List[str] = Field(..., description="失败的检查项")
    requirement: Dict[str, Any] = Field(default=None, description="需求字典（可选）")
    target_score: float = Field(default=0.9, description="目标分数")


# 创建 LangChain Tool
content_optimization_tool = StructuredTool.from_function(
    func=ContentOptimizationSkill().execute,
    name="content_optimization",
    description="根据质量检查结果优化内容，提升质量分数",
    args_schema=ContentOptimizationInput,
)


class IterativeOptimizationSkill(BaseSkill):
    """
    迭代优化 Skill

    通过多轮迭代逐步提升内容质量
    """

    name = "iterative_optimization"
    description = "通过多轮迭代优化内容，直到达到目标分数"
    version = "1.0.0"
    category = "content"

    async def execute(
        self,
        content: Dict[str, Any],
        quality_check_skill,
        requirement: Dict[str, Any] = None,
        max_iterations: int = 3,
        target_score: float = 0.9,
    ) -> str:
        """
        迭代优化内容

        Args:
            content: 内容字典
            quality_check_skill: 质量检查 Skill
            requirement: 需求字典
            max_iterations: 最大迭代次数
            target_score: 目标分数

        Returns:
            str: JSON 格式的迭代优化结果
        """
        try:
            logger.info(f"[IterativeOptimization] 开始迭代优化，目标分数: {target_score}")

            current_content = content.copy()
            improvements = []

            # 初始质量检查
            quality_result_str = await quality_check_skill.execute(current_content, requirement)
            # 从字符串中解析分数（简化处理）
            import re

            score_match = re.search(r"质量分数: ([\d.]+)", quality_result_str)
            initial_score = float(score_match.group(1)) if score_match else 0.7

            logger.info(f"[IterativeOptimization] 初始分数: {initial_score}")

            # 迭代优化
            for iteration in range(max_iterations):
                if initial_score >= target_score:
                    logger.info(f"[IterativeOptimization] 达到目标分数，迭代 {iteration + 1} 轮")
                    break

                # 优化
                optimizer = ContentOptimizationSkill(llm=self.llm)
                optimization_result_str = await optimizer.execute(
                    current_content, [], requirement  # 简化：不传入具体检查项
                )

                # 解析优化结果
                try:
                    import json

                    optimization_result = json.loads(optimization_result_str)
                    current_content = optimization_result.get("optimized", current_content)
                    improvements.extend(optimization_result.get("improvements", []))
                except:
                    logger.warning(f"[IterativeOptimization] 解析优化结果失败")

                # 重新检查质量
                quality_result_str = await quality_check_skill.execute(current_content, requirement)
                score_match = re.search(r"质量分数: ([\d.]+)", quality_result_str)
                current_score = float(score_match.group(1)) if score_match else initial_score

                logger.info(f"[IterativeOptimization] 第 {iteration + 1} 轮后分数: {current_score}")
                initial_score = current_score

            # 返回 JSON 格式结果
            import json

            result = {
                "final_content": current_content,
                "initial_score": initial_score,
                "final_score": current_score,
                "iterations": len(improvements),
                "improvements": improvements,
                "target_met": current_score >= target_score,
            }

            return json.dumps(result, ensure_ascii=False)

        except Exception as e:
            logger.error(f"[IterativeOptimization] 迭代失败: {e}", exc_info=True)
            return f"错误：{str(e)}"
