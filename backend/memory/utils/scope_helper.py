"""
Scope Helper Utilities (简化版)

只保留应用层实际需要的功能：
- 作用域推断（简化版）
- 作用域ID获取（简化版）
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def infer_scope_from_key(key: str) -> str:
    """
    从键名推断作用域（简化版）

    规则：
    - 包含 "preference" 或 "profile" → USER（用户偏好）
    - 其他 → TASK（任务级缓存）

    Args:
        key: 记忆键

    Returns:
        推断的作用域 (TASK 或 USER)
    """
    key_lower = key.lower()

    # 用户偏好相关的键
    if "preference" in key_lower or "profile" in key_lower:
        logger.debug(f"[ScopeHelper] Inferred scope 'USER' for key '{key}'")
        return "USER"

    # 其他都是任务级
    logger.debug(f"[ScopeHelper] Inferred scope 'TASK' for key '{key}'")
    return "TASK"


def get_scope_id(scope: str, context: Dict[str, Optional[str]]) -> str:
    """
    获取作用域ID（简化版）

    规则：
    - USER → 使用 user_id（默认 "anonymous"）
    - TASK → 使用 task_id（默认 "default"）

    Args:
        scope: 作用域 (TASK 或 USER)
        context: 上下文字典，包含 task_id、user_id

    Returns:
        作用域ID
    """
    if scope == "USER":
        return context.get("user_id") or "anonymous"
    else:  # TASK or default
        return context.get("task_id") or "default"


# 向后兼容的导出（删除旧版本后移除）
__all__ = [
    "infer_scope_from_key",
    "get_scope_id",
]
