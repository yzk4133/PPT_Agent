#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Redis缓存服务
实现read-through/write-back策略
"""
import os
import json
import logging
from typing import Any, Dict, Optional
from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis缓存管理器"""

    # 默认TTL（秒）
    DEFAULT_TTL = 3600  # 1小时
    SESSION_TTL = 3600  # 会话缓存1小时
    USER_PREF_TTL = 86400  # 用户偏好缓存24小时
    VECTOR_TTL = 7200  # 向量检索结果缓存2小时

    def __init__(self):
        """初始化Redis连接"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        try:
            self.client = Redis.from_url(
                redis_url,
                decode_responses=True,  # 自动解码为字符串
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            # 测试连接
            self.client.ping()
            logger.info(f"Redis connected: {self._mask_url(redis_url)}")

        except RedisError as e:
            logger.warning(f"Redis connection failed, cache disabled: {e}")
            self.client = None

    @staticmethod
    def _mask_url(url: str) -> str:
        """隐藏密码"""
        if "@" in url and ":" in url:
            parts = url.split("@")
            if ":" in parts[0]:
                user_pass = parts[0].rsplit(":", 1)
                return f"{user_pass[0].split('//')[0]}//****:****@{parts[1]}"
        return url

    def is_available(self) -> bool:
        """检查Redis是否可用"""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except RedisError:
            return False

    async def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        if not self.client:
            return None

        try:
            value = self.client.get(key)
            if value:
                logger.debug(f"Cache hit: {key}")
            return value
        except RedisError as e:
            logger.warning(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        if not self.client:
            return False

        try:
            ttl = ttl or self.DEFAULT_TTL
            self.client.setex(key, ttl, value)
            logger.debug(f"Cache set: {key} (TTL={ttl}s)")
            return True
        except RedisError as e:
            logger.warning(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.client:
            return False

        try:
            result = self.client.delete(key)
            logger.debug(f"Cache delete: {key} (deleted={result})")
            return result > 0
        except RedisError as e:
            logger.warning(f"Redis delete error: {e}")
            return False

    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """获取JSON格式缓存"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error for key {key}: {e}")
                return None
        return None

    async def set_json(
        self, key: str, value: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """设置JSON格式缓存"""
        try:
            json_str = json.dumps(value, ensure_ascii=False)
            return await self.set(key, json_str, ttl)
        except (TypeError, ValueError) as e:
            logger.warning(f"JSON encode error: {e}")
            return False

    # ===== 业务特定方法 =====

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话缓存"""
        key = f"session:{session_id}"
        return await self.get_json(key)

    async def set_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """设置会话缓存"""
        key = f"session:{session_id}"
        return await self.set_json(key, data, self.SESSION_TTL)

    async def delete_session(self, session_id: str) -> bool:
        """删除会话缓存"""
        key = f"session:{session_id}"
        return await self.delete(key)

    async def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户偏好缓存"""
        key = f"user_pref:{user_id}"
        return await self.get_json(key)

    async def set_user_preferences(
        self, user_id: str, preferences: Dict[str, Any]
    ) -> bool:
        """设置用户偏好缓存"""
        key = f"user_pref:{user_id}"
        return await self.set_json(key, preferences, self.USER_PREF_TTL)

    async def get_vector_results(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """获取向量检索结果缓存"""
        key = f"vector:{query_hash}"
        return await self.get_json(key)

    async def set_vector_results(
        self, query_hash: str, results: Dict[str, Any]
    ) -> bool:
        """设置向量检索结果缓存"""
        key = f"vector:{query_hash}"
        return await self.set_json(key, results, self.VECTOR_TTL)

    async def invalidate_pattern(self, pattern: str) -> int:
        """批量删除匹配模式的缓存"""
        if not self.client:
            return 0

        try:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Invalidated {deleted} keys matching: {pattern}")
                return deleted
            return 0
        except RedisError as e:
            logger.warning(f"Redis pattern delete error: {e}")
            return 0
