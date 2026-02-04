"""
Presentation Service

演示文稿服务，负责PPT生成的业务编排。

Updated to support the new "1 Master + 5 Sub" architecture.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from domain.models import (
    Presentation,
    PresentationRequest,
    PresentationStatus,
    TopicList,
    ResearchResults,
    SlideList
)
from domain.interfaces import IAgentFactory, IIAgentContext


logger = logging.getLogger(__name__)


class PresentationService:
    """
    演示文稿服务

    负责协调各个Agent完成PPT生成的完整流程。

    支持两种架构模式：
    1. 传统3阶段架构（向后兼容）
    2. 新"1主5子"架构（推荐）
    """

    def __init__(
        self,
        agent_factory: IAgentFactory,
        user_preference_service=None,
        use_master_coordinator: bool = True
    ):
        """
        初始化演示文稿服务

        Args:
            agent_factory: Agent工厂
            user_preference_service: 用户偏好服务（可选）
            use_master_coordinator: 是否使用新的主协调智能体架构（默认True）
        """
        self.agent_factory = agent_factory
        self.user_preference_service = user_preference_service
        self.use_master_coordinator = use_master_coordinator

        # 延迟导入主协调智能体
        self._master_coordinator = None
        if use_master_coordinator:
            try:
                from agents.orchestrator.agents.master_coordinator import master_coordinator_agent
                self._master_coordinator = master_coordinator_agent
                logger.info("Using Master Coordinator architecture")
            except ImportError as e:
                logger.warning(f"Master Coordinator not available: {e}, falling back to legacy mode")
                self.use_master_coordinator = False

    async def create_presentation(
        self,
        request: PresentationRequest,
        session_id: Optional[str] = None
    ) -> Presentation:
        """
        创建演示文稿

        Args:
            request: 演示文稿生成请求
            session_id: 会话ID（可选）

        Returns:
            Presentation实例
        """
        # 生成演示文稿ID
        presentation_id = f"ppt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.user_id}"

        # 创建演示文稿实例
        presentation = Presentation(
            id=presentation_id,
            title=self._extract_title(request.outline),
            outline=request.outline,
            status=PresentationStatus.DRAFT
        )

        # 创建上下文
        context = IAgentContext(
            session_id=session_id or presentation_id,
            user_id=request.user_id,
            state={
                "numSlides": request.num_slides,
                "language": request.language,
                "metadata": request.metadata
            }
        )

        # 加载用户偏好（如果可用）
        if self.user_preference_service:
            await self._load_user_preferences(context)

        return presentation

    async def generate_presentation(
        self,
        presentation: Presentation,
        context: IAgentContext
    ) -> Presentation:
        """
        生成演示文稿

        执行完整的三阶段生成流程：
        1. 主题拆分
        2. 并行研究
        3. PPT生成

        Args:
            presentation: 演示文稿实例
            context: Agent上下文

        Returns:
            更新后的Presentation实例
        """
        try:
            presentation.mark_generating()
            logger.info(f"开始生成演示文稿: {presentation.id}")

            # Stage 1: 主题拆分
            logger.info("Stage 1: 主题拆分...")
            topics = await self._stage1_split_topics(presentation, context)
            presentation.topics = topics
            logger.info(f"Stage 1 完成，拆分出 {topics.total_count} 个主题")

            # Stage 2: 并行研究
            logger.info("Stage 2: 并行研究...")
            research_results = await self._stage2_parallel_research(
                presentation, context, topics
            )
            presentation.research_results = research_results
            logger.info(f"Stage 2 完成，成功研究 {research_results.success_count} 个主题")

            # Stage 3: PPT生成
            logger.info("Stage 3: PPT生成...")
            await self._stage3_generate_ppt(
                presentation, context, research_results
            )
            logger.info("Stage 3 完成")

            presentation.mark_completed()
            logger.info(f"演示文稿生成完成: {presentation.id}")

        except Exception as e:
            logger.error(f"演示文稿生成失败: {e}")
            presentation.mark_failed()
            raise

        return presentation

    async def _load_user_preferences(self, context: IAgentContext) -> None:
        """
        加载用户偏好

        Args:
            context: Agent上下文
        """
        try:
            user_prefs = await self.user_preference_service.get_user_preferences(
                context.user_id, create_if_not_exists=True
            )

            # 合并用户偏好到上下文
            for key, value in user_prefs.items():
                if key not in context.state or context.state[key] is None:
                    context.state[key] = value

            logger.info(f"加载用户偏好: {context.user_id}")

        except Exception as e:
            logger.warning(f"加载用户偏好失败: {e}")

    async def _stage1_split_topics(
        self,
        presentation: Presentation,
        context: IAgentContext
    ) -> TopicList:
        """
        Stage 1: 主题拆分

        Args:
            presentation: 演示文稿实例
            context: Agent上下文

        Returns:
            TopicList实例
        """
        # 使用Agent工厂创建主题拆分Agent
        agent = self.agent_factory.create_topic_splitter(
            config=None  # 使用默认配置
        )

        # 调用Agent拆分主题
        result = await agent.run(context, presentation.outline)

        # 解析结果
        from domain.models import TopicList
        topic_list = TopicList.from_dict({
            "topics": result.content if isinstance(result.content, list) else []
        })

        return topic_list

    async def _stage2_parallel_research(
        self,
        presentation: Presentation,
        context: IAgentContext,
        topics: TopicList
    ) -> ResearchResults:
        """
        Stage 2: 并行研究

        Args:
            presentation: 演示文稿实例
            context: Agent上下文
            topics: 主题列表

        Returns:
            ResearchResults实例
        """
        # 使用Agent工厂创建研究Agent
        agent = self.agent_factory.create_research_agent(
            config=None  # 使用默认配置
        )

        # 将主题列表转换为字典格式
        topics_dict = [topic.to_dict() for topic in topics.topics]

        # 调用Agent进行并行研究
        research_contents = await agent.research_topics_parallel(
            context, topics_dict
        )

        # 创建研究结果
        from domain.models import ResearchResults, ResearchResult, ResearchStatus
        results = ResearchResults()

        for i, content in enumerate(research_contents):
            result = ResearchResult(
                topic_id=topics.topics[i].id,
                topic_title=topics.topics[i].title,
                content=content,
                status=ResearchStatus.COMPLETED
            )
            results.add_result(result)

        return results

    async def _stage3_generate_ppt(
        self,
        presentation: Presentation,
        context: IAgentContext,
        research_results: ResearchResults
    ) -> None:
        """
        Stage 3: PPT生成

        Args:
            presentation: 演示文稿实例
            context: Agent上下文
            research_results: 研究结果
        """
        # 使用Agent工厂创建幻灯片写入Agent
        agent = self.agent_factory.create_slide_writer(
            config=None  # 使用默认配置
        )

        # 提取研究内容
        research_contents = [r.content for r in research_results.results]

        # 生成完整演示文稿
        ppt_content = await agent.generate_presentation(context, research_contents)

        # 保存生成的内容
        presentation.generated_content = ppt_content
        presentation.slides = SlideList()  # 可以进一步解析XML创建Slide对象

    def _extract_title(self, outline: str) -> str:
        """
        从大纲中提取标题

        Args:
            outline: 大纲内容

        Returns:
            提取的标题
        """
        # 简单提取第一行作为标题
        lines = outline.strip().split('\n')
        return lines[0][:50] if lines else "未命名演示文稿"


# 便捷函数
async def create_presentation_from_request(
    request: PresentationRequest,
    agent_factory: IAgentFactory,
    user_preference_service=None
) -> Presentation:
    """
    从请求创建演示文稿的便捷函数

    Args:
        request: 演示文稿请求
        agent_factory: Agent工厂
        user_preference_service: 用户偏好服务

    Returns:
        Presentation实例
    """
    service = PresentationService(agent_factory, user_preference_service)
    presentation = await service.create_presentation(request)

    # 创建上下文
    context = IAgentContext(
        session_id=presentation.id,
        user_id=request.user_id
    )

    # 生成演示文稿
    presentation = await service.generate_presentation(presentation, context)

    return presentation


if __name__ == "__main__":
    # 测试代码
    from domain.models import PresentationRequest

    request = PresentationRequest(
        outline="人工智能的发展历程和应用",
        num_slides=10,
        language="EN-US"
    )

    print(f"Request: {request.to_dict()}")
