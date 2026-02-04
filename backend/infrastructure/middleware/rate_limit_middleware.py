"""
限流中间件

提供基于 Redis 的限流功能：
- 滑动窗口算法
- 可配置的限流策略
"""

import logging
import time
from typing import Optional
from fastapi import Request, HTTPException, status
from redis import Redis

from infrastructure.config.common_config import get_config
from infrastructure.exceptions import RateLimitExceededException

logger = logging.getLogger(__name__)

class RateLimiter:
    """基于 Redis 的限流器"""

    def __init__(self):
        """初始化限流器"""
        config = get_config()
        redis_url = getattr(config.database, 'redis_url', 'redis://localhost:6379/0')
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.enabled = getattr(config, 'rate_limit_enabled', True)

    async def check_rate_limit(
        self,
        user_id: str,
        limit: int = 100,
        window: int = 60
    ):
        """
        检查限流

        使用滑动窗口算法实现限流。

        Args:
            user_id: 用户 ID 或 IP 地址
            limit: 时间窗口内最大请求次数
            window: 时间窗口（秒）

        Raises:
            RateLimitExceededException: 超过限流阈值
        """
        if not self.enabled:
            return

        key = f"rate_limit:{user_id}"
        current_time = int(time.time())
        window_start = current_time - window

        try:
            # 使用 Redis sorted set 实现滑动窗口
            pipe = self.redis.pipeline()

            # 移除窗口外的记录
            pipe.zremrangebyscore(key, 0, window_start)

            # 获取当前窗口内的请求计数
            pipe.zcard(key)

            # 添加当前请求
            pipe.zadd(key, {str(current_time): current_time})

            # 设置过期时间
            pipe.expire(key, window + 1)

            results = pipe.execute()
            request_count = results[1]

            if request_count >= limit:
                logger.warning(f"Rate limit exceeded for {user_id}: {request_count} requests")
                raise RateLimitExceededException(limit, window)

        except Exception as e:
            # Redis 故障时，记录日志但不阻塞请求
            logger.error(f"Rate limiter error: {e}")

# 全局限流器实例
rate_limiter = RateLimiter()

# FastAPI 依赖
async def rate_limit_check(
    request: Request,
    limit: int = 100,
    window: int = 60
):
    """
    限流检查依赖

    示例：
        @router.post("/api/endpoint")
        async def endpoint(
            data: RequestData,
            _: None = Depends(rate_limit_check)
        ):
            pass

    Args:
        request: FastAPI 请求对象
        limit: 时间窗口内最大请求次数（默认 100）
        window: 时间窗口（秒，默认 60）
    """
    # 获取用户 ID 或 IP 地址
    user_id = getattr(request.state, "user_id", None) or request.client.host

    await rate_limiter.check_rate_limit(user_id, limit, window)

async def strict_rate_limit_check(
    request: Request
):
    """
    严格限流检查依赖（50次/分钟）

    用于高负载端点。
    """
    await rate_limit_check(request, limit=50, window=60)

async def loose_rate_limit_check(
    request: Request
):
    """
    宽松限流检查依赖（200次/分钟）

    用于低负载端点。
    """
    await rate_limit_check(request, limit=200, window=60)
