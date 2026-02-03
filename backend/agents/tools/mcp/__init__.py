#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skill Framework - Integrations Module

This module provides integrations with external tool systems.
"""

from .mcp_integration import (
    load_mcp_config_from_file,
    load_mcp_tools,
    mcp_tools_to_skills,
    load_all_tools,
    get_mcp_tool_info,
    load_mcp_tools_legacy,
)
from .base_mcp_tool import BaseMCPTool

# MCP tool functions
from .web_search import web_search
from .fetch_url import fetch_url
from .search_images import search_images
from .create_pptx import create_pptx
from .state_store import state_store
from .vector_search import vector_search
from .weixin_search import weixin_search
from .xml_converter import xml_converter

__all__ = [
    # MCP Integration
    "load_mcp_config_from_file",
    "load_mcp_tools",
    "mcp_tools_to_skills",
    "load_all_tools",
    "get_mcp_tool_info",
    "load_mcp_tools_legacy",
    # Base class
    "BaseMCPTool",
    # MCP Tools
    "web_search",
    "fetch_url",
    "search_images",
    "create_pptx",
    "state_store",
    "vector_search",
    "weixin_search",
    "xml_converter",
]
