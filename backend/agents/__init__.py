"""
Agents Module

This module provides all agent-related functionality including:
- Agent Factory: Unified agent creation and management
- Core Agents: Planning, Research, Generation, Rendering agents
- Orchestrator: Workflow orchestration and coordination
- Tools: Unified tool registry and management
"""

# ==================== Agent Factory ====================
from .factory import (
    AgentFactory,
    get_agent_factory,
    reset_agent_factory,
)

# ==================== Core Agents ====================
from .core import (
    # Planning (including requirements)
    split_topic_agent,
    framework_designer_agent,
    FrameworkDesignerAgent,
    requirement_parser_agent,
    RequirementParserAgent,
    # Research
    parallel_search_agent,
    optimized_research_agent,
    OptimizedResearchAgent,
    # Generation
    ppt_generator_loop_agent,
    content_material_agent,
    ContentMaterialAgent,
    # Rendering
    template_renderer_agent,
    TemplateRendererAgent,
    # Quality
    QualityDimension,
    QualityScore,
    QualityAssessment,
    QualityAssessor,
    RuleBasedAssessor,
    FeedbackLoopAgent,
    get_default_assessor,
)

# ==================== Orchestrator ====================
from .orchestrator import (
    # Main Agents
    master_coordinator_agent,
    MasterCoordinatorAgent,
    AgentGateway,
    # Flat Architecture (Deprecated)
    FlatPPTGenerationAgent,
    flat_root_agent,
    FlatSlideOutlineAgent,
    create_flat_outline_agent,
    Stage1RequirementAnalysisAgent,
    Stage2ParallelResearchAgent,
    Stage3OutlineComposerAgent,
    # Components
    ProgressTracker,
    get_progress_tracker,
    ProgressUpdate,
    RevisionHandler,
    RevisionType,
    RevisionPlan,
    RevisionResult,
    get_revision_handler,
    PagePipeline,
    PagePipelineConfig,
    get_master_coordinator_agent,
)

# Try to import memory versions if available
try:
    from .orchestrator import (
        master_coordinator_agent_with_memory,
        MasterCoordinatorAgentWithMemory,
    )
except ImportError:
    # Define as None if not available
    master_coordinator_agent_with_memory = None  # type: ignore
    MasterCoordinatorAgentWithMemory = None  # type: ignore

# ==================== Tools ====================
from .tools import (
    UnifiedToolRegistry,
    get_unified_registry,
    register_tool,
    get_tool,
    list_all_tools,
    ToolCategory,
    ToolMetadata,
    ToolRegistration,
)

# Build __all__ conditionally
_all_exports = [
    # ========== Agent Factory ==========
    "AgentFactory",
    "get_agent_factory",
    "reset_agent_factory",
    # ========== Core Agents ==========
    # Planning
    "split_topic_agent",
    "framework_designer_agent",
    "FrameworkDesignerAgent",
    "requirement_parser_agent",
    "RequirementParserAgent",
    # Research
    "parallel_search_agent",
    "optimized_research_agent",
    "OptimizedResearchAgent",
    # Generation
    "ppt_generator_loop_agent",
    "content_material_agent",
    "ContentMaterialAgent",
    # Rendering
    "template_renderer_agent",
    "TemplateRendererAgent",
    # Quality
    "QualityDimension",
    "QualityScore",
    "QualityAssessment",
    "QualityAssessor",
    "RuleBasedAssessor",
    "FeedbackLoopAgent",
    "get_default_assessor",
    # ========== Orchestrator ==========
    # Main Agents
    "master_coordinator_agent",
    "MasterCoordinatorAgent",
    "AgentGateway",
    # Flat Architecture
    "FlatPPTGenerationAgent",
    "flat_root_agent",
    "FlatSlideOutlineAgent",
    "create_flat_outline_agent",
    "Stage1RequirementAnalysisAgent",
    "Stage2ParallelResearchAgent",
    "Stage3OutlineComposerAgent",
    # Components
    "ProgressTracker",
    "get_progress_tracker",
    "ProgressUpdate",
    "RevisionHandler",
    "RevisionType",
    "RevisionPlan",
    "RevisionResult",
    "get_revision_handler",
    "PagePipeline",
    "PagePipelineConfig",
    "get_master_coordinator_agent",
    # ========== Tools ==========
    "UnifiedToolRegistry",
    "get_unified_registry",
    "register_tool",
    "get_tool",
    "list_all_tools",
    "ToolCategory",
    "ToolMetadata",
    "ToolRegistration",
]

# Add memory versions if they were imported successfully
if master_coordinator_agent_with_memory is not None:
    _all_exports.insert(
        _all_exports.index("AgentGateway") + 1,
        "master_coordinator_agent_with_memory",
    )
    _all_exports.insert(
        _all_exports.index("master_coordinator_agent_with_memory") + 1,
        "MasterCoordinatorAgentWithMemory",
    )

__all__ = _all_exports
