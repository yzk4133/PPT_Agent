"""性能监控模块

追踪系统性能指标，用于优化和分析
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from time import time
from functools import wraps
import statistics


@dataclass
class MetricRecord:
    """单条性能记录"""
    name: str
    duration_ms: float
    timestamp: float
    metadata: Dict[str, any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.records: List[MetricRecord] = []
        self.active_timings: Dict[str, float] = {}

    def start_timer(self, name: str) -> None:
        """开始计时"""
        self.active_timings[name] = time()

    def stop_timer(self, name: str, **metadata) -> MetricRecord:
        """停止计时并记录"""
        if name not in self.active_timings:
            raise ValueError(f"未找到计时器: {name}")

        start_time = self.active_timings.pop(name)
        duration = (time() - start_time) * 1000  # 转换为毫秒

        record = MetricRecord(
            name=name,
            duration_ms=duration,
            timestamp=time(),
            metadata=metadata
        )

        self.records.append(record)
        return record

    def record_metric(self, record: MetricRecord) -> None:
        """直接记录性能指标"""
        self.records.append(record)

    def get_statistics(self, name: Optional[str] = None) -> Dict[str, any]:
        """获取统计数据

        Args:
            name: 指标名称，为None时返回所有指标

        Returns:
            统计信息字典
        """
        filtered = [r for r in self.records if name is None or r.name == name]

        if not filtered:
            return {}

        durations = [r.duration_ms for r in filtered]

        return {
            "count": len(filtered),
            "total_ms": sum(durations),
            "avg_ms": statistics.mean(durations),
            "median_ms": statistics.median(durations),
            "min_ms": min(durations),
            "max_ms": max(durations),
            "success_rate": sum(1 for r in filtered if r.success) / len(filtered)
        }

    def get_slowest_records(self, limit: int = 10) -> List[MetricRecord]:
        """获取最慢的记录"""
        return sorted(self.records, key=lambda r: r.duration_ms, reverse=True)[:limit]

    def clear(self) -> None:
        """清空所有记录"""
        self.records.clear()
        self.active_timings.clear()


# 全局监控实例
_global_monitor = PerformanceMonitor()


def track_performance(name: Optional[str] = None):
    """性能追踪装饰器

    Usage:
        @track_performance("task_name")
        async def my_function():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            task_name = name or func.__name__
            _global_monitor.start_timer(task_name)
            try:
                result = await func(*args, **kwargs)
                _global_monitor.stop_timer(task_name, success=True)
                return result
            except Exception as e:
                _global_monitor.stop_timer(task_name, success=False, error=str(e))
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            task_name = name or func.__name__
            _global_monitor.start_timer(task_name)
            try:
                result = func(*args, **kwargs)
                _global_monitor.stop_timer(task_name, success=True)
                return result
            except Exception as e:
                _global_monitor.stop_timer(task_name, success=False, error=str(e))
                raise

        # 根据函数类型返回相应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def get_monitor() -> PerformanceMonitor:
    """获取全局监控实例"""
    return _global_monitor
