#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MCP Tool Base Class with Performance Monitoring

This module provides the base class for all MCP tools with built-in
performance monitoring, success rate tracking, and statistics collection.
"""

import json
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime


class BaseMCPTool:
    """
    Base class for all MCP tools with performance monitoring.

    All MCP tools should inherit from this class and implement the execute method.
    Performance metrics are automatically tracked including:
    - Call count
    - Success/error count
    - Success rate
    - Average execution time
    - Total execution time
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

        # Performance stats
        self._call_count = 0
        self._success_count = 0
        self._error_count = 0
        self._total_execution_time = 0.0

    async def execute(self, **kwargs) -> str:
        """
        Execute the tool with performance monitoring.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            JSON string with success/error response
        """
        start_time = time.time()
        self._call_count += 1

        try:
            # Call actual implementation
            result = await self._execute_impl(**kwargs)

            # Record success
            execution_time = time.time() - start_time
            self._success_count += 1
            self._total_execution_time += execution_time

            self.logger.info(
                f"Tool {self.name} executed successfully in {execution_time:.3f}s "
                f"(success_rate: {self._get_success_rate():.1%})"
            )

            return self._success(result, metadata={
                "execution_time": execution_time,
                "call_count": self._call_count
            })

        except Exception as e:
            # Record failure
            execution_time = time.time() - start_time
            self._error_count += 1
            self._total_execution_time += execution_time

            self.logger.error(
                f"Tool {self.name} failed after {execution_time:.3f}s: {e}"
            )

            return self._error(
                message=str(e),
                details={"execution_time": execution_time},
                code="EXECUTION_ERROR"
            )

    async def _execute_impl(self, **kwargs) -> Dict[str, Any]:
        """
        Actual implementation to be overridden by subclasses.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Dictionary with result data

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError(f"{self.name}._execute_impl() not implemented")

    def _get_success_rate(self) -> float:
        """Get success rate"""
        if self._call_count == 0:
            return 1.0
        return self._success_count / self._call_count

    def _get_avg_execution_time(self) -> float:
        """Get average execution time"""
        if self._call_count == 0:
            return 0.0
        return self._total_execution_time / self._call_count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics

        Returns:
            Dictionary with performance metrics
        """
        return {
            "name": self.name,
            "call_count": self._call_count,
            "success_count": self._success_count,
            "error_count": self._error_count,
            "success_rate": self._get_success_rate(),
            "avg_execution_time": self._get_avg_execution_time(),
            "total_execution_time": self._total_execution_time
        }

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
        Get tool metadata

        Returns:
            Dictionary with tool metadata including stats
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": "mcp_tool",
            "stats": self.get_stats()
        }

    def reset_stats(self) -> None:
        """Reset performance statistics"""
        self._call_count = 0
        self._success_count = 0
        self._error_count = 0
        self._total_execution_time = 0.0
        self.logger.info(f"Reset stats for tool {self.name}")
