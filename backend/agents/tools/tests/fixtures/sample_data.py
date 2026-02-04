"""
Sample data for testing.
"""
from backend.agents.tools.registry.unified_registry import (
    ToolMetadata,
    ToolCategory,
    ToolRegistration,
)
from backend.agents.tools.skills.skill_metadata import SkillMetadata, SkillCategory


# Sample ToolMetadata instances
SAMPLE_WEB_SEARCH_METADATA = ToolMetadata(
    name="web_search",
    description="Search the web using Bing Search API",
    category=ToolCategory.SEARCH,
    parameters={
        "query": {"type": "string", "description": "Search query", "required": True},
        "num_results": {
            "type": "integer",
            "description": "Number of results to return",
            "default": 10,
        },
        "time_range": {
            "type": "string",
            "description": "Time range filter",
            "enum": ["day", "week", "month", "year", "all"],
            "default": "all",
        },
    },
    examples=[
        {"query": "Python programming", "num_results": 5},
        {"query": "AI news", "time_range": "week"},
    ],
)

SAMPLE_FETCH_URL_METADATA = ToolMetadata(
    name="fetch_url",
    description="Fetch and extract content from a URL",
    category=ToolCategory.SEARCH,
    parameters={
        "url": {"type": "string", "description": "URL to fetch", "required": True},
        "use_cache": {
            "type": "boolean",
            "description": "Whether to use cache",
            "default": True,
        },
    },
    examples=[{"url": "https://example.com/article"}],
)

SAMPLE_CREATE_PPTX_METADATA = ToolMetadata(
    name="create_pptx",
    description="Create a PowerPoint presentation",
    category=ToolCategory.PRESENTATION,
    parameters={
        "presentation_data": {
            "type": "object",
            "description": "Presentation data with slides",
            "required": True,
        },
        "template_path": {
            "type": "string",
            "description": "Path to template file",
            "default": None,
        },
        "theme": {"type": "string", "description": "Theme to apply", "default": None},
    },
    examples=[
        {
            "presentation_data": {
                "title": "Sample Presentation",
                "slides": [
                    {
                        "title": "Slide 1",
                        "content": [{"type": "text", "text": "Hello"}],
                        "layout": "TitleOnly",
                    }
                ],
            }
        }
    ],
)

SAMPLE_STATE_STORE_METADATA = ToolMetadata(
    name="state_store",
    description="Store and retrieve state data",
    category=ToolCategory.UTILITY,
    parameters={
        "operation": {
            "type": "string",
            "description": "Operation to perform",
            "enum": ["get", "set", "delete", "clear"],
            "required": True,
        },
        "key": {"type": "string", "description": "State key"},
        "value": {"type": "any", "description": "State value"},
        "namespace": {"type": "string", "description": "Namespace for isolation"},
    },
    examples=[
        {"operation": "set", "key": "user_id", "value": "12345"},
        {"operation": "get", "key": "user_id"},
    ],
)

SAMPLE_VECTOR_SEARCH_METADATA = ToolMetadata(
    name="vector_search",
    description="Search for similar content using vector embeddings",
    category=ToolCategory.SEARCH,
    parameters={
        "query": {"type": "string", "description": "Search query", "required": True},
        "top_k": {
            "type": "integer",
            "description": "Number of results to return",
            "default": 5,
        },
        "collection": {
            "type": "string",
            "description": "Collection to search in",
            "default": "default",
        },
    },
    examples=[
        {"query": "machine learning algorithms", "top_k": 10},
    ],
)

# Sample SkillMetadata instances
SAMPLE_RESEARCH_SKILL_METADATA = SkillMetadata(
    name="research_skill",
    description="Conduct comprehensive research on a given topic",
    category=SkillCategory.RESEARCH,
    parameters={
        "topic": {"type": "string", "description": "Research topic", "required": True},
        "depth": {
            "type": "string",
            "description": "Depth of research",
            "enum": ["basic", "detailed", "comprehensive"],
            "default": "detailed",
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of results",
            "default": 10,
        },
        "sources": {
            "type": "array",
            "description": "Specific sources to search",
            "items": {"type": "string"},
        },
    },
    examples=[
        {
            "topic": "Latest AI developments",
            "depth": "detailed",
            "max_results": 15,
        },
        {"topic": "Climate change", "depth": "comprehensive"},
    ],
    tags=["research", "web", "analysis"],
)

SAMPLE_LAYOUT_SKILL_METADATA = SkillMetadata(
    name="layout_skill",
    description="Suggest appropriate PowerPoint layouts for different content types",
    category=SkillCategory.PRESENTATION,
    parameters={
        "content_type": {
            "type": "string",
            "description": "Type of content to layout",
            "enum": ["title", "text", "image", "chart", "mixed", "comparison"],
            "required": True,
        },
        "aspect_ratio": {
            "type": "string",
            "description": "Slide aspect ratio",
            "enum": ["16:9", "4:3", "widescreen"],
            "default": "16:9",
        },
    },
    examples=[
        {"content_type": "title"},
        {"content_type": "image", "aspect_ratio": "16:9"},
        {"content_type": "comparison"},
    ],
    tags=["layout", "presentation", "design"],
)

