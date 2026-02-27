"""
Tests for LangChain Memory Integration
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from backend.memory.memory_aware_agent import (
    MemoryAwareAgent,
    LangGraphAgentMixin,
)


@pytest.fixture
def mock_state():
    """Mock LangChain state"""
    return {
        "task_id": "test_task_123",
        "user_id": "test_user",
        "session_id": "test_session",
        "user_input": "Create a PPT about AI",
    }


@pytest.fixture
def memory_manager(mock_state):
    """Create memory manager for testing"""
    with patch("backend.agents.memory.state_bound_manager._MEMORY_AVAILABLE", True):
        # Mock the memory services
        with patch("backend.agents.memory.state_bound_manager._memory_services") as mock_services:
            # Create mock manager
            mock_memory_mgr = AsyncMock()
            mock_memory_mgr.set = AsyncMock(return_value=True)
            mock_memory_mgr.get = AsyncMock(return_value=("test_value", MagicMock(layer=MagicMock(value="TASK"))))
            mock_memory_mgr.delete = AsyncMock()

            # Create mock scope
            mock_scope = MagicMock()
            mock_scope.TASK = "TASK"
            mock_scope.USER = "USER"

            # Mock services
            mock_services = {
                "manager": MagicMock(return_value=mock_memory_mgr),
                "MemoryScope": MagicMock(return_value=mock_scope),
                "SharedWorkspaceService": MagicMock,
                "UserPreferenceService": MagicMock,
                "AgentDecisionService": MagicMock,
            }

            manager = StateBoundMemoryManager(
                state=mock_state,
                agent_name="TestAgent",
                enable_memory=True
            )
            manager._memory_manager = mock_memory_mgr
            manager._MemoryScope = mock_scope

            yield manager


class TestStateBoundMemoryManager:
    """Tests for StateBoundMemoryManager"""

    def test_initialization(self, mock_state):
        """Test manager initialization"""
        with patch("backend.agents.memory.state_bound_manager._MEMORY_AVAILABLE", False):
            manager = StateBoundMemoryManager(
                state=mock_state,
                agent_name="TestAgent",
                enable_memory=True
            )

            assert manager.agent_name == "TestAgent"
            assert manager.task_id == "test_task_123"
            assert manager.user_id == "test_user"
            assert manager.session_id == "test_session"
            assert not manager.is_enabled()

    @pytest.mark.asyncio
    async def test_remember(self, memory_manager):
        """Test remember operation"""
        result = await memory_manager.remember(
            key="test_key",
            value="test_value",
            importance=0.8,
            scope="TASK"
        )

        assert result is True
        memory_manager._memory_manager.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_recall(self, memory_manager):
        """Test recall operation"""
        result = await memory_manager.recall(key="test_key", scope="TASK")

        assert result == "test_value"
        memory_manager._memory_manager.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_forget(self, memory_manager):
        """Test forget operation"""
        result = await memory_manager.forget(key="test_key", scope="TASK")

        assert result is True
        memory_manager._memory_manager.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_share_data(self, memory_manager):
        """Test share_data operation"""
        with patch.object(memory_manager, "_shared_workspace", AsyncMock()) as mock_workspace:
            mock_workspace.share_data = AsyncMock(return_value="data_id_123")

            result = await memory_manager.share_data(
                data_type="test_type",
                data_key="test_key",
                data_content={"data": "content"},
            )

            assert result == "data_id_123"

    def test_infer_scope_from_key(self, memory_manager):
        """Test scope inference from key"""
        assert memory_manager._infer_scope_from_key("research_results") == "USER"
        assert memory_manager._infer_scope_from_key("cache_data") == "USER"
        assert memory_manager._infer_scope_from_key("framework") == "USER"
        assert memory_manager._infer_scope_from_key("current_state") == "TASK"
        assert memory_manager._infer_scope_from_key("status") == "TASK"
        assert memory_manager._infer_scope_from_key("random_key") == "TASK"

    def test_get_scope_id(self, memory_manager):
        """Test scope ID retrieval"""
        assert memory_manager._get_scope_id("USER") == "test_user"
        assert memory_manager._get_scope_id("TASK") == "test_task_123"
        assert memory_manager._get_scope_id("WORKSPACE") == "test_session"


class TestMemoryAwareAgent:
    """Tests for MemoryAwareAgent"""

    def test_initialization(self):
        """Test agent initialization"""
        agent = MemoryAwareAgent(agent_name="TestAgent", enable_memory=True)

        assert agent.agent_name == "TestAgent"
        assert agent._memory is None

    def test_get_memory(self, mock_state):
        """Test memory lazy initialization"""
        with patch("backend.agents.memory.memory_aware_agent.get_memory_manager_for_state") as mock_factory:
            mock_manager = MagicMock()
            mock_factory.return_value = mock_manager

            agent = MemoryAwareAgent(agent_name="TestAgent")
            memory = agent._get_memory(mock_state)

            assert memory == mock_manager
            mock_factory.assert_called_once()

    def test_has_memory(self):
        """Test has_memory property"""
        agent = MemoryAwareAgent(agent_name="TestAgent")
        assert not agent.has_memory

    @pytest.mark.asyncio
    async def test_convenience_methods(self, mock_state):
        """Test convenience methods delegate to memory"""
        agent = MemoryAwareAgent(agent_name="TestAgent")

        with patch.object(agent, "_memory") as mock_memory:
            mock_memory.is_enabled.return_value = True
            mock_memory.remember = AsyncMock(return_value=True)
            mock_memory.recall = AsyncMock(return_value="value")
            mock_memory.forget = AsyncMock(return_value=True)

            # Test remember
            result = await agent.remember("key", "value")
            assert result is True

            # Test recall
            result = await agent.recall("key")
            assert result == "value"

            # Test forget
            result = await agent.forget("key")
            assert result is True


@pytest.mark.asyncio
async def test_factory_function(mock_state):
    """Test get_memory_manager_for_state factory"""
    with patch("backend.agents.memory.state_bound_manager._MEMORY_AVAILABLE", False):
        manager = get_memory_manager_for_state(
            state=mock_state,
            agent_name="TestAgent",
            enable_memory=True
        )

        assert isinstance(manager, StateBoundMemoryManager)
        assert manager.agent_name == "TestAgent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
