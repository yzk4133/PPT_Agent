"""
Cognition Module

Core AI reasoning capabilities including memory, prompts, and planning.
"""

from .prompts import PromptManager

# Don't import memory by default due to SQLAlchemy initialization issues
# Import specific modules as needed:
# from .memory.core import HierarchicalMemoryManager

__all__ = [
    "PromptManager",
]
