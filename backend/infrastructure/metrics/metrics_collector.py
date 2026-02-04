"""
Metrics Collection System

Provides Prometheus-compatible metrics collection for:
- Counters (monotonically increasing values)
- Histograms (distributions like latency, request sizes)
- Gauges (values that can go up and down)
- Summaries (statistics like percentiles)
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
from functools import wraps
import re

logger = logging.getLogger(__name__)


# Prometheus metric name validation
METRIC_NAME_RE = re.compile(r'^[a-zA-Z_:][a-zA-Z0-9_:]*$')
LABEL_NAME_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


@dataclass
class MetricValue:
    """
    单个指标的值
    """
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class Counter:
    """
    计数器

    单调递增的值，用于计数事件（如请求数、错误数）。
    """

    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        """
        初始化计数器

        Args:
            name: 指标名称
            description: 指标描述
            labels: 标签名称列表
        """
        if not METRIC_NAME_RE.match(name):
            raise ValueError(f"Invalid metric name: {name}")

        self.name = name
        self.description = description
        self.labels = labels or []
        self._values: Dict[tuple, float] = defaultdict(float)
        self._created = time.time()
        self._lock = threading.Lock()

    def inc(self, value: float = 1.0, **label_values):
        """
        增加计数

        Args:
            value: 增加的值（必须为正数）
            **label_values: 标签值
        """
        if value < 0:
            raise ValueError("Counter can only be incremented by non-negative values")

        label_key = self._get_label_key(label_values)

        with self._lock:
            self._values[label_key] += value

    def get(self, **label_values) -> float:
        """
        获取当前值

        Args:
            **label_values: 标签值

        Returns:
            当前计数值
        """
        label_key = self._get_label_key(label_values)
        return self._values.get(label_key, 0.0)

    def get_all(self) -> List[MetricValue]:
        """获取所有值"""
        with self._lock:
            return [
                MetricValue(value=v, labels=dict(zip(self.labels, k)))
                for k, v in self._values.items()
            ]

    def _get_label_key(self, label_values: Dict[str, str]) -> tuple:
        """获取标签键"""
        if set(label_values.keys()) != set(self.labels):
            raise ValueError(
                f"Expected labels {self.labels}, got {list(label_values.keys())}"
            )
        return tuple(label_values.get(label, "") for label in self.labels)

    def export(self) -> str:
        """
        导出 Prometheus 格式

        Returns:
            Prometheus 格式字符串
        """
        lines = [
            f"# HELP {self.name} {self.description}",
            f"# TYPE {self.name} counter",
        ]

        for metric_value in self.get_all():
            label_str = self._format_labels(metric_value.labels)
            lines.append(f"{self.name}{label_str} {metric_value.value}")

        return "\n".join(lines)

    def _format_labels(self, labels: Dict[str, str]) -> str:
        """格式化标签"""
        if not labels:
            return ""

        label_pairs = [f'{k}="{v}"' for k, v in labels.items()]
        return "{" + ",".join(label_pairs) + "}"


class Gauge:
    """
    仪表

    可增可减的值，用于表示当前状态（如温度、内存使用）。
    """

    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        """
        初始化仪表

        Args:
            name: 指标名称
            description: 指标描述
            labels: 标签名称列表
        """
        if not METRIC_NAME_RE.match(name):
            raise ValueError(f"Invalid metric name: {name}")

        self.name = name
        self.description = description
        self.labels = labels or []
        self._values: Dict[tuple, float] = defaultdict(float)
        self._created = time.time()
        self._lock = threading.Lock()

    def set(self, value: float, **label_values):
        """
        设置值

        Args:
            value: 要设置的值
            **label_values: 标签值
        """
        label_key = self._get_label_key(label_values)

        with self._lock:
            self._values[label_key] = value

    def inc(self, value: float = 1.0, **label_values):
        """增加值"""
        label_key = self._get_label_key(label_values)

        with self._lock:
            self._values[label_key] += value

    def dec(self, value: float = 1.0, **label_values):
        """减少值"""
        label_key = self._get_label_key(label_values)

        with self._lock:
            self._values[label_key] -= value

    def get(self, **label_values) -> float:
        """获取当前值"""
        label_key = self._get_label_key(label_values)
        return self._values.get(label_key, 0.0)

    def get_all(self) -> List[MetricValue]:
        """获取所有值"""
        with self._lock:
            return [
                MetricValue(value=v, labels=dict(zip(self.labels, k)))
                for k, v in self._values.items()
            ]

    def _get_label_key(self, label_values: Dict[str, str]) -> tuple:
        """获取标签键"""
        if set(label_values.keys()) != set(self.labels):
            raise ValueError(
                f"Expected labels {self.labels}, got {list(label_values.keys())}"
            )
        return tuple(label_values.get(label, "") for label in self.labels)

    def export(self) -> str:
        """导出 Prometheus 格式"""
        lines = [
            f"# HELP {self.name} {self.description}",
            f"# TYPE {self.name} gauge",
        ]

        for metric_value in self.get_all():
            label_str = self._format_labels(metric_value.labels)
            lines.append(f"{self.name}{label_str} {metric_value.value}")

        return "\n".join(lines)

    def _format_labels(self, labels: Dict[str, str]) -> str:
        """格式化标签"""
        if not labels:
            return ""

        label_pairs = [f'{k}="{v}"' for k, v in labels.items()]
        return "{" + ",".join(label_pairs) + "}"


class Histogram:
    """
    直方图

    用于记录值的分布（如延迟、请求大小）。
    """

    # 默认的桶边界（秒）
    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)

    def __init__(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[tuple] = None,
    ):
        """
        初始化直方图

        Args:
            name: 指标名称
            description: 指标描述
            labels: 标签名称列表
            buckets: 桶边界
        """
        if not METRIC_NAME_RE.match(name):
            raise ValueError(f"Invalid metric name: {name}")

        self.name = name
        self.description = description
        self.labels = labels or []
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self._counts: Dict[tuple, List[float]] = defaultdict(list)
        self._sum: Dict[tuple, float] = defaultdict(float)
        self._created = time.time()
        self._lock = threading.Lock()

    def observe(self, value: float, **label_values):
        """
        观察一个值

        Args:
            value: 要观察的值
            **label_values: 标签值
        """
        label_key = self._get_label_key(label_values)

        with self._lock:
            self._counts[label_key].append(value)
            self._sum[label_key] += value

    def get_buckets(self, **label_values) -> Dict[str, float]:
        """
        获取桶计数

        Args:
            **label_values: 标签值

        Returns:
            桶计数字典
        """
        label_key = self._get_label_key(label_values)
        values = self._counts.get(label_key, [])

        bucket_counts = {}
        cumulative_count = 0

        for bucket in self.buckets:
            count = sum(1 for v in values if v <= bucket)
            cumulative_count += count
            bucket_counts[str(bucket)] = cumulative_count

        # +Inf 桶（所有值）
        bucket_counts["+Inf"] = len(values)

        return bucket_counts

    def get_sum(self, **label_values) -> float:
        """获取总和"""
        label_key = self._get_label_key(label_values)
        return self._sum.get(label_key, 0.0)

    def get_count(self, **label_values) -> int:
        """获取计数"""
        label_key = self._get_label_key(label_values)
        return len(self._counts.get(label_key, []))

    def _get_label_key(self, label_values: Dict[str, str]) -> tuple:
        """获取标签键"""
        if set(label_values.keys()) != set(self.labels):
            raise ValueError(
                f"Expected labels {self.labels}, got {list(label_values.keys())}"
            )
        return tuple(label_values.get(label, "") for label in self.labels)

    def export(self) -> str:
        """导出 Prometheus 格式"""
        lines = [
            f"# HELP {self.name} {self.description}",
            f"# TYPE {self.name} histogram",
        ]

        # 获取所有唯一的标签组合
        all_keys = set(self._counts.keys())

        for label_key in all_keys:
            labels = dict(zip(self.labels, label_key))
            label_str = self._format_labels(labels)

            # 导出桶
            buckets = self.get_buckets(**labels)
            for bucket, count in buckets.items():
                lines.append(f"{self.name}_bucket{label_str} {count} {bucket}")

            # 导出总和和计数
            lines.append(f"{self.name}_sum{label_str} {self.get_sum(**labels)}")
            lines.append(f"{self.name}_count{label_str} {self.get_count(**labels)}")

        return "\n".join(lines)

    def _format_labels(self, labels: Dict[str, str]) -> str:
        """格式化标签"""
        if not labels:
            return ""

        label_pairs = [f'{k}="{v}"' for k, v in labels.items()]
        return "{" + ",".join(label_pairs) + "}"


class MetricsCollector:
    """
    指标收集器

    管理所有指标并导出 Prometheus 格式。
    """

    def __init__(self, service_name: str = "multiagent_ppt"):
        """
        初始化指标收集器

        Args:
            service_name: 服务名称
        """
        self.service_name = service_name
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._lock = threading.Lock()

        # 注册默认指标
        self._register_default_metrics()

    def _register_default_metrics(self):
        """注册默认指标"""
        # 系统指标
        self.gauge("up", "Service availability (1=up, 0=down)")
        self.gauge("start_time_seconds", "Service start time", labels=["service"])

        # LLM 指标
        self.counter("llm_requests_total", "Total LLM requests", labels=["provider", "model", "status"])
        self.histogram("llm_request_duration_seconds", "LLM request duration", labels=["provider", "model"])

        # Agent 指标
        self.counter("agent_executions_total", "Total agent executions", labels=["agent", "status"])
        self.histogram("agent_execution_duration_seconds", "Agent execution duration", labels=["agent"])

        # 缓存指标
        self.counter("cache_requests_total", "Total cache requests", labels=["operation", "status"])
        self.gauge("cache_size", "Current cache size", labels=["cache_type"])

        # 工具指标
        self.counter("tool_calls_total", "Total tool calls", labels=["tool", "status"])
        self.histogram("tool_duration_seconds", "Tool call duration", labels=["tool"])

    def counter(self, name: str, description: str, labels: Optional[List[str]] = None) -> Counter:
        """
        创建或获取计数器

        Args:
            name: 指标名称
            description: 指标描述
            labels: 标签名称列表

        Returns:
            Counter 实例
        """
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name, description, labels)
            return self._counters[name]

    def gauge(self, name: str, description: str, labels: Optional[List[str]] = None) -> Gauge:
        """
        创建或获取仪表

        Args:
            name: 指标名称
            description: 指标描述
            labels: 标签名称列表

        Returns:
            Gauge 实例
        """
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name, description, labels)
            return self._gauges[name]

    def histogram(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[tuple] = None,
    ) -> Histogram:
        """
        创建或获取直方图

        Args:
            name: 指标名称
            description: 指标描述
            labels: 标签名称列表
            buckets: 桶边界

        Returns:
            Histogram 实例
        """
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name, description, labels, buckets)
            return self._histograms[name]

    def export_metrics(self) -> str:
        """
        导出所有指标为 Prometheus 格式

        Returns:
            Prometheus 格式字符串
        """
        lines = []

        # 导出所有计数器
        for counter in self._counters.values():
            lines.append(counter.export())

        # 导出所有仪表
        for gauge in self._gauges.values():
            lines.append(gauge.export())

        # 导出所有直方图
        for histogram in self._histograms.values():
            lines.append(histogram.export())

        return "\n\n".join(lines)

    def get_metric_names(self) -> List[str]:
        """获取所有指标名称"""
        with self._lock:
            return list(self._counters.keys()) + list(self._gauges.keys()) + list(self._histograms.keys())

    def reset(self):
        """重置所有指标（用于测试）"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._register_default_metrics()


