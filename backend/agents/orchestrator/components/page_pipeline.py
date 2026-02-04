"""
Page Pipeline Executor

Implements page-level pipeline parallel execution for research and content generation.
"""

import asyncio
import logging
import sys
import os
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

# Add parent directories to path

from google.adk.agents.invocation_context import InvocationContext
from domain.models.page_state import (
    PageState,
    PageStateManager,
    PagePipelineConfig,
    PagePipelineResult,
    PageStatus
)
from domain.models.framework import PPTFramework, PageDefinition

logger = logging.getLogger(__name__)

class PagePipeline:
    """
    页面级流水线并行执行器

    实现页面级流水线并行，让每个页面的Research和Content可以同时进行。

    架构:
        当前: Research(所有页) → Content(所有页)  [串行]
        目标:
          Page1: Research ─────────────────→ Content
          Page2:    Research ──────────────→ Content
          Page3:      Research ───────────→ Content
          [流水线并行]

    使用示例:
        pipeline = PagePipeline(
            research_agent=research_agent,
            content_agent=content_agent,
            config=PagePipelineConfig(max_concurrency=3)
        )

        results = await pipeline.execute_pages(
            framework=framework,
            ctx=ctx,
            progress_callback=progress_callback
        )
    """

    def __init__(
        self,
        research_agent,
        content_agent,
        config: Optional[PagePipelineConfig] = None
    ):
        """
        初始化页面流水线

        Args:
            research_agent: 研究智能体（需实现 research_single_page 方法）
            content_agent: 内容生成智能体（需实现 generate_single_page 方法）
            config: 流水线配置
        """
        self.research_agent = research_agent
        self.content_agent = content_agent
        self.config = config or PagePipelineConfig()
        logger.info(f"PagePipeline initialized: max_concurrency={self.config.max_concurrency}")

    async def execute_pages(
        self,
        framework: PPTFramework,
        ctx: InvocationContext,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        流水线执行所有页面

        Args:
            framework: PPT框架
            ctx: 调用上下文
            progress_callback: 进度回调函数

        Returns:
            内容素材列表
        """
        start_time = datetime.now()
        total_pages = len(framework.pages)

        # 初始化状态管理器
        state_manager = PageStateManager(total_pages=total_pages)
        logger.info(f"Starting page pipeline: {total_pages} pages")

        # 信号量控制并发
        semaphore = asyncio.Semaphore(self.config.max_concurrency)

        # 收集所有任务结果
        content_materials = [None] * total_pages
        errors = []

        # 进度追踪
        completed_pages = 0

        async def process_page(page: PageDefinition) -> Optional[Dict[str, Any]]:
            """处理单个页面（研究 + 内容生成）"""
            page_no = page.page_no
            state = state_manager.get_state(page_no)

            async with semaphore:
                try:
                    logger.info(f"Processing page {page_no}/{total_pages}: {page.title}")

                    # 步骤1: 研究（如果需要）
                    research_result = None
                    if page.is_need_research and self.config.enable_research:
                        state.mark_researching()
                        state_manager.set_state(page_no, state)

                        if progress_callback:
                            progress = state_manager.get_overall_progress()
                            progress_callback(progress * 0.3 + 30)  # 30% → 60% range

                        research_result = await self._research_single_page(
                            ctx=ctx,
                            page=page
                        )

                        state.update_research_progress(100)
                        state_manager.set_state(page_no, state)

                        logger.info(f"Research completed for page {page_no}")

                    # 步骤2: 内容生成
                    if self.config.enable_content_generation:
                        state.mark_content_generating()
                        state_manager.set_state(page_no, state)

                        content_material = await self._generate_content_single_page(
                            ctx=ctx,
                            page=page,
                            research_result=research_result
                        )

                        state.update_content_progress(100)
                        state.mark_completed()
                        state_manager.set_state(page_no, state)

                        # 更新进度
                        nonlocal completed_pages
                        completed_pages += 1
                        if progress_callback:
                            progress = state_manager.get_overall_progress()
                            progress_callback(progress * 0.5 + 50)  # 50% → 100% range

                        logger.info(f"Content generated for page {page_no} ({completed_pages}/{total_pages})")
                        return content_material
                    else:
                        state.mark_skipped("Content generation disabled")
                        return None

                except Exception as e:
                    error_msg = f"Page {page_no} failed: {str(e)}"
                    logger.error(error_msg)
                    state.mark_failed(error_msg)
                    state_manager.set_state(page_no, state)
                    errors.append(error_msg)
                    return None

        # 创建所有页面任务
        tasks = [
            process_page(page)
            for page in framework.pages
        ]

        # 并发执行所有页面
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Page {i+1} raised exception: {result}")
                errors.append(f"Page {i+1}: {str(result)}")
            elif result is not None:
                content_materials[i] = result

        # 过滤掉None值
        content_materials = [m for m in content_materials if m is not None]

        # 记录执行时间
        elapsed_time = (datetime.now() - start_time).total_seconds()

        logger.info(
            f"Page pipeline completed: "
            f"{len(content_materials)}/{total_pages} pages, "
            f"{elapsed_time:.1f}s, "
            f"{len(errors)} errors"
        )

        # 返回结果
        return content_materials

    async def _research_single_page(
        self,
        ctx: InvocationContext,
        page: PageDefinition
    ) -> Dict[str, Any]:
        """
        研究单个页面

        Args:
            ctx: 调用上下文
            page: 页面定义

        Returns:
            研究结果字典
        """
        # 检查research_agent是否有research_single_page方法
        if hasattr(self.research_agent, 'research_single_page'):
            return await self.research_agent.research_single_page(
                page_no=page.page_no,
                page_title=page.title,
                keywords=page.keywords or [],
                core_content=page.core_content
            )
        else:
            # 兼容旧版本：使用现有的并行研究机制
            logger.warning(
                f"Research agent does not have research_single_page method, "
                f"using fallback for page {page.page_no}"
            )
            return {
                "page_no": page.page_no,
                "page_title": page.title,
                "research_type": "未实现",
                "content": f"页面{page.page_no}的研究内容",
                "source": "",
                "data_points": [],
                "is_visualizable": False
            }

    async def _generate_content_single_page(
        self,
        ctx: InvocationContext,
        page: PageDefinition,
        research_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成单个页面的内容素材

        Args:
            ctx: 调用上下文
            page: 页面定义
            research_result: 研究结果（可选）

        Returns:
            内容素材字典
        """
        # 检查content_agent是否有generate_single_page方法
        if hasattr(self.content_agent, 'generate_single_page'):
            return await self.content_agent.generate_single_page(
                page=page,
                research_result=research_result
            )
        else:
            # 兼容旧版本：创建基本内容素材
            logger.warning(
                f"Content agent does not have generate_single_page method, "
                f"using fallback for page {page.page_no}"
            )
            return self._generate_fallback_content(page, research_result)

    def _generate_fallback_content(
        self,
        page: PageDefinition,
        research_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成fallback内容素材"""
        research_content = ""
        if research_result:
            research_content = research_result.get("content", "")

        return {
            "page_no": page.page_no,
            "page_title": page.title,
            "page_type": page.page_type.value if hasattr(page.page_type, 'value') else str(page.page_type),
            "content_text": f"{page.title}\n\n{page.core_content}\n\n{research_content}",
            "chart_data": None,
            "has_chart": page.is_need_chart,
            "image_suggestion": None,
            "has_image": page.is_need_image,
            "keywords": page.keywords or [],
            "content_type": page.content_type.value if hasattr(page.content_type, 'value') else str(page.content_type)
        }

    async def execute_with_progress_tracking(
        self,
        framework: PPTFramework,
        ctx: InvocationContext,
        progress_tracker
    ) -> PagePipelineResult:
        """
        执行并返回完整结果

        Args:
            framework: PPT框架
            ctx: 调用上下文
            progress_tracker: 进度追踪器

        Returns:
            PagePipelineResult对象
        """
        start_time = datetime.now()
        state_manager = PageStateManager(total_pages=len(framework.pages))

        # 定义进度回调
        def progress_callback(progress: float):
            """进度回调"""
            if progress_tracker:
                # 这里可以调用progress_tracker更新进度
                pass

        # 执行流水线
        try:
            content_materials = await self.execute_pages(
                framework=framework,
                ctx=ctx,
                progress_callback=progress_callback
            )
        except Exception as e:
            logger.error(f"Page pipeline execution failed: {e}")
            return PagePipelineResult(
                success=False,
                total_pages=len(framework.pages),
                completed_pages=0,
                failed_pages=len(framework.pages),
                skipped_pages=0,
                total_time=(datetime.now() - start_time).total_seconds(),
                page_states=state_manager.get_all_states(),
                errors=[str(e)]
            )

        # 创建结果
        elapsed_time = (datetime.now() - start_time).total_seconds()
        result = PagePipelineResult.from_manager(
            manager=state_manager,
            total_time=elapsed_time
        )

        # 更新completed_pages count
        result.completed_pages = len(content_materials)

        logger.info(f"Pipeline result: {result.to_dict()}")
        return result

# 创建全局实例
_global_pipeline: Optional[PagePipeline] = None

def get_page_pipeline() -> Optional[PagePipeline]:
    """获取全局PagePipeline实例"""
    return _global_pipeline

def set_page_pipeline(pipeline: PagePipeline) -> None:
    """设置全局PagePipeline实例"""
    global _global_pipeline
    _global_pipeline = pipeline

if __name__ == "__main__":
    # 测试代码
    import asyncio
    from domain.models.framework import PageType, ContentType

    async def test_page_pipeline():
        print("Testing PagePipeline")
        print("=" * 60)

        # 创建模拟框架
        pages = []
        for i in range(1, 11):
            page = PageDefinition(
                page_no=i,
                title=f"第{i}页",
                page_type=PageType.CONTENT,
                core_content=f"第{i}页的内容",
                is_need_chart=(i % 2 == 0),
                is_need_research=(i % 3 == 0),
                is_need_image=(i % 2 != 0),
                content_type=ContentType.TEXT_WITH_CHART if (i % 2 == 0) else ContentType.TEXT_ONLY,
                keywords=[f"关键词{i}"],
                estimated_word_count=100
            )
            pages.append(page)

        framework = PPTFramework(total_page=len(pages), pages=pages)

        # 创建模拟agent
        class MockResearchAgent:
            async def research_single_page(self, page_no, page_title, keywords, core_content):
                await asyncio.sleep(0.1)  # 模拟处理时间
                return {
                    "page_no": page_no,
                    "page_title": page_title,
                    "content": f"研究内容: {core_content}",
                    "source": "测试来源"
                }

        class MockContentAgent:
            async def generate_single_page(self, page, research_result=None):
                await asyncio.sleep(0.15)  # 模拟处理时间
                return {
                    "page_no": page.page_no,
                    "page_title": page.title,
                    "content_text": f"内容: {page.core_content}"
                }

        # 创建流水线
        config = PagePipelineConfig(max_concurrency=3)
        pipeline = PagePipeline(
            research_agent=MockResearchAgent(),
            content_agent=MockContentAgent(),
            config=config
        )

        # 执行
        print("\n1. Executing pipeline...")
        start = datetime.now()
        results = await pipeline.execute_pages(
            framework=framework,
            ctx=None,
            progress_callback=lambda p: print(f"   Progress: {p:.1f}%")
        )
        elapsed = (datetime.now() - start).total_seconds()

        print(f"\n2. Results:")
        print(f"   Generated {len(results)} pages")
        print(f"   Elapsed time: {elapsed:.2f}s")
        print(f"   Avg time per page: {elapsed/len(pages):.2f}s")

    asyncio.run(test_page_pipeline())
