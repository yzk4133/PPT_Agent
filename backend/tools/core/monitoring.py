"""
Tool Performance Monitoring Decorator

Provides performance monitoring for LangChain native tools.
Tracks call counts, success/failure rates, and execution durations.
"""

import functools
import time
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


class ToolMetrics:
    """Tool performance metrics collector"""

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.call_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_duration = 0.0
        self.success_durations = []
        self.error_durations = []

    def record_call(self, success: bool, duration: float):
        """Record a tool call attempt"""
        self.call_count += 1
        self.total_duration += duration

        if success:
            self.success_count += 1
            self.success_durations.append(duration)
        else:
            self.error_count += 1
            self.error_durations.append(duration)

    def get_success_rate(self) -> float:
        """Calculate success rate (0-1)"""
        if self.call_count == 0:
            return 1.0
        return self.success_count / self.call_count

    def get_avg_duration(self) -> float:
        """Get average execution duration in seconds"""
        if self.call_count == 0:
            return 0.0
        return self.total_duration / self.call_count

    def get_avg_success_duration(self) -> float:
        """Get average successful execution duration in seconds"""
        if not self.success_durations:
            return 0.0
        return sum(self.success_durations) / len(self.success_durations)

    def get_summary(self) -> dict:
        """Get metrics summary as dictionary"""
        return {
            "tool_name": self.tool_name,
            "call_count": self.call_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.get_success_rate(),
            "avg_duration_ms": self.get_avg_duration() * 1000,
            "avg_success_duration_ms": self.get_avg_success_duration() * 1000,
        }


# Global metrics storage
_tool_metrics: dict[str, ToolMetrics] = {}


def get_tool_metrics(tool_name: str) -> ToolMetrics:
    """Get or create metrics for a specific tool"""
    if tool_name not in _tool_metrics:
        _tool_metrics[tool_name] = ToolMetrics(tool_name)
    return _tool_metrics[tool_name]


def get_all_metrics() -> dict[str, ToolMetrics]:
    """Get all tool metrics"""
    return _tool_metrics.copy()


def reset_metrics(tool_name: str = None):
    """Reset metrics for a specific tool or all tools"""
    if tool_name:
        _tool_metrics.pop(tool_name, None)
    else:
        _tool_metrics.clear()


def monitor_tool(func: Callable) -> Callable:
    """
    Decorator to monitor tool execution performance

    Automatically tracks:
    - Call count
    - Success/failure rates
    - Execution duration

    Usage:
        @monitor_tool
        async def my_tool(param: str) -> dict:
            # Tool implementation
            return {"result": "success"}

    Args:
        func: The async function to monitor

    Returns:
        Wrapped function with monitoring
    """
    @functools.wraps(func)
    async def wrapped(*args, **kwargs):
        tool_name = func.__name__
        start_time = time.time()
        success = False

        try:
            # Execute the actual function
            result = await func(*args, **kwargs)
            success = True
            duration = time.time() - start_time

            logger.info(
                f"[{tool_name}] Success in {duration*1000:.2f}ms"
            )
            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"[{tool_name}] Failed after {duration*1000:.2f}ms: {e}"
            )
            raise

        finally:
            # Record metrics
            metrics = get_tool_metrics(tool_name)
            metrics.record_call(success, duration)

    return wrapped


def log_metrics_summary():
    """Log a summary of all tool metrics"""
    if not _tool_metrics:
        logger.info("No tool metrics available")
        return

    logger.info("=" * 60)
    logger.info("Tool Performance Metrics Summary")
    logger.info("=" * 60)

    for tool_name, metrics in sorted(_tool_metrics.items()):
        summary = metrics.get_summary()
        logger.info(
            f"{tool_name}: "
            f"{summary['call_count']} calls, "
            f"{summary['success_rate']:.1%} success, "
            f"{summary['avg_duration_ms']:.2f}ms avg"
        )

    logger.info("=" * 60)
