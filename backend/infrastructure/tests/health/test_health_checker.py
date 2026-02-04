"""
Health Checker 测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from infrastructure.health.health_checker import (
    HealthStatus,
    HealthCheckResult,
    SystemHealthReport,
    HealthChecker,
    get_health_checker,
    check_postgresql,
    check_redis,
    check_cache,
)

@pytest.mark.unit
class TestHealthStatus:
    """测试 HealthStatus 枚举"""

    def test_health_status_values(self):
        """测试健康状态值"""
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.DEGRADED == "degraded"
        assert HealthStatus.UNHEALTHY == "unhealthy"
        assert HealthStatus.UNKNOWN == "unknown"

@pytest.mark.unit
class TestHealthCheckResult:
    """测试 HealthCheckResult 类"""

    def test_health_check_result_creation(self):
        """测试健康检查结果创建"""
        result = HealthCheckResult(
            status=HealthStatus.HEALTHY,
            message="Component is healthy",
        )

        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Component is healthy"
        assert result.response_time_ms is None

    def test_health_check_result_to_dict(self):
        """测试转换为字典"""
        result = HealthCheckResult(
            status=HealthStatus.HEALTHY,
            message="OK",
            details={"key": "value"},
            response_time_ms=100.0,
        )

        data = result.to_dict()

        assert data["status"] == "healthy"
        assert data["message"] == "OK"
        assert data["details"]["key"] == "value"
        assert data["response_time_ms"] == 100.0

@pytest.mark.unit
@pytest.mark.asyncio
class TestHealthChecker:
    """测试 HealthChecker 类"""

    async def test_register_checker(self):
        """测试注册检查器"""
        checker = HealthChecker()

        async def mock_check():
            return HealthCheckResult(status=HealthStatus.HEALTHY, message="OK")

        checker.register_checker("test_component", mock_check)

        # 检查器应该被注册
        assert "test_component" in checker._checkers

    async def test_check_component(self):
        """测试检查组件"""
        checker = HealthChecker()

        async def mock_check():
            return HealthCheckResult(status=HealthStatus.HEALTHY, message="OK")

        checker.register_checker("test_component", mock_check)

        result = await checker.check_component("test_component")

        assert result.status == HealthStatus.HEALTHY
        assert result.message == "OK"

    async def test_check_component_unknown(self):
        """测试检查未知组件"""
        checker = HealthChecker()

        result = await checker.check_component("unknown_component")

        assert result.status == HealthStatus.UNKNOWN

    async def test_check_component_exception(self):
        """测试检查组件时抛出异常"""
        checker = HealthChecker()

        async def failing_check():
            raise Exception("Check failed")

        checker.register_checker("failing_component", failing_check)

        result = await checker.check_component("failing_component")

        assert result.status == HealthStatus.UNHEALTHY

    async def test_check_health(self):
        """测试检查整体健康状态"""
        checker = HealthChecker()

        async def healthy_check():
            return HealthCheckResult(status=HealthStatus.HEALTHY, message="OK")

        async def degraded_check():
            return HealthCheckResult(status=HealthStatus.DEGRADED, message="Degraded")

        checker.register_checker("component1", healthy_check)
        checker.register_checker("component2", degraded_check)

        report = await checker.check_health()

        assert report.status == HealthStatus.DEGRADED
        assert report.summary["healthy"] == 1
        assert report.summary["degraded"] == 1

    async def test_check_health_unhealthy(self):
        """测试有组件不健康时的整体状态"""
        checker = HealthChecker()

        async def healthy_check():
            return HealthCheckResult(status=HealthStatus.HEALTHY, message="OK")

        async def unhealthy_check():
            return HealthCheckResult(status=HealthStatus.UNHEALTHY, message="Failed")

        checker.register_checker("component1", healthy_check)
        checker.register_checker("component2", unhealthy_check)

        report = await checker.check_health()

        assert report.status == HealthStatus.UNHEALTHY

    async def test_get_last_result(self):
        """测试获取上次检查结果"""
        checker = HealthChecker()

        async def mock_check():
            return HealthCheckResult(status=HealthStatus.HEALTHY, message="OK")

        checker.register_checker("test_component", mock_check)

        await checker.check_component("test_component")

        result = checker.get_last_result("test_component")

        assert result is not None
        assert result.status == HealthStatus.HEALTHY

@pytest.mark.unit
@pytest.mark.asyncio
class TestPredefinedHealthChecks:
    """测试预定义的健康检查函数"""

    async def test_check_postgresql(self):
        """测试检查 PostgreSQL"""
        db_manager = MagicMock()
        db_manager.check_postgres_health = AsyncMock(
            return_value={
                "status": "healthy",
                "message": "OK",
            }
        )

        result = await check_postgresql(db_manager)

        assert result.status == HealthStatus.HEALTHY
        assert "OK" in result.message

    async def test_check_redis(self):
        """测试检查 Redis"""
        db_manager = MagicMock()
        db_manager.check_redis_health = AsyncMock(
            return_value={
                "status": "healthy",
                "message": "OK",
            }
        )

        result = await check_redis(db_manager)

        assert result.status == HealthStatus.HEALTHY

    async def test_check_cache(self):
        """测试检查缓存"""
        cache = MagicMock()
        stats = MagicMock()
        stats.size = 100
        stats.hit_rate = 0.8
        stats.total_requests = 1000
        cache.get_stats = MagicMock(return_value=stats)

        result = await check_cache(cache)

        assert result.status == HealthStatus.HEALTHY
        assert result.details["size"] == 100

@pytest.mark.unit
class TestGlobalHealthChecker:
    """测试全局健康检查器"""

    def test_get_health_checker_singleton(self):
        """测试全局健康检查器单例"""
        checker1 = get_health_checker()
        checker2 = get_health_checker()

        assert checker1 is checker2
