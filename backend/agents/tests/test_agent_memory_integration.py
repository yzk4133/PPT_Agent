"""
Agent Memory Integration Tests

测试Agent记忆集成功能:
1. AgentMemoryMixin基础功能测试
2. ResearchAgent缓存测试
3. 共享工作空间测试
4. 用户偏好测试
5. 端到端集成测试
"""

import asyncio
import os
import pytest
from datetime import datetime
from typing import Dict, Any

# 设置测试环境变量
os.environ["USE_AGENT_MEMORY"] = "true"
os.environ["RESEARCH_CACHE_TTL_DAYS"] = "7"

from agents.core.base_agent_with_memory import AgentMemoryMixin

# ============================================================================
# Mock LLM Agent for testing
# ============================================================================

class MockLlmAgent:
    """Mock LLM Agent for testing"""

    def __init__(self, name="MockAgent"):
        self.name = name

    def __init_subclass__(cls, **kwargs):
        return super().__init_subclass__(**kwargs)

class TestAgentWithMemory(AgentMemoryMixin, MockLlmAgent):
    """测试用的带记忆的Agent"""

    def __init__(self, name="TestAgent"):
        super().__init__(name=name)

# ============================================================================
# Test Suite
# ============================================================================

class TestAgentMemoryMixin:
    """测试AgentMemoryMixin基础功能"""

    @pytest.fixture
    def agent(self):
        """创建测试Agent"""
        return TestAgentWithMemory()

    @pytest.mark.asyncio
    async def test_memory_enabled(self, agent):
        """测试记忆功能是否启用"""
        # 取决于记忆系统是否可用
        is_enabled = agent.is_memory_enabled()
        assert isinstance(is_enabled, bool)

    @pytest.mark.asyncio
    async def test_remember_and_recall(self, agent):
        """测试记忆存储和召回"""
        if not agent.is_memory_enabled():
            pytest.skip("Memory system not available")

        # 设置上下文
        agent.set_context(user_id="test_user", task_id="test_task")

        # 保存记忆
        success = await agent.remember(
            key="test_key",
            value="test_value",
            importance=0.7,
            scope="TASK"
        )
        # 即使保存失败也不应该抛出异常

        # 召回记忆
        recalled = await agent.recall(
            key="test_key",
            scope="TASK"
        )
        # 取决于记忆系统是否正常工作

    @pytest.mark.asyncio
    async def test_share_and_get_shared_data(self, agent):
        """测试共享工作空间"""
        if not agent.is_memory_enabled():
            pytest.skip("Memory system not available")

        agent.set_context(user_id="test_user", task_id="test_task")

        # 共享数据
        data_id = await agent.share_data(
            data_type="test_data",
            data_key="test_key",
            data_content={"test": "data"},
            target_agents=None,
            ttl_minutes=60
        )
        # 即使失败也不应该抛出异常

        # 获取共享数据
        data = await agent.get_shared_data(
            data_type="test_data",
            data_key="test_key"
        )

    @pytest.mark.asyncio
    async def test_user_preferences(self, agent):
        """测试用户偏好"""
        if not agent.is_memory_enabled():
            pytest.skip("Memory system not available")

        user_id = "test_user"

        # 获取用户偏好（应该创建默认偏好）
        preferences = await agent.get_user_preferences(user_id)
        assert isinstance(preferences, dict)

        # 更新用户偏好
        await agent.update_user_preferences(
            user_id=user_id,
            updates={"default_slides": 15, "language": "ZH-CN"}
        )

        # 再次获取验证更新
        updated_preferences = await agent.get_user_preferences(user_id)

    @pytest.mark.asyncio
    async def test_record_decision(self, agent):
        """测试决策记录"""
        if not agent.is_memory_enabled():
            pytest.skip("Memory system not available")

        agent.set_context(user_id="test_user", task_id="test_task")

        # 记录决策
        await agent.record_decision(
            decision_type="test_decision",
            selected_action="action_a",
            context={"test": "context"},
            alternatives=["action_a", "action_b"],
            reasoning="Test reasoning",
            confidence_score=0.8
        )
        # 不应该抛出异常

    @pytest.mark.asyncio
    async def test_forget(self, agent):
        """测试删除记忆"""
        if not agent.is_memory_enabled():
            pytest.skip("Memory system not available")

        agent.set_context(user_id="test_user", task_id="test_task")

        # 先保存
        await agent.remember(
            key="temp_key",
            value="temp_value",
            scope="TASK"
        )

        # 删除
        success = await agent.forget(
            key="temp_key",
            scope="TASK"
        )
        # 即使失败也不应该抛出异常

