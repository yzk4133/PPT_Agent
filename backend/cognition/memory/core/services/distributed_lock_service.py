"""
分布式锁服务 - Distributed Lock Service

使用Redis实现分布式锁，基于Redlock算法：

1. 自动重试机制 - 获取锁失败时自动重试
2. 安全释放 - 使用token确保只释放自己持有的锁
3. 续期机制 - 支持锁续期，防止任务超时
4. 上下文管理器 - 支持with语句

使用示例：
```python
lock_service = DistributedLockService(redis_client)

# 方式1: 使用上下文管理器（推荐）
async with lock_service.acquire("user_profile:update:123", ttl=10):
    # 安全地更新用户配置
    await update_user_profile(...)

# 方式2: 手动获取和释放
lock = await lock_service.acquire("user_profile:update:123", ttl=10)
try:
    await update_user_profile(...)
finally:
    await lock.release()
```
"""

import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Optional, List, Any
from datetime import datetime, timedelta
from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


# ============================================================================
# 锁异常类
# ============================================================================

class LockError(Exception):
    """锁基础异常"""
    pass


class LockAcquisitionError(LockError):
    """获取锁失败"""
    pass


class LockReleaseError(LockError):
    """释放锁失败"""
    pass


class LockAlreadyHeldError(LockError):
    """锁已被持有"""
    pass


# ============================================================================
# 配置
# ============================================================================

class LockConfig:
    """分布式锁配置"""

    # 默认TTL（毫秒）
    DEFAULT_TTL = 10000  # 10秒

    # 重试配置
    MAX_RETRIES = 3
    RETRY_DELAY_MS = 200  # 重试延迟（毫秒）

    # 锁续期配置
    AUTO_RENEWAL_THRESHOLD = 0.7  # 当剩余时间 < 70% TTL时自动续期


# ============================================================================
# 分布式锁
# ============================================================================

@dataclass
class DistributedLock:
    """
    分布式锁实例

    Attributes:
        key: 锁键名
        token: 锁令牌（唯一标识）
        ttl: 锁TTL（毫秒）
        acquired_at: 获取时间
        service: 所属服务实例
    """
    key: str
    token: str
    ttl: int
    acquired_at: datetime
    service: 'DistributedLockService'
    _renewal_task: Optional[asyncio.Task] = None
    _auto_renewal: bool = False

    async def release(self) -> bool:
        """
        释放锁

        使用Lua脚本确保只释放自己持有的锁（防止误删其他客户端的锁）

        Returns:
            是否成功释放
        """
        if self._renewal_task:
            self._renewal_task.cancel()
            try:
                await self._renewal_task
            except asyncio.CancelledError:
                pass

        return await self.service._release_lock(self.key, self.token)

    async def extend(self, additional_ttl: Optional[int] = None) -> bool:
        """
        延长锁的TTL

        Args:
            additional_ttl: 延长的TTL（毫秒），None则使用原始TTL

        Returns:
            是否成功延长
        """
        ttl = additional_ttl or self.ttl
        return await self.service._extend_lock(self.key, self.token, ttl)

    async def _auto_renewal_loop(self):
        """自动续期循环"""
        while True:
            try:
                # 计算续期间隔
                interval = self.ttl * LockConfig.AUTO_RENEWAL_THRESHOLD / 1000
                await asyncio.sleep(interval)

                # 尝试续期
                success = await self.extend()
                if not success:
                    logger.warning(f"Failed to auto-renew lock: {self.key}")
                    break

                logger.debug(f"Auto-renewed lock: {self.key}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto-renewal loop: {e}")
                break

    def enable_auto_renewal(self):
        """启用自动续期"""
        if not self._auto_renewal:
            self._auto_renewal = True
            self._renewal_task = asyncio.create_task(self._auto_renewal_loop())
            logger.debug(f"Auto-renewal enabled for lock: {self.key}")

    def disable_auto_renewal(self):
        """禁用自动续期"""
        self._auto_renewal = False
        if self._renewal_task:
            self._renewal_task.cancel()
            self._renewal_task = None

    @property
    def remaining_time_ms(self) -> Optional[int]:
        """
        获取锁剩余时间（毫秒）

        Returns:
            剩余时间，锁已过期返回None
        """
        elapsed = (datetime.now() - self.acquired_at).total_seconds() * 1000
        remaining = self.ttl - elapsed
        return max(0, int(remaining)) if remaining > 0 else None

    @property
    def is_expired(self) -> bool:
        """检查锁是否已过期"""
        return self.remaining_time_ms is None

    async def __aenter__(self):
        """进入上下文"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时自动释放锁"""
        await self.release()
        return False


