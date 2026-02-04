"""
Metrics Collector 测试
"""

import pytest
import time
from infrastructure.metrics.metrics_collector import (
    Counter,
    Gauge,
    Histogram,
    MetricsCollector,
    get_metrics_collector,
    reset_metrics_collector,
    measure_time,
    count_exceptions,
)

@pytest.mark.unit
class TestCounter:
    """测试 Counter 类"""

    def test_counter_initialization(self):
        """测试计数器初始化"""
        counter = Counter("test_counter", "Test counter", labels=["method", "status"])

        assert counter.name == "test_counter"
        assert counter.labels == ["method", "status"]
        assert counter.get() == 0.0

    def test_counter_inc(self):
        """测试增加计数"""
        counter = Counter("test_counter", "Test counter")

        counter.inc()
        counter.inc(5)

        assert counter.get() == 6.0

    def test_counter_with_labels(self):
        """测试带标签的计数"""
        counter = Counter("requests", "Request count", labels=["method", "status"])

        counter.inc(1, method="GET", status="200")
        counter.inc(2, method="POST", status="201")

        assert counter.get(method="GET", status="200") == 1.0
        assert counter.get(method="POST", status="201") == 2.0

    def test_counter_negative_increment(self):
        """测试负数增量（应该失败）"""
        counter = Counter("test_counter", "Test counter")

        with pytest.raises(ValueError):
            counter.inc(-1)

    def test_counter_export(self):
        """测试导出 Prometheus 格式"""
        counter = Counter("test_total", "Test counter")

        counter.inc(10)

        exported = counter.export()

        assert "HELP test_total" in exported
        assert "TYPE test_total counter" in exported
        assert "test_total 10.0" in exported

@pytest.mark.unit
class TestGauge:
    """测试 Gauge 类"""

    def test_gauge_initialization(self):
        """测试仪表初始化"""
        gauge = Gauge("temperature", "Temperature gauge")

        assert gauge.name == "temperature"
        assert gauge.get() == 0.0

    def test_gauge_set(self):
        """测试设置值"""
        gauge = Gauge("temperature", "Temperature")

        gauge.set(25.5)

        assert gauge.get() == 25.5

    def test_gauge_inc(self):
        """测试增加值"""
        gauge = Gauge("counter", "Counter gauge")

        gauge.set(10)
        gauge.inc(5)

        assert gauge.get() == 15.0

    def test_gauge_dec(self):
        """测试减少值"""
        gauge = Gauge("counter", "Counter gauge")

        gauge.set(10)
        gauge.dec(3)

        assert gauge.get() == 7.0

    def test_gauge_export(self):
        """测试导出 Prometheus 格式"""
        gauge = Gauge("temperature", "Temperature")

        gauge.set(25.5)

        exported = gauge.export()

        assert "HELP temperature" in exported
        assert "TYPE temperature gauge" in exported
        assert "temperature 25.5" in exported

@pytest.mark.unit
class TestHistogram:
    """测试 Histogram 类"""

    def test_histogram_initialization(self):
        """测试直方图初始化"""
        histogram = Histogram("latency", "Latency histogram")

        assert histogram.name == "latency"
        assert histogram.get_count() == 0
        assert histogram.get_sum() == 0.0

    def test_histogram_observe(self):
        """测试观察值"""
        histogram = Histogram("latency", "Latency histogram")

        histogram.observe(0.1)
        histogram.observe(0.5)
        histogram.observe(1.0)

        assert histogram.get_count() == 3
        assert histogram.get_sum() == 1.6

    def test_histogram_get_buckets(self):
        """测试获取桶计数"""
        histogram = Histogram("latency", "Latency histogram")

        for value in [0.1, 0.2, 0.5, 1.0, 2.5]:
            histogram.observe(value)

        buckets = histogram.get_buckets()

        assert "+Inf" in buckets
        assert buckets["+Inf"] == 5

    def test_histogram_export(self):
        """测试导出 Prometheus 格式"""
        histogram = Histogram("latency", "Latency histogram")

        histogram.observe(0.5)
        histogram.observe(1.0)

        exported = histogram.export()

        assert "HELP latency" in exported
        assert "TYPE latency histogram" in exported
        assert "latency_count" in exported
        assert "latency_sum" in exported

@pytest.mark.unit
class TestMetricsCollector:
    """测试 MetricsCollector 类"""

    def test_metrics_collector_initialization(self):
        """测试指标收集器初始化"""
        collector = MetricsCollector()

        assert collector.service_name == "multiagent_ppt"
        assert len(collector.get_metric_names()) > 0  # 应该有默认指标

    def test_counter(self):
        """测试创建计数器"""
        collector = MetricsCollector()

        counter = collector.counter("test_counter", "Test counter")

        assert counter is not None
        assert "test_counter" in collector._counters

    def test_gauge(self):
        """测试创建仪表"""
        collector = MetricsCollector()

        gauge = collector.gauge("test_gauge", "Test gauge")

        assert gauge is not None
        assert "test_gauge" in collector._gauges

    def test_histogram(self):
        """测试创建直方图"""
        collector = MetricsCollector()

        histogram = collector.histogram("test_histogram", "Test histogram")

        assert histogram is not None
        assert "test_histogram" in collector._histograms

    def test_export_metrics(self):
        """测试导出所有指标"""
        collector = MetricsCollector()

        exported = collector.export_metrics()

        assert "HELP" in exported
        assert "TYPE" in exported

    def test_reset(self):
        """测试重置指标"""
        collector = MetricsCollector()

        counter = collector.counter("test_counter", "Test")
        counter.inc(100)

        collector.reset()

        # 重置后应该重新注册默认指标
        assert len(collector.get_metric_names()) > 0

@pytest.mark.unit
class TestDecorators:
    """测试装饰器"""

    def test_measure_time_decorator(self):
        """测试测量时间装饰器"""
        collector = MetricsCollector()

        @measure_time(labels=["function"])
        def test_function():
            time.sleep(0.1)
            return "result"

        result = test_function()

        assert result == "result"

    def test_count_exceptions_decorator(self):
        """测试计数异常装饰器"""
        collector = MetricsCollector()

        @count_exceptions(labels=["function"])
        def test_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            test_function()

@pytest.mark.unit
class TestGlobalMetricsCollector:
    """测试全局指标收集器"""

    def test_get_metrics_collector_singleton(self):
        """测试全局指标收集器单例"""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        assert collector1 is collector2

    def test_reset_metrics_collector(self):
        """测试重置全局指标收集器"""
        collector1 = get_metrics_collector()

        counter = collector1.counter("test", "Test")
        counter.inc(100)

        reset_metrics_collector()

        collector2 = get_metrics_collector()
        # 重置后应该创建新的实例（或清空）
        assert collector2 is not None
