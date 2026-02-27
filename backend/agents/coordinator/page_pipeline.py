"""
页面级流水线 - LangChain 实现

此模块处理研究和内容生成的并行页面级执行。
保持原架构的 30%-60% 性能优化。

关键特性：
- 使用 asyncio.Semaphore 进行并发控制的并行执行
- 失败页面的重试机制
- 进度跟踪
- 支持部分成功的错误处理
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from ..models.state import PPTGenerationState, update_state_progress
from ..models.framework import PPTFramework, PageDefinition

logger = logging.getLogger(__name__)


class PagePipeline:
    """
    页面级流水线 - 并行执行器

    功能：
    1. 并行执行页面级任务（研究、内容生成）
    2. 使用Semaphore控制并发数
    3. 重试失败的页面
    4. 追踪进度

    与原架构对比：
    - 原 Google ADK: PagePipeline components/page_pipeline.py
    - LangChain 版本: 保持相同的并行逻辑，但使用 LangChain 节点
    """

    def __init__(self, max_concurrency: int = 3, max_retries: int = 2, retry_delay: float = 1.0):
        """
        初始化页面流水线

        参数：
            max_concurrency: 最大并发数
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.max_concurrency = max_concurrency
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # 创建信号量
        self.semaphore = asyncio.Semaphore(max_concurrency)

        logger.info(
            f"[PagePipeline] Initialized: "
            f"max_concurrency={max_concurrency}, "
            f"max_retries={max_retries}"
        )

    async def execute_pages(
        self,
        pages: List[Dict[str, Any]],
        executor_func: Callable,
        progress_callback: Optional[Callable] = None,
    ) -> List[Dict[str, Any]]:
        """
        并行执行页面任务

        参数：
            pages: 页面定义列表
            executor_func: 执行函数，接收单个页面，返回结果
            progress_callback: 进度回调函数

        返回：
            执行结果列表
        """
        if not pages:
            logger.warning("[PagePipeline] No pages to execute")
            return []

        total_pages = len(pages)
        logger.info(
            f"[PagePipeline] Executing {total_pages} pages with max_concurrency={self.max_concurrency}"
        )

        # 创建任务
        tasks = []
        for page in pages:
            task = self._process_page_with_semaphore(
                page, executor_func, progress_callback, total_pages
            )
            tasks.append(task)

        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        successful_results = []
        failed_pages = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"[PagePipeline] Page {i+1} failed: {result}")
                failed_pages.append((pages[i], result))
            else:
                successful_results.append(result)

        logger.info(
            f"[PagePipeline] Completed: "
            f"{len(successful_results)}/{total_pages} pages successful, "
            f"{len(failed_pages)} failed"
        )

        return successful_results

    async def _process_page_with_semaphore(
        self,
        page: Dict[str, Any],
        executor_func: Callable,
        progress_callback: Optional[Callable],
        total_pages: int,
    ) -> Dict[str, Any]:
        """
        使用信号量控制并发的页面处理

        参数：
            page: 页面定义
            executor_func: 执行函数
            progress_callback: 进度回调
            total_pages: 总页数

        返回：
            执行结果
        """
        async with self.semaphore:
            return await self._process_page_with_retry(
                page, executor_func, progress_callback, total_pages
            )

    async def _process_page_with_retry(
        self,
        page: Dict[str, Any],
        executor_func: Callable,
        progress_callback: Optional[Callable],
        total_pages: int,
    ) -> Dict[str, Any]:
        """
        带重试的页面处理

        参数：
            page: 页面定义
            executor_func: 执行函数
            progress_callback: 进度回调
            total_pages: 总页数

        返回：
            执行结果

        引发：
            Exception: 如果所有重试都失败
        """
        page_no = page.get("page_no", 1)
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"[PagePipeline] Processing page {page_no}, attempt {attempt + 1}")

                # 执行任务
                result = await executor_func(page)

                # 调用进度回调
                if progress_callback:
                    await progress_callback(page_no, total_pages)

                return result

            except Exception as e:
                last_error = e
                logger.warning(
                    f"[PagePipeline] Page {page_no} failed on attempt {attempt + 1}: {e}"
                )

                if attempt < self.max_retries:
                    # 等待后重试
                    await asyncio.sleep(self.retry_delay)
                else:
                    # 最后一次尝试也失败了
                    logger.error(
                        f"[PagePipeline] Page {page_no} failed after {self.max_retries + 1} attempts"
                    )
                    raise

    async def execute_research_pipeline(
        self, state: PPTGenerationState, research_agent
    ) -> PPTGenerationState:
        """
        执行研究流水线

        参数：
            state: 当前状态
            research_agent: 研究智能体

        返回：
            更新后的状态
        """
        logger.info("[PagePipeline] Starting research pipeline")

        framework = state.get("ppt_framework", {})
        pages = framework.get("ppt_framework", [])
        research_indices = framework.get("research_page_indices", [])

        if not research_indices:
            logger.info("[PagePipeline] No pages need research")
            state["research_results"] = []
            return state

        # 筛选需要研究的页面
        pages_to_research = [p for p in pages if p.get("page_no") in research_indices]

        # 创建进度回调
        async def progress_callback(page_no: int, total: int):
            progress = 30 + (page_no / total) * 20  # 30% -> 50%
            update_state_progress(state, "research", int(progress))
            logger.debug(f"[PagePipeline] Research progress: {page_no}/{total} ({int(progress)}%)")

        # 执行研究
        results = await self.execute_pages(
            pages_to_research, research_agent.research_page, progress_callback
        )

        state["research_results"] = results

        logger.info(f"[PagePipeline] Research pipeline completed: {len(results)} pages")
        return state

    async def execute_content_pipeline(
        self, state: PPTGenerationState, content_agent
    ) -> PPTGenerationState:
        """
        执行内容生成流水线

        参数：
            state: 当前状态
            content_agent: 内容生成智能体

        返回：
            更新后的状态
        """
        logger.info("[PagePipeline] Starting content generation pipeline")

        framework = state.get("ppt_framework", {})
        pages = framework.get("ppt_framework", [])
        research_results = state.get("research_results", [])

        # 创建进度回调
        async def progress_callback(page_no: int, total: int):
            progress = 50 + (page_no / total) * 30  # 50% -> 80%
            update_state_progress(state, "content_generation", int(progress))
            logger.debug(f"[PagePipeline] Content progress: {page_no}/{total} ({int(progress)}%)")

        # 创建执行函数（绑定研究结果）
        async def generate_content(page: Dict[str, Any]) -> Dict[str, Any]:
            return await content_agent.generate_content_for_page(page, research_results)

        # 执行内容生成
        results = await self.execute_pages(pages, generate_content, progress_callback)

        state["content_materials"] = results

        logger.info(f"[PagePipeline] Content pipeline completed: {len(results)} pages")
        return state


