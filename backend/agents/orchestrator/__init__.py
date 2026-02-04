"""
Agents Orchestrator Module

Workflow orchestration and execution engine.
Includes the new Master Coordinator for the "1 Master + 5 Sub" architecture.

New structure:
- agents/: Orchestration agents (master_coordinator, flat_root_agent, flat_outline_agent)
- components/: Support components (agent_gateway, progress_tracker, revision_handler, page_pipeline)
- deprecated/: Deprecated code (workflow_executor, parallel_executor)

支持记忆系统集成（通过环境变量 USE_AGENT_MEMORY 控制）
"""

import os
import logging

logger = logging.getLogger(__name__)

# =====================================
# Main Orchestration Agents
# =====================================
from .agents.master_coordinator import master_coordinator_agent, MasterCoordinatorAgent
from .agents.flat_root_agent import FlatPPTGenerationAgent, flat_root_agent
from .agents.flat_outline_agent import (
    FlatSlideOutlineAgent,
    create_flat_outline_agent,
    Stage1RequirementAnalysisAgent,
    Stage2ParallelResearchAgent,
    Stage3OutlineComposerAgent,
)

# 检查是否启用记忆功能
USE_MEMORY = os.getenv("USE_AGENT_MEMORY", "true").lower() == "true"

# 尝试导入带记忆的版本
if USE_MEMORY:
    try:
        from .master_coordinator_with_memory import (
            MasterCoordinatorAgentWithMemory,
            master_coordinator_agent_with_memory,
        )

        # 使用带记忆的版本作为默认导出
        master_coordinator_agent = master_coordinator_agent_with_memory

        logger.info("使用带记忆功能的主协调智能体")
    except ImportError as e:
        logger.warning(f"无法导入带记忆的主协调智能体，使用原始版本: {e}")
        master_coordinator_agent = master_coordinator_agent
else:
    master_coordinator_agent = master_coordinator_agent
    logger.info("使用原始主协调智能体（记忆功能已禁用）")

# =====================================
# Components
# =====================================
from .components.agent_gateway import AgentGateway
from .components.progress_tracker import (
    ProgressTracker,
    get_progress_tracker,
    ProgressUpdate,
)
from .components.revision_handler import (
    RevisionHandler,
    RevisionType,
    RevisionPlan,
    RevisionResult,
    get_revision_handler,
)
from .components.page_pipeline import (
    PagePipeline,
    PagePipelineConfig,
)

# =====================================
# Deprecated (will be removed in future)
# =====================================
# from .deprecated.workflow_executor import WorkflowExecutor, AgentOrchestrator
# from .deprecated.parallel_executor import ParallelExecutionStrategy

# Build __all__ conditionally based on what was imported
_all_exports = [
    # ========== Main Agents ==========
    # Master Coordinator (Recommended)
    "master_coordinator_agent",
    "MasterCoordinatorAgent",
    "AgentGateway",

    # Flat Architecture (Deprecated - use Master Coordinator instead)
    "FlatPPTGenerationAgent",
    "flat_root_agent",
    "FlatSlideOutlineAgent",
    "create_flat_outline_agent",
    "Stage1RequirementAnalysisAgent",
    "Stage2ParallelResearchAgent",
    "Stage3OutlineComposerAgent",

    # ========== Components ==========
    # Progress tracking
    "ProgressTracker",
    "get_progress_tracker",
    "ProgressUpdate",

    # Revision handling
    "RevisionHandler",
    "RevisionType",
    "RevisionPlan",
    "RevisionResult",
    "get_revision_handler",

    # Page pipeline
    "PagePipeline",
    "PagePipelineConfig",

    # ========== Helper Functions ==========
    "get_master_coordinator_agent",
]

# Add memory versions if they were imported successfully
try:
    master_coordinator_agent_with_memory
    MasterCoordinatorAgentWithMemory
    _all_exports.extend([
        "master_coordinator_agent_with_memory",
        "MasterCoordinatorAgentWithMemory",
    ])
except NameError:
    pass

__all__ = _all_exports


def get_master_coordinator_agent():
    """
    获取主协调智能体实例

    根据环境变量USE_AGENT_MEMORY自动选择版本
    """
    return master_coordinator_agent
