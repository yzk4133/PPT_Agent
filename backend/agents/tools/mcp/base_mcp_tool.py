#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MCP Tool Base Class

This module provides the base class for all MCP tools.
MCP (Model Context Protocol) tools are wrappers around external APIs and services.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime


class BaseMCPTool:
    """
    Base class for all MCP tools.

    All MCP tools should inherit from this class and implement the execute method.
    """

    def __init__(self, name: str, description: str = ""):
        """
        Initialize the MCP tool.

        Args:
            name: Tool name
            description: Tool description
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"mcp.{name}")

    async def execute(self, **kwargs) -> str:
        """
        Execute the tool.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            JSON string with success/error response
        """
        raise NotImplementedError(f"{self.name}.execute() not implemented")

    def _success(self, result: Dict[str, Any], metadata: Optional[Dict] = None) -> str:
        """
        Create a success response.

        Args:
            result: Result data
            metadata: Optional metadata

        Returns:
            JSON string
        """
        response = {
            "success": True,
            "result": result,
            "error": None,
            "tool": self.name,
            "timestamp": datetime.now().isoformat()
        }
        if metadata:
            response["metadata"] = metadata
        return json.dumps(response, ensure_ascii=False, default=str)

    def _error(self, message: str, details: Optional[Dict] = None, code: Optional[str] = None) -> str:
        """
        Create an error response.

        Args:
            message: Error message
            details: Optional error details
            code: Optional error code

        Returns:
            JSON string
        """
        response = {
            "success": False,
            "result": None,
            "error": {
                "message": message,
                "details": details or {},
                "code": code
            },
            "tool": self.name,
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(response, ensure_ascii=False, default=str)

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get tool metadata.

        Returns:
            Dictionary with tool metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": "mcp_tool"
        }
