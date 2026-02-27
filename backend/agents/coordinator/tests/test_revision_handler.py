"""
Tests for Revision Handler and Progress Tracker
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from backend.agents.coordinator.revision_handler import (
    RevisionHandler,
    RevisionRequest,
)
from backend.agents.coordinator.progress_tracker import (
    ProgressTracker,
    ProgressUpdate,
    StageProgressMapper,
    create_progress_tracker,
)
from backend.agents.models.state import create_initial_state


@pytest.fixture
def sample_state():
    """Create sample state for testing"""
    state = create_initial_state(
        user_input="Create a PPT about AI",
        task_id="test_task_123"
    )
    state["content_materials"] = [
        {
            "page_index": 0,
            "content": "Original content for page 0",
        },
        {
            "page_index": 1,
            "content": "Original content for page 1",
        },
    ]
    return state


class TestRevisionRequest:
    """Tests for RevisionRequest dataclass"""

    def test_creation(self):
        """Test creating a revision request"""
        request = RevisionRequest(
            type="content",
            target="all",
            instructions="Make the content more detailed"
        )

        assert request.type == "content"
        assert request.target == "all"
        assert request.instructions == "Make the content more detailed"

    def test_with_page_indices(self):
        """Test revision request with specific page indices"""
        request = RevisionRequest(
            type="content",
            target="page_index",
            instructions="Fix page 0",
            page_indices=[0]
        )

        assert request.page_indices == [0]


class TestRevisionHandler:
    """Tests for RevisionHandler"""

    def test_initialization(self):
        """Test handler initialization"""
        with patch("backend.agents.coordinator.revision_handler.ChatOpenAI"):
            handler = RevisionHandler(model=None)
            assert handler is not None

    @pytest.mark.asyncio
    async def test_handle_content_revision_all_pages(self, sample_state):
        """Test handling content revision for all pages"""
        handler = RevisionHandler(model=None)

        with patch.object(handler, "model") as mock_model:
            mock_response = MagicMock()
            mock_response.content = "Revised content"
            mock_model.ainvoke = AsyncMock(return_value=mock_response)

            request = {
                "type": "content",
                "target": "all",
                "instructions": "Make more detailed"
            }

            result = await handler.handle_revision_request(sample_state, request)

            assert "revision_history" in result
            assert len(result["revision_history"]) == 1
            assert result["revision_history"][0]["type"] == "content"

    @pytest.mark.asyncio
    async def test_handle_content_revision_specific_page(self, sample_state):
        """Test handling content revision for specific page"""
        handler = RevisionHandler(model=None)

        with patch.object(handler, "model") as mock_model:
            mock_response = MagicMock()
            mock_response.content = "Revised content for page 0"
            mock_model.ainvoke = AsyncMock(return_value=mock_response)

            request = {
                "type": "content",
                "target": "page_index",
                "instructions": "Fix page 0",
                "page_indices": [0]
            }

            result = await handler.handle_revision_request(sample_state, request)

            # Only page 0 should be revised
            assert result["content_materials"][0]["revised"] is True
            assert "revised" not in result["content_materials"][1]

    @pytest.mark.asyncio
    async def test_handle_style_revision(self, sample_state):
        """Test handling style revision"""
        handler = RevisionHandler(model=None)

        with patch.object(handler, "model") as mock_model:
            mock_response = MagicMock()
            mock_response.content = "Styled content"
            mock_model.ainvoke = AsyncMock(return_value=mock_response)

            with patch.object(handler, "_revise_content", new=AsyncMock(return_value=sample_state)):
                request = {
                    "type": "style",
                    "target": "all",
                    "instructions": "Make more formal"
                }

                result = await handler.handle_revision_request(sample_state, request)

                assert result["revision_history"][0]["type"] == "style"

    @pytest.mark.asyncio
    async def test_handle_structure_revision(self, sample_state):
        """Test handling structure revision"""
        handler = RevisionHandler(model=None)

        request = {
            "type": "structure",
            "target": "all",
            "instructions": "Reorganize sections"
        }

        result = await handler.handle_revision_request(sample_state, request)

        assert result["needs_framework_revision"] is True
        assert result["framework_revision_instructions"] == "Reorganize sections"

    @pytest.mark.asyncio
    async def test_apply_incremental_revision(self, sample_state):
        """Test applying incremental revision"""
        handler = RevisionHandler(model=None)

        new_content = "Incrementally revised content"
        result = await handler.apply_incremental_revision(
            sample_state,
            page_index=0,
            new_content=new_content
        )

        assert result["content_materials"][0]["content"] == new_content
        assert result["content_materials"][0]["revised"] is True

    def test_get_revision_summary(self, sample_state):
        """Test getting revision summary"""
        handler = RevisionHandler(model=None)

        sample_state["revision_history"] = [
            {
                "timestamp": "2024-01-01T00:00:00",
                "type": "content",
                "instructions": "Fix content",
                "target": "all"
            },
            {
                "timestamp": "2024-01-01T01:00:00",
                "type": "style",
                "instructions": "Make formal",
                "target": "all"
            }
        ]

        summary = handler.get_revision_summary(sample_state)

        assert summary["total_revisions"] == 2
        assert summary["latest_revision"]["type"] == "style"
        assert "content" in summary["revision_types"]
        assert "style" in summary["revision_types"]


class TestProgressUpdate:
    """Tests for ProgressUpdate"""

    def test_creation(self):
        """Test creating progress update"""
        update = ProgressUpdate(
            stage="content_generation",
            progress=50,
            message="Generating content"
        )

        assert update.stage == "content_generation"
        assert update.progress == 50
        assert update.message == "Generating content"
        assert isinstance(update.timestamp, datetime)

    def test_to_dict(self):
        """Test converting to dictionary"""
        update = ProgressUpdate(
            stage="content_generation",
            progress=50,
            message="Generating content"
        )

        data = update.to_dict()

        assert data["stage"] == "content_generation"
        assert data["progress"] == 50
        assert "timestamp" in data


class TestProgressTracker:
    """Tests for ProgressTracker"""

    def test_initialization(self):
        """Test tracker initialization"""
        tracker = ProgressTracker(task_id="test_task")

        assert tracker.task_id == "test_task"
        assert tracker._current_stage == "init"
        assert tracker._current_progress == 0

    def test_update_stage(self):
        """Test updating progress"""
        tracker = ProgressTracker(task_id="test_task")

        tracker.update_stage("content_generation", 50, "Half done")

        assert tracker._current_stage == "content_generation"
        assert tracker._current_progress == 50

    def test_update_stage_with_callback(self):
        """Test update with callback"""
        callback_called = []

        def callback(update):
            callback_called.append(update)

        tracker = ProgressTracker(task_id="test_task", on_progress=callback)

        tracker.update_stage("content_generation", 50, "Half done")

        assert len(callback_called) == 1
        assert callback_called[0].stage == "content_generation"
        assert callback_called[0].progress == 50

    def test_stage_complete(self):
        """Test marking stage complete"""
        stage_complete_called = []

        def callback(stage, state):
            stage_complete_called.append((stage, state))

        tracker = ProgressTracker(
            task_id="test_task",
            on_stage_complete=callback
        )

        state = {"task_id": "test"}
        tracker.stage_complete("content_generation", state)

        assert len(stage_complete_called) == 1
        assert stage_complete_called[0][0] == "content_generation"

    def test_error(self):
        """Test error handling"""
        error_called = []

        def callback(stage, error):
            error_called.append((stage, error))

        tracker = ProgressTracker(
            task_id="test_task",
            on_error=callback
        )

        test_error = Exception("Test error")
        tracker.error("content_generation", test_error)

        assert len(error_called) == 1
        assert error_called[0][0] == "content_generation"
        assert error_called[0][1] == test_error

    def test_get_elapsed_time(self):
        """Test getting elapsed time"""
        tracker = ProgressTracker(task_id="test_task")

        elapsed = tracker.get_elapsed_time()

        assert elapsed >= 0
        assert elapsed < 1  # Should be very small

    def test_get_history(self):
        """Test getting progress history"""
        tracker = ProgressTracker(task_id="test_task")

        tracker.update_stage("stage1", 25, "First")
        tracker.update_stage("stage2", 50, "Second")

        history = tracker.get_history()

        assert len(history) == 2
        assert history[0]["stage"] == "stage1"
        assert history[1]["stage"] == "stage2"

    def test_get_summary(self):
        """Test getting progress summary"""
        tracker = ProgressTracker(task_id="test_task")

        tracker.update_stage("content_generation", 75, "Almost done")

        summary = tracker.get_summary()

        assert summary["task_id"] == "test_task"
        assert summary["current_stage"] == "content_generation"
        assert summary["current_progress"] == 75


class TestStageProgressMapper:
    """Tests for StageProgressMapper"""

    def test_get_progress_for_stage(self):
        """Test getting progress for stage"""
        progress = StageProgressMapper.get_progress_for_stage("framework_designer")

        # framework_designer comes after requirement_parser (10%)
        assert progress == 10

    def test_get_stage_progress_range(self):
        """Test getting stage progress range"""
        start, end = StageProgressMapper.get_stage_progress_range("content_generation")

        # content_generation has weight 25%
        # Before it: requirement_parser(10) + framework_designer(20) + research(30) = 60
        assert start == 60
        assert end == 85

    def test_custom_weights(self):
        """Test with custom stage weights"""
        custom_weights = {
            "requirement_parser": 20,
            "framework_designer": 30,
            "research": 50,
        }

        progress = StageProgressMapper.get_progress_for_stage(
            "research",
            custom_weights
        )

        # research comes after requirement_parser(20) + framework_designer(30) = 50
        assert progress == 50


class TestCreateProgressTracker:
    """Tests for create_progress_tracker factory"""

    def test_factory_function(self):
        """Test factory function"""
        state = create_initial_state(
            user_input="Test",
            task_id="test_task"
        )

        tracker = create_progress_tracker(state)

        assert tracker.task_id == "test_task"

    def test_factory_with_callbacks(self):
        """Test factory with callbacks"""
        state = create_initial_state(
            user_input="Test",
            task_id="test_task"
        )

        progress_cb = MagicMock()
        stage_cb = MagicMock()
        error_cb = MagicMock()

        tracker = create_progress_tracker(
            state,
            on_progress=progress_cb,
            on_stage_complete=stage_cb,
            on_error=error_cb
        )

        assert tracker.on_progress == progress_cb
        assert tracker.on_stage_complete == stage_cb
        assert tracker.on_error == error_cb


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
