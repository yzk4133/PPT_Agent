"""
扁平化 PPT 生成 Agent

3 阶段扁平化架构：
1. Stage 1: 主题拆分 (带 JSON 降级)
2. Stage 2: 并行研究 (带并发控制和部分成功处理)
3. Stage 3: 批量生成 PPT (带条件化质量检查)
"""

import os
import sys
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional, AsyncIterator

from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

# 导入基础设施
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from infrastructure.config import get_config
from infrastructure.llm import create_model_with_fallback
from infrastructure.llm.fallback import JSONFallbackParser, PartialSuccessHandler
from infrastructure.llm.retry_decorator import async_retry_with_fallback, RetryableError

# 从共享的 agents 模块导入（Phase 1 迁移）
from agents.core.planning.topic_splitter_agent import split_topic_agent
from agents.core.research.parallel_research_agent import parallel_search_agent
from agents.core.generation.slide_writer_agent import ppt_generator_loop_agent

# 导入用户偏好服务
try:
    from persistent_memory import UserPreferenceService
    user_pref_service = UserPreferenceService(enable_cache=True)
    PERSISTENT_MEMORY_AVAILABLE = True
except ImportError:
    user_pref_service = None
    PERSISTENT_MEMORY_AVAILABLE = False


logger = logging.getLogger(__name__)


