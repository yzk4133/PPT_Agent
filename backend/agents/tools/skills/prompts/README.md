# Skills Prompts

This directory contains **prompt-based Skills** - reusable knowledge and methodology templates in Markdown format.

## What are Prompt-based Skills?

Prompt-based Skills are Markdown files with YAML frontmatter that describe:
- How to perform a specific task
- Decision-making processes
- Best practices and patterns
- Methodologies for complex workflows

These Skills are injected into agent system prompts to guide LLM behavior.

## File Structure

Each Skill file follows this format:

```markdown
---
skill_id: unique_skill_id
name: Human Readable Name
version: 1.0.0
category: research
tags: [research, analysis, web]
description: Brief description of what this Skill does
author: MultiAgentPPT
enabled: true
---

# Skill Name

## Overview
Description of what this Skill does...

## When to Use
- Condition 1
- Condition 2

## Steps
1. Step one
2. Step two
...

## Tips & Best Practices
- Tip 1
- Tip 2
```

## Available Skills

| Skill ID | Name | Description |
|----------|------|-------------|
| `research_topic` | Deep Research | Comprehensive research methodology |
| `select_layout` | Layout Selection | Choose appropriate slide layouts |
| `quality_check` | Quality Check | Validate content quality |
| `synthesize_info` | Information Synthesis | Combine information from multiple sources |
| `optimize_content` | Content Optimization | Improve content clarity and impact |

## Using These Skills

Skills in this directory are automatically loaded by `MarkdownSkillLoader` and made available through `SkillManager`.

To use a Skill in an agent:

```python
from backend.agents.tools.skills.managers.skill_manager import SkillManager

skill_manager = SkillManager()

# Get descriptive content for system prompt
content = skill_manager.get_descriptive_content_for_prompt(
    skill_ids=["research_topic", "quality_check"]
)

# Inject into agent prompt
system_prompt = f"You are a research assistant.\n\n{content}"
```
