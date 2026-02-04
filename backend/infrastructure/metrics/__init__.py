"""
Infrastructure metrics module

Provides Prometheus-compatible metrics collection for:
- Counters (monotonically increasing values)
- Histograms (distributions like latency, request sizes)
- Gauges (values that can go up and down)
"""

from .metrics_collector import (
    MetricValue,
    Counter,
    Gauge,
    Histogram,
    MetricsCollector,
    get_metrics_collector,
    reset_metrics_collector,
    count_exceptions,
    measure_time,
)

__all__ = [
    "MetricValue",
    "Counter",
    "Gauge",
    "Histogram",
    "MetricsCollector",
    "get_metrics_collector",
    "reset_metrics_collector",
    "count_exceptions",
    "measure_time",
]
