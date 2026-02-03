# Tools & Skills System

This directory contains the **Tools & Skills** system for the MultiAgentPPT project - a comprehensive framework for providing agents with capabilities to interact with external services and execute complex workflows.

## 📁 Directory Structure

```
backend/agents/tools/
├── mcp/                          # MCP Tools (External API Access)
│   ├── __init__.py
│   ├── base_mcp_tool.py          # Base class for all MCP tools
│   ├── web_search.py             # Bing Search API integration
│   ├── fetch_url.py              # Web scraping with readability
│   ├── search_images.py          # Unsplash/Pexels image search
│   ├── create_pptx.py            # PowerPoint generation
│   ├── state_store.py            # Redis/file state storage
│   └── vector_search.py          # Vector database search wrapper
│
├── skills/                       # Skills Framework
│   ├── __init__.py
│   ├── skill_decorator.py        # @Skill decorator for Python skills
│   ├── skill_metadata.py         # Skill metadata classes
│   ├── skill_wrapper.py          # Wrappers for skill integration
│   ├── skill_loaders.py          # Loaders for different skill formats
│   ├── skill_registry.py         # Central skill registry
│   ├── skill_metadata_lazy.py    # Lazy loading support
│   ├── skill_metadata_progressive.py
│   ├── managers/
│   │   └── skill_manager.py      # High-level skill management API
│   ├── prompts/                  # [NEW] Prompt-based Skills (md)
│   │   ├── README.md
│   │   ├── research_topic.md
│   │   ├── select_layout.md
│   │   ├── quality_check.md
│   │   ├── synthesize_info.md
│   │   └── optimize_content.md
│   └── functions/                # [NEW] Function-based Skills (py)
│       ├── __init__.py
│       ├── research_skill.py
│       ├── layout_skill.py
│       ├── scheduler_skill.py
│       └── retry_skill.py
│
├── registry/                     # Unified Tool Registry
│   ├── __init__.py
│   ├── tool_registry.py          # [DEPRECATED] Old registry
│   └── unified_registry.py       # [CURRENT] Unified registry
│
├── search/                       # [DEPRECATED] Legacy search tools
│   └── document_search.py
│
├── media/                        # [DEPRECATED] Legacy media tools
│   └── image_search.py
│
├── tests/                        # [NEW] Test suite
│   ├── __init__.py
│   ├── test_mcp_tools.py
│   └── test_skills.py
│
└── README.md                     # This file
```

## 🎯 Core Concepts

### MCP Tools vs Skills

| Aspect | MCP Tools | Skills |
|--------|-----------|---------|
| **Purpose** | Access external APIs and services | Encapsulate workflows and knowledge |
| **Format** | Python async functions | Python classes **or** Markdown files |
| **Use Case** | Web search, image search, PPT generation | Research methodology, layout selection |
| **Execution** | Direct function calls | Can be called or used as prompts |

### Tool Categories

- **SEARCH**: Web search, URL fetching
- **MEDIA**: Image search, media processing
- **DATABASE**: State storage, caching
- **VECTOR**: Semantic search
- **UTILITY**: PPT generation, task scheduling
- **MCP**: All MCP protocol tools

## 🚀 Quick Start

### 1. Using MCP Tools

```python
from backend.agents.tools.mcp import web_search, fetch_url, search_images

# Web search
result = await web_search(
    query="artificial intelligence",
    num_results=5,
    search_engine="bing"
)

# Fetch URL content
content = await fetch_url(
    url="https://example.com/article",
    extract_type="main_content"
)

# Search for images
images = await search_images(
    query="business meeting",
    num_results=5,
    orientation="landscape"
)
```

### 2. Using Function-Based Skills

```python
from backend.agents.tools.skills.functions import ResearchTopicSkill

# Create skill instance
skill = ResearchTopicSkill()

# Execute skill
result = await skill.execute(
    topic="Quantum Computing",
    depth=3,
    max_sources=10
)
```

### 3. Using Prompt-Based Skills

```python
from backend.agents.tools.skills.managers.skill_manager import SkillManager

skill_manager = SkillManager()

# Get descriptive skills for system prompt
content = skill_manager.get_descriptive_content_for_prompt(
    skill_ids=["research_topic", "quality_check"]
)

# Inject into agent prompt
system_prompt = f"You are a research assistant.\n\n{content}"
```

