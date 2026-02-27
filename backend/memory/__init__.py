"""
LangChain Memory System - Restructured Architecture (v5.0 极简版)

This module provides a comprehensive memory system for LangChain agents,
supporting user preferences and core memory operations.

Architecture v5.0:
    - Adapter: MemoryAwareAgent + UserPreferenceMixin
    - Services: UserPreferenceService only (简化)
    - Storage: Database models and caching
    - Utils: Helper functions for scope inference

Simplified in v5.0:
    - ❌ Removed DecisionService - 过度设计
    - ❌ Removed WorkspaceService - 功能与LangGraph State重复
    - ❌ Removed complex utility functions - 简化为2个核心函数

Usage:
    from backend.memory import MemoryAwareAgent

    # Use in agent
    class MyAgent(MemoryAwareAgent):
        async def run_node(self, state):
            self._get_memory(state)
            await self.remember("key", "value")
            result = await self.recall("key")
            return state
"""

# Core exports (from memory_aware_agent directly)
from .memory_aware_agent import (
    MemoryAwareAgent,
)

# System exports (from core module, if available)
try:
    from .core import (
        MemorySystem,
        get_global_memory_system,
        initialize_memory_system,
        shutdown_memory_system,
        MemoryConfig,
        load_config_from_env,
        validate_config,
        get_global_config,
    )
    _SYSTEM_AVAILABLE = True
except ImportError:
    _SYSTEM_AVAILABLE = False

# Service exports (简化版)
from .services import (
    UserPreferenceService,
)

# Storage exports (简化版)
from .storage.models import (
    Base,
    BaseModel,
    UserProfile,
)

from .storage.database import DatabaseManager, get_db, get_db_session
from .storage.redis_cache import RedisCache

# Utility exports (简化版)
from .utils import (
    infer_scope_from_key,
    get_scope_id,
)

__all__ = [
    # Core (MemoryAwareAgent)
    "MemoryAwareAgent",
]

# Add system exports if available
if _SYSTEM_AVAILABLE:
    __all__.extend([
        # System
        "MemorySystem",
        "get_global_memory_system",
        "initialize_memory_system",
        "shutdown_memory_system",
        # Config
        "MemoryConfig",
        "load_config_from_env",
        "validate_config",
        "get_global_config",
    ])

# Version info
__version__ = "5.0.0"
__author__ = "MultiAgentPPT Team"
