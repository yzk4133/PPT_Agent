"""
Research Agent with Memory Integration

将记忆系统集成到研究智能体中，实现：
1. 研究结果缓存（避免重复研究）
2. 跨Agent共享研究成果
3. 决策记录和追踪
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List

from google.adk.agents import ParallelAgent
from google.adk.agents.invocation_context import InvocationContext
from google.genai import types
from google.adk.events.event import Event

# 导入基础研究Agent
from .research_agent import OptimizedResearchAgent, research_agent_before_model_callback

# 导入记忆适配器
from ..base_agent_with_memory import AgentMemoryMixin

logger = logging.getLogger(__name__)

class ResearchAgentWithMemory(AgentMemoryMixin, OptimizedResearchAgent):
    """
    带记忆功能的研究智能体

    扩展功能:
    1. 研究结果缓存：相同主题的研究结果会被缓存7天
    2. 共享工作空间：研究结果自动共享给ContentMaterialAgent
    3. 决策记录：记录每次研究的决策过程
    4. 向量检索：支持语义相似的研究结果复用
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 配置 - 使用 object.__setattr__ 避免 Pydantic 的字段检查
        object.__setattr__(self, 'research_cache_ttl_days', int(os.getenv("RESEARCH_CACHE_TTL_DAYS", "7")))
        object.__setattr__(self, 'enable_semantic_search', os.getenv("ENABLE_SEMANTIC_SEARCH", "true").lower() == "true")

        # 统计信息
        object.__setattr__(self, 'stats', {
            "cache_hits": 0,
            "cache_misses": 0,
            "shared_reuse": 0,
            "new_research": 0,
        })

        logger.info(
            f"[{self.agent_name}] 初始化完成: "
            f"cache_ttl={self.research_cache_ttl_days}天, "
            f"semantic={self.enable_semantic_search}"
        )

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> Any:
        """
        执行研究任务（带记忆）

        覆盖父类方法，添加记忆逻辑
        """
        # 设置上下文
        self._setup_context(ctx)

        try:
            # 1. 获取框架
            framework_dict = ctx.session.state.get("ppt_framework")
            if not framework_dict:
                logger.warning("No ppt_framework found, skipping research")
                ctx.session.state["research_results"] = []
                yield Event(
                    author=self.name,
                    content=types.Content(
                        parts=[types.Part(text="无需研究资料")]
                    ),
                )
                return

            # 2. 提取需要研究的页面
            research_page_indices = framework_dict.get("research_page_indices", [])
            pages = framework_dict.get("ppt_framework", [])

            if not research_page_indices:
                logger.info("No pages marked for research")
                ctx.session.state["research_results"] = []
                yield Event(
                    author=self.name,
                    content=types.Content(
                        parts=[types.Part(text="框架中无需研究资料的页面")]
                    ),
                )
                return

            research_pages = [p for p in pages if p.get("is_need_research", False)]

            if not research_pages:
                logger.info("No research pages found after filtering")
                ctx.session.state["research_results"] = []
                yield Event(
                    author=self.name,
                    content=types.Content(
                        parts=[types.Part(text="没有需要研究资料的页面")]
                    ),
                )
                return

            logger.info(f"Found {len(research_pages)} pages requiring research")

            # 3. 为每个页面执行研究（带缓存）
            research_results = []
            for page in research_pages:
                result = await self._research_page_with_memory(page, ctx)
                if result:
                    research_results.append(result)

            # 4. 保存结果到上下文
            ctx.session.state["research_results"] = research_results

            # 5. 记录统计信息
            await self._record_research_stats()

            logger.info(
                f"Research completed: {len(research_results)} pages "
                f"(cache_hits={self.stats['cache_hits']}, "
                f"shared_reuse={self.stats['shared_reuse']}, "
                f"new_research={self.stats['new_research']})"
            )

            # 6. 产生完成事件
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[types.Part(
                        text=f"资料研究完成：\n"
                        f"- 研究页面数: {len(research_results)}\n"
                        f"- 缓存命中: {self.stats['cache_hits']}\n"
                        f"- 共享复用: {self.stats['shared_reuse']}\n"
                        f"- 新研究: {self.stats['new_research']}\n"
                        f"- 研究结果已整理"
                    )]
                ),
            )

        except Exception as e:
            logger.error(f"ResearchAgent with memory failed: {e}", exc_info=True)
            ctx.session.state["research_results"] = []
            yield Event(
                author=self.name,
                content=types.Content(
                    parts=[types.Part(text=f"研究失败: {str(e)}")]
                ),
            )

    async def _research_page_with_memory(
        self,
        page: Dict[str, Any],
        ctx: InvocationContext,
    ) -> Optional[Dict[str, Any]]:
        """
        研究单个页面（带记忆）

        流程:
        1. 检查L1/L2/L3缓存
        2. 检查共享工作空间
        3. 执行新研究
        4. 存入缓存和共享空间

        Args:
            page: 页面信息
            ctx: 调用上下文

        Returns:
            研究结果字典
        """
        page_no = page.get("page_no", 1)
        page_title = page.get("title", "")
        keywords = page.get("keywords", [])
        core_content = page.get("core_content", "")

        # 生成缓存键
        cache_key = self._generate_cache_key(page_title, keywords)

        # ========== 1. 检查缓存 ==========
        cached_research = await self._check_research_cache(cache_key, page_title)
        if cached_research:
            return cached_research

        # ========== 2. 检查共享工作空间 ==========
        shared_research = await self.get_shared_data(
            data_type="research_result",
            data_key=page_title,
        )
        if shared_research:
            logger.info(f"[{self.agent_name}] 使用共享研究: {page_title}")
            self.stats["shared_reuse"] += 1

            await self.record_decision(
                decision_type="research_reuse",
                selected_action="use_shared_research",
                context={
                    "page_title": page_title,
                    "source": shared_research.get("source", "unknown"),
                },
                reasoning="使用其他Agent共享的研究结果",
                confidence_score=0.85,
            )

            return shared_research

        # ========== 3. 执行新研究 ==========
        logger.info(f"[{self.agent_name}] 执行新研究: {page_title}")

        await self.record_decision(
            decision_type="research_execution",
            selected_action="perform_new_research",
            context={
                "page_title": page_title,
                "keywords": keywords,
                "cache_key": cache_key,
            },
            reasoning="无缓存数据，执行新研究",
            confidence_score=1.0,
        )

        # 执行实际研究
        research_result = await self._perform_research_internal(
            page_no=page_title,
            page_title=page_title,
            core_content=core_content,
            keywords=keywords,
            ctx=ctx,
        )

        # 添加缓存元数据
        research_result["cached_at"] = datetime.now().isoformat()
        research_result["page_title"] = page_title
        research_result["keywords"] = keywords
        research_result["cache_key"] = cache_key

        # ========== 4. 存入缓存 ==========
        await self.remember(
            key=cache_key,
            value=research_result,
            importance=0.8,
            scope="USER",
            scope_id="research_cache",
            tags=["research", "cache", page_title],
        )

        self.stats["new_research"] += 1

        # ========== 5. 共享到工作空间 ==========
        await self.share_data(
            data_type="research_result",
            data_key=page_title,
            data_content=research_result,
            target_agents=["ContentMaterialAgent", "TemplateRendererAgent"],
            ttl_minutes=180,  # 3小时有效期
        )

        logger.info(f"[{self.agent_name}] 研究完成并缓存: {page_title}")

        return research_result

    async def _check_research_cache(
        self,
        cache_key: str,
        page_title: str,
    ) -> Optional[Dict[str, Any]]:
        """
        检查研究缓存

        Args:
            cache_key: 缓存键
            page_title: 页面标题

        Returns:
            缓存的研究结果，如果过期或不存在返回None
        """
        cached_research = await self.recall(
            key=cache_key,
            scope="USER",
            scope_id="research_cache",
        )

        if not cached_research:
            return None

        # 检查是否过期
        cached_at_str = cached_research.get("cached_at")
        if cached_at_str:
            try:
                cached_at = datetime.fromisoformat(cached_at_str)
                age_days = (datetime.now() - cached_at).days

                if age_days < self.research_cache_ttl_days:
                    logger.info(
                        f"[{self.agent_name}] 使用缓存研究: {page_title} (缓存{age_days}天)"
                    )
                    self.stats["cache_hits"] += 1

                    await self.record_decision(
                        decision_type="research_reuse",
                        selected_action="use_cached_research",
                        context={"page_title": page_title, "age_days": age_days},
                        reasoning=f"使用{age_days}天前的缓存研究，节省API调用",
                        confidence_score=0.9,
                    )

                    return cached_research
                else:
                    logger.info(
                        f"[{self.agent_name}] 缓存过期: {page_title} (缓存{age_days}天)"
                    )
                    # 删除过期缓存
                    await self.forget(key=cache_key, scope="USER", scope_id="research_cache")
            except ValueError as e:
                logger.warning(f"Failed to parse cache date: {e}")

        self.stats["cache_misses"] += 1
        return None

    async def _perform_research_internal(
        self,
        page_no: int,
        page_title: str,
        core_content: str,
        keywords: List[str],
        ctx: InvocationContext,
    ) -> Dict[str, Any]:
        """
        执行实际研究（内部方法）

        复用父类的research_single_page方法

        Args:
            page_no: 页码
            page_title: 页面标题
            core_content: 核心内容
            keywords: 关键词
            ctx: 调用上下文

        Returns:
            研究结果字典
        """
        # 使用父类的单页研究方法
        result = await self.research_single_page(
            page_no=page_no,
            page_title=page_title,
            keywords=keywords,
            core_content=core_content,
        )

        return result

    def _generate_cache_key(self, page_title: str, keywords: List[str]) -> str:
        """
        生成缓存键

        Args:
            page_title: 页面标题
            keywords: 关键词列表

        Returns:
            缓存键
        """
        import hashlib

        # 组合标题和关键词
        combined = f"{page_title}:{','.join(sorted(keywords))}"

        # 生成哈希
        hash_obj = hashlib.md5(combined.encode("utf-8"))
        return f"research_{hash_obj.hexdigest()}"

    def _setup_context(self, ctx: InvocationContext):
        """设置上下文信息"""
        task_id = ctx.session.state.get("task_id")
        user_id = ctx.session.state.get("user_id", "anonymous")

        self.set_context(
            task_id=task_id,
            user_id=user_id,
            session_id=task_id,
        )

    async def _record_research_stats(self):
        """记录研究统计信息"""
        await self.remember(
            key="research_stats",
            value=self.stats,
            importance=0.3,
            scope="TASK",
            tags=["stats", "research"],
        )

# 创建全局实例
research_agent_with_memory = ResearchAgentWithMemory(
    name="ResearchAgentWithMemory",
    description="带记忆功能的研究智能体，支持缓存和共享"
)

if __name__ == "__main__":
    # 测试代码
    async def test_agent():
        import asyncio

        agent = research_agent_with_memory

        print(f"Testing {agent.__class__.__name__}")
        print("=" * 60)
        print(f"Agent name: {agent.name}")
        print(f"Memory enabled: {agent.is_memory_enabled()}")
        print(f"Cache TTL: {agent.research_cache_ttl_days} days")
        print(f"Semantic search: {agent.enable_semantic_search}")

        # 测试缓存键生成
        cache_key = agent._generate_cache_key(
            page_title="AI技术趋势",
            keywords=["AI", "技术", "趋势"]
        )
        print(f"Generated cache key: {cache_key}")

    asyncio.run(test_agent())
