"""
Rate Limit Middleware 测试
"""

import pytest
import time
from unittest.mock import MagicMock, AsyncMock, patch
from redis import Redis

from infrastructure.middleware.rate_limit_middleware import (
    RateLimiter,
    rate_limit_check,
    strict_rate_limit_check,
    loose_rate_limit_check,
    rate_limiter,
)
from infrastructure.exceptions import RateLimitExceededException

@pytest.mark.unit
class TestRateLimiter:
    """测试 RateLimiter 类"""

    def test_rate_limiter_initialization(self):
        """测试限流器初始化"""
        limiter = RateLimiter()

        assert limiter.redis is not None
        assert limiter.enabled is True

    @pytest.mark.asyncio
    async def test_check_rate_limit_disabled(self):
        """测试禁用限流"""
        limiter = RateLimiter()
        limiter.enabled = False

        # 禁用时应该不抛出异常
        await limiter.check_rate_limit("user123", limit=10, window=60)

    @pytest.mark.asyncio
    async def test_check_rate_limit_under_threshold(self):
        """测试低于阈值时不触发限流"""
        limiter = RateLimiter()

        with patch.object(limiter.redis, 'pipeline') as mock_pipeline:
            mock_pipe = MagicMock()
            mock_pipeline.return_value = mock_pipe
            mock_pipe.execute.return_value = [0, 5, None, True]  # 5 个请求，低于限制

            # 不应该抛出异常
            await limiter.check_rate_limit("user123", limit=10, window=60)

    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeds_threshold(self):
        """测试超过阈值时触发限流"""
        limiter = RateLimiter()

        with patch.object(limiter.redis, 'pipeline') as mock_pipeline:
            mock_pipe = MagicMock()
            mock_pipeline.return_value = mock_pipe
            # 模拟已达到限制
            mock_pipe.execute.return_value = [0, 10, None, True]

            with pytest.raises(RateLimitExceededException):
                await limiter.check_rate_limit("user123", limit=10, window=60)

    @pytest.mark.asyncio
    async def test_check_rate_limit_redis_error(self):
        """测试 Redis 错误处理"""
        limiter = RateLimiter()

        with patch.object(limiter.redis, 'pipeline', side_effect=Exception("Redis error")):
            # Redis 错误时不应该抛出异常，只记录日志
            await limiter.check_rate_limit("user123", limit=10, window=60)

    @pytest.mark.asyncio
    async def test_check_rate_limit_sliding_window(self):
        """测试滑动窗口算法"""
        limiter = RateLimiter()

        with patch.object(limiter.redis, 'pipeline') as mock_pipeline:
            mock_pipe = MagicMock()
            mock_pipeline.return_value = mock_pipe

            # 模拟滑动窗口操作
            mock_pipe.zremrangebyscore.return_value = mock_pipe
            mock_pipe.zcard.return_value = mock_pipe
            mock_pipe.zadd.return_value = mock_pipe
            mock_pipe.expire.return_value = mock_pipe
            mock_pipe.execute.return_value = [0, 5, None, True]

            await limiter.check_rate_limit("user123", limit=10, window=60)

            # 验证 Redis 操作
            assert mock_pipe.zremrangebyscore.called
            assert mock_pipe.zcard.called
            assert mock_pipe.zadd.called
            assert mock_pipe.expire.called

@pytest.mark.unit
@pytest.mark.asyncio
class TestRateLimitDependencies:
    """测试限流依赖函数"""

    async def test_rate_limit_check_with_user_id(self):
        """测试带用户 ID 的限流检查"""
        request = MagicMock()
        request.state = MagicMock()
        request.state.user_id = "user123"
        request.client = MagicMock()
        request.client.host = "192.168.1.1"

        with patch.object(rate_limiter, 'check_rate_limit', new_callable=AsyncMock) as mock_check:
            await rate_limit_check(request, limit=100, window=60)

            # 应该使用 user_id
            mock_check.assert_called_once_with("user123", 100, 60)

    async def test_rate_limit_check_with_ip(self):
        """测试使用 IP 地址的限流检查"""
        request = MagicMock()
        request.state = MagicMock()
        request.state.user_id = None
        request.client = MagicMock()
        request.client.host = "192.168.1.1"

        with patch.object(rate_limiter, 'check_rate_limit', new_callable=AsyncMock) as mock_check:
            await rate_limit_check(request, limit=100, window=60)

            # 应该使用 IP 地址
            mock_check.assert_called_once_with("192.168.1.1", 100, 60)

    async def test_strict_rate_limit_check(self):
        """测试严格限流检查"""
        request = MagicMock()
        request.state = MagicMock()
        request.state.user_id = "user123"
        request.client = MagicMock()
        request.client.host = "192.168.1.1"

        with patch.object(rate_limiter, 'check_rate_limit', new_callable=AsyncMock) as mock_check:
            await strict_rate_limit_check(request)

            # 应该使用严格的限制 (50/分钟)
            mock_check.assert_called_once_with("user123", 50, 60)

    async def test_loose_rate_limit_check(self):
        """测试宽松限流检查"""
        request = MagicMock()
        request.state = MagicMock()
        request.state.user_id = "user123"
        request.client = MagicMock()
        request.client.host = "192.168.1.1"

        with patch.object(rate_limiter, 'check_rate_limit', new_callable=AsyncMock) as mock_check:
            await loose_rate_limit_check(request)

            # 应该使用宽松的限制 (200/分钟)
            mock_check.assert_called_once_with("user123", 200, 60)

@pytest.mark.unit
class TestRateLimitException:
    """测试限流异常"""

    def test_rate_limit_exception(self):
        """测试限流异常创建"""
        exc = RateLimitExceededException(limit=100, window=60)

        assert exc.status_code == 429
        assert "100" in exc.message or "rate limit" in exc.message.lower()

@pytest.mark.unit
@pytest.mark.asyncio
class TestRateLimiterIntegration:
    """测试限流器集成"""

    async def test_concurrent_requests_under_limit(self):
        """测试并发请求低于限制"""
        limiter = RateLimiter()

        with patch.object(limiter.redis, 'pipeline') as mock_pipeline:
            mock_pipe = MagicMock()
            mock_pipeline.return_value = mock_pipe
            mock_pipe.execute.return_value = [0, 5, None, True]

            # 多个并发请求
            import asyncio

            tasks = [
                limiter.check_rate_limit("user123", limit=10, window=60)
                for _ in range(5)
            ]

            # 不应该抛出异常
            await asyncio.gather(*tasks)

    async def test_requests_exceeding_limit(self):
        """测试请求超过限制"""
        limiter = RateLimiter()

        with patch.object(limiter.redis, 'pipeline') as mock_pipeline:
            mock_pipe = MagicMock()
            mock_pipeline.return_value = mock_pipe

            # 前几次成功，最后一次失败
            call_count = [0]

            def mock_execute():
                call_count[0] += 1
                if call_count[0] <= 10:
                    return [0, call_count[0], None, True]
                else:
                    return [0, 10, None, True]  # 达到限制

            mock_pipe.execute.side_effect = mock_execute

            # 前 10 次应该成功
            for _ in range(10):
                await limiter.check_rate_limit("user123", limit=10, window=60)

            # 第 11 次应该失败
            with pytest.raises(RateLimitExceededException):
                await limiter.check_rate_limit("user123", limit=10, window=60)
