"""
重试与熔断装饰器

基于 tenacity 实现统一的重试和熔断机制，支持：
- 指数退避重试
- 错误分类（可重试 vs 不可重试）
- 熔断器模式
- 重试统计和监控
"""

import logging
import functools
from typing import Optional, Callable, Any, Type, Tuple
from datetime import datetime, timedelta

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_not_exception_type,
    before_sleep_log,
    after_log,
)

from .config import get_config


logger = logging.getLogger(__name__)


# ==================== 异常分类 ====================


class RetryableError(Exception):
    """可重试的错误（如临时性网络问题、rate limit）"""

    pass


class FallbackError(Exception):
    """触发降级的错误（如模型不可用）"""

    pass


class FatalError(Exception):
    """致命错误，不应重试（如配置错误、认证失败）"""

    pass


# ==================== 熔断器 ====================


class CircuitBreaker:
    """
    简单的熔断器实现

    状态：CLOSED（正常）→ OPEN（熔断）→ HALF_OPEN（试探）→ CLOSED
    """

    def __init__(
        self, failure_threshold: int = 5, success_threshold: int = 2, timeout: int = 60
    ):
        """
        Args:
            failure_threshold: 连续失败次数阈值
            success_threshold: HALF_OPEN 状态需要的成功次数
            timeout: 熔断后的恢复时间（秒）
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        执行函数并管理熔断器状态

        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数

        Returns:
            函数执行结果

        Raises:
            Exception: 熔断或函数执行失败
        """
        # OPEN 状态：检查是否可以进入 HALF_OPEN
        if self.state == "OPEN":
            if (
                self.last_failure_time
                and datetime.now() - self.last_failure_time
                > timedelta(seconds=self.timeout)
            ):
                self.state = "HALF_OPEN"
                self.success_count = 0
                logger.info(
                    f"Circuit breaker entering HALF_OPEN state for {func.__name__}"
                )
            else:
                raise FatalError(f"Circuit breaker is OPEN for {func.__name__}")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """成功回调"""
        self.failure_count = 0

        if self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = "CLOSED"
                logger.info("Circuit breaker recovered to CLOSED state")

    def _on_failure(self):
        """失败回调"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == "HALF_OPEN":
            self.state = "OPEN"
            logger.warning("Circuit breaker re-opened from HALF_OPEN")
        elif self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(f"Circuit breaker opened after {self.failure_count} failures")

    def reset(self):
        """重置熔断器"""
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
        logger.info("Circuit breaker reset to CLOSED state")


# 全局熔断器注册表
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str) -> CircuitBreaker:
    """获取或创建熔断器"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker()
    return _circuit_breakers[name]


# ==================== 重试装饰器 ====================


def retry_with_exponential_backoff(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    exceptions: Tuple[Type[Exception], ...] = (RetryableError, Exception),
):
    """
    指数退避重试装饰器

    Args:
        max_attempts: 最大重试次数
        min_wait: 最小等待时间（秒）
        max_wait: 最大等待时间（秒）
        exceptions: 需要重试的异常类型

    Returns:
        装饰器函数
    """

    def decorator(func):
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.INFO),
        )
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def retry_with_fallback(
    max_attempts: int = 3,
    fallback_func: Optional[Callable] = None,
    exceptions: Tuple[Type[Exception], ...] = (RetryableError,),
):
    """
    带降级的重试装饰器

    Args:
        max_attempts: 最大重试次数
        fallback_func: 降级函数（所有重试失败后调用）
        exceptions: 需要重试的异常类型

    Returns:
        装饰器函数
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}"
                    )
                    if attempt < max_attempts - 1:
                        # 等待时间：1s, 2s, 4s, ...
                        wait_time = 2**attempt
                        import time

                        time.sleep(wait_time)
                except FatalError as e:
                    # 致命错误，不重试
                    logger.error(f"Fatal error in {func.__name__}: {e}")
                    raise

            # 所有重试都失败
            if fallback_func:
                logger.info(f"All retries failed for {func.__name__}, using fallback")
                try:
                    return fallback_func(*args, **kwargs)
                except Exception as fb_error:
                    logger.error(f"Fallback also failed: {fb_error}")
                    raise last_exception
            else:
                raise last_exception

        return wrapper

    return decorator


def retry_with_circuit_breaker(
    circuit_breaker_name: str,
    max_attempts: int = 3,
    exceptions: Tuple[Type[Exception], ...] = (RetryableError,),
):
    """
    带熔断器的重试装饰器

    Args:
        circuit_breaker_name: 熔断器名称
        max_attempts: 最大重试次数
        exceptions: 需要重试的异常类型

    Returns:
        装饰器函数
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            circuit_breaker = get_circuit_breaker(circuit_breaker_name)

            # 检查熔断器状态
            if circuit_breaker.state == "OPEN":
                raise FatalError(f"Circuit breaker {circuit_breaker_name} is OPEN")

            # 带重试的执行
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    result = circuit_breaker.call(func, *args, **kwargs)
                    return result
                except exceptions as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed: {e}")
                    if attempt < max_attempts - 1:
                        import time

                        time.sleep(2**attempt)
                except FatalError:
                    # 致命错误或熔断器 OPEN，直接抛出
                    raise

            raise last_exception

        return wrapper

    return decorator


