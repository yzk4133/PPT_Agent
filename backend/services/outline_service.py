"""
Outline Service

大纲服务，负责大纲生成的业务编排
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from domain.interfaces import IAgentFactory, AgentContext, AgentResult


logger = logging.getLogger(__name__)


class OutlineService:
    """
    大纲服务

    负责协调Agent完成大纲生成任务。
    """

    def __init__(
        self,
        agent_factory: IAgentFactory,
        user_preference_service=None
    ):
        """
        初始化大纲服务

        Args:
            agent_factory: Agent工厂
            user_preference_service: 用户偏好服务（可选）
        """
        self.agent_factory = agent_factory
        self.user_preference_service = user_preference_service

    async def generate_outline(
        self,
        topic: str,
        user_id: str = "anonymous",
        language: str = "EN-US",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        生成大纲

        Args:
            topic: 主题
            user_id: 用户ID
            language: 语言
            metadata: 元数据

        Returns:
            AgentResult实例
        """
        # 创建上下文
        context = AgentContext(
            session_id=f"outline_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            user_id=user_id,
            state={
                "language": language,
                "metadata": metadata or {}
            }
        )

        # 加载用户偏好（如果可用）
        if self.user_preference_service:
            await self._load_user_preferences(context)

        # 生成大纲
        try:
            logger.info(f"开始生成大纲: {topic}")

            # 这里应该调用专门的大纲生成Agent
            # 暂时返回模拟结果
            result = AgentResult(
                success=True,
                content=f"# {topic}\n\n这是生成的大纲内容..."
            )

            logger.info(f"大纲生成完成")

        except Exception as e:
            logger.error(f"大纲生成失败: {e}")
            result = AgentResult(
                success=False,
                error=str(e)
            )

        return result

    async def _load_user_preferences(self, context: AgentContext) -> None:
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


# 便捷函数
async def generate_outline_simple(
    topic: str,
    language: str = "EN-US",
    user_id: str = "anonymous"
) -> str:
    """
    简单生成大纲的便捷函数

    Args:
        topic: 主题
        language: 语言
        user_id: 用户ID

    Returns:
        大纲内容
    """
    from domain.interfaces import IAgentFactory

    # 这里需要传入实际的Agent工厂
    # 暂时返回模拟结果
    return f"# {topic}\n\n这是生成的大纲内容..."


if __name__ == "__main__":
    # 测试代码
    import asyncio

    async def test():
        outline = await generate_outline_simple("人工智能的发展")
        print(outline)

    asyncio.run(test())
