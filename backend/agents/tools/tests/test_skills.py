#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for Skills

This module contains tests for:
- Prompt-based Skills (md files)
- Function-based Skills (py classes)
"""

import pytest
import asyncio
import json
from pathlib import Path

class TestPromptBasedSkills:
    """Tests for prompt-based Skills (Markdown files)"""

    def test_skill_files_exist(self):
        """Test that all expected Skill md files exist"""
        from backend.agents.tools.skills import __file__ as skills_init

        skills_dir = Path(skills_init).parent / "prompts"

        expected_skills = [
            "research_topic.md",
            "select_layout.md",
            "quality_check.md",
            "synthesize_info.md",
            "optimize_content.md"
        ]

        for skill_file in expected_skills:
            skill_path = skills_dir / skill_file
            assert skill_path.exists(), f"Skill file {skill_file} not found"

    def test_skill_files_have_frontmatter(self):
        """Test that Skill md files have valid YAML frontmatter"""
        from backend.agents.tools.skills import __file__ as skills_init

        skills_dir = Path(skills_init).parent / "prompts"

        for md_file in skills_dir.glob("*.md"):
            if md_file.name == "README.md":
                continue

            content = md_file.read_text()
            assert content.startswith("---"), f"{md_file.name} missing frontmatter delimiter"

    def test_markdown_skill_loader(self):
        """Test MarkdownSkillLoader can load Skills"""
        from backend.agents.tools.skills.skill_loaders import MarkdownSkillLoader
        from backend.agents.tools import __file__ as tools_init

        skills_dir = Path(tools_init).parent / "skills" / "prompts"

        loader = MarkdownSkillLoader([str(skills_dir)])
        skills = loader.load_all()

        # Should load at least the 5 skill files
        assert len(skills) >= 5

        # Check each skill has required fields
        for skill in skills:
            assert hasattr(skill, "skill_id")
            assert hasattr(skill, "name")
            assert hasattr(skill, "category")
            assert hasattr(skill, "content")

class TestFunctionBasedSkills:
    """Tests for function-based Skills (Python classes)"""

    @pytest.mark.asyncio
    async def test_research_topic_skill(self):
        """Test ResearchTopicSkill basic execution"""
        from backend.agents.tools.skills.functions.research_skill import ResearchTopicSkill

        skill = ResearchTopicSkill()

        result = await skill.execute(
            topic="Test Topic",
            depth=2,
            max_sources=5
        )

        data = json.loads(result)
        # Mock implementation should succeed
        assert "success" in data
        if data["success"]:
            assert "result" in data
            assert "topic" in data["result"]
            assert data["result"]["topic"] == "Test Topic"

    @pytest.mark.asyncio
    async def test_select_slide_layout_skill(self):
        """Test SelectSlideLayoutSkill"""
        from backend.agents.tools.skills.functions.layout_skill import SelectSlideLayoutSkill

        skill = SelectSlideLayoutSkill()

        # Test various content types
        test_cases = [
            {"content_type": "title_page", "expected_layout": "Title"},
            {"content_type": "section", "expected_layout": "Section Header"},
            {"content_type": "toc", "expected_layout": "Title and Content"},
            {"content_type": "standard", "has_image": True, "bullet_count": 5},
        ]

        for test_case in test_cases:
            result = await skill.execute(
                content_type=test_case["content_type"],
                has_image=test_case.get("has_image", False),
                bullet_count=test_case.get("bullet_count", 3)
            )

            data = json.loads(result)
            assert data["success"] == True
            assert "recommended_layout" in data["result"]

            if "expected_layout" in test_case:
                assert data["result"]["recommended_layout"] == test_case["expected_layout"]

    @pytest.mark.asyncio
    async def test_task_scheduler_skill(self):
        """Test TaskSchedulerSkill"""
        from backend.agents.tools.skills.functions.scheduler_skill import TaskSchedulerSkill

        skill = TaskSchedulerSkill()

        # Create test tasks with dependencies
        tasks = [
            {
                "id": "task1",
                "function": lambda: {"status": "done"},
                "params": {},
                "depends_on": []
            },
            {
                "id": "task2",
                "function": lambda: {"status": "done"},
                "params": {},
                "depends_on": ["task1"]
            },
            {
                "id": "task3",
                "function": lambda: {"status": "done"},
                "params": {},
                "depends_on": []
            }
        ]

        result = await skill.execute(
            tasks=tasks,
            max_parallel=2
        )

        data = json.loads(result)
        assert data["success"] == True
        assert "result" in data
        assert data["result"]["tasks_executed"] == 3

    @pytest.mark.asyncio
    async def test_retry_with_backoff_skill(self):
        """Test RetryWithBackoffSkill"""
        from backend.agents.tools.skills.functions.retry_skill import RetryWithBackoffSkill

        skill = RetryWithBackoffSkill()

        # Test with a function that succeeds
        async def success_func():
            return {"result": "success"}

        result = await skill.execute(
            func=success_func,
            max_retries=3
        )

        data = json.loads(result)
        assert data["success"] == True
        assert data["result"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_retry_with_backoff_fails_after_retries(self):
        """Test RetryWithBackoffSkill eventually fails"""
        from backend.agents.tools.skills.functions.retry_skill import RetryWithBackoffSkill

        skill = RetryWithBackoffSkill()

        # Test with a function that always fails
        call_count = 0

        async def fail_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        result = await skill.execute(
            func=fail_func,
            max_retries=2,
            base_delay=0.01  # Very short delay for testing
        )

        data = json.loads(result)
        assert data["success"] == False
        assert call_count == 2  # Should have tried max_retries times

class TestSkillMetadata:
    """Tests for Skill metadata"""

    def test_function_based_skills_have_metadata(self):
        """Test that function-based Skills have proper metadata"""
        from backend.agents.tools.skills.functions import (
            ResearchTopicSkill,
            SelectSlideLayoutSkill,
            TaskSchedulerSkill,
            RetryWithBackoffSkill,
        )

        skills = [
            ResearchTopicSkill(),
            SelectSlideLayoutSkill(),
            TaskSchedulerSkill(),
            RetryWithBackoffSkill(),
        ]

        for skill in skills:
            metadata = skill.get_skill_metadata()
            assert metadata is not None
            assert hasattr(metadata, "skill_id")
            assert hasattr(metadata, "name")
            assert hasattr(metadata, "version")
            assert hasattr(metadata, "category")
            assert hasattr(metadata, "enabled")

class TestSkillsIntegration:
    """Integration tests for Skills"""

    def test_skills_loaded_by_composite_loader(self):
        """Test that CompositeSkillLoader loads both prompt and function Skills"""
        from backend.agents.tools.skills.skill_loaders import CompositeSkillLoader
        from backend.agents.tools import __file__ as tools_init

        skills_dir = str(Path(tools_init).parent / "skills")

        config = {
            "skill_directories": [skills_dir],
            "config_directory": skills_dir + "/configs"
        }

        loader = CompositeSkillLoader(config)
        all_skills = loader.load_all()

        # Should have both executable and descriptive skills
        assert "executable" in all_skills
        assert "descriptive" in all_skills
        assert len(all_skills["descriptive"]) >= 5  # At least 5 md Skills

    def test_skill_decorator(self):
        """Test @Skill decorator functionality"""
        from backend.agents.tools.skills.skill_decorator import Skill
        from backend.agents.tools.skills.skill_metadata import SkillCategory

        @Skill(
            name="TestSkill",
            version="1.0.0",
            category=SkillCategory.UTILITY,
            tags=["test"],
            description="Test skill"
        )
        class TestSkillClass:
            pass

        # Check metadata is attached
        assert hasattr(TestSkillClass, "__skill_metadata__")

        metadata = TestSkillClass.get_skill_metadata()
        assert metadata.name == "TestSkill"
        assert metadata.version == "1.0.0"
        assert metadata.category == SkillCategory.UTILITY

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