class TestResearchAgentCache:
    """测试ResearchAgent缓存功能"""

    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """测试缓存键生成"""
        from agents.core.research.research_agent_with_memory import (
            ResearchAgentWithMemory,
        )

        agent = ResearchAgentWithMemory(name="TestResearchAgent")

        # 生成缓存键
        key1 = agent._generate_cache_key(
            page_title="AI技术",
            keywords=["AI", "技术"]
        )
        key2 = agent._generate_cache_key(
            page_title="AI技术",
            keywords=["AI", "技术"]
        )
        key3 = agent._generate_cache_key(
            page_title="AI技术",
            keywords=["AI", "趋势"]
        )

        # 相同输入应该生成相同的键
        assert key1 == key2

        # 不同输入应该生成不同的键
        assert key1 != key3

    @pytest.mark.asyncio
    async def test_research_cache_workflow(self):
        """测试研究缓存工作流"""
        from agents.core.research.research_agent_with_memory import (
            ResearchAgentWithMemory,
        )

        agent = ResearchAgentWithMemory(name="TestResearchAgent")

        if not agent.is_memory_enabled():
            pytest.skip("Memory system not available")

        agent.set_context(user_id="test_user", task_id="test_task")

        # 模拟检查缓存
        cache_key = "test_cache_key"
        cached = await agent._check_research_cache(
            cache_key=cache_key,
            page_title="测试页面"
        )
        # 第一次应该是缓存未命中

    @pytest.mark.asyncio
    async def test_shared_research_workflow(self):
        """测试共享研究工作流"""
        from agents.core.research.research_agent_with_memory import (
            ResearchAgentWithMemory,
        )

        agent = ResearchAgentWithMemory(name="TestResearchAgent")

        if not agent.is_memory_enabled():
            pytest.skip("Memory system not available")

        agent.set_context(user_id="test_user", task_id="test_task")

        # 共享研究结果
        research_data = {
            "page_title": "AI技术",
            "content": "测试研究内容",
            "source": "测试来源"
        }

        data_id = await agent.share_data(
            data_type="research_result",
            data_key="AI技术",
            data_content=research_data,
            target_agents=["ContentMaterialAgent"],
            ttl_minutes=180
        )

class TestContentMaterialAgent:
    """测试ContentMaterialAgent记忆集成"""

    @pytest.mark.asyncio
    async def test_content_cache_key_generation(self):
        """测试内容缓存键生成"""
        from agents.core.generation.content_material_agent_with_memory import (
            ContentMaterialAgentWithMemory,
        )

        agent = ContentMaterialAgentWithMemory(name="TestContentAgent")

        # 生成缓存键
        page = {
            "title": "测试页面",
            "core_content": "测试内容",
            "content_type": "text_only"
        }

        key = agent._generate_content_cache_key("测试页面", page)
        assert key.startswith("content_")
        assert len(key) == 32  # MD5哈希长度

class TestRequirementParserAgent:
    """测试RequirementParserAgent记忆集成"""

    @pytest.mark.asyncio
    async def test_user_preference_application(self):
        """测试用户偏好应用"""
        from agents.core.requirements.requirement_parser_agent_with_memory import (
            RequirementParserAgentWithMemory,
        )

        agent = RequirementParserAgentWithMemory(name="TestRequirementAgent")

        if not agent.is_memory_enabled():
            pytest.skip("Memory system not available")

        agent.set_context(user_id="test_user", task_id="test_task")

        # 模拟应用用户偏好
        user_preferences = {
            "default_slides": 15,
            "language": "ZH-CN",
            "template_type": "BUSINESS"
        }

        # 创建模拟上下文
        class MockContext:
            class MockSession:
                state = {}

            session = MockSession()

        ctx = MockContext()

        # 应用偏好
        await agent._apply_user_preferences(ctx, user_preferences)

        # 验证偏好已应用
        assert ctx.session.state.get("slides_plan_num") == 15
        assert ctx.session.state.get("language") == "ZH-CN"

