"""
BaseAgent单元测试

测试基础类的核心功能：
- 模型创建
- 链创建
- 记忆操作便捷方法
- 错误处理
- 降级策略
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import StrOutputParser

from backend.agents.core.base_agent import BaseAgent, BaseToolAgent
from backend.agents.models.state import PPTGenerationState


class SimpleTestAgent(BaseAgent):
    """用于测试的简单Agent实现"""

    def _create_chain(self) -> Runnable:
        prompt = ChatPromptTemplate.from_template("Tell me about {topic}")
        return prompt | self.model | StrOutputParser()

    async def execute_task(self, state: PPTGenerationState) -> PPTGenerationState:
        topic = state.get("topic", "test")

        # 测试缓存
        cache_key = f"test_{topic}"
        cached = await self.check_cache(cache_key, state)
        if cached:
            state["result"] = cached
            return state

        # 执行任务
        result = await self.chain.ainvoke({"topic": topic})
        state["result"] = result

        # 保存缓存
        await self.save_to_cache(cache_key, result, state=state)

        return state

    def get_fallback_result(self, state: PPTGenerationState) -> Optional[PPTGenerationState]:
        state["result"] = "fallback result"
        return state


class TestBaseAgent:
    """测试BaseAgent基础功能"""

    def test_initialization(self):
        """测试初始化"""
        agent = SimpleTestAgent(
            agent_name="TestAgent",
            enable_memory=False
        )

        assert agent.agent_name == "TestAgent"
        assert agent.model is not None
        assert agent.chain is not None
        assert agent.has_memory is False

    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test-key',
        'LLM_MODEL': 'gpt-4o-mini'
    })
    def test_model_creation_with_env_vars(self):
        """测试从环境变量创建模型"""
        agent = SimpleTestAgent(enable_memory=False)

        assert isinstance(agent.model, ChatOpenAI)
        assert agent.model.model_name == "gpt-4o-mini"
        assert agent.model.api_key == "test-key"

    @patch.dict('os.environ', {}, clear=True)
    def test_model_creation_fallback_to_mock(self):
        """测试无API key时使用mock模式"""
        agent = SimpleTestAgent(enable_memory=False)

        assert isinstance(agent.model, ChatOpenAI)
        assert agent.model.api_key == "sk-mock-key"

    def test_create_chain(self):
        """测试链创建"""
        agent = SimpleTestAgent(enable_memory=False)
        chain = agent._create_chain()

        assert isinstance(chain, Runnable)

    @pytest.mark.asyncio
    async def test_execute_task(self):
        """测试任务执行"""
        agent = SimpleTestAgent(enable_memory=False)
        state = {"topic": "AI"}

        result_state = await agent.execute_task(state)

        assert "result" in result_state
        assert isinstance(result_state["result"], str)

    @pytest.mark.asyncio
    async def test_run_node_template_method(self):
        """测试run_node模板方法"""
        agent = SimpleTestAgent(enable_memory=False)
        state = {"topic": "testing"}

        result_state = await agent.run_node(state)

        assert "result" in result_state

    @pytest.mark.asyncio
    async def test_fallback_strategy(self):
        """测试降级策略"""
        agent = SimpleTestAgent(enable_memory=False)

        state = {"topic": "test"}
        fallback = agent.get_fallback_result(state)

        assert fallback["result"] == "fallback result"

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""

        class FailingAgent(BaseAgent):
            def _create_chain(self) -> Runnable:
                raise NotImplementedError()

            async def execute_task(self, state):
                raise ValueError("Test error")

            def get_fallback_result(self, state):
                state["recovered"] = True
                return state

        agent = FailingAgent(enable_memory=False)
        state = {}

        result_state = await agent.run_node(state)

        # 应该调用降级策略
        assert result_state.get("recovered") is True

    @pytest.mark.asyncio
    async def test_cache_operations(self):
        """测试缓存便捷方法"""
        agent = SimpleTestAgent(enable_memory=True)
        state = {
            "task_id": "test_task",
            "user_id": "test_user"
        }

        # 测试save_to_cache
        await agent.save_to_cache(
            "test_key",
            "test_value",
            state=state
        )

        # 测试check_cache
        # 注意：这需要实际的记忆系统才能测试
        # 这里只是验证方法可以调用


class TestBaseToolAgent:
    """测试BaseToolAgent功能"""

    def test_initialization_without_tools(self):
        """测试不使用工具的初始化"""
        from backend.agents.core.base_agent import BaseToolAgent

        class SimpleToolAgent(BaseToolAgent):
            def _create_chain(self) -> Runnable:
                prompt = ChatPromptTemplate.from_template("Query: {query}")
                return prompt | self.model

            async def execute_task(self, state: PPTGenerationState) -> PPTGenerationState:
                return state

        agent = SimpleToolAgent(
            use_tools=False,
            enable_memory=False
        )

        assert agent.tools == []
        assert agent.agent_executor is None

    def test_initialization_with_tools(self):
        """测试使用工具的初始化"""
        # 这个测试需要实际的工具注册表
        # 在真实环境中可以测试
        pass


class TestConvenienceMethods:
    """测试便捷方法"""

    @pytest.mark.asyncio
    async def test_share_with_agents(self):
        """测试数据共享"""
        agent = SimpleTestAgent(enable_memory=True)
        state = {
            "task_id": "test_task",
            "user_id": "test_user"
        }

        # 初始化记忆
        agent._get_memory(state)

        # 测试共享
        await agent.share_with_agents(
            data_type="test",
            data_key="test_data",
            data_content={"key": "value"},
            target_agents=["OtherAgent"]
        )

        # 验证方法可以调用（实际效果需要记忆系统支持）

    @pytest.mark.asyncio
    async def test_retrieve_shared_data(self):
        """测试获取共享数据"""
        agent = SimpleTestAgent(enable_memory=True)
        state = {
            "task_id": "test_task",
            "user_id": "test_user"
        }

        # 初始化记忆
        agent._get_memory(state)

        # 测试获取（可能返回None，因为没有实际共享数据）
        data = await agent.retrieve_shared_data("test", "test_data")
        # 不抛出异常即成功


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_agent_workflow(self):
        """测试完整的Agent工作流"""
        agent = SimpleTestAgent(enable_memory=True)
        state = {
            "topic": "Python programming",
            "task_id": "test_001",
            "user_id": "test_user"
        }

        # 执行完整流程
        result_state = await agent.run_node(state)

        # 验证结果
        assert "result" in result_state
        assert result_state["topic"] == "Python programming"


# 运行测试的便捷函数
def run_tests():
    """运行所有测试"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()
