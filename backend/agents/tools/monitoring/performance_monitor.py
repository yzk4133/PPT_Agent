"""
Performance Monitor Module

This module provides performance monitoring and reporting for all MCP tools.
It collects statistics from tools and generates performance reports.
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Performance monitor for all tools

    Provides functionality to collect stats from all registered tools
    and generate performance reports.
    """

    @staticmethod
    def collect_stats() -> Dict[str, Any]:
        """
        Collect performance stats from all tools

        Returns:
            Dictionary mapping tool names to their stats
        """
        from backend.agents.tools.registry.unified_registry import get_unified_registry

        registry = get_unified_registry()
        stats = {}

        for tool_name, registration in registry.get_all_tools().items():
            # Try to get stats from tool class instances
            if registration.tool_class and hasattr(registration.tool_class, 'get_stats'):
                try:
                    # Check if it's a class or instance
                    if isinstance(registration.tool_class, type):
                        # It's a class, create an instance
                        instance = registration.tool_class()
                        if hasattr(instance, 'get_stats'):
                            stats[tool_name] = instance.get_stats()
                    else:
                        # It's already an instance
                        if hasattr(registration.tool_class, 'get_stats'):
                            stats[tool_name] = registration.tool_class.get_stats()
                except Exception as e:
                    logger.warning(f"Failed to get stats for {tool_name}: {e}")

        return stats

    @staticmethod
    def generate_report() -> str:
        """
        Generate performance report

        Returns:
            Formatted report string
        """
        stats = PerformanceMonitor.collect_stats()

        report = ["# 工具性能监控报告\n"]
        report.append(f"生成时间: {datetime.now().isoformat()}\n")

        total_calls = sum(s.get("call_count", 0) for s in stats.values())
        total_errors = sum(s.get("error_count", 0) for s in stats.values())

        report.append("## 总体统计")
        report.append(f"- 总调用次数: {total_calls}")
        report.append(f"- 总错误次数: {total_errors}")
        if total_calls > 0:
            report.append(f"- 整体成功率: {(total_calls - total_errors) / total_calls:.1%}\n")

        report.append("## 各工具详情\n")
        for tool_name, tool_stats in stats.items():
            report.append(f"### {tool_name}")
            report.append(f"- 调用次数: {tool_stats.get('call_count', 0)}")
            report.append(f"- 成功次数: {tool_stats.get('success_count', 0)}")
            report.append(f"- 失败次数: {tool_stats.get('error_count', 0)}")
            report.append(f"- 成功率: {tool_stats.get('success_rate', 1):.1%}")
            report.append(f"- 平均执行时间: {tool_stats.get('avg_execution_time', 0):.3f}s")
            report.append(f"- 总执行时间: {tool_stats.get('total_execution_time', 0):.3f}s\n")

        return "\n".join(report)

    @staticmethod
    def get_slow_tools(threshold: float = 5.0) -> list:
        """
        Get tools with average execution time above threshold

        Args:
            threshold: Time threshold in seconds

        Returns:
            List of tool names that exceed the threshold
        """
        stats = PerformanceMonitor.collect_stats()
        slow_tools = []

        for tool_name, tool_stats in stats.items():
            avg_time = tool_stats.get('avg_execution_time', 0)
            if avg_time > threshold:
                slow_tools.append(tool_name)

        return slow_tools

    @staticmethod
    def get_error_prone_tools(error_threshold: float = 0.1) -> list:
        """
        Get tools with error rate above threshold

        Args:
            error_threshold: Error rate threshold (0.0 to 1.0)

        Returns:
            List of tool names with high error rates
        """
        stats = PerformanceMonitor.collect_stats()
        error_prone = []

        for tool_name, tool_stats in stats.items():
            success_rate = tool_stats.get('success_rate', 1.0)
            error_rate = 1.0 - success_rate
            if error_rate > error_threshold:
                error_prone.append(tool_name)

        return error_prone

    @staticmethod
    def print_report() -> None:
        """Print performance report to console"""
        report = PerformanceMonitor.generate_report()
        print(report)

    @staticmethod
    def save_report(filepath: str) -> None:
        """
        Save performance report to file

        Args:
            filepath: Path to save the report
        """
        report = PerformanceMonitor.generate_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"Performance report saved to {filepath}")


if __name__ == "__main__":
    # 测试性能监控
    logging.basicConfig(level=logging.INFO)

    PerformanceMonitor.print_report()

    # 检查慢速工具
    slow_tools = PerformanceMonitor.get_slow_tools(threshold=5.0)
    if slow_tools:
        print(f"\n⚠️  慢速工具 (>5s): {', '.join(slow_tools)}")

    # 检查高错误率工具
    error_prone = PerformanceMonitor.get_error_prone_tools(error_threshold=0.1)
    if error_prone:
        print(f"\n⚠️  高错误率工具 (>10%): {', '.join(error_prone)}")