# 工厂函数


def create_page_pipeline(
    max_concurrency: int = 3, max_retries: int = 2, retry_delay: float = 1.0
) -> PagePipeline:
    """
    创建页面流水线

    参数：
        max_concurrency: 最大并发数
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）

    返回：
        PagePipeline实例
    """
    return PagePipeline(
        max_concurrency=max_concurrency, max_retries=max_retries, retry_delay=retry_delay
    )


# 便捷函数


async def execute_page_pipeline(
    pages: List[Dict[str, Any]], executor_func: Callable, max_concurrency: int = 3
) -> List[Dict[str, Any]]:
    """
    直接执行页面流水线（便捷函数）

    参数：
        pages: 页面列表
        executor_func: 执行函数
        max_concurrency: 最大并发数

    返回：
        结果列表
    """
    pipeline = create_page_pipeline(max_concurrency=max_concurrency)
    return await pipeline.execute_pages(pages, executor_func)


if __name__ == "__main__":
    import asyncio

    async def test():
        # 测试页面流水线

        # 模拟页面列表
        test_pages = [
            {"page_no": 1, "title": "第1页"},
            {"page_no": 2, "title": "第2页"},
            {"page_no": 3, "title": "第3页"},
            {"page_no": 4, "title": "第4页"},
            {"page_no": 5, "title": "第5页"},
        ]

        # 模拟执行函数
        async def mock_executor(page: Dict[str, Any]) -> Dict[str, Any]:
            await asyncio.sleep(0.5)  # 模拟耗时操作
            return {"page_no": page["page_no"], "result": f"内容 for {page['title']}"}

        # 创建进度回调
        completed_count = [0]

        async def progress_callback(page_no: int, total: int):
            completed_count[0] += 1
            print(f"进度: {completed_count[0]}/{total} 页已完成")

        # 执行流水线
        start_time = datetime.now()

        pipeline = create_page_pipeline(max_concurrency=3)
        results = await pipeline.execute_pages(test_pages, mock_executor, progress_callback)

        elapsed = (datetime.now() - start_time).total_seconds()

        print(f"\n结果: {len(results)} 页在 {elapsed:.2f} 秒内完成")
        for result in results:
            print(f"  - 第 {result['page_no']} 页: {result['result']}")

    asyncio.run(test())
