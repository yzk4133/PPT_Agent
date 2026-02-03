"""
Content Material Agent with Memory Integration

将共享工作空间系统集成到内容素材智能体中，实现：
1. 从工作空间获取共享的研究结果
2. 使用用户偏好优化内容生成
3. 内容缓存和复用
"""

import json
import logging
import os
from typing import AsyncGenerator, Optional, Dict, Any, List

from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.genai import types
from google.adk.events.event import Event

# 导入基础内容素材Agent
from .content_material_agent import (
    ContentMaterialAgent,
    before_agent_callback,
)

# 导入记忆适配器
from ..base_agent_with_memory import AgentMemoryMixin

logger = logging.getLogger(__name__)


class ContentMaterialAgentWithMemory(AgentMemoryMixin, ContentMaterialAgent):
    """
    带记忆功能的内容素材智能体

    扩展功能:
    1. 共享研究获取：从工作空间获取ResearchAgent共享的研究结果
    2. 用户偏好应用：应用用户偏好到内容生成
    3. 内容缓存：缓存生成的内容供复用
    4. 决策记录：记录内容生成决策
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 配置
        self.enable_content_cache = os.getenv("ENABLE_CONTENT_CACHE", "true").lower() == "true"
        self.content_cache_ttl_hours = int(os.getenv("CONTENT_CACHE_TTL_HOURS", "24"))

        # 统计信息
        self.stats = {
            "shared_research_used": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "new_generation": 0,
        }

        logger.info(
            f"[{self.agent_name}] 初始化完成: "
            f"content_cache={self.enable_content_cache}, "
            f"cache_ttl={self.content_cache_ttl_hours}h"
        )

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        执行内容素材生成（带记忆）

        覆盖父类方法，添加共享工作空间逻辑
        """
        # 设置上下文
        self._setup_context(ctx)

        try:
            # 1. 获取框架
            framework_dict = ctx.session.state.get("ppt_framework")
            if not framework_dict:
                raise ValueError("Missing ppt_framework in session state")

            pages = framework_dict.get("ppt_framework", [])
            logger.info(f"[{self.agent_name}] processing {len(pages)} pages")

            # 2. 加载用户偏好
            user_id = self._get_user_id()
            user_preferences = await self.get_user_preferences(user_id)

            # 3. 为每页生成内容素材
            content_material_list = []

            for i, page in enumerate(pages):
                page_no = page.get("page_no", i + 1)
                page_title = page.get("title", "")

                # ========== 尝试从缓存获取 ==========
                if self.enable_content_cache:
                    cached_material = await self._check_content_cache(
                        page_title, page
                    )
                    if cached_material:
                        content_material_list.append(cached_material)
                        continue

                # ========== 尝试从工作空间获取研究 ==========
                shared_research = await self.get_shared_data(
                    data_type="research_result",
                    data_key=page_title,
                )

                # ========== 生成页面素材 ==========
                page_material = await self._generate_page_material_with_memory(
                    ctx=ctx,
                    page=page,
                    page_index=i,
                    shared_research=shared_research,
                    user_preferences=user_preferences,
                )

                content_material_list.append(page_material)

                # ========== 缓存生成的内容 ==========
                if self.enable_content_cache and not page_material.get("error"):
                    await self._cache_content_material(page_title, page_material)

                # 更新进度
                progress = int((i + 1) / len(pages) * 100)
                logger.info(
                    f"[{self.agent_name}] Generated material for page {page_no}/{len(pages)} ({progress}%)"
                )

            # 4. 保存到上下文
            ctx.session.state["content_material"] = content_material_list

            # 5. 记录统计信息
            await self._record_generation_stats()

            logger.info(
                f"[{self.agent_name}] Content material generation completed: {len(content_material_list)} pages "
                f"(shared_research={self.stats['shared_research_used']}, "
                f"cache_hits={self.stats['cache_hits']}, "
                f"new_generation={self.stats['new_generation']})"
            )

            # 6. 产生完成事件
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[types.Part(
                        text=f"内容素材生成完成（带记忆）：\n"
                        f"- 生成页面数: {len(content_material_list)}\n"
                        f"- 共享研究使用: {self.stats['shared_research_used']}\n"
                        f"- 缓存命中: {self.stats['cache_hits']}\n"
                        f"- 新生成: {self.stats['new_generation']}\n"
                        f"- 包含图表: {sum(1 for m in content_material_list if m.get('has_chart'))}页\n"
                        f"- 包含配图: {sum(1 for m in content_material_list if m.get('has_image'))}页"
                    )]
                ),
            )

        except Exception as e:
            logger.error(f"[{self.agent_name}] failed: {e}", exc_info=True)
            # 降级到父类逻辑
            async for event in super()._run_async_impl(ctx):
                yield event

    async def _generate_page_material_with_memory(
        self,
        ctx,
        page: Dict[str, Any],
        page_index: int,
        shared_research: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        生成单个页面的内容素材（带记忆）

        Args:
            ctx: 调用上下文
            page: 页面信息
            page_index: 页面索引
            shared_research: 共享的研究结果
            user_preferences: 用户偏好

        Returns:
            页面素材字典
        """
        page_no = page.get("page_no", page_index + 1)
        page_title = page.get("title", "")
        page_type = page.get("page_type", "content")
        core_content = page.get("core_content", "")
        is_need_chart = page.get("is_need_chart", False)
        is_need_research = page.get("is_need_research", False)
        is_need_image = page.get("is_need_image", False)
        content_type = page.get("content_type", "text_only")
        keywords = page.get("keywords", [])

        # 使用共享研究（如果可用）
        research_content = ""
        if shared_research and is_need_research:
            research_content = shared_research.get("content", "")
            self.stats["shared_research_used"] += 1
            logger.info(f"[{self.agent_name}] 使用共享研究: {page_title}")

            await self.record_decision(
                decision_type="content_generation",
                selected_action="use_shared_research",
                context={
                    "page_title": page_title,
                    "research_source": shared_research.get("source", "unknown"),
                },
                reasoning="使用工作空间中的共享研究结果",
                confidence_score=0.85,
            )

        # 应用用户偏好
        if user_preferences:
            content_style = user_preferences.get("style_preference", "专业")
            # 可以根据风格调整内容生成
            if content_style == "活泼":
                # 调整内容风格
                pass
            elif content_style == "专业":
                # 使用专业风格
                pass

        # 生成页面素材
        page_material = await self._generate_page_material_async(
            page_no=page_no,
            page_title=page_title,
            page_type=page_type,
            core_content=core_content,
            research_content=research_content,
            is_need_chart=is_need_chart,
            is_need_image=is_need_image,
            content_type=content_type,
            keywords=keywords,
        )

        self.stats["new_generation"] += 1

        return page_material

    async def _check_content_cache(
        self,
        page_title: str,
        page: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        检查内容缓存

        Args:
            page_title: 页面标题
            page: 页面信息

        Returns:
            缓存的内容素材，如果过期或不存在返回None
        """
        cache_key = self._generate_content_cache_key(page_title, page)

        cached_material = await self.recall(
            key=cache_key,
            scope="USER",
            scope_id="content_cache",
        )

        if not cached_material:
            self.stats["cache_misses"] += 1
            return None

        # 检查是否过期
        cached_at_str = cached_material.get("cached_at")
        if cached_at_str:
            from datetime import datetime, timedelta

            try:
                cached_at = datetime.fromisoformat(cached_at_str)
                age_hours = (datetime.now() - cached_at).total_seconds() / 3600

                if age_hours < self.content_cache_ttl_hours:
                    logger.info(
                        f"[{self.agent_name}] 使用缓存内容: {page_title} (缓存{age_hours:.1f}小时)"
                    )
                    self.stats["cache_hits"] += 1

                    await self.record_decision(
                        decision_type="content_reuse",
                        selected_action="use_cached_content",
                        context={"page_title": page_title, "age_hours": age_hours},
                        reasoning=f"使用{age_hours:.1f}小时前的缓存内容",
                        confidence_score=0.9,
                    )

                    return cached_material
                else:
                    # 删除过期缓存
                    await self.forget(
                        key=cache_key, scope="USER", scope_id="content_cache"
                    )
            except ValueError as e:
                logger.warning(f"Failed to parse cache date: {e}")

        self.stats["cache_misses"] += 1
        return None

    async def _cache_content_material(
        self,
        page_title: str,
        material: Dict[str, Any],
    ):
        """
        缓存生成的内容素材

        Args:
            page_title: 页面标题
            material: 内容素材字典
        """
        from datetime import datetime

        cache_key = self._generate_content_cache_key(page_title, material)

        # 添加缓存元数据
        material["cached_at"] = datetime.now().isoformat()
        material["page_title"] = page_title

        await self.remember(
            key=cache_key,
            value=material,
            importance=0.6,
            scope="USER",
            scope_id="content_cache",
            tags=["content", "cache", page_title],
        )

        logger.debug(f"[{self.agent_name}] 内容已缓存: {page_title}")

    def _generate_content_cache_key(
        self,
        page_title: str,
        page_or_material: Dict[str, Any],
    ) -> str:
        """
        生成内容缓存键

        Args:
            page_title: 页面标题
            page_or_material: 页面信息或素材字典

        Returns:
            缓存键
        """
        import hashlib

        # 提取关键特征
        core_content = page_or_material.get("core_content", "")
        content_type = page_or_material.get("content_type", "text_only")

        # 组合特征
        combined = f"{page_title}:{core_content}:{content_type}"

        # 生成哈希
        hash_obj = hashlib.md5(combined.encode("utf-8"))
        return f"content_{hash_obj.hexdigest()}"

    def _setup_context(self, ctx):
        """设置上下文信息"""
        task_id = ctx.session.state.get("task_id")
        user_id = ctx.session.state.get("user_id", "anonymous")

        self.set_context(
            task_id=task_id,
            user_id=user_id,
            session_id=task_id,
        )

    async def _record_generation_stats(self):
        """记录生成统计信息"""
        await self.remember(
            key="content_generation_stats",
            value=self.stats,
            importance=0.3,
            scope="TASK",
            tags=["stats", "content"],
        )


# 创建全局实例
content_material_agent_with_memory = ContentMaterialAgentWithMemory(
    before_agent_callback=before_agent_callback
)


if __name__ == "__main__":
    # 测试代码
    async def test_agent():
        import asyncio

        agent = content_material_agent_with_memory

        print(f"Testing {agent.__class__.__name__}")
        print("=" * 60)
        print(f"Agent name: {agent.name}")
        print(f"Memory enabled: {agent.is_memory_enabled()}")
        print(f"Content cache: {agent.enable_content_cache}")
        print(f"Cache TTL: {agent.content_cache_ttl_hours} hours")

    asyncio.run(test_agent())
