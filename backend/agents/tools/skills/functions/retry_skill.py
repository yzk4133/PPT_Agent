#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skill: Retry with Backoff

Implements the RetryWithBackoffSkill - automatic retry logic with
exponential backoff for handling transient failures.
"""

import json
import asyncio
import logging
from typing import Optional, Dict, Any, Callable

from ..skill_decorator import Skill
from ..skill_metadata import SkillCategory


logger = logging.getLogger(__name__)


@Skill(
    name="RetryWithBackoffSkill",
    version="1.0.0",
    category=SkillCategory.UTILITY,
    tags=["retry", "backoff", "resilience", "error-handling"],
    description="Execute functions with automatic retry and exponential backoff",
    author="MultiAgentPPT",
    enabled=True
)
class RetryWithBackoffSkill:
    """
    RetryWithBackoffSkill - Automatic Retry with Exponential Backoff

    This Skill provides resilience for operations that may fail transiently.
    Features:
    - Configurable retry attempts
    - Exponential backoff delay
    - Jitter to avoid thundering herd
    - Retry on specific exceptions
    """

    def __init__(self):
        """Initialize the retry skill"""
        self.logger = logger

    async def execute(
        self,
        func: Callable,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        retry_on: Optional[tuple] = None,
        tool_context: Optional[Any] = None
    ) -> str:
        """
        Execute function with retry logic

        Args:
            func: Function to execute (can be async or sync)
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay between retries
            backoff_factor: Multiplier for exponential backoff
            jitter: Add random jitter to delay
            retry_on: Tuple of exception types to retry on
            tool_context: Optional tool context

        Returns:
            JSON string with execution result
        """
        self.logger.info(f"[RetryWithBackoffSkill] Executing with max_retries={max_retries}")

        try:
            result = await self._execute_with_retry(
                func=func,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                backoff_factor=backoff_factor,
                jitter=jitter,
                retry_on=retry_on
            )

            return json.dumps({
                "success": True,
                "result": {
                    "status": "completed",
                    "data": result
                }
            }, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Retry failed after {max_retries} attempts: {e}")
            return json.dumps({
                "success": False,
                "error": {
                    "message": str(e),
                    "type": type(e).__name__
                },
                "result": None
            }, ensure_ascii=False)

    async def _execute_with_retry(
        self,
        func: Callable,
        max_retries: int,
        base_delay: float,
        max_delay: float,
        backoff_factor: float,
        jitter: bool,
        retry_on: Optional[tuple]
    ) -> Any:
        """Execute function with retry logic"""

        last_exception = None

        for attempt in range(max_retries):
            try:
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func()
                else:
                    result = func()

                # Success - return result
                if attempt > 0:
                    self.logger.info(f"  ✓ Success on attempt {attempt + 1}")

                return result

            except Exception as e:
                last_exception = e

                # Check if we should retry on this exception
                if retry_on and not isinstance(e, retry_on):
                    # Not a retryable exception, raise immediately
                    raise

                # If this is the last attempt, raise
                if attempt == max_retries - 1:
                    self.logger.error(f"  ✗ Failed after {attempt + 1} attempts")
                    raise

                # Calculate delay
                delay = min(base_delay * (backoff_factor ** attempt), max_delay)

                # Add jitter if enabled
                if jitter:
                    import random
                    delay = delay * (0.5 + random.random())

                self.logger.warning(
                    f"  ⚠ Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )

                # Wait before retry
                await asyncio.sleep(delay)

        # Should never reach here, but just in case
        if last_exception:
            raise last_exception

    def get_skill_metadata(self):
        """Get skill metadata"""
        from ..skill_metadata import SkillMetadata
        return SkillMetadata(
            skill_id="retry_with_backoff",
            name="RetryWithBackoffSkill",
            version="1.0.0",
            category=SkillCategory.UTILITY,
            tags=["retry", "backoff", "resilience", "error-handling"],
            description="Execute functions with automatic retry",
            enabled=True
        )


# Convenience function
async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retry_on: Optional[tuple] = None,
    tool_context: Optional[Any] = None
) -> str:
    """
    Execute function with retry logic

    Args:
        func: Function to execute
        max_retries: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        backoff_factor: Exponential backoff multiplier
        jitter: Add random jitter to delay
        retry_on: Exception types to retry on
        tool_context: Optional tool context

    Returns:
        JSON string with execution result
    """
    skill = RetryWithBackoffSkill()
    return await skill.execute(
        func=func,
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        jitter=jitter,
        retry_on=retry_on,
        tool_context=tool_context
    )


# Decorator version for convenience
def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True
):
    """
    Decorator to add retry logic to any function

    Usage:
        @with_retry(max_retries=3)
        async def my_function():
            # Code that might fail
            pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            skill = RetryWithBackoffSkill()
            result = await skill._execute_with_retry(
                func=lambda: func(*args, **kwargs),
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                backoff_factor=backoff_factor,
                jitter=jitter,
                retry_on=None
            )
            return result
        return wrapper
    return decorator
