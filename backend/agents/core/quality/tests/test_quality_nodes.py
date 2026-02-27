"""
Tests for Quality Control Nodes
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.core.quality.nodes import (
    check_content_quality,
    should_refine_content,
    check_framework_quality,
    should_refine_framework,
)
from backend.agents.models.state import create_initial_state


@pytest.fixture
def sample_state():
    """Create sample state for testing"""
    return create_initial_state(
        user_input="Create a PPT about AI",
        task_id="test_task_123"
    )


@pytest.fixture
def state_with_content(sample_state):
    """Create state with content materials"""
    sample_state["content_materials"] = [
        {
            "page_index": 0,
            "content": "This is a well-written page about artificial intelligence. It has sufficient content and is clearly structured.",
        },
        {
            "page_index": 1,
            "content": "Short.",
        },
    ]
    return sample_state


@pytest.fixture
def state_with_framework(sample_state):
    """Create state with PPT framework"""
    sample_state["ppt_framework"] = {
        "total_page": 3,
        "ppt_framework": [
            {
                "page_type": "title",
                "title": "AI Presentation",
                "content_description": "Introduction to AI"
            },
            {
                "page_type": "content",
                "title": "What is AI",
                # Missing content_description
            },
        ]
    }
    return sample_state


class TestCheckContentQuality:
    """Tests for check_content_quality node"""

    @pytest.mark.asyncio
    async def test_no_quality_system(self, sample_state):
        """Test behavior when quality system is unavailable"""
        with patch("backend.agents.core.quality.nodes._QUALITY_AVAILABLE", False):
            result = await check_content_quality(sample_state)

            assert "quality_assessment" in result
            assert result["quality_assessment"]["passes_threshold"] is True
            assert result["quality_assessment"]["system_available"] is False

    @pytest.mark.asyncio
    async def test_no_content_materials(self, sample_state):
        """Test behavior with no content materials"""
        with patch("backend.agents.core.quality.nodes._QUALITY_AVAILABLE", True):
            result = await check_content_quality(sample_state)

            assert "quality_assessment" in result
            assert result["quality_assessment"]["passes_threshold"] is False

    @pytest.mark.asyncio
    async def test_with_content_materials(self, state_with_content):
        """Test quality check with actual content"""
        with patch("backend.agents.core.quality.nodes._QUALITY_AVAILABLE", True):
            # Mock the assessor
            mock_assessor = MagicMock()
            mock_assessment = MagicMock()
            mock_assessment.overall_score = 0.85
            mock_assessment.passes_threshold = True
            mock_assessment.dimension_scores = []

            mock_assessor.assess = AsyncMock(return_value=mock_assessment)

            result = await check_content_quality(
                state_with_content,
                assessor=mock_assessor,
                threshold=0.8
            )

            assert "quality_assessment" in result
            assert result["quality_assessment"]["overall_score"] == 0.85
            assert result["quality_assessment"]["passes_threshold"] is True

    @pytest.mark.asyncio
    async def test_custom_threshold(self, state_with_content):
        """Test custom threshold"""
        with patch("backend.agents.core.quality.nodes._QUALITY_AVAILABLE", True):
            mock_assessor = MagicMock()
            mock_assessment = MagicMock()
            mock_assessment.overall_score = 0.7
            mock_assessment.passes_threshold = False
            mock_assessment.dimension_scores = []

            mock_assessor.assess = AsyncMock(return_value=mock_assessment)

            result = await check_content_quality(
                state_with_content,
                assessor=mock_assessor,
                threshold=0.8
            )

            assert result["quality_assessment"]["passes_threshold"] is False
            assert result["quality_assessment"]["threshold"] == 0.8


class TestShouldRefineContent:
    """Tests for should_refine_content conditional edge"""

    def test_passes_threshold(self):
        """Test when quality passes threshold"""
        state = {
            "quality_assessment": {
                "passes_threshold": True,
                "overall_score": 0.9
            },
            "refinement_count": 0
        }

        result = should_refine_content(state)

        assert result == "proceed"

    def test_fails_threshold(self):
        """Test when quality fails threshold"""
        state = {
            "quality_assessment": {
                "passes_threshold": False,
                "overall_score": 0.6
            },
            "refinement_count": 0
        }

        result = should_refine_content(state)

        assert result == "refine"

    def test_max_refinements_reached(self):
        """Test when max refinements is reached"""
        state = {
            "quality_assessment": {
                "passes_threshold": False,
                "overall_score": 0.6
            },
            "refinement_count": 3  # Max reached
        }

        result = should_refine_content(state)

        assert result == "proceed"  # Should proceed despite failing

    def test_no_assessment(self):
        """Test when no assessment exists"""
        state = {
            "refinement_count": 0
        }

        result = should_refine_content(state)

        assert result == "proceed"  # Default to proceed


class TestCheckFrameworkQuality:
    """Tests for check_framework_quality node"""

    @pytest.mark.asyncio
    async def test_no_quality_system(self, sample_state):
        """Test when quality system unavailable"""
        with patch("backend.agents.core.quality.nodes._QUALITY_AVAILABLE", False):
            result = await check_framework_quality(sample_state)

            assert "framework_quality_assessment" in result
            assert result["framework_quality_assessment"]["system_available"] is False

    @pytest.mark.asyncio
    async def test_no_framework(self, sample_state):
        """Test with no framework"""
        with patch("backend.agents.core.quality.nodes._QUALITY_AVAILABLE", True):
            result = await check_framework_quality(sample_state)

            assert result["framework_quality_assessment"]["passes_threshold"] is False

    @pytest.mark.asyncio
    async def test_complete_framework(self, state_with_framework):
        """Test with complete framework"""
        with patch("backend.agents.core.quality.nodes._QUALITY_AVAILABLE", True):
            # Fix the framework to be complete
            state_with_framework["ppt_framework"]["ppt_framework"][1]["content_description"] = "Content"

            result = await check_framework_quality(state_with_framework)

            assert "framework_quality_assessment" in result
            # Should have high score for complete framework
            assert result["framework_quality_assessment"]["overall_score"] > 0.5

    @pytest.mark.asyncio
    async def test_incomplete_framework(self, state_with_framework):
        """Test with incomplete framework"""
        with patch("backend.agents.core.quality.nodes._QUALITY_AVAILABLE", True):
            result = await check_framework_quality(state_with_framework)

            assert "framework_quality_assessment" in result
            # Should have lower score due to missing field
            assert result["framework_quality_assessment"]["missing_fields"] > 0


class TestShouldRefineFramework:
    """Tests for should_refine_framework conditional edge"""

    def test_passes_threshold(self):
        """Test when framework passes threshold"""
        state = {
            "framework_quality_assessment": {
                "passes_threshold": True,
                "overall_score": 0.9
            }
        }

        result = should_refine_framework(state)

        assert result == "proceed"

    def test_fails_threshold(self):
        """Test when framework fails threshold"""
        state = {
            "framework_quality_assessment": {
                "passes_threshold": False,
                "overall_score": 0.6
            }
        }

        result = should_refine_framework(state)

        assert result == "refine"

    def test_no_assessment(self):
        """Test when no assessment exists"""
        state = {}

        result = should_refine_framework(state)

        assert result == "proceed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
