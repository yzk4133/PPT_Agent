"""
Orchestrator Components Module

This module provides core components for agent orchestration:
- ProgressTracker: Track progress of multi-stage tasks
- RevisionHandler: Handle task revisions and feedback
- PagePipeline: Parallel page-level processing pipeline
- AgentGateway: Gateway for agent communication
"""

from .agent_gateway import AgentGateway
from .page_pipeline import PagePipeline, PagePipelineConfig
from .progress_tracker import ProgressTracker, get_progress_tracker, ProgressUpdate
from .revision_handler import RevisionHandler, get_revision_handler, RevisionType, RevisionPlan, RevisionResult

__all__ = [
    # Agent Gateway
    "AgentGateway",
    # Progress Tracking
    "ProgressTracker",
    "get_progress_tracker",
    "ProgressUpdate",
    # Revision Handling
    "RevisionHandler",
    "get_revision_handler",
    "RevisionType",
    "RevisionPlan",
    "RevisionResult",
    # Page Pipeline
    "PagePipeline",
    "PagePipelineConfig",
]
