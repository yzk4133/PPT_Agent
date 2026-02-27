"""
主题分解 Skill

将大主题分解为逻辑相关的子主题
"""

import json
import logging
from typing import Dict, Any, List
from backend.tools.skills.base_skill import BaseSkill


logger = logging.getLogger(__name__)


class TopicDecompositionSkill(BaseSkill):
    """
    主题分解 Skill

    职责：
    - 将大主题分解为 3-7 个子主题
    - 确保子主题的逻辑性
    - 支持不同的分解策略
    """

    name = "topic_decomposition"
    description = "将复杂主题分解为逻辑清晰的子主题"
    version = "1.0.0"
    category = "framework"

    async def execute(
        self,
        topic: str,
        num_parts: int = 5,
        strategy: str = "logical",
        audience: str = "general"
    ) -> str:
        """
        执行主题分解

        Args:
            topic: 主题
            num_parts: 分解数量（3-7）
            strategy: 分解策略
                - "logical": 逻辑递进（基础→进阶→高级）
                - "chronological": 时间顺序（历史→现在→未来）
                - "problem_solution": 问题解决（问题→分析→解决）
                - "component": 组件分解（各个组成部分）
            audience: 目标受众

        Returns:
            str: JSON 格式的子主题列表
        """
        try:
            logger.info(f"[TopicDecomposition] 分解主题: {topic}, 数量: {num_parts}, 策略: {strategy}")

            # 步骤 1: 分析主题类型
            topic_type = await self._analyze_topic_type(topic)

            # 步骤 2: 选择分解策略
            if strategy == "logical":
                subtopics = await self._decompose_logically(topic, num_parts, audience)
            elif strategy == "chronological":
                subtopics = await self._decompose_chronologically(topic, num_parts, audience)
            elif strategy == "problem_solution":
                subtopics = await self._decompose_problem_solution(topic, num_parts, audience)
            elif strategy == "component":
                subtopics = await self._decompose_by_components(topic, num_parts, audience)
            else:
                # 自动选择策略
                subtopics = await self._auto_decompose(topic, num_parts, audience)

            # 步骤 3: 验证逻辑性
            subtopics = await self._validate_logic(subtopics, topic)

            # 步骤 4: 添加关键词
            for subtopic in subtopics:
                subtopic["keywords"] = await self._extract_keywords(subtopic["title"])

            logger.info(f"[TopicDecomposition] 分解完成: {len(subtopics)} 个子主题")

            # 返回 JSON 格式
            import json
            result = {
                "topic": topic,
                "subtopics": subtopics,
                "strategy": strategy,
                "total": len(subtopics)
            }

            return json.dumps(result, ensure_ascii=False)

        except Exception as e:
            logger.error(f"[TopicDecomposition] 分解失败: {e}", exc_info=True)
            return f"错误：{str(e)}"

    async def _analyze_topic_type(self, topic: str) -> str:
        """分析主题类型"""
        if not self.llm:
            return "general"

        prompt = f"""
        分析以下主题的类型：

        主题：{topic}

        判断属于哪种类型：
        1. historical: 历史发展类
        2. technical: 技术原理类
        3. problem: 问题解决类
        4. component: 组件构成类
        5. general: 通用类

        只返回类型名称。
        """

        try:
            result = await self.llm.ainvoke(prompt)
            return result.strip().lower()
        except:
            return "general"

    async def _decompose_logically(
        self,
        topic: str,
        num_parts: int,
        audience: str
    ) -> List[Dict[str, Any]]:
        """
        逻辑递进分解

        结构：基础 → 进阶 → 高级 → 应用
        """
        if not self.llm:
            # 降级：使用模板
            return self._fallback_decompose(topic, num_parts)

        prompt = f"""
        将以下主题分解为 {num_parts} 个逻辑递进的子主题：

        主题：{topic}
        受众：{audience}

        要求：
        1. 按照"基础认知 → 核心原理 → 深入理解 → 实际应用 → 总结展望"的逻辑
        2. 每个子主题有明确的标题
        3. 子主题之间有递进关系
        4. 适合 {audience} 受众理解

        返回 JSON 格式：
        [
            {{"title": "子主题1", "description": "描述"}},
            {{"title": "子主题2", "description": "描述"}},
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

            subtopics_data = json.loads(result)

            # 添加顺序
            return [
                {
                    "title": item["title"],
                    "description": item.get("description", ""),
                    "order": i + 1
                }
                for i, item in enumerate(subtopics_data)
            ]

        except Exception as e:
            logger.warning(f"[TopicDecomposition] 逻辑分解失败: {e}")
            return self._fallback_decompose(topic, num_parts)

    async def _decompose_chronologically(
        self,
        topic: str,
        num_parts: int,
        audience: str
    ) -> List[Dict[str, Any]]:
        """
        时间顺序分解

        结构：过去 → 现在 → 未来
        """
        if not self.llm:
            return self._fallback_decompose(topic, num_parts)

        prompt = f"""
        将以下主题按时间顺序分解为 {num_parts} 个子主题：

        主题：{topic}
        受众：{audience}

        要求：
        1. 按照时间发展顺序：起源 → 发展 → 现状 → 展望
        2. 每个阶段有明确的时间特征
        3. 突出关键转折点

        返回 JSON 格式：
        [
            {{"title": "子主题1", "description": "描述", "time_period": "时间范围"}},
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

            subtopics_data = json.loads(result)

            return [
                {
                    "title": item["title"],
                    "description": item.get("description", ""),
                    "order": i + 1,
                    "time_period": item.get("time_period", "")
                }
                for i, item in enumerate(subtopics_data)
            ]

        except Exception as e:
            logger.warning(f"[TopicDecomposition] 时间分解失败: {e}")
            return self._fallback_decompose(topic, num_parts)

    async def _decompose_problem_solution(
        self,
        topic: str,
        num_parts: int,
        audience: str
    ) -> List[Dict[str, Any]]:
        """
        问题解决分解

        结构：问题 → 原因 → 分析 → 解决
        """
        if not self.llm:
            return self._fallback_decompose(topic, num_parts)

        prompt = f"""
        将以下主题按"问题解决"逻辑分解为 {num_parts} 个子主题：

        主题：{topic}
        受众：{audience}

        要求：
        1. 结构：提出问题 → 分析原因 → 探讨影响 → 提出方案 → 展望效果
        2. 每个子主题对应问题解决的一个环节
        3. 保持逻辑连贯性

        返回 JSON 格式：
        [
            {{"title": "子主题1", "description": "描述"}},
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

            subtopics_data = json.loads(result)

            return [
                {
                    "title": item["title"],
                    "description": item.get("description", ""),
                    "order": i + 1
                }
                for i, item in enumerate(subtopics_data)
            ]

        except Exception as e:
            logger.warning(f"[TopicDecomposition] 问题解决分解失败: {e}")
            return self._fallback_decompose(topic, num_parts)

    async def _decompose_by_components(
        self,
        topic: str,
        num_parts: int,
        audience: str
    ) -> List[Dict[str, Any]]:
        """
        组件分解

        结构：组成部分1 → 组成部分2 → 组成部分3
        """
        if not self.llm:
            return self._fallback_decompose(topic, num_parts)

        prompt = f"""
        将以下主题按"组成部分"分解为 {num_parts} 个子主题：

        主题：{topic}
        受众：{audience}

        要求：
        1. 识别主题的主要组成部分
        2. 每个子主题对应一个组成部分
        3. 确保组成部分之间没有重叠
        4. 按照重要性或逻辑顺序排列

        返回 JSON 格式：
        [
            {{"title": "子主题1", "description": "描述"}},
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

            subtopics_data = json.loads(result)

            return [
                {
                    "title": item["title"],
                    "description": item.get("description", ""),
                    "order": i + 1
                }
                for i, item in enumerate(subtopics_data)
            ]

        except Exception as e:
            logger.warning(f"[TopicDecomposition] 组件分解失败: {e}")
            return self._fallback_decompose(topic, num_parts)

    async def _auto_decompose(
        self,
        topic: str,
        num_parts: int,
        audience: str
    ) -> List[Dict[str, Any]]:
        """自动选择分解策略"""
        # 先分析主题类型
        topic_type = await self._analyze_topic_type(topic)

        # 根据类型选择策略
        strategy_map = {
            "historical": "chronological",
            "technical": "logical",
            "problem": "problem_solution",
            "component": "component",
            "general": "logical"
        }

        strategy = strategy_map.get(topic_type, "logical")

        # 调用对应的分解方法
        if strategy == "chronological":
            return await self._decompose_chronologically(topic, num_parts, audience)
        elif strategy == "problem_solution":
            return await self._decompose_problem_solution(topic, num_parts, audience)
        elif strategy == "component":
            return await self._decompose_by_components(topic, num_parts, audience)
        else:
            return await self._decompose_logically(topic, num_parts, audience)

    async def _validate_logic(
        self,
        subtopics: List[Dict[str, Any]],
        original_topic: str
    ) -> List[Dict[str, Any]]:
        """验证子主题的逻辑性"""
        # 检查数量
        if len(subtopics) < 3:
            logger.warning(f"[TopicDecomposition] 子主题数量过少: {len(subtopics)}")

        # 检查标题重复
        titles = [s["title"] for s in subtopics]
        if len(titles) != len(set(titles)):
            logger.warning(f"[TopicDecomposition] 存在重复标题")

        return subtopics

    async def _extract_keywords(self, title: str) -> List[str]:
        """从子主题标题中提取关键词"""
        if not self.llm:
            # 简化：分词
            return title.split()

        prompt = f"""
        从以下标题中提取 2-3 个关键词：

        标题：{title}

        返回 JSON 数组：["关键词1", "关键词2", ...]
        """

        try:
            result = await self.llm.ainvoke(prompt)
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]

            keywords = json.loads(result)
            return keywords[:3]

        except:
            return title.split()[:3]

    def _fallback_decompose(
        self,
        topic: str,
        num_parts: int
    ) -> List[Dict[str, Any]]:
        """降级分解：使用模板"""
        subtopics = []

        # 通用模板
        templates = [
            f"{topic}概述",
            f"{topic}的核心原理",
            f"{topic}的主要特点",
            f"{topic}的应用场景",
            f"{topic}的发展趋势",
            f"{topic}的挑战与机遇",
            f"{topic}的未来展望"
        ]

        for i in range(min(num_parts, len(templates))):
            subtopics.append({
                "title": templates[i],
                "description": f"{templates[i]}的详细内容",
                "order": i + 1
            })

        return subtopics


# ============================================================================
# LangChain Tool 包装器
# ============================================================================

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class TopicDecompositionInput(BaseModel):
    """主题分解输入参数"""
    topic: str = Field(..., description="主题")
    num_parts: int = Field(default=5, description="分解数量（3-7）")
    strategy: str = Field(default="logical", description="分解策略 (logical/chronological/problem_solution/component)")
    audience: str = Field(default="general", description="目标受众")


# 创建 LangChain Tool
topic_decomposition_tool = StructuredTool.from_function(
    func=TopicDecompositionSkill().execute,
    name="topic_decomposition",
    description="将复杂主题分解为逻辑清晰的子主题",
    args_schema=TopicDecompositionInput
)
