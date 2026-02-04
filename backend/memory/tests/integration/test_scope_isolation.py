"""
Integration tests for scope isolation in memory layers.

Tests for:
- Task-level scope isolation
- Session-level scope isolation
- Agent-level scope isolation
- Workspace-level scope sharing
- User-level scope global visibility
- Cross-scope data leak prevention
"""

import pytest
from unittest.mock import Mock

from memory.models import MemoryLayer, MemoryScope
from memory.layers.l1_transient import L1TransientLayer
from memory.layers.l2_short_term import L2ShortTermLayer


class TestTaskScopeIsolation:
    """Test task-level scope isolation."""

    @pytest.mark.asyncio
    async def test_different_tasks_isolated(self):
        """Test that different tasks have isolated data."""
        layer = L1TransientLayer(capacity=100)

        # Write same key to different tasks
        await layer.set("shared_key", {"task": "task1"}, MemoryScope.TASK, "task_1")
        await layer.set("shared_key", {"task": "task2"}, MemoryScope.TASK, "task_2")

        # Verify isolation
        value1, _ = await layer.get("shared_key", MemoryScope.TASK, "task_1")
        value2, _ = await layer.get("shared_key", MemoryScope.TASK, "task_2")

        assert value1["task"] == "task1"
        assert value2["task"] == "task2"

    @pytest.mark.asyncio
    async def test_task_not_visible_to_other_tasks(self):
        """Test that task data is not visible to other tasks."""
        layer = L1TransientLayer(capacity=100)

        # Write to task_1
        await layer.set("secret", {"data": "secret"}, MemoryScope.TASK, "task_1")

        # Try to read from task_2
        result = await layer.get("secret", MemoryScope.TASK, "task_2")

        assert result is None


class TestSessionScopeIsolation:
    """Test session-level scope isolation."""

    @pytest.mark.asyncio
    async def test_different_sessions_isolated(self):
        """Test that different sessions have isolated data."""
        layer = L1TransientLayer(capacity=100)

        # Write same key to different sessions
        await layer.set("user_data", {"session": "session1"}, MemoryScope.SESSION, "session_1")
        await layer.set("user_data", {"session": "session2"}, MemoryScope.SESSION, "session_2")

        # Verify isolation
        value1, _ = await layer.get("user_data", MemoryScope.SESSION, "session_1")
        value2, _ = await layer.get("user_data", MemoryScope.SESSION, "session_2")

        assert value1["session"] == "session1"
        assert value2["session"] == "session2"

    @pytest.mark.asyncio
    async def test_session_isolation_in_l2(self):
        """Test session isolation in L2 layer."""
        l2 = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
        l2.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)

        # Write same key to different sessions
        await l2.set("session_key", {"id": "s1"}, MemoryScope.SESSION, "session_1")
        await l2.set("session_key", {"id": "s2"}, MemoryScope.SESSION, "session_2")

        # Verify isolation
        value1, _ = await l2.get("session_key", MemoryScope.SESSION, "session_1")
        value2, _ = await l2.get("session_key", MemoryScope.SESSION, "session_2")

        assert value1["id"] == "s1"
        assert value2["id"] == "s2"


class TestAgentScopeIsolation:
    """Test agent-level scope isolation."""

    @pytest.mark.asyncio
    async def test_different_agents_isolated(self):
        """Test that different agents have isolated data."""
        layer = L1TransientLayer(capacity=100)

        # Write same key to different agents
        await layer.set("agent_state", {"agent": "agent1"}, MemoryScope.AGENT, "agent_1")
        await layer.set("agent_state", {"agent": "agent2"}, MemoryScope.AGENT, "agent_2")

        # Verify isolation
        value1, _ = await layer.get("agent_state", MemoryScope.AGENT, "agent_1")
        value2, _ = await layer.get("agent_state", MemoryScope.AGENT, "agent_2")

        assert value1["agent"] == "agent1"
        assert value2["agent"] == "agent2"

    @pytest.mark.asyncio
    async def test_agent_private_data(self):
        """Test that agent private data is isolated."""
        layer = L1TransientLayer(capacity=100)

        # Agent 1 writes private data
        await layer.set("private_key", {"secret": "agent1_secret"}, MemoryScope.AGENT, "agent_1")

        # Agent 2 cannot access it
        result = await layer.get("private_key", MemoryScope.AGENT, "agent_2")

        assert result is None