### 4. Using Unified Registry

```python
from backend.agents.tools.registry.unified_registry import get_unified_registry

registry = get_unified_registry()

# Get ADK tools for agent
tools = registry.get_adk_tools(categories=["SEARCH", "MEDIA"])

# Use in agent creation
agent = Agent(tools=tools, ...)
```

## 📦 MCP Tools Reference

### web_search

Execute web search using Bing Search API.

```python
await web_search(
    query: str,           # Search query
    num_results: int = 5, # Number of results (1-10)
    search_engine: str = "bing",
    language: str = "zh-CN",
    time_range: str = "any"  # any, day, week, month, year
)
```

**Returns:**
```json
{
  "success": true,
  "result": {
    "results": [
      {
        "title": "Result Title",
        "url": "https://example.com",
        "snippet": "Description...",
        "source": "example.com"
      }
    ]
  }
}
```

### fetch_url

Fetch and extract content from URLs.

```python
await fetch_url(
    url: str,                     # Target URL
    timeout: int = 10,            # Timeout in seconds
    extract_type: str = "main_content",  # full, main_content, text_only
    use_cache: bool = True        # Use caching
)
```

**Returns:**
```json
{
  "success": true,
  "result": {
    "url": "https://example.com",
    "title": "Page Title",
    "text_content": "Extracted text...",
    "word_count": 1500
  }
}
```

### search_images

Search for images using Unsplash/Pexels.

```python
await search_images(
    query: str,                   # Search query
    num_results: int = 5,         # Number of results
    orientation: str = "landscape",  # landscape, portrait, squarish
    size: str = "large",          # small, medium, large, original
    color: str = "any",           # Color filter
    source: str = "unsplash"      # unsplash, pexels
)
```

### create_pptx

Create PowerPoint files from structured data.

```python
await create_pptx(
    slides: List[Dict],           # Slide data
    output_path: str,             # Output file path
    template_path: str = None,    # Optional template
    theme: Dict = None            # Optional theme
)
```

**Slide data format:**
```python
{
    "layout": "Title and Content",
    "title": "Slide Title",
    "content": ["Point 1", "Point 2"],
    "images": ["url1", "url2"],
    "notes": "Speaker notes"
}
```

### state_store

Store and retrieve agent state.

```python
await state_store(
    operation: str,       # get, set, delete, list
    key: str,            # State key
    value: Any,          # State value (for set)
    namespace: str = "default"
)
```

### vector_search

Semantic vector search in knowledge base.

```python
await vector_search(
    query: str,
    collection: str = "default",
    top_k: int = 5,
    filter_metadata: Dict = None
)
```

## 🎨 Skills Reference

### Prompt-Based Skills (Markdown)

Located in `skills/prompts/`:

| Skill | Description |
|-------|-------------|
| `research_topic.md` | Deep research methodology |
| `select_layout.md` | Slide layout selection framework |
| `quality_check.md` | Content quality assessment |
| `synthesize_info.md` | Information synthesis techniques |
| `optimize_content.md` | Content optimization best practices |

### Function-Based Skills (Python)

Located in `skills/functions/`:

#### ResearchTopicSkill

Comprehensive research workflow combining web search and content extraction.

```python
from backend.agents.tools.skills.functions import ResearchTopicSkill

skill = ResearchTopicSkill()
result = await skill.execute(
    topic="Machine Learning",
    depth=3,
    max_sources=10
)
```

#### SelectSlideLayoutSkill

Decision framework for selecting appropriate slide layouts.

```python
from backend.agents.tools.skills.functions import SelectSlideLayoutSkill

skill = SelectSlideLayoutSkill()
result = await skill.execute(
    content_type="standard",
    has_image=True,
    bullet_count=5
)
```

#### TaskSchedulerSkill

DAG-based task scheduling with parallel execution.

```python
from backend.agents.tools.skills.functions import TaskSchedulerSkill

skill = TaskSchedulerSkill()
result = await skill.execute(
    tasks=[
        {
            "id": "task1",
            "function": my_func,
            "params": {},
            "depends_on": []
        }
    ],
    max_parallel=3
)
```

#### RetryWithBackoffSkill

Automatic retry with exponential backoff.

