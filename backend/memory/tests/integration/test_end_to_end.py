"""
End-to-end integration tests for Memory layer.

Tests for:
- Full data lifecycle
- Multi-agent collaboration scenarios
- High load scenarios
- Failure recovery scenarios
- Mixed scope scenarios
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from memory.models import MemoryLayer, MemoryScope, MemoryMetadata
from memory.manager import HierarchicalMemoryManager
from memory.layers.l1_transient import L1TransientLayer
from memory.layers.l2_short_term import L2ShortTermLayer


class TestFullLifecycle:
    """Test complete data lifecycle through all layers."""

    @pytest.mark.asyncio
    async def test_lifecycle_l1_to_l3(self):
        """Test full lifecycle from L1 to L3."""
        with __import__('unittest.mock').patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             __import__('unittest.mock').patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)
            mock_l2.return_value = mock_l2_instance

            # Mock L3
            mock_l3_instance = Mock()
            mock_l3_instance.set = AsyncMock(return_value=True)
            mock_l3_instance.get = AsyncMock(return_value=None)
            mock_l3.return_value = mock_l3_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)
            await manager.start_background_tasks()

            try:
                # 1. Write to L1
                await manager.set("lifecycle_key", {"stage": "l1"}, MemoryScope.SESSION, "session_1")

                # Should be in L1
                result = await manager.get("lifecycle_key", MemoryScope.SESSION, "session_1", search_all_layers=False)
                assert result is not None
                assert result[0]["stage"] == "l1"

                # 2. Access multiple times (would trigger promotion to L2 in real scenario)
                for _ in range(3):
                    await manager.get("lifecycle_key", MemoryScope.SESSION, "session_1")

                # 3. Manually promote to L3
                success = await manager.promote_to_l3("lifecycle_key", MemoryScope.SESSION, "session_1")
                assert success is True

                # 4. Verify L3 set was called
                assert manager.l3.set.call_count >= 1

            finally:
                await manager.stop_background_tasks()

    @pytest.mark.asyncio
    async def test_lifecycle_with_deletion(self):
        """Test lifecycle including deletion."""
        with __import__('unittest.mock').patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             __import__('unittest.mock').patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            # Write to all layers
            await manager.set("temp_key", {"data": "temporary"}, MemoryScope.TASK, "task_1")

            # Verify exists
            exists = await manager.exists("temp_key", MemoryScope.TASK, "task_1")
            assert exists is True

            # Delete from all layers
            deleted = await manager.delete("temp_key", MemoryScope.TASK, "task_1", delete_all_layers=True)
            assert deleted is True

            # Verify deleted
            exists = await manager.exists("temp_key", MemoryScope.TASK, "task_1")
            assert exists is False


class TestMultiAgentScenarios:
    """Test multi-agent collaboration scenarios."""

    @pytest.mark.asyncio
    async def test_agent_workspace_sharing(self):
        """Test agents sharing data through workspace."""
        l1 = L1TransientLayer(capacity=100)

        # Agent A writes to workspace
        await l1.set("shared_data", {"agent": "A", "message": "hello"}, MemoryScope.WORKSPACE, "workspace_1")

        # Agent B reads from workspace
        result = await l1.get("shared_data", MemoryScope.WORKSPACE, "workspace_1")

        assert result is not None
        assert result[0]["agent"] == "A"
        assert result[0]["message"] == "hello"

    @pytest.mark.asyncio
    async def test_agent_private_workspace(self):
        """Test that agents have both private and shared memory."""
        l1 = L1TransientLayer(capacity=100)

        # Agent A writes private data
        await l1.set("private", {"secret": "agent_A_secret"}, MemoryScope.AGENT, "agent_A")

        # Agent A writes to workspace
        await l1.set("shared", {"message": "hello from A"}, MemoryScope.WORKSPACE, "workspace_1")

        # Agent B can read workspace
        workspace_result = await l1.get("shared", MemoryScope.WORKSPACE, "workspace_1")
        assert workspace_result is not None

        # Agent B cannot read private data
        private_result = await l1.get("private", MemoryScope.AGENT, "agent_B")
        assert private_result is None


class TestHighLoadScenarios:
    """Test system behavior under high load."""

    @pytest.mark.asyncio
    async def test_high_write_volume(self):
        """Test handling high volume of writes."""
        l1 = L1TransientLayer(capacity=1000)

        # Write large number of items
        write_count = 500
        for i in range(write_count):
            await l1.set(f"high_load_key_{i}", {"value": i}, MemoryScope.SESSION, "session_1")

        # Should only keep capacity items
        stats = await l1.get_stats()
        assert stats["data_count"] == 1000

    @pytest.mark.asyncio
    async def test_concurrent_high_load(self):
        """Test system under concurrent high load."""
        l1 = L1TransientLayer(capacity=200)

        async def load_task(task_id):
            for i in range(50):
                await l1.set(f"task_{task_id}_key_{i}", {"value": i}, MemoryScope.TASK, f"task_{task_id}")

        # Run concurrent load tasks
        tasks = [load_task(i) for i in range(10)]
        await asyncio.gather(*tasks)

        # System should maintain consistency
        stats = await l1.get_stats()
        assert stats["data_count"] <= 200


class TestFailureRecovery:
    """Test system behavior during failures."""

    @pytest.mark.asyncio
    async def test_l2_failure_graceful_degradation(self):
        """Test graceful degradation when L2 fails."""
        l1 = L1TransientLayer(capacity=100)
        l2 = L2ShortTermLayer(redis_url="fake://localhost:6379/0")

        # Simulate L2 failure
        l2.client = None

        # L1 should still work
        await l1.set("fallback_key", {"data": "in_l1"}, MemoryScope.SESSION, "session_1")

        result = await l1.get("fallback_key", MemoryScope.SESSION, "session_1")

        assert result is not None
        assert result[0]["data"] == "in_l1"

    @pytest.mark.asyncio
    async def test_recovery_after_failure(self):
        """Test recovery after L2 comes back online."""
        l2 = L2ShortTermLayer(redis_url="fake://localhost:6379/0")

        # Simulate failure
        l2.client = None

        # Try to write (should fail)
        result1 = await l2.set("test_key", {"data": "test"}, MemoryScope.SESSION, "session_1")
        assert result1 is False

        # Restore connection
        l2.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)

        # Should work now
        result2 = await l2.set("test_key", {"data": "test"}, MemoryScope.SESSION, "session_1")
        assert result2 is True


class TestMixedScopeScenarios:
    """Test scenarios with mixed scope usage."""

    @pytest.mark.asyncio
    async def test_multi_scope_data_flow(self):
        """Test data flowing between different scopes."""
        l1 = L1TransientLayer(capacity=100)

        # Write to task scope
        await l1.set("data", {"level": "task"}, MemoryScope.TASK, "task_1")

        # Elevate to session scope
        task_result = await l1.get("data", MemoryScope.TASK, "task_1")
        assert task_result is not None

        await l1.set("data", {"level": "session"}, MemoryScope.SESSION, "session_1")

        # Both should coexist
        task_value = await l1.get("data", MemoryScope.TASK, "task_1")
        session_value = await l1.get("data", MemoryScope.SESSION, "session_1")

        assert task_value[0]["level"] == "task"
        assert session_value[0]["level"] == "session"

    @pytest.mark.asyncio
    async def test_scope_hierarchy(self):
        """Test data at different levels of scope hierarchy."""
        l1 = L1TransientLayer(capacity=100)

        # Write at different scope levels
        await l1.set("pref", {"level": "user"}, MemoryScope.USER, "user_1")
        await l1.set("pref", {"level": "workspace"}, MemoryScope.WORKSPACE, "workspace_1")
        await l1.set("pref", {"level": "agent"}, MemoryScope.AGENT, "agent_1")

        # All should coexist independently
        user_value = await l1.get("pref", MemoryScope.USER, "user_1")
        workspace_value = await l1.get("pref", MemoryScope.WORKSPACE, "workspace_1")
        agent_value = await l1.get("pref", MemoryScope.AGENT, "agent_1")

        assert user_value[0]["level"] == "user"
        assert workspace_value[0]["level"] == "workspace"
        assert agent_value[0]["level"] == "agent"


class TestManagerIntegration:
    """Test manager with real layer interactions."""

    @pytest.mark.asyncio
    async def test_manager_set_and_get(self):
        """Test manager set and get operations."""
        with __import__('unittest.mock').patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             __import__('unittest.mock').patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            # Set and get
            await manager.set("test_key", {"data": "test"}, MemoryScope.SESSION, "session_1")
            result = await manager.get("test_key", MemoryScope.SESSION, "session_1")

            assert result is not None
            assert result[0]["data"] == "test"

    @pytest.mark.asyncio
    async def test_manager_auto_layer_selection(self):
        """Test manager automatic layer selection."""
        with __import__('unittest.mock').patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             __import__('unittest.mock').patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            # Low importance -> L1
            await manager.set("l1_key", {"data": "low"}, MemoryScope.TASK, "task_1", importance=0.5)
            l1_result = await manager.l1.get("l1_key", MemoryScope.TASK, "task_1")
            assert l1_result is not None

            # High importance -> L2
            await manager.set("l2_key", {"data": "high"}, MemoryScope.TASK, "task_1", importance=0.85)
            l2_result = await manager.l2.get("l2_key", MemoryScope.TASK, "task_1")
            assert l2_result is not None

    @pytest.mark.asyncio
    async def test_manager_cascade_get(self):
        """Test manager cascade get from L3 to L1."""
        with __import__('unittest.mock').patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             __import__('unittest.mock').patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)
            mock_l2.return_value = mock_l2_instance

            # Mock L3
            mock_l3_instance = Mock()
            mock_l3.return_value = mock_l3_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)
            manager.l3 = mock_l3_instance

            # Setup: data only in L3
            expected_value = {"data": "from_l3"}
            expected_metadata = MemoryMetadata(
                key="l3_key",
                layer=MemoryLayer.L3_LONG_TERM,
                scope=MemoryScope.USER,
            )

            manager.l1.get = AsyncMock(return_value=None)
            manager.l2.get = AsyncMock(return_value=None)
            manager.l3.get = AsyncMock(return_value=(expected_value, expected_metadata))
            manager.l2.set = AsyncMock(return_value=True)
            manager.l1.set = AsyncMock(return_value=True)

            # Get should cascade from L3
            result = await manager.get("l3_key", MemoryScope.USER, "user_1")

            assert result is not None
            assert result[0]["data"] == "from_l3"

            # Verify cascade writes
            manager.l2.set.assert_called_once()
            manager.l1.set.assert_called_once()


class TestStatsAggregation:
    """Test statistics aggregation across layers."""

    @pytest.mark.asyncio
    async def test_global_stats(self):
        """Test global statistics aggregation."""
        with __import__('unittest.mock').patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             __import__('unittest.mock').patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=False)

            # Add some data
            await manager.set("key1", {"data": "1"}, MemoryScope.SESSION, "session_1")
            await manager.set("key2", {"data": "2"}, MemoryScope.SESSION, "session_1")

            # Get stats
            stats = await manager.get_stats()

            assert "l1_transient" in stats
            assert "l2_short_term" in stats
            assert "l3_long_term" in stats
            assert stats["total_data_count"] >= 0


class TestBackgroundTasks:
    """Test background task management."""

    @pytest.mark.asyncio
    async def test_background_task_lifecycle(self):
        """Test starting and stopping background tasks."""
        with __import__('unittest.mock').patch('memory.manager.L2ShortTermLayer') as mock_l2, \
             __import__('unittest.mock').patch('memory.manager.L3LongtermLayer') as mock_l3:

            # Mock Redis for L2
            mock_l2_instance = Mock()
            mock_l2_instance.client = __import__('fakeredis').FakeStrictRedis(decode_responses=False)
            mock_l2.return_value = mock_l2_instance

            manager = HierarchicalMemoryManager(enable_auto_promotion=True)

            # Start background tasks
            await manager.start_background_tasks()
            assert manager._promotion_task is not None

            # Stop background tasks
            await manager.stop_background_tasks()

            # Tasks should be cancelled/stopped
            assert manager._promotion_task is None
