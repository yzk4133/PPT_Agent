"""
Requirements Package

需求解析智能体包

支持记忆系统集成（通过环境变量 USE_AGENT_MEMORY 控制）
"""

import os
import logging

logger = logging.getLogger(__name__)

from .requirement_parser_agent import (
    requirement_parser_agent,
    RequirementParserAgent,
    before_model_callback,
)

# 检查是否启用记忆功能
USE_MEMORY = os.getenv("USE_AGENT_MEMORY", "true").lower() == "true"

# 尝试导入带记忆的版本
if USE_MEMORY:
    try:
        from .requirement_parser_agent_with_memory import (
            RequirementParserAgentWithMemory,
            requirement_parser_agent_with_memory,
        )

        # 使用带记忆的版本作为默认导出
        requirement_parser_agent = requirement_parser_agent_with_memory

        logger.info("使用带记忆功能的需求解析智能体")
    except ImportError as e:
        logger.warning(f"无法导入带记忆的需求解析智能体，使用原始版本: {e}")
        requirement_parser_agent = requirement_parser_agent
else:
    requirement_parser_agent = requirement_parser_agent
    logger.info("使用原始需求解析智能体（记忆功能已禁用）")

__all__ = [
    "requirement_parser_agent",
    "RequirementParserAgent",
    "requirement_parser_agent_with_memory",
    "RequirementParserAgentWithMemory",
    "before_model_callback",
    "get_requirement_parser_agent",
]

def get_requirement_parser_agent():
    """
    获取需求解析智能体实例

    根据环境变量USE_AGENT_MEMORY自动选择版本
    """
    return requirement_parser_agent
