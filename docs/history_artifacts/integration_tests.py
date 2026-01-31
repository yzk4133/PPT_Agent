"""集成测试套件

测试各模块之间的协作
"""

import pytest
import asyncio
from typing import Dict, Any

from backend.core.coordinator import TaskCoordinator
from backend.core.content_agent import ContentGeneratorAgent
from backend.core.design_agent import DesignAgent
from backend.core.code_generator_agent import CodeGeneratorAgent
from backend.core.agent_base import AgentConfig


@pytest.mark.asyncio
async def test_full_pipeline():
    """测试完整的PPT生成流程"""
    # 1. 创建协调器
    coordinator = TaskCoordinator()

    # 2. 注册Agent
    coordinator.register_agent(
        "content_generator",
        ContentGeneratorAgent(AgentConfig(
            name="content_generator",
            role="内容生成",
            model_provider="anthropic"
        ))
    )

    coordinator.register_agent(
        "design_agent",
        DesignAgent(AgentConfig(
            name="design_agent",
            role="设计建议",
            model_provider="anthropic"
        ))
    )

    coordinator.register_agent(
        "code_generator",
        CodeGeneratorAgent(AgentConfig(
            name="code_generator",
            role="代码生成",
            model_provider="anthropic"
        ))
    )

    # 3. 分解任务
    user_input = "创建一个关于人工智能的PPT"
    tasks = coordinator.decompose_requirement(user_input)

    # 4. 验证任务分解
    assert len(tasks) > 0
    assert any(t.required_agent == "content_generator" for t in tasks)

    # 5. 执行任务
    results = await coordinator.execute(tasks)

    # 6. 验证结果
    assert len(results) > 0


@pytest.mark.asyncio
async def test_agent_communication():
    """测试Agent间通信"""
    from backend.core.agent_base import AgentMessage

    # 创建测试消息
    message = AgentMessage.create(
        from_agent="coordinator",
        to_agent="content_generator",
        content={
            "task_type": "generate_outline",
            "requirement": "AI技术介绍"
        }
    )

    # 验证消息结构
    assert message.id is not None
    assert message.from_agent == "coordinator"
    assert message.to_agent == "content_generator"
    assert "task_type" in message.content


def test_configuration_loading():
    """测试配置加载"""
    from backend.core.config import SystemConfig, AnthropicConfig

    # 创建测试配置
    config = SystemConfig(
        anthropic=AnthropicConfig(
            api_key="test_key",
            model="claude-3-5-sonnet-20241022"
        )
    )

    # 验证配置
    assert config.anthropic.api_key == "test_key"
    assert config.anthropic.model == "claude-3-5-sonnet-20241022"

    # 验证配置有效性
    assert config.validate() is True


def test_template_system():
    """测试模板系统"""
    from backend.core.template_system import TemplateLibrary, TemplateCategory

    library = TemplateLibrary()

    # 列出所有模板
    templates = library.list_templates()
    assert len(templates) > 0

    # 按分类过滤
    business_templates = library.list_templates(TemplateCategory.BUSINESS)
    assert len(business_templates) > 0

    # 获取特定模板
    template = library.get_template("business_classic")
    assert template is not None
    assert template.name == "经典商务"


@pytest.mark.asyncio
async def test_memory_system():
    """测试记忆系统"""
    from backend.core.memory import ContextMemory

    memory = ContextMemory()

    # 添加记忆
    memory_id = memory.add(
        agent_name="test_agent",
        content={"key": "value"},
        ttl=60
    )

    # 获取记忆
    retrieved = memory.get(memory_id)
    assert retrieved is not None
    assert retrieved.content["key"] == "value"

    # 按Agent获取
    agent_memories = memory.get_by_agent("test_agent")
    assert len(agent_memories) > 0


@pytest.mark.asyncio
async def test_error_handling():
    """测试错误处理"""
    from backend.core.exceptions import PPTSystemException, ErrorCode, ContentException

    # 创建异常
    exc = ContentException(
        code=ErrorCode.LLM_API_ERROR,
        message="API调用失败",
        details={"status_code": 500}
    )

    # 验证异常信息
    assert exc.code == ErrorCode.LLM_API_ERROR
    assert "API调用失败" in str(exc)

    # 转换为字典
    error_dict = exc.to_dict()
    assert error_dict["error_code"] == "E202"
    assert error_dict["message"] == "API调用失败"