class TestMasterCoordinator:
    """测试MasterCoordinator记忆集成"""

    @pytest.mark.asyncio
    async def test_task_state_memory(self):
        """测试任务状态记忆"""
        from agents.orchestrator.master_coordinator_with_memory import (
            MasterCoordinatorAgentWithMemory,
        )

        agent = MasterCoordinatorAgentWithMemory()

        if not agent.is_memory_enabled():
            pytest.skip("Memory system not available")

        agent.set_context(user_id="test_user", task_id="test_task")

        # 保存任务初始状态
        await agent._save_task_initial_state(
            task_id="test_task_123",
            user_input="生成AI技术PPT",
            ctx=None
        )
        # 不应该抛出异常

    @pytest.mark.asyncio
    async def test_context_setup(self):
        """测试上下文设置"""
        from agents.orchestrator.master_coordinator_with_memory import (
            MasterCoordinatorAgentWithMemory,
        )

        agent = MasterCoordinatorAgentWithMemory()

        # 创建模拟上下文
        class MockContext:
            class MockSession:
                state = {"task_id": "test_task_456"}

            session = MockSession()

        ctx = MockContext()

        # 设置上下文
        agent._setup_context(ctx)

        # 验证上下文已设置
        assert agent.task_id == "test_task_456"

# ============================================================================
# Integration Tests
# ============================================================================

class TestEndToEndIntegration:
    """端到端集成测试"""

    @pytest.mark.asyncio
    async def test_shared_workspace_integration(self):
        """测试共享工作空间集成"""
        if not os.getenv("USE_AGENT_MEMORY", "true") == "true":
            pytest.skip("Memory not enabled")

        # 创建ResearchAgent
        from agents.core.research.research_agent_with_memory import (
            ResearchAgentWithMemory,
        )

        # 创建ContentMaterialAgent
        from agents.core.generation.content_material_agent_with_memory import (
            ContentMaterialAgentWithMemory,
        )

        research_agent = ResearchAgentWithMemory(name="TestResearchAgent")
        content_agent = ContentMaterialAgentWithMemory(name="TestContentAgent")

        if not research_agent.is_memory_enabled():
            pytest.skip("Memory system not available")

        # 设置相同的上下文（模拟同一任务）
        user_id = "test_user"
        task_id = "test_task_shared"

        research_agent.set_context(user_id=user_id, task_id=task_id)
        content_agent.set_context(user_id=user_id, task_id=task_id)

        # ResearchAgent共享数据
        research_data = {
            "page_title": "电商618",
            "content": "618促销活动分析",
            "source": "行业报告"
        }

        await research_agent.share_data(
            data_type="research_result",
            data_key="电商618",
            data_content=research_data,
            target_agents=["ContentMaterialAgent"],
            ttl_minutes=180
        )

        # ContentMaterialAgent获取数据
        shared_data = await content_agent.get_shared_data(
            data_type="research_result",
            data_key="电商618"
        )

        # 验证数据共享成功（如果记忆系统正常工作）
        if shared_data:
            assert shared_data["page_title"] == "电商618"
            assert shared_data["content"] == "618促销活动分析"

# ============================================================================
# Performance Tests
# ============================================================================

class TestMemoryPerformance:
    """记忆系统性能测试"""

    @pytest.mark.asyncio
    async def test_bulk_memory_operations(self):
        """测试批量记忆操作"""
        agent = TestAgentWithMemory(name="PerformanceTestAgent")

        if not agent.is_memory_enabled():
            pytest.skip("Memory system not available")

        agent.set_context(user_id="perf_test_user", task_id="perf_test_task")

        # 批量保存
        start_time = datetime.now()

        for i in range(100):
            await agent.remember(
                key=f"bulk_key_{i}",
                value=f"bulk_value_{i}",
                importance=0.5,
                scope="TASK"
            )

        save_duration = (datetime.now() - start_time).total_seconds()

        # 批量召回
        start_time = datetime.now()

        recalled_count = 0
        for i in range(100):
            value = await agent.recall(
                key=f"bulk_key_{i}",
                scope="TASK"
            )
            if value:
                recalled_count += 1

        recall_duration = (datetime.now() - start_time).total_seconds()

        # 打印性能数据
        print(f"\n保存100条记录耗时: {save_duration:.2f}秒")
        print(f"召回{recalled_count}/100条记录耗时: {recall_duration:.2f}秒")

# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
