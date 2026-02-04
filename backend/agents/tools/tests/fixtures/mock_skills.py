"""
Mock skills for testing.
"""
from typing import Any, Dict, List
from backend.agents.tools.skills.skill_metadata import SkillMetadata, SkillCategory
from backend.agents.tools.registry.unified_registry import ToolCategory


class MockSkill:
    """Mock skill class for testing."""

    def __init__(
        self,
        name: str,
        category: SkillCategory = SkillCategory.UTILITY,
        enabled: bool = True,
    ):
        self.name = name
        self.category = category
        self.enabled = enabled
        self.call_count = 0

    async def __call__(self, *args, **kwargs) -> Dict[str, Any]:
        self.call_count += 1
        return {"result": f"MockSkill {self.name} called", "count": self.call_count}

    def get_skill_metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name=self.name,
            description=f"Mock skill {self.name}",
            category=self.category,
            parameters={
                "input": {
                    "type": "string",
                    "description": "Input parameter",
                    "required": True,
                }
            },
            examples=[{"input": "test"}],
        )


class MockResearchSkill:
    """Mock research skill for testing."""

    async def research(
        self, topic: str, depth: str = "basic", max_results: int = 5
    ) -> Dict[str, Any]:
        """Perform mock research."""
        return {
            "topic": topic,
            "depth": depth,
            "results": [
                {"title": f"Result {i}", "url": f"http://example.com/{i}"}
                for i in range(max_results)
            ],
            "count": max_results,
        }


class MockLayoutSkill:
    """Mock layout skill for testing."""

    def suggest_layout(self, content_type: str) -> str:
        """Suggest a layout for the given content type."""
        layout_map = {
            "title": "TitleOnly",
            "text": "TitleAndBody",
            "image": "TitleContentAndCaption",
            "mixed": "TwoColumns",
        }
        return layout_map.get(content_type, "Blank")


class MockSchedulerSkill:
    """Mock scheduler skill for testing."""

    async def execute_schedule(
        self, tasks: List[Dict], max_parallel: int = 3
    ) -> Dict[str, Any]:
        """Execute tasks according to schedule."""
        results = []
        for task in tasks:
            results.append({"task_id": task["id"], "status": "completed"})
        return {"results": results, "total": len(results)}


class MockRetrySkill:
    """Mock retry skill for testing."""

    import asyncio

    def __init__(self, max_retries: int = 3, base_delay: float = 0.1):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.attempt_count = 0

    async def execute_with_retry(self, func, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        for attempt in range(self.max_retries):
            self.attempt_count = attempt + 1
            try:
                if self.attempt_count < 3:  # Fail first 2 attempts for testing
                    raise Exception("Simulated failure")
                result = await func(*args, **kwargs)
                return {"result": result, "attempts": self.attempt_count}
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await self.asyncio.sleep(self.base_delay * (2**attempt))


# Sample skill functions for testing
def sample_skill_function(input_text: str) -> Dict[str, Any]:
    """Sample skill function for testing."""
    return {"processed": input_text.upper(), "length": len(input_text)}


async def async_sample_skill_function(input_text: str) -> Dict[str, Any]:
    """Async sample skill function for testing."""
    return {"processed_async": input_text.lower(), "reversed": input_text[::-1]}


def failing_skill_function() -> Dict[str, Any]:
    """Skill function that always fails."""
    raise ValueError("This skill always fails")


# Sample skill metadata
SAMPLE_SKILL_METADATA = SkillMetadata(
    name="sample_skill",
    description="A sample skill for testing",
    category=SkillCategory.UTILITY,
    parameters={
        "input": {"type": "string", "description": "Input text", "required": True}
    },
    examples=[{"input": "test text"}],
    tags=["test", "sample"],
)

SAMPLE_RESEARCH_METADATA = SkillMetadata(
    name="research_skill",
    description="Performs web research on a topic",
    category=SkillCategory.RESEARCH,
    parameters={
        "topic": {"type": "string", "description": "Research topic", "required": True},
        "depth": {
            "type": "string",
            "description": "Research depth",
            "default": "basic",
            "enum": ["basic", "detailed", "comprehensive"],
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum results",
            "default": 5,
        },
    },
    examples=[
        {"topic": "AI", "depth": "basic", "max_results": 3},
        {"topic": "Machine Learning", "depth": "detailed"},
    ],
    tags=["research", "web"],
)

SAMPLE_LAYOUT_METADATA = SkillMetadata(
    name="layout_skill",
    description="Suggests appropriate layouts for content",
    category=SkillCategory.PRESENTATION,
    parameters={
        "content_type": {
            "type": "string",
            "description": "Type of content",
            "required": True,
            "enum": ["title", "text", "image", "mixed"],
        }
    },
    examples=[
        {"content_type": "title"},
        {"content_type": "image"},
    ],
    tags=["layout", "presentation"],
)
