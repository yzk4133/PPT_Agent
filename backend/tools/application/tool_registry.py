"""
Native LangChain Tool Registry

Simplified tool registry for LangChain native tools.
Auto-registers tools and provides category-based access.
"""

import sys
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

# 确保 backend 在 sys.path 中
_backend_root = Path(__file__).parent.parent.parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))


class NativeToolRegistry:
    """
    Simplified LangChain tool registry

    Categories:
    - SEARCH: Web search tools (web_search, fetch_url, weixin_search)
    - MEDIA: Media search tools (search_images)
    - UTILITY: Utility tools (create_pptx, xml_converter, a2a_client)
    - DATABASE: Database tools (state_store)
    - VECTOR: Vector search tools (vector_search)
    - SKILL: Python Skills converted to LangChain Tools (content_generation, etc.)
    """

    # Tool categories
    SEARCH = "SEARCH"
    MEDIA = "MEDIA"
    UTILITY = "UTILITY"
    DATABASE = "DATABASE"
    VECTOR = "VECTOR"
    SKILL = "SKILL"  # New: Python Skills converted to tools
    GENERAL = "GENERAL"

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {
            self.SEARCH: [],
            self.MEDIA: [],
            self.UTILITY: [],
            self.DATABASE: [],
            self.VECTOR: [],
            self.SKILL: [],  # New: Skills category
            self.GENERAL: [],
        }

    def register_tool(self, tool: BaseTool, category: str = GENERAL) -> None:
        """
        Register a LangChain tool

        Args:
            tool: LangChain BaseTool instance
            category: Tool category for filtering
        """
        tool_name = tool.name
        self._tools[tool_name] = tool

        # Add to category
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(tool_name)

        logger.debug(f"[NativeToolRegistry] Registered: {tool_name} " f"(category: {category})")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a specific tool by name

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)

    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """
        Get all tools in a category

        Args:
            category: Category name

        Returns:
            List of tools in the category
        """
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def get_all_tools(self) -> List[BaseTool]:
        """
        Get all registered tools

        Returns:
            List of all tools
        """
        return list(self._tools.values())

    def get_tool_count(self) -> int:
        """
        Get total number of registered tools

        Returns:
            Number of tools
        """
        return len(self._tools)

    def get_categories(self) -> List[str]:
        """
        Get all category names

        Returns:
            List of category names
        """
        return list(self._categories.keys())

    def list_tools_by_category(self) -> Dict[str, List[str]]:
        """
        Get a mapping of categories to tool names

        Returns:
            Dict mapping category names to lists of tool names
        """
        return {
            category: [name for name in tool_names if name in self._tools]
            for category, tool_names in self._categories.items()
        }

    def clear(self):
        """Clear all registered tools"""
        self._tools.clear()
        for category in self._categories:
            self._categories[category].clear()
        logger.info("[NativeToolRegistry] Cleared all tools")

    def log_summary(self):
        """Log a summary of registered tools"""
        logger.info(f"[NativeToolRegistry] Total tools: {self.get_tool_count()}")

        for category in self.get_categories():
            tools = self.get_tools_by_category(category)
            if tools:
                tool_names = [t.name for t in tools]
                logger.info(f"  {category}: {len(tools)} tools - {', '.join(tool_names)}")


# Global registry singleton
_global_registry: Optional[NativeToolRegistry] = None


def get_native_registry() -> NativeToolRegistry:
    """
    Get the global native tool registry

    Auto-initializes and registers all native tools on first call.

    Returns:
        Global NativeToolRegistry instance
    """
    global _global_registry

    if _global_registry is None:
        _global_registry = NativeToolRegistry()
        _auto_register_tools()
        _global_registry.log_summary()

    return _global_registry