```python
from backend.agents.tools.skills.functions import RetryWithBackoffSkill

skill = RetryWithBackoffSkill()
result = await skill.execute(
    func=my_function,
    max_retries=3,
    base_delay=1.0
)
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# MCP Tools Configuration
BING_SEARCH_API_KEY=your_key_here
UNSPLASH_ACCESS_KEY=your_key_here
PEXELS_API_KEY=your_key_here
REDIS_URL=redis://localhost:6379/0

# MCP Cache Configuration
MCP_CACHE_DIR=./data/mcp_cache
MCP_CACHE_ENABLED=true
MCP_CACHE_TTL=3600

# State Storage
MCP_STATE_DIR=./data/state
MCP_STATE_NAMESPACE=default
```

### Dependencies

Install required packages:

```bash
pip install -r backend/requirements.txt
```

New MCP tool dependencies:
- `readability-lxml>=0.8.1` - Web content extraction
- `html2text>=2020.1.16` - HTML to text conversion
- `python-pptx>=0.6.21` - PowerPoint generation
- `lxml>=4.9.0` - XML processing

## 🧪 Testing

Run the test suite:

```bash
# Test MCP tools
pytest backend/agents/tools/tests/test_mcp_tools.py -v

# Test Skills
pytest backend/agents/tools/tests/test_skills.py -v

# All tests
pytest backend/agents/tools/tests/ -v
```

## 📝 Development

### Creating a New MCP Tool

1. Create file in `backend/agents/tools/mcp/`
2. Inherit from `BaseMCPTool`
3. Implement `execute()` method
4. Add to `mcp/__init__.py`
5. Register in `unified_registry.py`

Example:

```python
from .base_mcp_tool import BaseMCPTool

class MyTool(BaseMCPTool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="My tool description"
        )

    async def execute(self, **kwargs) -> str:
        # Implementation
        return self._success({"result": "data"})

async def my_tool(**kwargs) -> str:
    tool = MyTool()
    return await tool.execute(**kwargs)
```

### Creating a New Skill

#### Prompt-Based Skill (Markdown)

Create `skills/prompts/my_skill.md`:

```markdown
---
skill_id: my_skill
name: My Skill
version: 1.0.0
category: utility
tags: [example]
description: My skill description
---

# My Skill

## Overview
Description of what this skill does...

## When to Use
- Condition 1
- Condition 2

## Steps
1. Step one
2. Step two
```

#### Function-Based Skill (Python)

Create `skills/functions/my_skill.py`:

```python
from ..skill_decorator import Skill
from ..skill_metadata import SkillCategory

@Skill(
    name="MySkill",
    version="1.0.0",
    category=SkillCategory.UTILITY,
    description="My skill description"
)
class MySkill:
    async def execute(self, **kwargs) -> str:
        # Implementation
        return result

    def get_skill_metadata(self):
        from ..skill_metadata import SkillMetadata
        return SkillMetadata(
            skill_id="my_skill",
            name="MySkill",
            version="1.0.0",
            category=SkillCategory.UTILITY,
            description="My skill"
        )
```

## 🔄 Migration from Legacy Tools

### DocumentSearch → web_search / vector_search

```python
# Old (DEPRECATED)
from backend.agents.tools.search.document_search import DocumentSearch
result = await DocumentSearch(keyword="AI", number=5)

# New (Recommended)
from backend.agents.tools.mcp import web_search, vector_search

# For web search
result = await web_search(query="AI", num_results=5)

# For semantic search
result = await vector_search(query="AI", top_k=5)
```

### SearchImage → search_images

```python
# Old (DEPRECATED)
from backend.agents.tools.media.image_search import SearchImage
result = await SearchImage(query="flowers")

# New (Recommended)
from backend.agents.tools.mcp import search_images
result = await search_images(
    query="flowers",
    num_results=5,
    source="unsplash"
)
```

## 📚 Additional Documentation

- [External Tools Design Guide](../../../../../docs/tools/external_tools_guide.md) - Comprehensive design documentation
- [Prompt Design Guide](../../../../../docs/tools/prompt_design_guide.md) - How to write effective prompts
- [Skills Framework](../../../../../docs/tools/skills_framework.md) - Skills architecture

## 🤝 Contributing

When adding new tools or skills:

1. Follow existing patterns and conventions
2. Add comprehensive docstrings
3. Include error handling
4. Write tests
5. Update this README

## 📄 License

Part of the MultiAgentPPT project.
