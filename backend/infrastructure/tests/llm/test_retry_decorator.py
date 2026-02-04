"""
Retry Decorator 测试
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from infrastructure.llm.retry_decorator import (
    RetryableError,
    FallbackError,
    FatalError,
    CircuitBreaker,
    get_circuit_breaker,
    retry_with_exponential_backoff,
    retry_with_fallback,
    retry_with_circuit_breaker,
    async_retry_with_exponential_backoff,
    async_retry_with_fallback,
    _circuit_breakers,
)

@pytest.mark.unit
class TestRetryableError:
    """测试 RetryableError 异常"""

    def test_retryable_error_creation(self):
        """测试创建 RetryableError"""
        error = RetryableError("Temporary failure")
        assert str(error) == "Temporary failure"
        assert isinstance(error, Exception)

@pytest.mark.unit
class TestFallbackError:
    """测试 FallbackError 异常"""

    def test_fallback_error_creation(self):
        """测试创建 FallbackError"""
        error = FallbackError("Model unavailable")
        assert str(error) == "Model unavailable"
        assert isinstance(error, Exception)

@pytest.mark.unit
class TestFatalError:
    """测试 FatalError 异常"""

    def test_fatal_error_creation(self):
        """测试创建 FatalError"""
        error = FatalError("Authentication failed")
        assert str(error) == "Authentication failed"
        assert isinstance(error, Exception)

@pytest.mark.unit
class TestCircuitBreaker:
    """测试熔断器"""

    def test_circuit_breaker_initialization(self):
        """测试熔断器初始化"""
        cb = CircuitBreaker(failure_threshold=5, success_threshold=2, timeout=60)

        assert cb.failure_threshold == 5
        assert cb.success_threshold == 2
        assert cb.timeout == 60
        assert cb.failure_count == 0
        assert cb.success_count == 0
        assert cb.state == "CLOSED"

    def test_circuit_breaker_call_success(self):
        """测试熔断器调用成功"""
        cb = CircuitBreaker()

        def success_func():
            return "success"

        result = cb.call(success_func)
        assert result == "success"
        assert cb.failure_count == 0
        assert cb.state == "CLOSED"

    def test_circuit_breaker_call_failure(self):
        """测试熔断器调用失败"""
        cb = CircuitBreaker(failure_threshold=3)

        def fail_func():
            raise RetryableError("Temporary failure")

        # 失败一次
        with pytest.raises(RetryableError):
            cb.call(fail_func)

        assert cb.failure_count == 1
        assert cb.state == "CLOSED"

        # 失败两次
        with pytest.raises(RetryableError):
            cb.call(fail_func)

        assert cb.failure_count == 2

        # 失败三次，触发熔断
        with pytest.raises(RetryableError):
            cb.call(fail_func)

        assert cb.failure_count == 3
        assert cb.state == "OPEN"

    def test_circuit_breaker_open_state(self):
        """测试熔断器 OPEN 状态"""
        cb = CircuitBreaker(failure_threshold=2, timeout=1)

        def fail_func():
            raise RetryableError("Failure")

        # 触发熔断
        with pytest.raises(RetryableError):
            cb.call(fail_func)
        with pytest.raises(RetryableError):
            cb.call(fail_func)

        assert cb.state == "OPEN"

        # OPEN 状态下应该直接抛出 FatalError
        with pytest.raises(FatalError, match="Circuit breaker is OPEN"):
            cb.call(fail_func)

    def test_circuit_breaker_half_open_state(self):
        """测试熔断器 HALF_OPEN 状态"""
        cb = CircuitBreaker(failure_threshold=2, success_threshold=2, timeout=0)

        def fail_func():
            raise RetryableError("Failure")

        def success_func():
            return "success"

        # 触发熔断
        with pytest.raises(RetryableError):
            cb.call(fail_func)
        with pytest.raises(RetryableError):
            cb.call(fail_func)

        assert cb.state == "OPEN"

        # 等待超时，进入 HALF_OPEN
        time.sleep(0.1)
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == "HALF_OPEN"
        assert cb.success_count == 1

        # 再次成功，恢复到 CLOSED
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == "CLOSED"
        assert cb.success_count == 0

    def test_circuit_breaker_half_open_failure(self):
        """测试 HALF_OPEN 状态下失败重新打开"""
        cb = CircuitBreaker(failure_threshold=2, success_threshold=2, timeout=0)

        def fail_func():
            raise RetryableError("Failure")

        def success_func():
            return "success"

        # 触发熔断
        with pytest.raises(RetryableError):
            cb.call(fail_func)
        with pytest.raises(RetryableError):
            cb.call(fail_func)

        # 等待超时，进入 HALF_OPEN
        time.sleep(0.1)
        cb.call(success_func)
        assert cb.state == "HALF_OPEN"

        # HALF_OPEN 状态下失败，重新打开
        with pytest.raises(RetryableError):
            cb.call(fail_func)

        assert cb.state == "OPEN"

    def test_circuit_breaker_reset(self):
        """测试重置熔断器"""
        cb = CircuitBreaker(failure_threshold=2)

        def fail_func():
            raise RetryableError("Failure")

        # 触发熔断
        with pytest.raises(RetryableError):
            cb.call(fail_func)
        with pytest.raises(RetryableError):
            cb.call(fail_func)

        assert cb.state == "OPEN"
        assert cb.failure_count == 2

        # 重置
        cb.reset()

        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
        assert cb.success_count == 0

@pytest.mark.unit
class TestCircuitBreakerGlobal:
    """测试全局熔断器"""

    def test_get_circuit_breaker(self):
        """测试获取熔断器"""
        cb1 = get_circuit_breaker("test_cb")
        cb2 = get_circuit_breaker("test_cb")

        assert cb1 is cb2

    def test_get_different_circuit_breakers(self):
        """测试获取不同的熔断器"""
        cb1 = get_circuit_breaker("cb1")
        cb2 = get_circuit_breaker("cb2")

        assert cb1 is not cb2

@pytest.mark.unit
class TestRetryWithExponentialBackoff:
    """测试指数退避重试装饰器"""

    def test_retry_on_failure(self):
        """测试失败时重试"""
        attempts = []

        @retry_with_exponential_backoff(max_attempts=3, min_wait=0.01, max_wait=0.1)
        def flaky_function():
            attempts.append(1)
            if len(attempts) < 3:
                raise RetryableError("Temporary failure")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert len(attempts) == 3

    def test_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        @retry_with_exponential_backoff(max_attempts=2, min_wait=0.01, max_wait=0.1)
        def always_fail_function():
            raise RetryableError("Always fails")

        with pytest.raises(RetryableError):
            always_fail_function()

    def test_no_retry_on_success(self):
        """测试成功时不重试"""
        attempts = []

        @retry_with_exponential_backoff(max_attempts=3)
        def success_function():
            attempts.append(1)
            return "success"

        result = success_function()
        assert result == "success"
        assert len(attempts) == 1

    def test_retry_with_custom_exceptions(self):
        """测试自定义异常重试"""
        class CustomError(Exception):
            pass

        @retry_with_exponential_backoff(
            max_attempts=3,
            min_wait=0.01,
            max_wait=0.1,
            exceptions=(CustomError,)
        )
        def function_with_custom_error():
            raise CustomError("Custom error")

        with pytest.raises(CustomError):
            function_with_custom_error()

@pytest.mark.unit
class TestRetryWithFallback:
    """测试带降级的重试装饰器"""

    def test_retry_with_fallback_success(self):
        """测试重试成功"""
        attempts = []

        @retry_with_fallback(max_attempts=3)
        def flaky_function():
            attempts.append(1)
            if len(attempts) < 2:
                raise RetryableError("Temporary failure")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert len(attempts) == 2

    def test_retry_with_fallback_function(self):
        """测试降级函数"""
        def fallback_handler(*args, **kwargs):
            return "fallback_result"

        @retry_with_fallback(max_attempts=2, fallback_func=fallback_handler)
        def always_fail_function():
            raise RetryableError("Always fails")

        result = always_fail_function()
        assert result == "fallback_result"

    def test_retry_with_fallback_failure(self):
        """测试降级也失败"""
        def failing_fallback(*args, **kwargs):
            raise ValueError("Fallback failed")

        @retry_with_fallback(max_attempts=2, fallback_func=failing_fallback)
        def always_fail_function():
            raise RetryableError("Always fails")

        with pytest.raises(RetryableError):
            always_fail_function()

    def test_retry_with_fatal_error_no_retry(self):
        """测试致命错误不重试"""
        attempts = []

        @retry_with_fallback(max_attempts=3)
        def function_with_fatal_error():
            attempts.append(1)
            raise FatalError("Fatal error")

        with pytest.raises(FatalError):
            function_with_fatal_error()

        # 致命错误不应该重试
        assert len(attempts) == 1

@pytest.mark.unit
class TestRetryWithCircuitBreaker:
    """测试带熔断器的重试装饰器"""

    def test_retry_with_circuit_breaker_success(self):
        """测试熔断器装饰器成功"""
        @retry_with_circuit_breaker(
            circuit_breaker_name="test_cb_success",
            max_attempts=2
        )
        def success_function():
            return "success"

        result = success_function()
        assert result == "success"

    def test_retry_with_circuit_breaker_open(self):
        """测试熔断器打开"""
        # 重置全局熔断器
        _circuit_breakers.clear()

        @retry_with_circuit_breaker(
            circuit_breaker_name="test_cb_open",
            failure_threshold=2,
            max_attempts=2
        )
        def fail_function():
            raise RetryableError("Failure")

        # 触发熔断
        with pytest.raises(RetryableError):
            fail_function()
        with pytest.raises(RetryableError):
            fail_function()

        # 熔断器应该打开
        with pytest.raises(FatalError, match="Circuit breaker.*is OPEN"):
            fail_function()

@pytest.mark.unit
@pytest.mark.asyncio
class TestAsyncRetryWithExponentialBackoff:
    """测试异步指数退避重试装饰器"""

    async def test_async_retry_on_failure(self):
        """测试异步重试"""
        attempts = []

        @async_retry_with_exponential_backoff(
            max_attempts=3,
            min_wait=0.01,
            max_wait=0.1
        )
        async def flaky_async_function():
            attempts.append(1)
            if len(attempts) < 3:
                raise RetryableError("Temporary failure")
            return "success"

        result = await flaky_async_function()
        assert result == "success"
        assert len(attempts) == 3

    async def test_async_retry_success(self):
        """测试异步成功"""
        @async_retry_with_exponential_backoff(max_attempts=3)
        async def success_async_function():
            return "success"

        result = await success_async_function()
        assert result == "success"

@pytest.mark.unit
@pytest.mark.asyncio
class TestAsyncRetryWithFallback:
    """测试异步带降级的重试装饰器"""

    async def test_async_retry_with_fallback(self):
        """测试异步降级"""
        attempts = []

        async def async_fallback(*args, **kwargs):
            return "async_fallback_result"

        @async_retry_with_fallback(
            max_attempts=2,
            fallback_func=async_fallback
        )
        async def always_fail_async_function():
            attempts.append(1)
            raise RetryableError("Always fails")

        result = await always_fail_async_function()
        assert result == "async_fallback_result"
        assert len(attempts) == 2

    async def test_async_retry_with_sync_fallback(self):
        """测试异步函数使用同步降级"""
        def sync_fallback(*args, **kwargs):
            return "sync_fallback_result"

        @async_retry_with_fallback(
            max_attempts=2,
            fallback_func=sync_fallback
        )
        async def always_fail_async_function():
            raise RetryableError("Always fails")

        result = await always_fail_async_function()
        assert result == "sync_fallback_result"

    async def test_async_fatal_error_no_retry(self):
        """测试异步致命错误不重试"""
        attempts = []

        @async_retry_with_fallback(max_attempts=3)
        async def function_with_fatal_error():
            attempts.append(1)
            raise FatalError("Fatal error")

        with pytest.raises(FatalError):
            await function_with_fatal_error()

        assert len(attempts) == 1