class TestWorkspaceScopeSharing:
    """Test workspace-level scope sharing."""

    @pytest.mark.asyncio
    async def test_workspace_shared_by_agents(self):
        """Test that workspace data is shared among agents in same workspace."""
        layer = L1TransientLayer(capacity=100)

        # Agent 1 writes to workspace
        await layer.set(
            "workspace_data",
            {"message": "hello"},
            MemoryScope.WORKSPACE,
            "workspace_abc",
        )

        # Agent 2 reads from workspace
        value, _ = await layer.get("workspace_data", MemoryScope.WORKSPACE, "workspace_abc")

        assert value["message"] == "hello"

    @pytest.mark.asyncio
    async def test_different_workspaces_isolated(self):
        """Test that different workspaces are isolated."""
        layer = L1TransientLayer(capacity=100)

        # Write to different workspaces
        await layer.set("data", {"workspace": "ws1"}, MemoryScope.WORKSPACE, "workspace_1")
        await layer.set("data", {"workspace": "ws2"}, MemoryScope.WORKSPACE, "workspace_2")

        # Verify isolation
        value1, _ = await layer.get("data", MemoryScope.WORKSPACE, "workspace_1")
        value2, _ = await layer.get("data", MemoryScope.WORKSPACE, "workspace_2")

        assert value1["workspace"] == "ws1"
        assert value2["workspace"] == "ws2"


class TestUserScopeGlobal:
    """Test user-level scope global visibility."""

    @pytest.mark.asyncio
    async def test_user_scope_globally_visible(self):
        """Test that user scope data is globally visible to that user."""
        layer = L1TransientLayer(capacity=100)

        # Write to user scope
        await layer.set("user_pref", {"theme": "dark"}, MemoryScope.USER, "user_123")

        # Should be accessible from any session/agent for same user
        value1, _ = await layer.get("user_pref", MemoryScope.USER, "user_123")
        value2, _ = await layer.get("user_pref", MemoryScope.USER, "user_123")

        assert value1["theme"] == "dark"
        assert value2["theme"] == "dark"

    @pytest.mark.asyncio
    async def test_different_users_isolated(self):
        """Test that different users have isolated data."""
        layer = L1TransientLayer(capacity=100)

        # Write for different users
        await layer.set("pref", {"user": "user1"}, MemoryScope.USER, "user_1")
        await layer.set("pref", {"user": "user2"}, MemoryScope.USER, "user_2")

        # Verify isolation
        value1, _ = await layer.get("pref", MemoryScope.USER, "user_1")
        value2, _ = await layer.get("pref", MemoryScope.USER, "user_2")

        assert value1["user"] == "user1"
        assert value2["user"] == "user2"


class TestCrossScopeDataLeak:
    """Test prevention of cross-scope data leaks."""

    @pytest.mark.asyncio
    async def test_no_cross_scope_leak_task_to_session(self):
        """Test that task data doesn't leak to session scope."""
        layer = L1TransientLayer(capacity=100)

        # Write to task scope
        await layer.set("sensitive", {"data": "task_only"}, MemoryScope.TASK, "task_1")

        # Try to read from session scope (should not work)
        result = await layer.get("sensitive", MemoryScope.SESSION, "session_1")

        assert result is None

    @pytest.mark.asyncio
    async def test_no_cross_scope_leak_agent_to_workspace(self):
        """Test that agent data doesn't leak to workspace scope."""
        layer = L1TransientLayer(capacity=100)

        # Write to agent scope
        await layer.set("private", {"data": "agent_private"}, MemoryScope.AGENT, "agent_1")

        # Try to read from workspace scope (should not work)
        result = await layer.get("private", MemoryScope.WORKSPACE, "workspace_1")

        assert result is None

    @pytest.mark.asyncio
    async def test_clear_scope_only_affects_target(self):
        """Test that clearing a scope only affects that scope."""
        layer = L1TransientLayer(capacity=100)

        # Write same key to different scopes
        await layer.set("data", {"scope": "task"}, MemoryScope.TASK, "task_1")
        await layer.set("data", {"scope": "session"}, MemoryScope.SESSION, "session_1")

        # Clear only task scope
        await layer.clear_scope(MemoryScope.TASK, "task_1")

        # Task scope should be empty
        task_result = await layer.get("data", MemoryScope.TASK, "task_1")
        assert task_result is None

        # Session scope should still exist
        session_result = await layer.get("data", MemoryScope.SESSION, "session_1")
        assert session_result is not None
        assert session_result[0]["scope"] == "session"

    @pytest.mark.asyncio
    async def test_list_keys_only_in_scope(self):
        """Test that listing keys only returns keys from that scope."""
        layer = L1TransientLayer(capacity=100)

        # Write to different scopes
        await layer.set("key1", {"data": "1"}, MemoryScope.TASK, "task_1")
        await layer.set("key2", {"data": "2"}, MemoryScope.SESSION, "session_1")
        await layer.set("key3", {"data": "3"}, MemoryScope.TASK, "task_1")

        # List keys in task scope
        task_keys = await layer.list_keys(MemoryScope.TASK, "task_1")

        # Should only have task keys
        assert "key1" in task_keys
        assert "key3" in task_keys
        assert "key2" not in task_keys


