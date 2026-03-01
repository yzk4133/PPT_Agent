"""
LangChain Native Tool: State Store

Implements state storage using Redis or file system backend.
"""

import json
import logging
import os
from pathlib import Path
from typing import Literal, Optional, Any

from langchain_core.tools import StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field

from backend.tools.core.monitoring import monitor_tool
from backend.tools.application.tool_registry import get_native_registry

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "")
STATE_DIR = Path(os.getenv("MCP_STATE_DIR", "./data/state"))
DEFAULT_NAMESPACE = os.getenv("MCP_STATE_NAMESPACE", "default")

logger = logging.getLogger(__name__)

# Backend state (module-level for caching)
_backend = None
_redis_client = None
_state_dir = STATE_DIR


def _init_backend():
    """Initialize storage backend"""
    global _backend, _redis_client, _state_dir

    if _backend is not None:
        return _backend

    if REDIS_URL:
        try:
            import redis

            _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            _redis_client.ping()
            _backend = "redis"
            logger.info("[state_store] Using Redis backend")
            return _backend
        except Exception as e:
            logger.warning(f"[state_store] Redis connection failed: {e}, using file backend")

    _backend = "file"
    _state_dir = STATE_DIR
    _state_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"[state_store] Using file backend at {_state_dir}")
    return _backend


# Input schemas
class StateStoreGetInput(BaseModel):
    """State store get input schema"""

    operation: Literal["get"] = Field(default="get", description="Operation type")
    key: str = Field(description="State key to retrieve")
    namespace: str = Field(default=DEFAULT_NAMESPACE, description="Namespace for isolation")


class StateStoreSetInput(BaseModel):
    """State store set input schema"""

    operation: Literal["set"] = Field(default="set", description="Operation type")
    key: str = Field(description="State key to set")
    value: Any = Field(description="State value to store")
    namespace: str = Field(default=DEFAULT_NAMESPACE, description="Namespace for isolation")


class StateStoreDeleteInput(BaseModel):
    """State store delete input schema"""

    operation: Literal["delete"] = Field(default="delete", description="Operation type")
    key: str = Field(description="State key to delete")
    namespace: str = Field(default=DEFAULT_NAMESPACE, description="Namespace for isolation")


class StateStoreListInput(BaseModel):
    """State store list input schema"""

    operation: Literal["list"] = Field(default="list", description="Operation type")
    namespace: str = Field(default=DEFAULT_NAMESPACE, description="Namespace to list")


@monitor_tool
async def state_store(
    operation: str,
    key: Optional[str] = None,
    value: Optional[Any] = None,
    namespace: str = DEFAULT_NAMESPACE,
) -> dict:
    """
    Store and retrieve agent execution state

    Manages persistent state storage with Redis or file backend.
    Supports get, set, delete, and list operations.

    Args:
        operation: Operation type (get, set, delete, list)
        key: State key (required for get, set, delete)
        value: State value (required for set)
        namespace: Namespace for isolation

    Returns:
        Dictionary with operation result

    Examples:
        # Get value
        state_store(operation="get", key="user_id")

        # Set value
        state_store(operation="set", key="user_id", value="12345")

        # List all keys
        state_store(operation="list")
    """
    backend = _init_backend()
    logger.info(f"[state_store] {operation} on {namespace}:{key}")

    try:
        if operation == "get":
            if not key:
                raise ValueError("Key is required for get operation")
            result = await _get(key, namespace, backend)
            return {"value": result}

        elif operation == "set":
            if not key:
                raise ValueError("Key is required for set operation")
            if value is None:
                raise ValueError("Value is required for set operation")
            await _set(key, value, namespace, backend)
            return {"key": key, "stored": True}

        elif operation == "delete":
            if not key:
                raise ValueError("Key is required for delete operation")
            deleted = await _delete(key, namespace, backend)
            return {"key": key, "deleted": deleted}

        elif operation == "list":
            keys = await _list(namespace, backend)
            return {"keys": keys, "count": len(keys)}

        else:
            raise ValueError(f"Unknown operation: {operation}")

    except Exception as e:
        logger.error(f"[state_store] Error: {e}", exc_info=True)
        raise


async def _get(key: str, namespace: str, backend: str) -> Optional[Any]:
    """Get value from store"""
    full_key = f"{namespace}:{key}"

    if backend == "redis":
        data = _redis_client.get(full_key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        return None
    else:
        path = _state_dir / namespace / f"{key}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None


async def _set(key: str, value: Any, namespace: str, backend: str):
    """Set value in store"""
    full_key = f"{namespace}:{key}"

    if backend == "redis":
        _redis_client.set(full_key, json.dumps(value, ensure_ascii=False))
    else:
        namespace_dir = _state_dir / namespace
        namespace_dir.mkdir(exist_ok=True)
        path = namespace_dir / f"{key}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=2)


async def _delete(key: str, namespace: str, backend: str) -> bool:
    """Delete value from store"""
    full_key = f"{namespace}:{key}"

    if backend == "redis":
        return bool(_redis_client.delete(full_key))
    else:
        path = _state_dir / namespace / f"{key}.json"
        if path.exists():
            path.unlink()
            return True
        return False


async def _list(namespace: str, backend: str) -> list:
    """List all keys in namespace"""
    if backend == "redis":
        pattern = f"{namespace}:*"
        keys = _redis_client.keys(pattern)
        # Remove namespace prefix
        return [k.replace(f"{namespace}:", "") for k in keys]
    else:
        namespace_dir = _state_dir / namespace
        if namespace_dir.exists():
            return [f.stem for f in namespace_dir.glob("*.json")]
        return []


# Create LangChain StructuredTool
tool = StructuredTool.from_function(
    func=state_store,
    name="state_store",
    description="Store and retrieve agent execution state. Use this to persist data across agent runs.",
    args_schema=StateStoreGetInput,  # Use get schema as default
)

# Auto-register with global registry
registry = get_native_registry()
registry.register_tool(tool, category=registry.DATABASE)

__all__ = ["tool", "state_store"]
