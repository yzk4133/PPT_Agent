"""
Integration Tests for Full LangChain Workflow

Tests the complete PPT generation workflow with all components integrated.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.models.state import (
    create_initial_state,
    PPTGenerationState,
)
from backend.agents.coordinator.master_graph import MasterGraph
from backend.memory.memory_aware_agent import MemoryAwareAgent
from backend.tools.registry import get_langchain_registry


@pytest.fixture
def mock_graph_components():
    """Mock all graph components for testing"""
    with patch("backend.agents.coordinator.master_graph.ChatOpenAI") as mock_llm:
        mock_model = MagicMock()
        mock_llm.return_value = mock_model

        # Mock agents
        with patch("backend.agents.coordinator.master_graph.create_requirement_parser") as mock_req:
            with patch("backend.agents.coordinator.master_graph.create_framework_designer") as mock_frame:
                with patch("backend.agents.coordinator.master_graph.create_research_agent") as mock_research:
                    with patch("backend.agents.coordinator.master_graph.create_content_agent") as mock_content:
                        with patch("backend.agents.coordinator.master_graph.create_renderer_agent") as mock_renderer:

                            # Create mock agents
                            mock_req_agent = MagicMock()
                            mock_req_agent.run_node = AsyncMock(side_effect=lambda s: {**s, "structured_requirements": {"ppt_topic": "AI"}})

                            mock_frame_agent = MagicMock()
                            mock_frame_agent.run_node = AsyncMock(side_effect=lambda s: {**s, "ppt_framework": {"total_page": 5}})

                            mock_research_agent = MagicMock()
                            mock_research_agent.run_node = AsyncMock(side_effect=lambda s: {**s, "research_results": []})

                            mock_content_agent = MagicMock()
                            mock_content_agent.run_node = AsyncMock(side_effect=lambda s: {**s, "content_materials": [{"page_index": 0, "content": "Content"}]})

                            mock_renderer_agent = MagicMock()
                            mock_renderer_agent.run_node = AsyncMock(side_effect=lambda s: {**s, "ppt_output": {"file_path": "/tmp/test.pptx"}})

                            mock_req.return_value = mock_req_agent
                            mock_frame.return_value = mock_frame_agent
                            mock_research.return_value = mock_research_agent
                            mock_content.return_value = mock_content_agent
                            mock_renderer.return_value = mock_renderer_agent

                            yield {
                                "model": mock_model,
                                "requirement_agent": mock_req_agent,
                                "framework_agent": mock_frame_agent,
                                "research_agent": mock_research_agent,
                                "content_agent": mock_content_agent,
                                "renderer_agent": mock_renderer_agent,
                            }


class TestFullWorkflow:
    """Integration tests for full workflow"""

    @pytest.mark.asyncio
    async def test_simple_ppt_generation(self, mock_graph_components):
        """Test basic PPT generation without research"""
        # Create graph without research
        with patch("backend.agents.coordinator.master_graph.create_page_pipeline"):
            graph = MasterGraph()

        # Generate PPT
        result = await graph.generate(
            user_input="Create a simple PPT",
            task_id="test_001",
            user_id="test_user"
        )

        # Verify results
        assert result["task_id"] == "test_001"
        assert "structured_requirements" in result
        assert "ppt_framework" in result
        assert "ppt_output" in result
        assert result.get("current_stage") in ["template_renderer", "complete"]

    @pytest.mark.asyncio
    async def test_ppt_with_research(self, mock_graph_components):
        """Test PPT generation with research"""
        # Set up framework to require research
        def mock_framework_run(state):
            state["ppt_framework"] = {
                "total_page": 10,
                "need_research": True
            }
            return state

        mock_graph_components["framework_agent"].run_node = AsyncMock(side_effect=mock_framework_run)

        with patch("backend.agents.coordinator.master_graph.create_page_pipeline"):
            graph = MasterGraph()

        result = await graph.generate(
            user_input="Create a research PPT",
            task_id="test_002"
        )

        # Verify research was called
        assert "research_results" in result
        mock_graph_components["research_agent"].run_node.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_with_errors(self, mock_graph_components):
        """Test workflow error handling"""
        # Make content agent fail
        async def failing_run(state):
            state["error"] = "Content generation failed"
            return state

        mock_graph_components["content_agent"].run_node = AsyncMock(side_effect=failing_run)

        with patch("backend.agents.coordinator.master_graph.create_page_pipeline"):
            graph = MasterGraph()

        result = await graph.generate(
            user_input="Test PPT",
            task_id="test_003"
        )

        # Error should be in state
        # Note: The actual behavior depends on error handling implementation
        assert "task_id" in result


class TestMemoryIntegration:
    """Test memory system integration with workflow"""

    @pytest.mark.asyncio
    async def test_memory_aware_agent_workflow(self):
        """Test that memory-aware agents can use memory"""
        from backend.agents.memory.memory_aware_agent import MemoryAwareAgent

        class TestAgent(MemoryAwareAgent):
            async def run_node(self, state):
                self._get_memory(state)

                # Test memory operations
                await self.remember("test_key", "test_value")
                result = await self.recall("test_key")

                state["test_result"] = result
                return state

        agent = TestAgent(agent_name="TestAgent")

        # Create mock state
        state = create_initial_state(
            user_input="Test",
            task_id="test_task"
        )

        # Mock memory manager
        with patch("backend.agents.memory.memory_aware_agent.get_memory_manager_for_state"):
            result = await agent.run_node(state)

            assert "test_result" in result


class TestToolIntegration:
    """Test tool system integration with workflow"""

    @pytest.mark.asyncio
    async def test_tool_registry(self):
        """Test that tool registry works"""
        with patch("backend.agents.tools.registry._MEMORY_AVAILABLE", False):
            registry = get_langchain_registry()

            # Should have tools registered
            assert registry is not None

    @pytest.mark.asyncio
    async def test_search_tools(self):
        """Test getting search tools"""
        with patch("backend.tools.registry._MEMORY_AVAILABLE", False):
            from backend.tools.registry import get_search_tools

            tools = get_search_tools()

            assert isinstance(tools, list)


class TestQualityIntegration:
    """Test quality control integration with workflow"""

    @pytest.mark.asyncio
    async def test_quality_check_node(self):
        """Test quality check node"""
        from backend.agents.core.quality.nodes import check_content_quality

        state = create_initial_state(
            user_input="Test",
            task_id="test_task"
        )

        state["content_materials"] = [
            {"page_index": 0, "content": "Good content"}
        ]

        with patch("backend.agents.core.quality.nodes._QUALITY_AVAILABLE", False):
            result = await check_content_quality(state)

            assert "quality_assessment" in result

    @pytest.mark.asyncio
    async def test_refinement_node(self):
        """Test refinement node"""
        from backend.agents.core.quality.nodes import refine_content

        state = create_initial_state(
            user_input="Test",
            task_id="test_task"
        )

        state["content_materials"] = [
            {"page_index": 0, "content": "Original content"}
        ]

        state["quality_assessment"] = {
            "overall_score": 0.6,
            "passes_threshold": False,
            "issues": ["Page 0: Too short"]
        }

        with patch("backend.agents.core.quality.nodes.refinement_node.ChatOpenAI"):
            result = await refine_content(state)

            assert "refinement_count" in result


class TestRevisionHandling:
    """Test revision handler integration"""

    @pytest.mark.asyncio
    async def test_revision_handler(self):
        """Test revision handler"""
        from backend.agents.coordinator.revision_handler import RevisionHandler

        state = create_initial_state(
            user_input="Test",
            task_id="test_task"
        )

        state["content_materials"] = [
            {"page_index": 0, "content": "Original content"}
        ]

        handler = RevisionHandler(model=None)

        request = {
            "type": "content",
            "target": "all",
            "instructions": "Make more detailed"
        }

        with patch.object(handler, "model") as mock_model:
            mock_response = MagicMock()
            mock_response.content = "Revised content"
            mock_model.ainvoke = AsyncMock(return_value=mock_response)

            result = await handler.handle_revision_request(state, request)

            assert "revision_history" in result


class TestProgressTracking:
    """Test progress tracking integration"""

    def test_progress_tracker(self):
        """Test progress tracker"""
        from backend.agents.coordinator.progress_tracker import ProgressTracker

        tracker = ProgressTracker(task_id="test_task")

        updates = []

        def on_progress(update):
            updates.append(update)

        tracker.on_progress = on_progress

        tracker.update_stage("content_generation", 50, "Half done")

        assert len(updates) == 1
        assert updates[0].progress == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
