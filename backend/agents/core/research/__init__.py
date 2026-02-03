"""
Research Package

研究智能体包，包括并行研究和优化版研究智能体

支持记忆系统集成（通过环境变量 USE_AGENT_MEMORY 控制）
"""

import os
import logging

logger = logging.getLogger(__name__)

from .parallel_research_agent import parallel_search_agent
from .research_agent import optimized_research_agent, OptimizedResearchAgent

# 检查是否启用记忆功能
USE_MEMORY = os.getenv("USE_AGENT_MEMORY", "true").lower() == "true"

# 尝试导入带记忆的版本
if USE_MEMORY:
    try:
        from .research_agent_with_memory import (
            ResearchAgentWithMemory,
            research_agent_with_memory,
        )

        # 使用带记忆的版本作为默认导出
        research_agent = research_agent_with_memory

        logger.info("使用带记忆功能的研究智能体")
    except ImportError as e:
        logger.warning(f"无法导入带记忆的研究智能体，使用原始版本: {e}")
        research_agent = optimized_research_agent
else:
    research_agent = optimized_research_agent
    logger.info("使用原始研究智能体（记忆功能已禁用）")

__all__ = [
    "parallel_search_agent",
    "optimized_research_agent",
    "OptimizedResearchAgent",
    "research_agent_with_memory",
    "ResearchAgentWithMemory",
    "research_agent",
    "get_research_agent",
]


def get_research_agent():
    """
    获取研究智能体实例

    根据环境变量USE_AGENT_MEMORY自动选择版本
    """
    return research_agent
