#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skill: Research Topic

Implements the ResearchTopicSkill - a comprehensive research workflow
that combines web search, content extraction, and information synthesis.
"""

import json
import asyncio
import logging
from typing import Optional, Dict, Any, List

from ..skill_decorator import Skill
from ..skill_metadata import SkillCategory

logger = logging.getLogger(__name__)

@Skill(
    name="ResearchTopicSkill",
    version="1.0.0",
    category=SkillCategory.SEARCH,
    tags=["research", "web", "synthesis"],
    description="Execute comprehensive research on a topic using web search and content extraction",
    author="MultiAgentPPT",
    enabled=True
)
class ResearchTopicSkill:
    """
    ResearchTopicSkill - Deep Research Workflow

    This Skill implements a complete research process:
    1. Decompose topic into sub-topics
    2. Parallel web search for each sub-topic
    3. Extract content from key URLs
    4. Synthesize information
    5. Generate structured report
    """

    def __init__(self):
        """Initialize the research skill"""
        self.logger = logger

    async def execute(
        self,
        topic: str,
        depth: int = 3,
        max_sources: int = 10,
        tool_context: Optional[Any] = None
    ) -> str:
        """
        Execute deep research on a topic

        Args:
            topic: Research topic
            depth: Research depth (1=quick, 3=standard, 5=deep)
            max_sources: Maximum number of sources to analyze
            tool_context: Optional tool context with access to other tools

        Returns:
            JSON string with research report
        """
        self.logger.info(f"[ResearchTopicSkill] Starting research on: {topic}")

        try:
            # Step 1: Decompose topic
            subtopics = await self._decompose_topic(topic, depth)
            self.logger.info(f"  → Decomposed into {len(subtopics)} sub-topics")

            # Step 2: Parallel web search
            search_results = await self._parallel_search(subtopics, max_sources)
            self.logger.info(f"  → Completed {len(search_results)} searches")

            # Step 3: Fetch key pages
            detailed_content = await self._fetch_key_pages(search_results, max_sources)
            self.logger.info(f"  → Fetched {len(detailed_content)} detailed pages")

            # Step 4: Synthesize information
            synthesized = await self._synthesize_information(topic, detailed_content)
            self.logger.info(f"  → Synthesized information")

            # Step 5: Generate report
            report = await self._generate_report(topic, subtopics, synthesized, search_results)
            self.logger.info(f"  → Research complete")

            return json.dumps({
                "success": True,
                "result": report
            }, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"Research error: {e}", exc_info=True)
            return json.dumps({
                "success": False,
                "error": str(e),
                "result": None
            }, ensure_ascii=False)

    async def _decompose_topic(self, topic: str, depth: int) -> List[str]:
        """Decompose topic into sub-topics using LLM"""
        # This would call LLM to decompose the topic
        # For now, return a simple decomposition
        num_subtopics = 3 + depth
        return [
            f"{topic} - Overview and definition",
            f"{topic} - Key benefits and advantages",
            f"{topic} - Challenges and limitations",
            f"{topic} - Current trends and developments",
            f"{topic} - Future outlook"
        ][:num_subtopics]

    async def _parallel_search(
        self,
        subtopics: List[str],
        max_sources: int
    ) -> List[str]:
        """Execute parallel web searches for each sub-topic"""
        results_per_search = max(2, max_sources // len(subtopics))

        # This would call the web_search MCP tool
        # For now, return mock results
        results = []
        for subtopic in subtopics[:3]:  # Limit for demo
            mock_result = {
                "query": subtopic,
                "total_results": results_per_search,
                "results": [
                    {
                        "title": f"Result {i+1} for {subtopic}",
                        "url": f"https://example.com/{i}",
                        "snippet": f"Snippet {i+1}"
                    }
                    for i in range(results_per_search)
                ]
            }
            results.append(json.dumps(mock_result))

        return results

    async def _fetch_key_pages(
        self,
        search_results: List[str],
        max_pages: int
    ) -> List[str]:
        """Fetch detailed content from key URLs"""
        # Extract all URLs from search results
        all_urls = []
        for result_json in search_results:
            try:
                result = json.loads(result_json)
                for item in result.get("results", []):
                    all_urls.append(item.get("url"))
            except json.JSONDecodeError:
                continue

        # Select top URLs
        selected_urls = all_urls[:max_pages]

        # This would call the fetch_url MCP tool
        # For now, return mock content
        contents = []
        for url in selected_urls[:3]:  # Limit for demo
            mock_content = {
                "url": url,
                "title": f"Content from {url}",
                "text_content": f"Detailed content from {url}..."
            }
            contents.append(json.dumps(mock_content))

        return contents

    async def _synthesize_information(
        self,
        topic: str,
        contents: List[str]
    ) -> Dict[str, Any]:
        """Synthesize information from multiple sources"""
        # This would call LLM to synthesize
        return {
            "summary": f"Comprehensive overview of {topic}",
            "key_findings": [
                "Finding 1 from synthesis",
                "Finding 2 from synthesis",
                "Finding 3 from synthesis"
            ],
            "trends": [
                "Trend 1",
                "Trend 2"
            ],
            "challenges": [
                "Challenge 1",
                "Challenge 2"
            ]
        }

    async def _generate_report(
        self,
        topic: str,
        subtopics: List[str],
        synthesized: Dict[str, Any],
        search_results: List[str]
    ) -> Dict[str, Any]:
        """Generate final research report"""
        # Extract all sources
        all_sources = []
        for result_json in search_results:
            try:
                result = json.loads(result_json)
                for item in result.get("results", []):
                    all_sources.append(item.get("url"))
            except json.JSONDecodeError:
                continue

        return {
            "topic": topic,
            "researched_at": asyncio.get_event_loop().time(),
            "subtopics": subtopics,
            "summary": synthesized.get("summary"),
            "key_findings": synthesized.get("key_findings", []),
            "trends": synthesized.get("trends", []),
            "challenges": synthesized.get("challenges", []),
            "all_sources": list(set(all_sources)),
            "total_sources": len(set(all_sources))
        }

    def get_skill_metadata(self):
        """Get skill metadata"""
        from ..skill_metadata import SkillMetadata
        return SkillMetadata(
            skill_id="research_topic",
            name="ResearchTopicSkill",
            version="1.0.0",
            category=SkillCategory.SEARCH,
            tags=["research", "web", "synthesis"],
            description="Execute comprehensive research on a topic",
            enabled=True
        )

# Convenience function
async def research_topic(
    topic: str,
    depth: int = 3,
    max_sources: int = 10,
    tool_context: Optional[Any] = None
) -> str:
    """
    Execute deep research on a topic

    Args:
        topic: Research topic
        depth: Research depth (1-5)
        max_sources: Maximum number of sources
        tool_context: Optional tool context

    Returns:
        JSON string with research report
    """
    skill = ResearchTopicSkill()
    return await skill.execute(
        topic=topic,
        depth=depth,
        max_sources=max_sources,
        tool_context=tool_context
    )