# ============================================================================
# 分布式锁服务
# ============================================================================

class DistributedLockService:
    """
    分布式锁服务

    基于Redis实现，使用Redlock算法确保分布式环境下的锁安全。
    """

    # Lua脚本：安全释放锁（只释放自己持有的锁）
    RELEASE_SCRIPT = """
        local token = ARGV[1]
        local lock_key = KEYS[1]
        local current_token = redis.call('GET', lock_key)

        if current_token == token then
            return redis.call('DEL', lock_key)
        else
            return 0
        end
    """

    # Lua脚本：延长锁TTL
    EXTEND_SCRIPT = """
        local token = ARGV[1]
        local lock_key = KEYS[1]
        local ttl = ARGV[2]
        local current_token = redis.call('GET', lock_key)

        if current_token == token then
            return redis.call('PEXPIRE', lock_key, ttl)
        else
            return 0
        end
    """

    def __init__(
        self,
        redis_client: Optional[Redis] = None,
        redis_url: Optional[str] = None,
        prefix: str = "lock",
    ):
        """
        初始化分布式锁服务

        Args:
            redis_client: Redis客户端实例
            redis_url: Redis连接URL
            prefix: 锁键名前缀
        """
        if redis_client is None:
            redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
            try:
                redis_client = Redis.from_url(
                    redis_url,
                    decode_responses=False,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                redis_client.ping()
                logger.info(f"DistributedLockService connected to Redis")
            except RedisError as e:
                logger.error(f"Failed to connect to Redis: {e}")
                redis_client = None

        self.redis = redis_client
        self.prefix = prefix
        self.config = LockConfig()

        # 注册Lua脚本
        if self.redis:
            self._release_script = self.redis.register_script(self.RELEASE_SCRIPT)
            self._extend_script = self.redis.register_script(self.EXTEND_SCRIPT)

        logger.info("DistributedLockService initialized")

    def _build_lock_key(self, key: str) -> str:
        """构建锁键名"""
        return f"{self.prefix}:{key}"

    async def acquire(
        self,
        key: str,
        ttl: Optional[int] = None,
        auto_renewal: bool = False,
        wait_timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ) -> DistributedLock:
        """
        获取分布式锁

        Args:
            key: 锁键名
            ttl: 锁TTL（毫秒），None使用默认值
            auto_renewal: 是否启用自动续期
            wait_timeout: 等待超时（毫秒），None表示不等待
            max_retries: 最大重试次数，None使用默认值

        Returns:
            分布式锁实例

        Raises:
            LockAcquisitionError: 获取锁失败
        """
        if not self.redis:
            raise LockAcquisitionError("Redis client not available")

        ttl = ttl or self.config.DEFAULT_TTL
        max_retries = max_retries or self.config.MAX_RETRIES

        lock_key = self._build_lock_key(key)
        token = str(uuid.uuid4())
        start_time = datetime.now()

        for attempt in range(max_retries + 1):
            try:
                # 尝试获取锁
                acquired = self.redis.set(
                    lock_key,
                    token,
                    px=ttl,
                    nx=True,  # 仅当键不存在时设置
                )

                if acquired:
                    lock = DistributedLock(
                        key=key,
                        token=token,
                        ttl=ttl,
                        acquired_at=datetime.now(),
                        service=self,
                    )

                    if auto_renewal:
                        lock.enable_auto_renewal()

                    logger.debug(
                        f"Lock acquired: {key} "
                        f"(attempt={attempt + 1}, ttl={ttl}ms)"
                    )

                    return lock

                # 检查等待超时
                if wait_timeout:
                    elapsed = (datetime.now() - start_time).total_seconds() * 1000
                    if elapsed >= wait_timeout:
                        raise LockAcquisitionError(
                            f"Lock acquisition timeout after {wait_timeout}ms"
                        )

                # 等待后重试
                if attempt < max_retries:
                    delay = self.config.RETRY_DELAY_MS / 1000
                    await asyncio.sleep(delay)

            except RedisError as e:
                logger.error(f"Redis error while acquiring lock {key}: {e}")
                raise LockAcquisitionError(f"Redis error: {e}")

        raise LockAcquisitionError(
            f"Failed to acquire lock after {max_retries + 1} attempts"
        )

    async def _release_lock(self, key: str, token: str) -> bool:
        """
        释放锁（内部方法）

        Args:
            key: 锁键名
            token: 锁令牌

        Returns:
            是否成功释放
        """
        if not self.redis:
            return False

        try:
            lock_key = self._build_lock_key(key)
            result = self._release_script(keys=[lock_key], args=[token])
            success = result > 0

            if success:
                logger.debug(f"Lock released: {key}")
            else:
                logger.warning(
                    f"Lock release failed (already expired or stolen): {key}"
                )

            return success

        except RedisError as e:
            logger.error(f"Redis error while releasing lock {key}: {e}")
            raise LockReleaseError(f"Redis error: {e}")

    async def _extend_lock(self, key: str, token: str, ttl: int) -> bool:
        """
        延长锁TTL（内部方法）

        Args:
            key: 锁键名
            token: 锁令牌
            ttl: 延长的TTL（毫秒）

        Returns:
            是否成功延长
        """
        if not self.redis:
            return False

        try:
            lock_key = self._build_lock_key(key)
            result = self._extend_script(keys=[lock_key], args=[token, ttl])
            success = result > 0

            if success:
                logger.debug(f"Lock extended: {key} (ttl={ttl}ms)")
            else:
                logger.warning(f"Lock extension failed (already expired): {key}")

            return success

        except RedisError as e:
            logger.error(f"Redis error while extending lock {key}: {e}")
            return False

    @asynccontextmanager
    async def lock(
        self,
        key: str,
        ttl: Optional[int] = None,
        auto_renewal: bool = False,
        wait_timeout: Optional[int] = None,
    ):
        """
        上下文管理器方式获取锁

        Args:
            key: 锁键名
            ttl: 锁TTL（毫秒）
            auto_renewal: 是否启用自动续期
            wait_timeout: 等待超时（毫秒）

        Yields:
            分布式锁实例
        """
        lock = await self.acquire(key, ttl, auto_renewal, wait_timeout)
        try:
            yield lock
        finally:
            await lock.release()

    async def is_locked(self, key: str) -> bool:
        """
        检查锁是否存在

        Args:
            key: 锁键名

        Returns:
            是否存在
        """
        if not self.redis:
            return False

        try:
            lock_key = self._build_lock_key(key)
            return self.redis.exists(lock_key) > 0
        except RedisError as e:
            logger.error(f"Redis error while checking lock {key}: {e}")
            return False

    async def get_lock_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取锁信息

        Args:
            key: 锁键名

        Returns:
            锁信息字典，锁不存在返回None
        """
        if not self.redis:
            return None

        try:
            lock_key = self._build_lock_key(key)
            pipeline = self.redis.pipeline()
            pipeline.exists(lock_key)
            pipeline.get(lock_key)
            pipeline.pttl(lock_key)
            results = pipeline.execute()

            exists, token, pttl = results

            if not exists:
                return None

            return {
                "key": key,
                "token": token.decode() if token else None,
                "remaining_ttl_ms": pttl if pttl > 0 else None,
                "is_expired": pttl == -2 or pttl == -1,
            }

        except RedisError as e:
            logger.error(f"Redis error while getting lock info {key}: {e}")
            return None

    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            是否健康
        """
        if not self.redis:
            return False

        try:
            self.redis.ping()
            return True
        except RedisError:
            return False


# ============================================================================
# 全局实例
# ============================================================================

_global_lock_service: Optional[DistributedLockService] = None


def get_lock_service() -> DistributedLockService:
    """获取全局分布式锁服务实例"""
    global _global_lock_service
    if _global_lock_service is None:
        _global_lock_service = DistributedLockService()
    return _global_lock_service


# ============================================================================
# 装饰器
# ============================================================================

def distributed_lock(
    key_func: Optional[str] = None,
    ttl: int = 10000,
    auto_renewal: bool = False,
    wait_timeout: Optional[int] = None,
):
    """
    分布式锁装饰器

    Args:
        key_func: 锁键名（支持f-string格式）
        ttl: 锁TTL（毫秒）
        auto_renewal: 是否启用自动续期
        wait_timeout: 等待超时（毫秒）

    使用示例：
    ```python
    @distributed_lock("update_user:{user_id}", ttl=5000)
    async def update_user(user_id: str, data: dict):
        ...
    ```
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 构建锁键名
            if key_func:
                # 支持f-string格式
                try:
                    lock_key = key_func.format(**kwargs)
                except (KeyError, AttributeError):
                    lock_key = key_func
            else:
                # 使用函数名作为锁键名
                lock_key = f"{func.__module__}.{func.__name__}"

            lock_service = get_lock_service()

            async with lock_service.lock(
                lock_key, ttl, auto_renewal, wait_timeout
            ):
                return await func(*args, **kwargs)

        return wrapper

    return decorator
