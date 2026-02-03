"""
Generation Package

生成智能体包，包括内容素材生成和PPT写入

支持记忆系统集成（通过环境变量 USE_AGENT_MEMORY 控制）
"""

import os
import logging

logger = logging.getLogger(__name__)

from .slide_writer_agent import (
    ppt_writer_sub_agent,
    ppt_checker_agent,
    ppt_generator_loop_agent,
)
from .content_material_agent import (
    content_material_agent,
    ContentMaterialAgent,
    before_agent_callback,
)

# 检查是否启用记忆功能
USE_MEMORY = os.getenv("USE_AGENT_MEMORY", "true").lower() == "true"

# 尝试导入带记忆的版本
if USE_MEMORY:
    try:
        from .content_material_agent_with_memory import (
            ContentMaterialAgentWithMemory,
            content_material_agent_with_memory,
        )

        # 使用带记忆的版本作为默认导出
        content_material_agent = content_material_agent_with_memory

        logger.info("使用带记忆功能的内容素材智能体")
    except ImportError as e:
        logger.warning(f"无法导入带记忆的内容素材智能体，使用原始版本: {e}")
        content_material_agent = content_material_agent
else:
    content_material_agent = content_material_agent
    logger.info("使用原始内容素材智能体（记忆功能已禁用）")

__all__ = [
    "ppt_writer_sub_agent",
    "ppt_checker_agent",
    "ppt_generator_loop_agent",
    "content_material_agent",
    "ContentMaterialAgent",
    "content_material_agent_with_memory",
    "ContentMaterialAgentWithMemory",
    "before_agent_callback",
    "get_content_material_agent",
]


def get_content_material_agent():
    """
    获取内容素材智能体实例

    根据环境变量USE_AGENT_MEMORY自动选择版本
    """
    return content_material_agent
