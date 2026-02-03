---
skill_id: research_topic
name: Research Topic Skill
version: 1.0.0
category: research
tags: [research, analysis, web, deep-dive]
description: Comprehensive methodology for conducting deep research on any topic
author: MultiAgentPPT
enabled: true
---

# ResearchTopicSkill - Deep Research Methodology

## Overview
This Skill provides a systematic approach to conducting comprehensive research on any topic. It combines web search, content extraction, and information synthesis to produce high-quality research reports.

## When to Use
- User needs in-depth information about a topic
- Exploring new domains or technologies
- Gathering data for presentations or reports
- Finding latest trends and developments

## Research Process

### Step 1: Topic Decomposition
Break down the main topic into 3-7 sub-topics for systematic research.

**Consider:**
- Different dimensions (technical, business, historical, etc.)
- Key questions that need answers
- User's potential interests and goals
- Depth vs breadth trade-off

**Example:**
For topic "Artificial Intelligence in Healthcare":
- Current applications of AI in healthcare
- Benefits and advantages
- Challenges and limitations
- Future trends and predictions
- Regulatory and ethical considerations
- Case studies and success stories
- Key companies and technologies

### Step 2: Parallel Web Search
Use `web_search` tool to search for each sub-topic.

**Search Parameters:**
- `num_results`: 5-10 results per sub-topic
- `time_range`: Use "month" or "year" for recent topics
- `language`: Match user's language preference

### Step 3: Deep Content Extraction
For the most relevant 5-10 URLs from search results, use `fetch_url` to get complete content.

**Extraction Type:**
- Use `main_content` for articles and blog posts
- Use `text_only` for faster processing when HTML parsing fails

### Step 4: Information Synthesis
Combine and analyze information from multiple sources.

**Key Elements to Extract:**
- Core concepts and definitions
- Statistics and data points
- Expert opinions and quotes
- Trends and patterns
- Conflicting viewpoints (if any)
- Source credibility assessment

### Step 5: Report Generation
Produce a structured research report.

## Output Format

```json
{
  "topic": "Research Topic",
  "researched_at": "2024-02-03T10:30:00Z",
  "subtopics": [
    {
      "name": "Sub-topic Name",
      "key_findings": [
        "Finding 1",
        "Finding 2"
      ],
      "sources": ["url1", "url2"]
    }
  ],
  "summary": "Executive summary of key findings...",
  "key_statistics": [
    {"statistic": "Value", "source": "URL"}
  ],
  "trends": ["Trend 1", "Trend 2"],
  "challenges": ["Challenge 1", "Challenge 2"],
  "future_outlook": "Brief outlook...",
  "all_sources": ["url1", "url2", ...]
}
```

## Available Tools
- `web_search`: Search the web for information
- `fetch_url`: Extract full content from URLs
- `vector_search`: Search existing knowledge base (optional)

## Best Practices
1. **Start Broad**: Begin with general searches, then narrow down to specifics
2. **Verify Sources**: Cross-check information from multiple credible sources
3. **Track Sources**: Always record where information came from
4. **Stay Current**: For rapidly evolving topics, use recent time filters
5. **Synthesize, Don't Copy**: Combine information into original insights
6. **Acknowledge Uncertainty**: If information is conflicting or unclear, state this

## Quality Indicators
✓ Covers multiple dimensions of the topic
✓ Includes recent data and developments
✓ Cites credible sources
✓ Presents balanced view (including counterarguments)
✓ Extracts actionable insights
✓ Identifies knowledge gaps
