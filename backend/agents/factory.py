"""
Agent Factory - 统一创建和管理所有 Agent
"""

import logging
import os
import sys
from typing import Optional, Dict, Any, List

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from google.adk.agents import Agent

# 导入所有 Agent
from agents.orchestrator.agents.flat_outline_agent import create_flat_outline_agent
from agents.orchestrator.agents.flat_root_agent import flat_root_agent
from agents.orchestrator.agents.master_coordinator import MasterCoordinatorAgent

# 导入子 Agent（用于主协调器）
from agents.core.planning.requirements.requirement_parser_agent import requirement_parser_agent
from agents.core.planning.framework_designer_agent import framework_designer_agent
from agents.core.research.research_agent import optimized_research_agent
from agents.core.generation.content_material_agent import content_material_agent
from agents.core.rendering.template_renderer_agent import template_renderer_agent

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Agent 工厂类

    提供统一的 Agent 创建接口，封装配置和初始化逻辑
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化工厂

        Args:
            config: 全局配置
        """
        self.config = config or {}
        self._agents: Dict[str, Agent] = {}

    # ==================== 大纲相关 Agent ====================

    def create_outline_agent(
        self,
        model_name: str = "deepseek-chat",
        provider: str = "deepseek",
        mcp_tools: Optional[List] = None,
        max_concurrency: int = 3
    ) -> Agent:
        """创建大纲生成 Agent"""
        return create_flat_outline_agent(
            model_name=model_name,
            provider=provider,
            mcp_tools=mcp_tools or [],
            max_concurrency=max_concurrency
        )

    # ==================== PPT 生成相关 Agent ====================

    def create_ppt_generation_agent(self) -> Agent:
        """创建 PPT 生成 Agent (flat_root_agent)"""
        return flat_root_agent

    # ==================== 主协调器 Agent ====================

    def create_master_coordinator(
        self,
        checkpoint_manager=None,
        enable_page_pipeline: bool = True,
        page_pipeline_config=None
    ) -> MasterCoordinatorAgent:
        """创建主协调器 Agent"""
        return MasterCoordinatorAgent(
            checkpoint_manager=checkpoint_manager,
            enable_page_pipeline=enable_page_pipeline,
            page_pipeline_config=page_pipeline_config
        )

    # ==================== 子 Agent（用于主协调器） ====================

    def create_requirement_parser(self) -> Agent:
        """创建需求解析 Agent"""
        return requirement_parser_agent

    def create_framework_designer(self) -> Agent:
        """创建框架设计 Agent"""
        return framework_designer_agent

    def create_research_agent(self) -> Agent:
        """创建研究 Agent"""
        return optimized_research_agent

    def create_content_material_agent(self) -> Agent:
        """创建内容素材 Agent"""
        return content_material_agent

    def create_template_renderer(self) -> Agent:
        """创建模板渲染 Agent"""
        return template_renderer_agent

    # ==================== 便捷方法 ====================

    def get_all_sub_agents(self) -> Dict[str, Agent]:
        """获取所有子 Agent（用于主协调器）"""
        return {
            "requirement_parser": requirement_parser_agent,
            "framework_designer": framework_designer_agent,
            "research": optimized_research_agent,
            "content_material": content_material_agent,
            "template_renderer": template_renderer_agent
        }


# 全局单例
_global_factory: Optional[AgentFactory] = None


def get_agent_factory(config: Optional[Dict[str, Any]] = None) -> AgentFactory:
    """获取全局 AgentFactory 实例"""
    global _global_factory
    if _global_factory is None:
        _global_factory = AgentFactory(config)
    return _global_factory


def reset_agent_factory():
    """重置全局 AgentFactory 实例（主要用于测试）"""
    global _global_factory
    _global_factory = None