SAMPLE_SCHEDULER_SKILL_METADATA = SkillMetadata(
    name="scheduler_skill",
    description="Schedule and execute tasks with dependencies",
    category=SkillCategory.UTILITY,
    parameters={
        "tasks": {
            "type": "array",
            "description": "List of tasks to execute",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "dependencies": {"type": "array", "items": {"type": "string"}},
                },
            },
            "required": True,
        },
        "max_parallel": {
            "type": "integer",
            "description": "Maximum parallel tasks",
            "default": 3,
        },
    },
    examples=[
        {
            "tasks": [
                {"id": "1", "name": "Task 1", "dependencies": []},
                {"id": "2", "name": "Task 2", "dependencies": ["1"]},
            ],
            "max_parallel": 2,
        }
    ],
    tags=["scheduling", "async", "tasks"],
)

SAMPLE_RETRY_SKILL_METADATA = SkillMetadata(
    name="retry_skill",
    description="Execute operations with automatic retry on failure",
    category=SkillCategory.UTILITY,
    parameters={
        "func": {"type": "function", "description": "Function to execute"},
        "max_retries": {
            "type": "integer",
            "description": "Maximum retry attempts",
            "default": 3,
        },
        "base_delay": {
            "type": "number",
            "description": "Base delay between retries",
            "default": 0.1,
        },
        "max_delay": {"type": "number", "description": "Maximum delay", "default": 1.0},
    },
    examples=[
        {"max_retries": 5, "base_delay": 0.5},
    ],
    tags=["retry", "resilience", "async"],
)


# Sample presentation data
SAMPLE_PRESENTATION = {
    "title": "Test Presentation",
    "slides": [
        {
            "title": "Introduction",
            "content": [
                {"type": "text", "text": "Welcome to this presentation"},
                {"type": "text", "text": "Overview of key concepts"},
            ],
            "layout": "TitleAndBody",
            "notes": "Introduction slides",
        },
        {
            "title": "Main Content",
            "content": [
                {"type": "heading", "text": "Key Point 1"},
                {"type": "text", "text": "Detailed explanation of point 1"},
                {"type": "image", "url": "https://example.com/image1.png"},
            ],
            "layout": "TitleContentAndCaption",
            "notes": "Main content slides",
        },
        {
            "title": "Conclusion",
            "content": [
                {"type": "text", "text": "Summary of key points"},
                {"type": "text", "text": "Next steps"},
            ],
            "layout": "TitleOnly",
        },
    ],
}

# Sample search results
SAMPLE_SEARCH_RESULTS = {
    "query": "artificial intelligence",
    "results": [
        {
            "title": "Introduction to AI",
            "url": "https://example.com/ai-intro",
            "snippet": "Artificial intelligence is transforming...",
            "date": "2025-01-15",
        },
        {
            "title": "Latest AI Research",
            "url": "https://example.com/ai-research",
            "snippet": "Recent advances in machine learning...",
            "date": "2025-02-01",
        },
        {
            "title": "AI Applications",
            "url": "https://example.com/ai-apps",
            "snippet": "Real-world applications of AI technology...",
            "date": "2025-01-28",
        },
    ],
    "total_results": 3,
}

# Sample research data
SAMPLE_RESEARCH_OUTPUT = {
    "topic": "Artificial Intelligence",
    "depth": "detailed",
    "findings": [
        {
            "source": "Academic Paper",
            "title": "Deep Learning Advances",
            "summary": "Recent breakthroughs in neural networks...",
            "url": "https://example.com/paper1",
        },
        {
            "source": "Industry Report",
            "title": "AI Market Trends 2025",
            "summary": "Market analysis showing growth in AI adoption...",
            "url": "https://example.com/report1",
        },
    ],
    "key_insights": [
        "AI adoption increased by 40% in 2024",
        "Healthcare and finance lead in AI implementation",
        "Natural language processing shows highest growth",
    ],
    "total_sources": 10,
}

# Sample layout mappings
LAYOUT_MAPPINGS = {
    "title": "TitleOnly",
    "subtitle": "TitleWithSubtitle",
    "text": "TitleAndBody",
    "bullet_points": "TitleAndBody",
    "image": "TitleContentAndCaption",
    "chart": "TitleAndChart",
    "mixed": "TwoColumns",
    "comparison": "Comparison",
    "section_header": "SectionHeader",
    "blank": "Blank",
}

# Sample state store data
SAMPLE_STATE_DATA = {
    "user_preferences": {
        "theme": "dark",
        "language": "en",
        "notifications": True,
    },
    "session_data": {
        "session_id": "sess_12345",
        "user_id": "user_67890",
        "started_at": "2025-02-04T10:00:00Z",
    },
    "cache_data": {
        "recent_searches": ["AI", "machine learning", "Python"],
        "favored_topics": ["technology", "science"],
    },
}

# Sample vector search results
SAMPLE_VECTOR_RESULTS = [
    {
        "id": "doc1",
        "score": 0.95,
        "metadata": {
            "title": "Introduction to Machine Learning",
            "content": "Machine learning is a subset of AI...",
            "source": "https://example.com/ml-intro",
        },
    },
    {
        "id": "doc2",
        "score": 0.87,
        "metadata": {
            "title": "Deep Learning Fundamentals",
            "content": "Deep learning uses neural networks...",
            "source": "https://example.com/dl-fund",
        },
    },
    {
        "id": "doc3",
        "score": 0.82,
        "metadata": {
            "title": "Natural Language Processing",
            "content": "NLP deals with human language...",
            "source": "https://example.com/nlp",
        },
    },
]
