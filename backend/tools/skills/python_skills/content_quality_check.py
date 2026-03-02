"""
内容质量检查 Skill

评估生成内容的质量并提供改进建议
"""

import json
import logging
from typing import Dict, Any, List
from backend.tools.skills.base_skill import BaseSkill


logger = logging.getLogger(__name__)


class ContentQualityCheckSkill(BaseSkill):
    """
    内容质量检查 Skill

    职责：
    - 评估内容的完整性、准确性、吸引力
    - 提供质量分数（0-1）
    - 识别需要改进的部分
    """

    name = "content_quality_check"
    description = "检查内容质量并给出评分，识别需要改进的部分"
    version = "1.0.0"
    category = "content"

    async def execute(self, content: Dict[str, Any], requirement: Dict[str, Any] = None) -> str:
        """
        执行质量检查

        Args:
            content: 内容字典
                {
                    "title": "标题",
                    "key_points": ["要点1", "要点2"],
                    "content_text": "正文内容",
                    "page_type": "content"
                }
            requirement: 需求字典（可选）

        Returns:
            str: 质量检查结果字符串
        """
        try:
            logger.info(f"[QualityCheck] 检查内容: {content.get('title', 'Unknown')}")

            # 执行检查
            checks = await self._run_all_checks(content, requirement)

            # 计算分数
            score = sum(checks.values()) / len(checks)

            # 识别问题
            issues = self._identify_issues(checks)

            # 生成建议
            suggestions = self._generate_suggestions(issues)

            # 判断是否通过
            passed = score >= 0.8

            # 格式化返回字符串
            result = f"质量分数: {score:.2f}\n"
            result += f"通过: {'是' if passed else '否'}\n"

            if issues:
                result += f"\n问题:\n"
                for issue in issues:
                    result += f"  - {issue}\n"

            if suggestions:
                result += f"\n建议:\n"
                for suggestion in suggestions:
                    result += f"  - {suggestion}\n"

            logger.info(f"[QualityCheck] 分数: {score:.2f}, 通过: {passed}")
            return result.strip()

        except Exception as e:
            logger.error(f"[QualityCheck] 检查失败: {e}", exc_info=True)
            return f"错误：{str(e)}"

    async def _run_all_checks(
        self, content: Dict[str, Any], requirement: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        运行所有检查项

        Returns:
            {检查项名称: 是否通过}
        """
        checks = {}

        # 1. 结构完整性检查
        checks.update(self._check_structure(content))

        # 2. 标题质量检查
        checks.update(self._check_title(content))

        # 3. 要点质量检查
        checks.update(self._check_key_points(content))

        # 4. 受众适配检查（如果有需求）
        if requirement:
            checks.update(self._check_audience_match(content, requirement))

        # 5. 长度检查
        checks.update(self._check_length(content))

        return checks

    def _check_structure(self, content: Dict[str, Any]) -> Dict[str, bool]:
        """检查结构完整性"""
        return {
            "has_title": bool(content.get("title")),
            "has_key_points": len(content.get("key_points", [])) > 0,
            "has_content": bool(content.get("content_text")),
        }

    def _check_title(self, content: Dict[str, Any]) -> Dict[str, bool]:
        """检查标题质量"""
        title = content.get("title", "")

        return {
            "title_length": 5 <= len(title) <= 20,
            "title_not_generic": not title.startswith("关于") and not title.startswith("介绍"),
            "title_attractive": self._is_title_attractive(title),
        }

    def _check_key_points(self, content: Dict[str, Any]) -> Dict[str, bool]:
        """检查要点质量"""
        key_points = content.get("key_points", [])

        if not key_points:
            return {"key_points_count": False}

        return {
            "key_points_count": 3 <= len(key_points) <= 5,
            "key_points_length": all(len(p) <= 50 for p in key_points),
            "key_points_parallel": self._check_parallel_structure(key_points),
        }

    def _check_audience_match(
        self, content: Dict[str, Any], requirement: Dict[str, Any]
    ) -> Dict[str, bool]:
        """检查受众匹配"""
        audience = requirement.get("audience", "general")
        content_text = content.get("content_text", "")

        # 简化检查：长度适配
        if audience == "expert":
            # 专家：内容应该详细
            is_appropriate = len(content_text) >= 200
        elif audience == "general":
            # 大众：内容应该适中
            is_appropriate = 100 <= len(content_text) <= 500
        else:  # student
            # 学生：内容应该详细且有示例
            is_appropriate = len(content_text) >= 200

        return {"audience_match": is_appropriate}

    def _check_length(self, content: Dict[str, Any]) -> Dict[str, bool]:
        """检查长度合理性"""
        content_text = content.get("content_text", "")
        key_points = content.get("key_points", [])

        # 正文长度检查（100-2000字）
        content_length_ok = 100 <= len(content_text) <= 2000

        # 要点数量检查（3-5个）
        points_count_ok = 3 <= len(key_points) <= 5

        return {"content_length_ok": content_length_ok, "points_count_ok": points_count_ok}

    def _is_title_attractive(self, title: str) -> bool:
        """判断标题是否有吸引力"""
        # 吸引力的特征
        attractive_patterns = [
            "?",  # 疑问式
            "！",  # 感叹式
            str.isdigit,  # 包含数字
        ]

        # 排除不吸引力的模式
        unattractive_patterns = ["关于", "介绍", "概述"]

        # 检查吸引力特征
        has_attractive = any(pattern in title for pattern in attractive_patterns)

        # 检查不吸引力特征
        has_unattractive = any(pattern in title for pattern in unattractive_patterns)

        return has_attractive or not has_unattractive

    def _check_parallel_structure(self, key_points: List[str]) -> bool:
        """检查要点是否平行结构"""
        if len(key_points) < 2:
            return True

        # 简化检查：首字是否都是动词/名词
        # 这里只检查长度一致性
        lengths = [len(p) for p in key_points]
        avg_length = sum(lengths) / len(lengths)

        # 如果长度差异太大，认为不平行
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
        return variance < 100  # 方差阈值

    def _identify_issues(self, checks: Dict[str, bool]) -> List[str]:
        """识别问题"""
        issues = []

        if not checks.get("has_title"):
            issues.append("缺少标题")

        if not checks.get("title_length"):
            issues.append("标题长度不符合要求（应为5-20字）")

        if not checks.get("title_attractive"):
            issues.append("标题缺乏吸引力")

        if not checks.get("key_points_count"):
            issues.append("要点数量不符合要求（应为3-5个）")

        if not checks.get("key_points_length"):
            issues.append("有要点过长（超过50字）")

        if not checks.get("key_points_parallel"):
            issues.append("要点结构不平行")

        if not checks.get("audience_match"):
            issues.append("内容长度与受众不匹配")

        if not checks.get("content_length_ok"):
            issues.append("正文长度不合理（应为100-2000字）")

        return issues

    def _generate_suggestions(self, issues: List[str]) -> List[str]:
        """生成改进建议"""
        suggestions = []

        issue_to_suggestion = {
            "缺少标题": "添加页面标题",
            "标题长度不符合要求": "调整标题长度到5-20字",
            "标题缺乏吸引力": "使用疑问式、数字式或对比式标题",
            "要点数量不符合要求": "调整为3-5个要点",
            "有要点过长": "精简要点，每个不超过50字",
            "要点结构不平行": "使用相同的语法结构（都是动词开头或都是名词开头）",
            "内容长度与受众不匹配": "根据目标受众调整内容长度：专家≥200字，大众100-500字",
            "正文长度不合理": "调整正文长度到100-2000字",
        }

        for issue in issues:
            suggestion = issue_to_suggestion.get(issue)
            if suggestion:
                suggestions.append(suggestion)

        return suggestions


class QuickQualityCheckSkill(BaseSkill):
    """
    快速质量检查 Skill（轻量级版本）

    只检查核心项，用于快速验证
    """

    name = "quick_quality_check"
    description = "快速检查核心质量指标"
    version = "1.0.0"
    category = "content"

    async def execute(self, content: Dict[str, Any]) -> str:
        """快速检查"""
        checks = {
            "has_title": bool(content.get("title")),
            "has_key_points": len(content.get("key_points", [])) >= 3,
            "title_length": 5 <= len(content.get("title", "")) <= 20,
        }

        score = sum(checks.values()) / len(checks)

        return f"质量分数: {score:.2f}\n通过: {'是' if score >= 0.8 else '否'}"


# ============================================================================
# LangChain Tool 包装器
# ============================================================================

from langchain_core.tools import StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field


class ContentQualityCheckInput(BaseModel):
    """内容质量检查输入参数"""

    content: Dict[str, Any] = Field(..., description="内容字典")
    requirement: Dict[str, Any] = Field(default=None, description="需求字典（可选）")


class QuickQualityCheckInput(BaseModel):
    """快速质量检查输入参数"""

    content: Dict[str, Any] = Field(..., description="内容字典")


# 创建 LangChain Tools
content_quality_check_tool = StructuredTool.from_function(
    func=ContentQualityCheckSkill().execute,
    name="content_quality_check",
    description="检查内容质量并给出评分，识别需要改进的部分",
    args_schema=ContentQualityCheckInput,
)

quick_quality_check_tool = StructuredTool.from_function(
    func=QuickQualityCheckSkill().execute,
    name="quick_quality_check",
    description="快速检查核心质量指标",
    args_schema=QuickQualityCheckInput,
)