class FlatPPTGenerationAgent(BaseAgent):
    """
    扁平化 PPT 生成 Agent
    
    核心改进：
    - 扁平化架构（3阶段而非4层嵌套）
    - 统一配置管理
    - 全面降级策略
    - 并发控制
    - 部分成功处理
    """
    
    def __init__(self, name: str = "FlatPPTGenerationAgent", **kwargs):
        super().__init__(name=name, **kwargs)
        # 使用 object.__setattr__ 避免 Pydantic 的字段检查
        config = get_config()
        object.__setattr__(self, 'config', config)
        object.__setattr__(self, '_semaphore', asyncio.Semaphore(config.research_agent.max_concurrency))
        logger.info(f" {name} initialized with flat architecture")
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncIterator[Event]:
        """
        主执行流程 - 3 阶段扁平化
        """
        try:
            # 加载用户偏好
            await self._load_user_preferences(ctx)
            
            # Stage 1: 主题拆分（带降级）
            yield Event(
                author=self.name,
                content=" 阶段1：正在拆分研究主题...",
                actions=EventActions()
            )
            topics = await self._stage1_split_topics(ctx)
            logger.info(f" Stage 1 完成，拆分出 {len(topics)} 个主题")
            
            # Stage 2: 并行研究（带并发控制）
            yield Event(
                author=self.name,
                content=f" 阶段2：正在并行研究 {len(topics)} 个主题...",
                actions=EventActions()
            )
            research_results = await self._stage2_parallel_research(ctx, topics)
            logger.info(f" Stage 2 完成，成功研究 {len(research_results)} 个主题")
            
            # Stage 3: 批量生成 PPT
            yield Event(
                author=self.name,
                content=" 阶段3：正在生成PPT...",
                actions=EventActions()
            )
            async for event in self._stage3_generate_ppt(ctx, research_results):
                yield event
            
            logger.info(" 所有阶段完成")
            
        except Exception as e:
            logger.error(f" FlatPPTGenerationAgent 执行失败: {e}")
            yield Event(
                author=self.name,
                content=f"生成失败: {str(e)}",
                actions=EventActions(escalate=True)
            )
    
    async def _load_user_preferences(self, ctx: InvocationContext):
        """加载用户偏好"""
        metadata = ctx.session.state.get("metadata", {})
        user_id = metadata.get("user_id", "anonymous")
        ctx.session.state["user_id"] = user_id
        
        if PERSISTENT_MEMORY_AVAILABLE and user_pref_service:
            try:
                user_prefs = await user_pref_service.get_user_preferences(
                    user_id, create_if_not_exists=True
                )
                merged_metadata = {**user_prefs, **metadata}
                slides_plan_num = merged_metadata.get("numSlides") or merged_metadata.get("default_slides", 10)
                language = merged_metadata.get("language", "EN-US")
                logger.info(f" 加载用户偏好: user={user_id}, slides={slides_plan_num}, lang={language}")
            except Exception as e:
                logger.warning(f"  加载用户偏好失败: {e}，使用默认值")
                slides_plan_num = metadata.get("numSlides", 10)
                language = metadata.get("language", "EN-US")
        else:
            slides_plan_num = metadata.get("numSlides", 10)
            language = metadata.get("language", "EN-US")
        
        ctx.session.state["slides_plan_num"] = slides_plan_num
        ctx.session.state["language"] = language
    
    async def _stage1_split_topics(self, ctx: InvocationContext) -> List[Dict]:
        """
        阶段1：主题拆分（带 JSON 降级策略）
        """
        # 调用原有的 split_topic_agent
        events = []
        async for event in split_topic_agent.run_async(ctx):
            events.append(event)
        
        # 提取 split_topics 输出
        topics_output = ctx.session.state.get("split_topics", "")
        
        # 使用降级策略解析 JSON
        parse_result = JSONFallbackParser.parse_with_fallback(
            topics_output,
            default_structure={"topics": [{"id": 1, "title": "General Topic", "keywords": []}]}
        )
        
        if not parse_result.success:
            logger.error(f" JSON 解析完全失败: {parse_result.error}")
            return [{"id": 1, "title": "General Topic", "keywords": []}]
        
        if parse_result.level != "primary":
            logger.warning(f"  使用降级策略: {parse_result.level}")
        
        topics = parse_result.data.get("topics", [])
        return topics
    
    async def _stage2_parallel_research(
        self, 
        ctx: InvocationContext, 
        topics: List[Dict]
    ) -> List[str]:
        """
        阶段2：并行研究（带并发控制和部分成功处理）
        """
        # 将 topics 存回 state
        ctx.session.state["split_topics"] = json.dumps({"topics": topics})
        
        # 调用原有的 parallel_search_agent（内部会处理并发）
        async for event in parallel_search_agent.run_async(ctx):
            pass  # 只关注最终结果
        
        # 提取研究结果
        research_outputs = ctx.session.state.get("research_outputs", [])
        
        # 使用部分成功处理
        results_with_status = [
            (True, output) if output and output.strip() else (False, None)
            for output in research_outputs
        ]
        
        partial_result = PartialSuccessHandler.handle_parallel_results(
            results_with_status,
            min_success_rate=0.5  # 至少50%成功
        )
        
        if not partial_result.success:
            logger.error(f" 研究失败率过高: {partial_result.metadata}")
            raise RetryableError("研究任务成功率低于阈值")
        
        if partial_result.level != "primary":
            logger.warning(f"  部分研究失败: {partial_result.metadata}")
        
        return partial_result.data
    
    async def _stage3_generate_ppt(
        self, 
        ctx: InvocationContext, 
        research_results: List[str]
    ) -> AsyncIterator[Event]:
        """
        阶段3：批量生成 PPT（带条件化质量检查）
        """
        # 将研究结果存回 state
        ctx.session.state["research_outputs"] = research_results
        ctx.session.state["research_outputs_content"] = "\\n\\n".join(research_results)
        
        # 检查是否启用质量检查
        enable_check = self.config.features.enable_quality_check
        ctx.session.state["enable_quality_check"] = enable_check
        
        if not enable_check:
            logger.info("ℹ  质量检查已禁用，将直接生成")
        
        # 调用原有的 ppt_generator_loop_agent
        async for event in ppt_generator_loop_agent.run_async(ctx):
            yield event


def before_agent_callback(callback_context: CallbackContext) -> None:
    """
    兼容原有的回调（用于非扁平化模式）
    """
    metadata = callback_context.state.get("metadata", {})
    slides_plan_num = metadata.get("numSlides", 10)
    language = metadata.get("language", "EN-US")
    callback_context.state["slides_plan_num"] = slides_plan_num
    callback_context.state["language"] = language
    return None


# 创建全局实例
flat_root_agent = FlatPPTGenerationAgent(
    name="FlatPPTGenerationAgent",
    description="扁平化架构的 PPT 生成 Agent（3阶段）"
)

