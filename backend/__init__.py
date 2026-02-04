"""
Multi-Agent PPT Backend Package

提供简洁的导入接口，优化项目内部模块引用。

使用示例:
    # 领域层
    from backend import Task, TaskStatus, Requirement

    # Agent 层
    from backend import master_coordinator_agent, get_progress_tracker

    # 基础设施层
    from backend import get_config, JSONFallbackParser

    # 服务层
    from backend import TaskService, PresentationService
"""

# 确保路径配置正确（仅用于兼容性，优先使用 PYTHONPATH）
import sys
import os
from pathlib import Path

# 获取项目根目录（MultiAgentPPT-main），使 backend, domain 等可作为顶层模块导入
# 检查是否在 backend 目录下运行
_current_file = Path(__file__).resolve()
_backend_root = _current_file.parent
_project_root = _backend_root.parent

# 将项目根目录添加到 sys.path
_project_root_str = str(_project_root)
if _project_root_str not in sys.path:
    sys.path.insert(0, _project_root_str)

# 同时将 backend 目录添加到 sys.path（用于 'from backend.xxx import'）
_backend_root_str = str(_backend_root)
if _backend_root_str not in sys.path:
    sys.path.insert(0, _backend_root_str)

# ============================================================================
# Google ADK / GenAI - 常用导入
# ============================================================================
from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.events.event import Event
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types as genai_types

# ============================================================================
# 领域层 (Domain)
# ============================================================================
from domain.models import (
    Task, TaskStatus, TaskStage,
    Requirement, PPTFramework,
    PageDefinition,
)
from domain.models.execution_mode import ExecutionMode
from domain.models.checkpoint import Checkpoint
from domain.services import (
    TaskProgressService, task_progress_service,
    TaskValidationService, task_validation_service,
)
from domain.exceptions import DomainError, ValidationError

# ============================================================================
# Agent 层
# ============================================================================
from agents import (
    # Factory
    AgentFactory, get_agent_factory,
    # Core Agents
    RequirementParserAgent, requirement_parser_agent,
    FrameworkDesignerAgent, framework_designer_agent,
    OptimizedResearchAgent, optimized_research_agent,
    ContentMaterialAgent, content_material_agent,
    TemplateRendererAgent, template_renderer_agent,
    # Orchestrator
    MasterCoordinatorAgent, master_coordinator_agent,
    AgentGateway,
)
from agents.orchestrator.components import (
    ProgressTracker, get_progress_tracker, ProgressUpdate,
    RevisionHandler, get_revision_handler, RevisionType, RevisionResult,
)

# ============================================================================
# 基础设施层 (Infrastructure)
# ============================================================================
from infrastructure.config import get_config, AppConfig
from infrastructure.llm.fallback import JSONFallbackParser
from infrastructure.middleware.error_handler import setup_exception_handlers
from infrastructure.checkpoint import CheckpointManager, get_checkpoint_manager
from infrastructure.security import PasswordHandler, JWTHandler

# ============================================================================
# 服务层 (Services)
# ============================================================================
from services import (
    TaskService,
    PresentationService,
    OutlineService,
    AuthService,
    UserService,
)

# ============================================================================
# 工具层 (Utils)
# ============================================================================
# from utils.save_ppt import PPTGenerator, get_ppt_generator  # 模块已重构
from utils.context_compressor import ContextCompressor

# ============================================================================
# 导出列表
# ============================================================================
__all__ = [
    # Google ADK
    "BaseAgent", "LlmAgent", "InvocationContext", "CallbackContext",
    "Event", "LlmRequest", "LlmResponse", "genai_types",

    # Domain
    "Task", "TaskStatus", "TaskStage", "Requirement", "PPTFramework",
    "PageDefinition", "ExecutionMode", "Checkpoint",
    "TaskProgressService", "task_progress_service",
    "TaskValidationService", "task_validation_service",
    "DomainError", "ValidationError",

    # Agents
    "AgentFactory", "get_agent_factory",
    "RequirementParserAgent", "requirement_parser_agent",
    "FrameworkDesignerAgent", "framework_designer_agent",
    "OptimizedResearchAgent", "optimized_research_agent",
    "ContentMaterialAgent", "content_material_agent",
    "TemplateRendererAgent", "template_renderer_agent",
    "MasterCoordinatorAgent", "master_coordinator_agent",
    "AgentGateway",
    "ProgressTracker", "get_progress_tracker", "ProgressUpdate",
    "RevisionHandler", "get_revision_handler", "RevisionType", "RevisionResult",

    # Infrastructure
    "get_config", "AppConfig",
    "JSONFallbackParser",
    "setup_exception_handlers",
    "CheckpointManager", "get_checkpoint_manager",
    "PasswordHandler", "JWTHandler",

    # Services
    "TaskService", "PresentationService", "OutlineService",
    "AuthService", "UserService",

    # Utils
    "PPTGenerator", "get_ppt_generator",
    "ContextCompressor",
]

# 版本信息
__version__ = "2.0.0"
__author__ = "Multi-Agent PPT Team"