def _auto_register_tools():
    """
    Auto-register all native LangChain tools

    This function is called once when the registry is first accessed.
    It imports all tool modules, which automatically register themselves.
    """
    try:
        logger.info("[NativeToolRegistry] Auto-registering native tools...")

        # Check if MCP version should be used for web_search
        use_mcp_web_search = os.getenv("USE_MCP_WEB_SEARCH", "false").lower() == "true"

        # Import search tools
        if use_mcp_web_search:
            try:
                from backend.tools.domain.search.web_search_mcp import web_search_mcp_tool

                _global_registry.register_tool(web_search_mcp_tool, category="SEARCH")
                logger.info("[NativeToolRegistry] Using MCP version of web_search")
            except ImportError as e:
                logger.warning(f"[NativeToolRegistry] MCP web_search not available: {e}")
                logger.warning("[NativeToolRegistry] Falling back to LangChain version")
                # Fallback to LangChain version
                from backend.tools.domain.search.web_search_tool import tool as web_search_tool

                _global_registry.register_tool(web_search_tool, category="SEARCH")
        else:
            from backend.tools.domain.search.web_search_tool import tool as web_search_tool

            _global_registry.register_tool(web_search_tool, category="SEARCH")

        # Import other search tools
        from backend.tools.domain.search.fetch_url_tool import tool as fetch_url_tool
        from backend.tools.domain.search.weixin_search_tool import tool as weixin_search_tool

        _global_registry.register_tool(fetch_url_tool, category="SEARCH")
        _global_registry.register_tool(weixin_search_tool, category="SEARCH")

        # Import media tools
        from backend.tools.domain.media.search_images_tool import tool as search_images_tool

        _global_registry.register_tool(search_images_tool, category="MEDIA")

        # Import utility tools
        from backend.tools.domain.utility.create_pptx_tool import tool as create_pptx_tool
        from backend.tools.domain.utility.xml_converter_tool import tool as xml_converter_tool
        from backend.tools.domain.utility.a2a_client_tool import tool as a2a_client_tool

        _global_registry.register_tool(create_pptx_tool, category="UTILITY")
        _global_registry.register_tool(xml_converter_tool, category="UTILITY")
        _global_registry.register_tool(a2a_client_tool, category="UTILITY")

        # Import database tools
        from backend.tools.domain.database.state_store_tool import tool as state_store_tool
        from backend.tools.domain.database.vector_search_tool import tool as vector_search_tool

        _global_registry.register_tool(state_store_tool, category="DATABASE")
        _global_registry.register_tool(vector_search_tool, category="VECTOR")

        # Register Python Skills as LangChain Tools (Directly - without adapter)
        try:
            # 直接导入所有 skill tools
            from backend.tools.skills.python_skills.research_workflow import research_workflow_tool
            from backend.tools.skills.python_skills.content_generation import (
                content_generation_tool,
                content_optimization_tool,
                content_quality_check_tool,
            )
            from backend.tools.skills.python_skills.framework_design import (
                framework_design_tool,
                topic_decomposition_tool,
                section_planning_tool,
            )
            from backend.tools.skills.python_skills.layout_selection import layout_selection_tool
            from backend.tools.skills.python_skills.content_optimization import (
                content_optimization_tool as content_opt_tool,
            )

            # 直接注册所有 skill tools
            skill_tools = [
                research_workflow_tool,
                content_generation_tool,
                content_optimization_tool,
                content_quality_check_tool,
                framework_design_tool,
                topic_decomposition_tool,
                section_planning_tool,
                layout_selection_tool,
                content_opt_tool,
            ]

            for tool in skill_tools:
                _global_registry.register_tool(tool, category="SKILL")

            logger.info(
                f"[NativeToolRegistry] Registered {len(skill_tools)} Python Skills as tools"
            )

        except Exception as e:
            logger.warning(f"[NativeToolRegistry] Failed to register Python Skills: {e}")
            logger.warning("[NativeToolRegistry] Continuing without Python Skills...")

        # Register MD Skills as LangChain Tools
        try:
            from backend.tools.skills.markdown_skill import MarkdownSkill, create_md_skill_tool
            from pathlib import Path

            md_skills_dir = Path(__file__).parent.parent / "skills" / "md_skills"

            if md_skills_dir.exists():
                md_skill_count = 0
                for md_file in md_skills_dir.glob("*.md"):
                    try:
                        md_skill = MarkdownSkill(md_file)
                        md_tool = create_md_skill_tool(md_skill)
                        _global_registry.register_tool(md_tool, category="SKILL")
                        md_skill_count += 1
                        logger.debug(f"[NativeToolRegistry] Registered MD Skill: {md_skill.name}")
                    except Exception as e:
                        logger.warning(f"[NativeToolRegistry] Failed to load {md_file.name}: {e}")

                logger.info(f"[NativeToolRegistry] Registered {md_skill_count} MD Skills as tools")

        except Exception as e:
            logger.warning(f"[NativeToolRegistry] Failed to register MD Skills: {e}")
            logger.warning("[NativeToolRegistry] Continuing without MD Skills...")

        logger.info("[NativeToolRegistry] All native tools registered")

    except ImportError as e:
        logger.warning(f"[NativeToolRegistry] Import error during auto-registration: {e}")
        logger.warning("[NativeToolRegistry] Some tools may not be available")
    except Exception as e:
        logger.error(f"[NativeToolRegistry] Error during auto-registration: {e}", exc_info=True)


def reset_global_registry():
    """Reset the global registry (useful for testing)"""
    global _global_registry
    if _global_registry:
        _global_registry.clear()
    _global_registry = None
    logger.info("[NativeToolRegistry] Global registry reset")