class TestScopeHierarchy:
    """Test scope hierarchy and relationships."""

    @pytest.mark.asyncio
    async def test_multiple_scopes_coexist(self):
        """Test that multiple scopes can coexist for same key."""
        layer = L1TransientLayer(capacity=100)

        # Write same key to different scopes with different scope_ids
        await layer.set("shared", {"type": "task"}, MemoryScope.TASK, "id_1")
        await layer.set("shared", {"type": "session"}, MemoryScope.SESSION, "id_1")
        await layer.set("shared", {"type": "agent"}, MemoryScope.AGENT, "id_1")

        # All should coexist
        task_value, _ = await layer.get("shared", MemoryScope.TASK, "id_1")
        session_value, _ = await layer.get("shared", MemoryScope.SESSION, "id_1")
        agent_value, _ = await layer.get("shared", MemoryScope.AGENT, "id_1")

        assert task_value["type"] == "task"
        assert session_value["type"] == "session"
        assert agent_value["type"] == "agent"

    @pytest.mark.asyncio
    async def test_scope_delete_doesnt_affect_others(self):
        """Test that deleting from one scope doesn't affect others."""
        layer = L1TransientLayer(capacity=100)

        # Write same key to different scopes
        await layer.set("key", {"scope": "task"}, MemoryScope.TASK, "id_1")
        await layer.set("key", {"scope": "session"}, MemoryScope.SESSION, "id_1")

        # Delete from task scope
        await layer.delete("key", MemoryScope.TASK, "id_1")

        # Task scope should be empty
        task_result = await layer.get("key", MemoryScope.TASK, "id_1")
        assert task_result is None

        # Session scope should still exist
        session_result = await layer.get("key", MemoryScope.SESSION, "id_1")
        assert session_result is not None


class TestScopeIsolationWithPromotion:
    """Test scope isolation during data promotion."""

    @pytest.mark.asyncio
    async def test_promotion_preserves_scope(self):
        """Test that promotion preserves scope information."""
        l1 = L1TransientLayer(capacity=100)
        l2 = L2ShortTermLayer(redis_url="fake://localhost:6379/0")
        l2.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)

        # Write to task scope in L1
        await l1.set("task_data", {"value": "important"}, MemoryScope.TASK, "task_1")

        # Access to mark as important
        await l1.get("task_data", MemoryScope.TASK, "task_1")
        await l1.get("task_data", MemoryScope.TASK, "task_1")

        # Manually move to L2
        value, metadata = await l1.get("task_data", MemoryScope.TASK, "task_1")
        metadata.layer = MemoryLayer.L2_SHORT_TERM
        await l2.set("task_data", value, MemoryScope.TASK, "task_1", metadata=metadata)

        # Verify scope is preserved in L2
        l2_value, l2_metadata = await l2.get("task_data", MemoryScope.TASK, "task_1")

        assert l2_value["value"] == "important"
        assert l2_metadata.scope == MemoryScope.TASK

        # Verify it's not accessible from different scope
        other_result = await l2.get("task_data", MemoryScope.SESSION, "session_1")
        assert other_result is None
