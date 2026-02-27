"""
Multi-Agent PPT Backend Package

提供简洁的导入接口，优化项目内部模块引用。

使用示例:
    # 导入模型
    from backend import ExecutionMode, Checkpoint

    # 导入协调器
    from backend import MasterGraph, create_master_graph

    # 导入配置
    from backend import get_config
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
# Models (formerly Domain)
# ============================================================================
from models.execution_mode import ExecutionMode
from models.checkpoint import Checkpoint

# ============================================================================
# Agent 层 (LangChain)
# ============================================================================
from agents import MasterGraph, create_master_graph

# ============================================================================
# 基础设施层 (Infrastructure)
# ============================================================================
from infrastructure.config import get_config, AppConfig
from infrastructure.middleware.error_handler import setup_exception_handlers
from infrastructure.checkpoint import CheckpointManager, get_checkpoint_manager

# ============================================================================
# 服务层 (Services) - 已合并到 API 层
# ============================================================================
# 服务层已合并到 API 层以简化架构
# from api.ppt_service import PptGenerationServiceLangChain, get_ppt_generation_service_langchain

# ============================================================================
# 工具层 (Utils)
# ============================================================================
# from utils.save_ppt import PPTGenerator, get_ppt_generator  # 模块已重构
from utils.context_compressor import ContextCompressor

# ============================================================================
# 导出列表
# ============================================================================
__all__ = [
    # Models
    "ExecutionMode", "Checkpoint",

    # Agents
    "MasterGraph", "create_master_graph",

    # Infrastructure
    "get_config", "AppConfig",
    "setup_exception_handlers",
    "CheckpointManager", "get_checkpoint_manager",

    # Utils
    "ContextCompressor",
]

# 版本信息
__version__ = "2.0.0"
__author__ = "Multi-Agent PPT Team"
