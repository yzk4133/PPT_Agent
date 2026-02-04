"""
Health Check System

Provides comprehensive health checking for all infrastructure components:
- Database (PostgreSQL, Redis)
- LLM providers
- Cache systems
- External services
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class HealthStatus(str, Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """
    单个组件的健康检查结果
    """
    status: HealthStatus
    message: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    details: Dict[str, Any] = field(default_factory=dict)
    response_time_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "details": self.details,
            "response_time_ms": self.response_time_ms,
        }

@dataclass
class SystemHealthReport:
    """
    系统整体健康报告
    """
    status: HealthStatus
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    checks: Dict[str, HealthCheckResult] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp,
            "checks": {k: v.to_dict() for k, v in self.checks.items()},
            "summary": self.summary,
        }

class HealthChecker:
    """
    系统健康检查器

    检查所有基础设施组件的健康状态，生成综合健康报告。
    """

    def __init__(self):
        """初始化健康检查器"""
        self._checkers: Dict[str, Callable] = {}
        self._last_results: Dict[str, HealthCheckResult] = {}
        self._check_intervals: Dict[str, timedelta] = {}
        self._last_check_time: Dict[str, datetime] = {}

    def register_checker(
        self,
        name: str,
        checker_func: Callable,
        check_interval: timedelta = timedelta(seconds=30),
    ):
        """
        注册健康检查函数

        Args:
            name: 检查器名称
            checker_func: 异步检查函数，返回 HealthCheckResult
            check_interval: 检查间隔（用于缓存结果）
        """
        self._checkers[name] = checker_func
        self._check_intervals[name] = check_interval
        logger.info(f"Registered health checker: {name}")

    def unregister_checker(self, name: str):
        """
        注销健康检查函数

        Args:
            name: 检查器名称
        """
        if name in self._checkers:
            del self._checkers[name]
            del self._check_intervals[name]
            if name in self._last_results:
                del self._last_results[name]
            if name in self._last_check_time:
                del self._last_check_time[name]
            logger.info(f"Unregistered health checker: {name}")

    async def check_component(self, name: str, force: bool = False) -> HealthCheckResult:
        """
        检查单个组件的健康状态

        Args:
            name: 组件名称
            force: 是否强制重新检查（忽略缓存）

        Returns:
            HealthCheckResult
        """
        if name not in self._checkers:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message=f"Unknown component: {name}",
            )

        # 检查是否可以使用缓存结果
        if not force:
            last_time = self._last_check_time.get(name)
            if last_time:
                elapsed = datetime.utcnow() - last_time
                if elapsed < self._check_intervals[name]:
                    logger.debug(f"Using cached result for {name}")
                    return self._last_results[name]

        # 执行检查
        start_time = datetime.utcnow()
        try:
            result = await self._checkers[name]()
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.response_time_ms = response_time

            self._last_results[name] = result
            self._last_check_time[name] = datetime.utcnow()

            return result
        except Exception as e:
            logger.error(f"Health check failed for {name}: {e}")
            result = HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {str(e)}",
                response_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
            )
            self._last_results[name] = result
            self._last_check_time[name] = datetime.utcnow()
            return result

    async def check_health(
        self,
        components: Optional[List[str]] = None,
        force: bool = False,
    ) -> SystemHealthReport:
        """
        检查所有组件的健康状态

        Args:
            components: 要检查的组件列表（None 则检查所有）
            force: 是否强制重新检查

        Returns:
            SystemHealthReport
        """
        if components is None:
            components = list(self._checkers.keys())

        checks = {}
        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0

        # 并发检查所有组件
        tasks = [self.check_component(name, force) for name in components]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for name, result in zip(components, results):
            if isinstance(result, Exception):
                checks[name] = HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check error: {str(result)}",
                )
            else:
                checks[name] = result

            # 统计
            if checks[name].status == HealthStatus.HEALTHY:
                healthy_count += 1
            elif checks[name].status == HealthStatus.DEGRADED:
                degraded_count += 1
            else:
                unhealthy_count += 1

        # 确定整体状态
        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        # 生成摘要
        summary = {
            "total": len(components),
            "healthy": healthy_count,
            "degraded": degraded_count,
            "unhealthy": unhealthy_count,
        }

        return SystemHealthReport(
            status=overall_status,
            checks=checks,
            summary=summary,
        )

    def get_last_result(self, name: str) -> Optional[HealthCheckResult]:
        """
        获取上次的检查结果

        Args:
            name: 组件名称

        Returns:
            HealthCheckResult 或 None
        """
        return self._last_results.get(name)

# 预定义的健康检查函数

async def check_postgresql(db_manager) -> HealthCheckResult:
    """
    检查 PostgreSQL 健康状态

    Args:
        db_manager: DatabaseManager 实例

    Returns:
        HealthCheckResult
    """
    try:
        result = await db_manager.check_postgres_health()
        return HealthCheckResult(
            status=HealthStatus(result["status"]),
            message=result["message"],
            details={"connection": result},
        )
    except Exception as e:
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message=f"PostgreSQL check failed: {str(e)}",
        )

async def check_redis(db_manager) -> HealthCheckResult:
    """
    检查 Redis 健康状态

    Args:
        db_manager: DatabaseManager 实例

    Returns:
        HealthCheckResult
    """
    try:
        result = await db_manager.check_redis_health()
        return HealthCheckResult(
            status=HealthStatus(result["status"]),
            message=result["message"],
            details={"connection": result},
        )
    except Exception as e:
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message=f"Redis check failed: {str(e)}",
        )

async def check_llm_provider(provider: str, api_key: Optional[str] = None) -> HealthCheckResult:
    """
    检查 LLM 提供商健康状态

    Args:
        provider: 提供商名称
        api_key: API 密钥

    Returns:
        HealthCheckResult
    """
    # 简化的检查 - 实际实现可能需要调用 LLM API
    # 这里只是示例
    if api_key:
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            message=f"{provider} provider is configured",
            details={"provider": provider},
        )
    else:
        return HealthCheckResult(
            status=HealthStatus.DEGRADED,
            message=f"{provider} API key not configured",
            details={"provider": provider},
        )

async def check_cache(cache) -> HealthCheckResult:
    """
    检查缓存系统健康状态

    Args:
        cache: AgentCache 实例

    Returns:
        HealthCheckResult
    """
    try:
        stats = cache.get_stats()
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            message="Cache is operational",
            details={
                "size": stats.size,
                "hit_rate": stats.hit_rate,
                "total_requests": stats.total_requests,
            },
        )
    except Exception as e:
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message=f"Cache check failed: {str(e)}",
        )

async def check_mcp_tools(mcp_manager) -> HealthCheckResult:
    """
    检查 MCP 工具健康状态

    Args:
        mcp_manager: MCPManager 实例

    Returns:
        HealthCheckResult
    """
    try:
        # 获取已加载的工具数量
        tool_count = len(mcp_manager.get_all_tools())
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            message=f"MCP tools loaded: {tool_count}",
            details={"tool_count": tool_count},
        )
    except Exception as e:
        return HealthCheckResult(
            status=HealthStatus.DEGRADED,
            message=f"MCP tools check failed: {str(e)}",
        )

# 全局单例
_global_health_checker: Optional[HealthChecker] = None

def get_health_checker() -> HealthChecker:
    """
    获取全局健康检查器实例

    Returns:
        HealthChecker 实例
    """
    global _global_health_checker
    if _global_health_checker is None:
        _global_health_checker = HealthChecker()
    return _global_health_checker

async def setup_default_checks(db_manager=None, cache=None, mcp_manager=None):
    """
    设置默认的健康检查

    Args:
        db_manager: DatabaseManager 实例
        cache: AgentCache 实例
        mcp_manager: MCPManager 实例
    """
    checker = get_health_checker()

    if db_manager:
        checker.register_checker(
            "postgresql",
            lambda: check_postgresql(db_manager),
        )
        checker.register_checker(
            "redis",
            lambda: check_redis(db_manager),
        )

    if cache:
        checker.register_checker(
            "cache",
            lambda: check_cache(cache),
        )

    if mcp_manager:
        checker.register_checker(
            "mcp_tools",
            lambda: check_mcp_tools(mcp_manager),
        )

# 便捷函数
async def check_system_health() -> Dict[str, Any]:
    """
    检查系统健康状态（便捷函数）

    Returns:
        健康报告字典
    """
    checker = get_health_checker()
    report = await checker.check_health()
    return report.to_dict()

async def check_component_health(name: str) -> Dict[str, Any]:
    """
    检查单个组件健康状态（便捷函数）

    Args:
        name: 组件名称

    Returns:
        健康检查结果字典
    """
    checker = get_health_checker()
    result = await checker.check_component(name)
    return result.to_dict()

if __name__ == "__main__":
    # 测试健康检查系统
    async def test_health_checker():
        print("Testing HealthChecker")
        print("=" * 60)

        checker = HealthChecker()

        # 注册测试检查器
        async def test_check_healthy():
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Test component is healthy",
            )

        async def test_check_degraded():
            return HealthCheckResult(
                status=HealthStatus.DEGRADED,
                message="Test component is degraded",
            )

        async def test_check_unhealthy():
            raise Exception("Test error")

        checker.register_checker("healthy_component", test_check_healthy)
        checker.register_checker("degraded_component", test_check_degraded)
        checker.register_checker("unhealthy_component", test_check_unhealthy)

        # 检查所有组件
        print("\n1. Checking all components...")
        report = await checker.check_health()
        print(f"   Overall: {report.status.value}")
        print(f"   Summary: {report.summary}")

        for name, result in report.checks.items():
            print(f"   - {name}: {result.status.value} - {result.message}")

        # 检查单个组件
        print("\n2. Checking single component...")
        result = await checker.check_component("healthy_component")
        print(f"   Result: {result.to_dict()}")

        # 测试缓存
        print("\n3. Testing cache...")
        result1 = await checker.check_component("healthy_component")
        result2 = await checker.check_component("healthy_component", force=False)
        print(f"   Same result cached: {result1 == result2}")

        print("\n" + "=" * 60)
        print("Test completed!")

    asyncio.run(test_health_checker())
