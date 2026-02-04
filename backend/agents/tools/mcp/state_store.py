#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MCP Tool: State Store

Implements state storage using Redis or file system backend.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from .base_mcp_tool import BaseMCPTool

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "")
STATE_DIR = Path(os.getenv("MCP_STATE_DIR", "./data/state"))
DEFAULT_NAMESPACE = os.getenv("MCP_STATE_NAMESPACE", "default")

logger = logging.getLogger(__name__)

class StateStoreTool(BaseMCPTool):
    """State storage tool using Redis or file backend"""

    def __init__(self):
        super().__init__(
            name="state_store",
            description="Store and retrieve agent execution state"
        )
        self.backend = None
        self.redis_client = None
        self.state_dir = STATE_DIR

        # Initialize backend
        if REDIS_URL:
            try:
                import redis
                self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                self.backend = "redis"
                logger.info("StateStore: Using Redis backend")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using file backend")
                self._init_file_backend()
        else:
            self._init_file_backend()

    def _init_file_backend(self):
        """Initialize file backend"""
        self.backend = "file"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"StateStore: Using file backend at {self.state_dir}")

    async def execute(
        self,
        operation: str,
        key: Optional[str] = None,
        value: Optional[Any] = None,
        namespace: str = DEFAULT_NAMESPACE,
        tool_context: Optional[Any] = None
    ) -> str:
        """
        Execute state operation

        Args:
            operation: Operation type (get, set, delete, list)
            key: State key (required for get, set, delete)
            value: State value (required for set)
            namespace: Namespace for isolation
            tool_context: Optional tool context

        Returns:
            JSON string with result
        """
        logger.info(f"[state_store] {operation} on {namespace}:{key}")

        try:
            if operation == "get":
                if not key:
                    return self._error(
                        message="Key is required for get operation",
                        code="MISSING_KEY"
                    )
                result = await self._get(key, namespace)
                return self._success({"value": result})

            elif operation == "set":
                if not key:
                    return self._error(
                        message="Key is required for set operation",
                        code="MISSING_KEY"
                    )
                if value is None:
                    return self._error(
                        message="Value is required for set operation",
                        code="MISSING_VALUE"
                    )
                await self._set(key, value, namespace)
                return self._success({"key": key, "stored": True})

            elif operation == "delete":
                if not key:
                    return self._error(
                        message="Key is required for delete operation",
                        code="MISSING_KEY"
                    )
                deleted = await self._delete(key, namespace)
                return self._success({"key": key, "deleted": deleted})

            elif operation == "list":
                keys = await self._list(namespace)
                return self._success({"keys": keys, "count": len(keys)})

            else:
                return self._error(
                    message=f"Unknown operation: {operation}",
                    code="UNKNOWN_OPERATION"
                )

        except Exception as e:
            logger.error(f"StateStore error: {e}", exc_info=True)
            return self._error(
                message=str(e),
                code="STORE_ERROR",
                details={"operation": operation, "key": key}
            )

    async def _get(self, key: str, namespace: str) -> Optional[Any]:
        """Get value from store"""
        full_key = f"{namespace}:{key}"

        if self.backend == "redis":
            data = self.redis_client.get(full_key)
            if data:
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    return data
            return None
        else:
            path = self.state_dir / namespace / f"{key}.json"
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None

    async def _set(self, key: str, value: Any, namespace: str):
        """Set value in store"""
        full_key = f"{namespace}:{key}"

        if self.backend == "redis":
            self.redis_client.set(full_key, json.dumps(value, ensure_ascii=False))
        else:
            namespace_dir = self.state_dir / namespace
            namespace_dir.mkdir(exist_ok=True)
            path = namespace_dir / f"{key}.json"
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(value, f, ensure_ascii=False, indent=2)

    async def _delete(self, key: str, namespace: str) -> bool:
        """Delete value from store"""
        full_key = f"{namespace}:{key}"

        if self.backend == "redis":
            return bool(self.redis_client.delete(full_key))
        else:
            path = self.state_dir / namespace / f"{key}.json"
            if path.exists():
                path.unlink()
                return True
            return False

    async def _list(self, namespace: str) -> List[str]:
        """List all keys in namespace"""
        if self.backend == "redis":
            pattern = f"{namespace}:*"
            keys = self.redis_client.keys(pattern)
            # Remove namespace prefix
            return [k.replace(f"{namespace}:", "") for k in keys]
        else:
            namespace_dir = self.state_dir / namespace
            if namespace_dir.exists():
                return [f.stem for f in namespace_dir.glob("*.json")]
            return []

# Global instance
_tool_instance = None

def get_tool() -> StateStoreTool:
    """Get or create the state store tool instance"""
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = StateStoreTool()
    return _tool_instance

async def state_store(
    operation: str,
    key: Optional[str] = None,
    value: Optional[Any] = None,
    namespace: str = DEFAULT_NAMESPACE,
    tool_context: Optional[Any] = None
) -> str:
    """
    Execute state operation

    Args:
        operation: Operation type (get, set, delete, list)
        key: State key (required for get, set, delete)
        value: State value (required for set)
        namespace: Namespace for isolation
        tool_context: Optional tool context

    Returns:
        JSON string with result
    """
    tool = get_tool()
    return await tool.execute(
        operation=operation,
        key=key,
        value=value,
        namespace=namespace,
        tool_context=tool_context
    )
