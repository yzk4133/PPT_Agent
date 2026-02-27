"""
LangChain 多Agent 架构

本模块包含基于 LangChain 的 MultiAgentPPT 系统实现。
它使用 LangGraph 提供清晰的声明式工作流。
"""

from .coordinator.master_graph import MasterGraph, create_master_graph

__all__ = [
    "MasterGraph",
    "create_master_graph",
]