# 全局单例
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    获取全局指标收集器实例

    Returns:
        MetricsCollector 实例
    """
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


def reset_metrics_collector():
    """重置全局指标收集器（用于测试）"""
    global _global_collector
    if _global_collector:
        _global_collector.reset()


# 装饰器
def count_exceptions(
    counter_name: str = "function_exceptions_total",
    labels: Optional[List[str]] = None,
):
    """
    计数函数异常装饰器

    Args:
        counter_name: 计数器名称
        labels: 标签名称列表

    Example:
        >>> @count_exceptions(labels=["function"])
        ... def my_function():
        ...     pass
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            counter = collector.counter(
                counter_name,
                f"Exceptions from {func.__name__}",
                labels or [],
            )

            try:
                return func(*args, **kwargs)
            except Exception:
                # 获取函数名作为标签
                label_values = {"function": func.__name__}
                counter.inc(**label_values)
                raise

        return wrapper

    return decorator


def measure_time(
    histogram_name: str = "function_duration_seconds",
    labels: Optional[List[str]] = None,
):
    """
    测量函数执行时间装饰器

    Args:
        histogram_name: 直方图名称
        labels: 标签名称列表

    Example:
        >>> @measure_time(labels=["function"])
        ... def my_function():
        ...     pass
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            histogram = collector.histogram(
                histogram_name,
                f"Duration of {func.__name__}",
                labels or [],
            )

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                label_values = {"function": func.__name__}
                histogram.observe(duration, **label_values)

        return wrapper

    return decorator


if __name__ == "__main__":
    # 测试指标收集器
    def test_metrics_collector():
        print("Testing MetricsCollector")
        print("=" * 60)

        collector = MetricsCollector()

        # 测试计数器
        print("\n1. Testing Counter...")
        counter = collector.counter("test_requests", "Test requests", labels=["method", "status"])
        counter.inc(1, method="GET", status="200")
        counter.inc(2, method="POST", status="201")
        counter.inc(1, method="GET", status="500")

        print(f"   GET 200: {counter.get(method='GET', status='200')}")
        print(f"   POST 201: {counter.get(method='POST', status='201')}")

        # 测试仪表
        print("\n2. Testing Gauge...")
        gauge = collector.gauge("test_temperature", "Test temperature")
        gauge.set(25.5)
        print(f"   Temperature: {gauge.get()}")

        # 测试直方图
        print("\n3. Testing Histogram...")
        histogram = collector.histogram("test_latency", "Test latency")
        for value in [0.1, 0.2, 0.5, 1.0, 2.5, 5.0]:
            histogram.observe(value)

        print(f"   Count: {histogram.get_count()}")
        print(f"   Sum: {histogram.get_sum()}")
        print(f"   Buckets: {histogram.get_buckets()}")

        # 测试装饰器
        print("\n4. Testing Decorators...")

        @measure_time(labels=["function"])
        def test_function():
            time.sleep(0.1)

        test_function()
        test_function()

        # 导出指标
        print("\n5. Exporting Metrics...")
        print("---")
        print(collector.export_metrics())
        print("---")

        print("\n" + "=" * 60)
        print("Test completed!")

    test_metrics_collector()
