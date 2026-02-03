#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
上下文窗口优化器 - P0功能
智能管理Token预算，动态加载必要内容
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
import sys
import os

# 导入项目模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 渐进式加载功能已被移除（依赖的模块已废弃）
# 如需重新启用，请使用 backend/agents/tools/skills/ 中的 Skills 框架
PROGRESSIVE_LOADING_AVAILABLE = False

from .vector_memory_service import VectorMemoryService
from .user_preference_service import UserPreferenceService

logger = logging.getLogger(__name__)


class ContextWindowOptimizer:
    """
    上下文窗口优化器

    核心功能：
    1. 智能分配Token预算
    2. 按需加载技能和记忆
    3. 优先级排序（必须项 > 相关历史 > 可选项）
    4. 避免超出模型上下文限制
    """

    # Token预算配置（基于Claude Sonnet 4.5的200K上下文）
    DEFAULT_TOKEN_BUDGET = 8000  # 保守估计，为输出预留空间
    MAX_TOKEN_BUDGET = 180000  # 最大可用

    # 优先级权重
    PRIORITY_REQUIRED = 1.0  # 必须项（当前任务相关技能）
    PRIORITY_RELEVANT = 0.7  # 相关项（历史记忆）
    PRIORITY_OPTIONAL = 0.3  # 可选项（用户偏好摘要）

    def __init__(
        self,
        skill_registry: Optional["ProgressiveSkillRegistry"] = None,
        vector_service: Optional[VectorMemoryService] = None,
        user_pref_service: Optional[UserPreferenceService] = None,
    ):
        """
        初始化优化器

        Args:
            skill_registry: 渐进式技能注册表
            vector_service: 向量记忆服务
            user_pref_service: 用户偏好服务
        """
        self.skill_registry = skill_registry
        self.vector_service = vector_service
        self.user_pref_service = user_pref_service
        logger.info("ContextWindowOptimizer initialized")

    async def build_optimized_context(
        self,
        agent_name: str,
        task_description: str,
        user_id: str,
        session_id: str,
        required_skills: Optional[List[str]] = None,
        token_budget: Optional[int] = None,
        include_history: bool = True,
        include_user_prefs: bool = True,
    ) -> Dict[str, Any]:
        """
        构建优化的上下文

        Args:
            agent_name: Agent名称
            task_description: 任务描述
            user_id: 用户ID
            session_id: 会话ID
            required_skills: 必须的技能ID列表
            token_budget: Token预算
            include_history: 是否包含历史记忆
            include_user_prefs: 是否包含用户偏好

        Returns:
            优化后的上下文字典
        """
        token_budget = token_budget or self.DEFAULT_TOKEN_BUDGET
        context_items = []
        tokens_used = 0

        logger.info(
            f"Building context for {agent_name}, budget={token_budget}, "
            f"required_skills={required_skills}"
        )

        # === 阶段1: 加载必须项（最高优先级） ===
        if required_skills and self.skill_registry:
            for skill_id in required_skills:
                if tokens_used >= token_budget * 0.8:  # 预留20%给其他内容
                    logger.warning(f"Token budget nearly exhausted at required skills")
                    break

                skill_content = self.skill_registry.get_full_content_for_skill(skill_id)
                skill_tokens = self._estimate_tokens(skill_content)

                if tokens_used + skill_tokens <= token_budget:
                    context_items.append(
                        {
                            "type": "skill",
                            "priority": self.PRIORITY_REQUIRED,
                            "content": skill_content,
                            "tokens": skill_tokens,
                            "metadata": {"skill_id": skill_id},
                        }
                    )
                    tokens_used += skill_tokens
                    logger.debug(f"Loaded skill: {skill_id} ({skill_tokens} tokens)")
                else:
                    # 技能太大，尝试加载标准描述
                    if hasattr(self.skill_registry, "_skills"):
                        skill_meta = self.skill_registry._skills.get(skill_id)
                        if skill_meta:
                            standard_desc = skill_meta.get_standard_description()
                            desc_tokens = self._estimate_tokens(standard_desc)
                            if tokens_used + desc_tokens <= token_budget:
                                context_items.append(
                                    {
                                        "type": "skill_summary",
                                        "priority": self.PRIORITY_REQUIRED,
                                        "content": standard_desc,
                                        "tokens": desc_tokens,
                                        "metadata": {"skill_id": skill_id},
                                    }
                                )
                                tokens_used += desc_tokens
                                logger.info(f"Loaded skill summary instead: {skill_id}")

        # === 阶段2: 加载相关历史（中优先级） ===
        if include_history and self.vector_service and tokens_used < token_budget * 0.9:
            remaining_budget = int(
                (token_budget - tokens_used) * 0.5
            )  # 为历史分配剩余的50%

            try:
                # 搜索相关历史
                relevant_memories = await self.vector_service.search(
                    query=task_description,
                    namespace=VectorMemoryService.NS_RESEARCH,
                    k=3,
                    user_id=user_id,
                )

                for memory in relevant_memories:
                    if tokens_used >= token_budget * 0.95:
                        break

                    memory_content = self._format_memory(memory)
                    memory_tokens = self._estimate_tokens(memory_content)

                    if tokens_used + memory_tokens <= token_budget:
                        context_items.append(
                            {
                                "type": "memory",
                                "priority": self.PRIORITY_RELEVANT,
                                "content": memory_content,
                                "tokens": memory_tokens,
                                "metadata": {
                                    "similarity": memory.get("similarity", 0),
                                    "memory_id": memory.get("id"),
                                },
                            }
                        )
                        tokens_used += memory_tokens
                        logger.debug(
                            f"Loaded memory ({memory_tokens} tokens, "
                            f"similarity={memory.get('similarity', 0):.2f})"
                        )

            except Exception as e:
                logger.warning(f"Failed to load history: {e}")

        # === 阶段3: 加载用户偏好摘要（低优先级） ===
        if include_user_prefs and self.user_pref_service and tokens_used < token_budget:
            try:
                user_prefs = await self.user_pref_service.get_user_preferences(user_id)
                prefs_summary = self._create_user_prefs_summary(user_prefs)
                prefs_tokens = self._estimate_tokens(prefs_summary)

                if tokens_used + prefs_tokens <= token_budget:
                    context_items.append(
                        {
                            "type": "user_preferences",
                            "priority": self.PRIORITY_OPTIONAL,
                            "content": prefs_summary,
                            "tokens": prefs_tokens,
                            "metadata": {"user_id": user_id},
                        }
                    )
                    tokens_used += prefs_tokens
                    logger.debug(f"Loaded user preferences ({prefs_tokens} tokens)")

            except Exception as e:
                logger.warning(f"Failed to load user preferences: {e}")

        # === 构建最终上下文 ===
        final_context = self._assemble_context(context_items)

        result = {
            "context": final_context,
            "tokens_used": tokens_used,
            "tokens_budget": token_budget,
            "utilization": round(tokens_used / token_budget * 100, 2),
            "items_loaded": len(context_items),
            "breakdown": {
                "skills": sum(
                    1
                    for item in context_items
                    if item["type"] in ["skill", "skill_summary"]
                ),
                "memories": sum(
                    1 for item in context_items if item["type"] == "memory"
                ),
                "preferences": sum(
                    1 for item in context_items if item["type"] == "user_preferences"
                ),
            },
        }

        logger.info(
            f"Context built: {tokens_used}/{token_budget} tokens "
            f"({result['utilization']}% utilized), "
            f"{result['items_loaded']} items"
        )

        return result

    def _estimate_tokens(self, text: str) -> int:
        """
        估算文本Token数

        粗略估算：
        - 英文: 1 token ≈ 4 characters
        - 中文: 1 token ≈ 2 characters
        - 混合: 取平均 3 characters/token
        """
        if not text:
            return 0
        return len(text) // 3

    def _format_memory(self, memory: Dict[str, Any]) -> str:
        """格式化记忆内容"""
        content = memory.get("content", "")
        metadata = memory.get("metadata", {})
        similarity = memory.get("similarity", 0)

        return f"""## 相关历史记忆 (相似度: {similarity:.2f})

{content}

---
"""

    def _create_user_prefs_summary(self, prefs: Dict[str, Any]) -> str:
        """创建用户偏好摘要"""
        key_prefs = {
            "language": prefs.get("language", "EN-US"),
            "default_slides": prefs.get("default_slides", 10),
            "style": prefs.get("style", "professional"),
        }

        summary = "## 用户偏好\n\n"
        for key, value in key_prefs.items():
            summary += f"- {key}: {value}\n"

        return summary

    def _assemble_context(self, items: List[Dict[str, Any]]) -> str:
        """
        组装最终上下文

        按优先级排序并合并内容
        """
        # 按优先级排序
        sorted_items = sorted(items, key=lambda x: x["priority"], reverse=True)

        # 合并内容
        context_parts = []
        for item in sorted_items:
            context_parts.append(item["content"])

        return "\n\n".join(context_parts)

    async def suggest_skill_loading(
        self,
        task_description: str,
        available_skills: List[str],
        top_k: int = 3,
    ) -> List[Tuple[str, float]]:
        """
        建议应该加载哪些技能

        基于任务描述和技能描述的相似度

        Args:
            task_description: 任务描述
            available_skills: 可用技能ID列表
            top_k: 返回Top-K个技能

        Returns:
            [(skill_id, relevance_score), ...]
        """
        if not self.skill_registry:
            return []

        suggestions = []

        for skill_id in available_skills:
            if skill_id not in self.skill_registry._skills:
                continue

            skill_meta = self.skill_registry._skills[skill_id]

            # 简单的相关性评分（基于关键词匹配）
            relevance = self._calculate_relevance(
                task_description,
                skill_meta.description,
                skill_meta.tags,
            )

            suggestions.append((skill_id, relevance))

        # 按相关性排序
        suggestions.sort(key=lambda x: x[1], reverse=True)

        return suggestions[:top_k]

    def _calculate_relevance(
        self,
        query: str,
        description: str,
        tags: List[str],
    ) -> float:
        """
        计算相关性评分（简化版）

        实际应用中可以使用向量相似度或更复杂的算法
        """
        query_lower = query.lower()
        score = 0.0

        # 描述匹配
        if description.lower() in query_lower or query_lower in description.lower():
            score += 0.6

        # 标签匹配
        for tag in tags:
            if tag.lower() in query_lower:
                score += 0.2

        return min(score, 1.0)


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def demo():
        print("ContextWindowOptimizer 示例")
        print("注意：渐进式加载功能已被移除，请使用 backend/agents/tools/skills/ 中的 Skills 框架")

        # 示例：仅使用向量记忆服务
        # 要使用完整功能，请集成新的 Skills 框架

    asyncio.run(demo())