# ==================== 异步版本 ====================


def async_retry_with_exponential_backoff(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    exceptions: Tuple[Type[Exception], ...] = (RetryableError, Exception),
):
    """异步版本的指数退避重试装饰器"""

    def decorator(func):
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.INFO),
        )
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def async_retry_with_fallback(
    max_attempts: int = 3,
    fallback_func: Optional[Callable] = None,
    exceptions: Tuple[Type[Exception], ...] = (RetryableError,),
):
    """异步版本的带降级重试装饰器"""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}"
                    )
                    if attempt < max_attempts - 1:
                        import asyncio

                        await asyncio.sleep(2**attempt)
                except FatalError as e:
                    logger.error(f"Fatal error in {func.__name__}: {e}")
                    raise

            # 所有重试都失败
            if fallback_func:
                logger.info(f"All retries failed for {func.__name__}, using fallback")
                try:
                    if asyncio.iscoroutinefunction(fallback_func):
                        return await fallback_func(*args, **kwargs)
                    else:
                        return fallback_func(*args, **kwargs)
                except Exception as fb_error:
                    logger.error(f"Fallback also failed: {fb_error}")
                    raise last_exception
            else:
                raise last_exception

        return wrapper

    return decorator


if __name__ == "__main__":
    # 测试重试装饰器
    import time

    logging.basicConfig(level=logging.INFO)

    # 测试 1：指数退避重试
    @retry_with_exponential_backoff(max_attempts=3)
    def flaky_function(succeed_on_attempt: int = 3):
        flaky_function.attempt = getattr(flaky_function, "attempt", 0) + 1
        print(f"Attempt {flaky_function.attempt}")
        if flaky_function.attempt < succeed_on_attempt:
            raise RetryableError("Temporary failure")
        return "Success!"

    print("\n=== Test 1: Exponential Backoff ===")
    result = flaky_function(succeed_on_attempt=2)
    print(f"Result: {result}")

    # 测试 2：带降级重试
    def fallback_handler(*args, **kwargs):
        return "Fallback result"

    @retry_with_fallback(max_attempts=2, fallback_func=fallback_handler)
    def always_fail_function():
        raise RetryableError("Always fails")

    print("\n=== Test 2: Retry with Fallback ===")
    result = always_fail_function()
    print(f"Result: {result}")

    # 测试 3：熔断器
    @retry_with_circuit_breaker(circuit_breaker_name="test_breaker", max_attempts=2)
    def circuit_breaker_test(fail: bool = True):
        if fail:
            raise RetryableError("Circuit breaker test failure")
        return "Success"

    print("\n=== Test 3: Circuit Breaker ===")
    for i in range(7):
        try:
            result = circuit_breaker_test(fail=True)
            print(f"Call {i+1}: {result}")
        except Exception as e:
            print(f"Call {i+1}: {type(e).__name__} - {e}")
        time.sleep(0.5)
