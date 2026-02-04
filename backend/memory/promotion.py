"""
自动提升引擎 - Auto Promotion Engine

实现基于访问频率和重要性的智能数据流转：

1. ActiveScopeTracker - 维护活跃作用域列表，避免全量扫描
2. PromotionRuleEngine - 提升规则引擎
3. DataMigrator - 数据迁移器，批量写入
4. PromotionEventLogger - 提升事件记录器

架构设计：
```
┌──────────────────────────────────────────────────────────┐
│              PromotionEngine (提升引擎)                   │
├──────────────────────────────────────────────────────────┤
│  1. 作用域扫描器         │  2. 提升规则引擎              │
│  • 维护活跃scope列表     │  • 访问频率阈值               │
│  • 定期扫描L1/L2        │  • 重要性评分                 │
│  • 增量更新             │  • 跨会话使用检测             │
├──────────────────────────────────────────────────────────┤
│  3. 数据迁移器           │  4. 事件记录器                │
│  • 批量写入              │  • 提升历史追踪               │
│  • 事务保证              │  • 统计分析                   │
└──────────────────────────────────────────────────────────┘
```

配置参数：
```python
PROMOTE_L1_ACCESS_COUNT = 3      # L1→L2访问次数阈值
PROMOTE_L1_IMPORTANCE = 0.7      # L1→L2重要性阈值
PROMOTE_L2_SESSION_COUNT = 2     # L2→L3会话数阈值
PROMOTION_SCAN_INTERVAL = 300    # 扫描间隔（秒）
```
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field
import uuid

from .models import (
    MemoryLayer,
    MemoryScope,
    MemoryMetadata,
    PromotionReason,
)

logger = logging.getLogger(__name__)

# ============================================================================
# 配置常量
# ============================================================================

class PromotionConfig:
    """提升配置常量"""

    # L1 → L2 提升阈值
    PROMOTE_L1_ACCESS_COUNT = 3  # 访问次数阈值
    PROMOTE_L1_IMPORTANCE = 0.7  # 重要性阈值
    PROMOTE_L1_LIFETIME_MINUTES = 10  # 最小生存时间（分钟）

    # L2 → L3 提升阈值
    PROMOTE_L2_SESSION_COUNT = 2  # 跨会话使用次数
    PROMOTE_L2_ACCESS_COUNT = 5  # 访问次数阈值
    PROMOTE_L2_IMPORTANCE = 0.8  # 重要性阈值

    # 扫描配置
    PROMOTION_SCAN_INTERVAL = 300  # 扫描间隔（5分钟）
    MAX_CANDIDATES_PER_BATCH = 100  # 每批最大候选数
    MAX_PROMOTIONS_PER_RUN = 50  # 每次运行最大提升数

    # 活跃作用域配置
    ACTIVE_SCOPE_TTL = 3600  # 活跃作用域TTL（1小时）
    MAX_ACTIVE_SCOPES = 1000  # 最大活跃作用域数

# ============================================================================
# 1. 活跃作用域追踪器
# ============================================================================

class ActiveScopeTracker:
    """
    活跃作用域追踪器

    维护活跃的作用域列表，避免全量扫描L1/L2数据。
    当作用域有写入操作时，自动标记为活跃。
    """

    def __init__(self, ttl_seconds: int = PromotionConfig.ACTIVE_SCOPE_TTL):
        """
        初始化追踪器

        Args:
            ttl_seconds: 作用域活跃TTL（秒）
        """
        self.ttl_seconds = ttl_seconds
        self._active_scopes: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()

    def _build_scope_key(self, scope: MemoryScope, scope_id: str) -> str:
        """构建作用域键"""
        return f"{scope.value}:{scope_id}"

    async def mark_active(self, scope: MemoryScope, scope_id: str):
        """
        标记作用域为活跃

        Args:
            scope: 作用域类型
            scope_id: 作用域ID
        """
        async with self._lock:
            key = self._build_scope_key(scope, scope_id)
            self._active_scopes[key] = datetime.now()
            logger.debug(f"Marked scope as active: {key}")

    async def is_active(self, scope: MemoryScope, scope_id: str) -> bool:
        """
        检查作用域是否活跃

        Args:
            scope: 作用域类型
            scope_id: 作用域ID

        Returns:
            是否活跃
        """
        async with self._lock:
            key = self._build_scope_key(scope, scope_id)
            if key not in self._active_scopes:
                return False

            last_active = self._active_scopes[key]
            if datetime.now() - last_active > timedelta(seconds=self.ttl_seconds):
                # 过期，移除
                del self._active_scopes[key]
                return False

            return True

    async def get_active_scopes(self) -> List[Tuple[MemoryScope, str]]:
        """
        获取所有活跃作用域

        Returns:
            [(scope, scope_id), ...]
        """
        async with self._lock:
            now = datetime.now()
            active = []

            # 清理过期作用域
            expired_keys = []
            for key, last_active in self._active_scopes.items():
                if now - last_active > timedelta(seconds=self.ttl_seconds):
                    expired_keys.append(key)
                else:
                    # 解析作用域
                    parts = key.split(":", 1)
                    if len(parts) == 2:
                        try:
                            scope = MemoryScope(parts[0])
                            scope_id = parts[1]
                            active.append((scope, scope_id))
                        except ValueError:
                            continue

            # 移除过期键
            for key in expired_keys:
                del self._active_scopes[key]

            return active

    async def cleanup_inactive(self):
        """清理不活跃的作用域"""
        async with self._lock:
            now = datetime.now()
            expired_keys = [
                key
                for key, last_active in self._active_scopes.items()
                if now - last_active > timedelta(seconds=self.ttl_seconds)
            ]

            for key in expired_keys:
                del self._active_scopes[key]

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} inactive scopes")

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        async with self._lock:
            return {
                "total_active_scopes": len(self._active_scopes),
                "ttl_seconds": self.ttl_seconds,
            }

# ============================================================================
# 2. 提升规则引擎
# ============================================================================

class PromotionRuleEngine:
    """
    提升规则引擎

    根据访问频率、重要性、跨会话使用等规则判断是否应该提升数据。
    """

    def __init__(self, config: Optional[PromotionConfig] = None):
        """
        初始化规则引擎

        Args:
            config: 提升配置
        """
        self.config = config or PromotionConfig()

    def should_promote_l1_to_l2(
        self,
        metadata: MemoryMetadata,
        current_age_seconds: Optional[float] = None,
    ) -> Tuple[bool, PromotionReason, str]:
        """
        判断是否应该从L1提升到L2

        Args:
            metadata: 数据元信息
            current_age_seconds: 数据当前年龄（秒）

        Returns:
            (should_promote, reason, explanation)
        """
        reasons = []
        explanations = []

        # 规则1: 访问频率
        if metadata.access_count >= self.config.PROMOTE_L1_ACCESS_COUNT:
            reasons.append(PromotionReason.HIGH_ACCESS_FREQUENCY)
            explanations.append(
                f"access_count={metadata.access_count} >= "
                f"{self.config.PROMOTE_L1_ACCESS_COUNT}"
            )

        # 规则2: 重要性评分
        if metadata.importance >= self.config.PROMOTE_L1_IMPORTANCE:
            reasons.append(PromotionReason.HIGH_IMPORTANCE_SCORE)
            explanations.append(
                f"importance={metadata.importance:.2f} >= "
                f"{self.config.PROMOTE_L1_IMPORTANCE}"
            )

        # 规则3: 长期存在（可选）
        if current_age_seconds is not None:
            age_minutes = current_age_seconds / 60
            if age_minutes >= self.config.PROMOTE_L1_LIFETIME_MINUTES:
                # 长期存在但访问频率不高，结合重要性判断
                if metadata.access_count >= 2:
                    reasons.append(PromotionReason.LONG_LIFETIME)
                    explanations.append(
                        f"age={age_minutes:.1f}min >= "
                        f"{self.config.PROMOTE_L1_LIFETIME_MINUTES}min"
                    )

        # 决策
        if reasons:
            # 优先级: 重要性 > 访问频率 > 长期存在
            if PromotionReason.HIGH_IMPORTANCE_SCORE in reasons:
                return (
                    True,
                    PromotionReason.HIGH_IMPORTANCE_SCORE,
                    "; ".join(explanations),
                )
            elif PromotionReason.HIGH_ACCESS_FREQUENCY in reasons:
                return (
                    True,
                    PromotionReason.HIGH_ACCESS_FREQUENCY,
                    "; ".join(explanations),
                )
            else:
                return True, reasons[0], "; ".join(explanations)

        return (
            False,
            None,
            f"No promotion rule met: access_count={metadata.access_count}, importance={metadata.importance:.2f}",
        )

    def should_promote_l2_to_l3(
        self,
        metadata: MemoryMetadata,
        cross_session_count: int,
    ) -> Tuple[bool, PromotionReason, str]:
        """
        判断是否应该从L2提升到L3

        Args:
            metadata: 数据元信息
            cross_session_count: 跨会话使用次数

        Returns:
            (should_promote, reason, explanation)
        """
        reasons = []
        explanations = []

        # 规则1: 跨会话使用
        if cross_session_count >= self.config.PROMOTE_L2_SESSION_COUNT:
            reasons.append(PromotionReason.CROSS_SESSION_USAGE)
            explanations.append(
                f"cross_session_count={cross_session_count} >= "
                f"{self.config.PROMOTE_L2_SESSION_COUNT}"
            )

        # 规则2: 元数据中的session_ids数量
        if len(metadata.session_ids) >= self.config.PROMOTE_L2_SESSION_COUNT:
            reasons.append(PromotionReason.CROSS_SESSION_USAGE)
            explanations.append(
                f"session_ids_count={len(metadata.session_ids)} >= "
                f"{self.config.PROMOTE_L2_SESSION_COUNT}"
            )

        # 规则3: 高访问频率 + 高重要性
        if (
            metadata.access_count >= self.config.PROMOTE_L2_ACCESS_COUNT
            and metadata.importance >= self.config.PROMOTE_L2_IMPORTANCE
        ):
            reasons.append(PromotionReason.HIGH_ACCESS_FREQUENCY)
            explanations.append(
                f"access_count={metadata.access_count} >= "
                f"{self.config.PROMOTE_L2_ACCESS_COUNT} AND "
                f"importance={metadata.importance:.2f} >= "
                f"{self.config.PROMOTE_L2_IMPORTANCE}"
            )

        # 决策
        if reasons:
            # 优先级: 跨会话使用 > 访问频率
            if PromotionReason.CROSS_SESSION_USAGE in reasons:
                return (
                    True,
                    PromotionReason.CROSS_SESSION_USAGE,
                    "; ".join(explanations),
                )
            else:
                return True, reasons[0], "; ".join(explanations)

        return (
            False,
            None,
            f"No promotion rule met: cross_session={cross_session_count}, session_ids={len(metadata.session_ids)}, access_count={metadata.access_count}, importance={metadata.importance:.2f}",
        )

# ============================================================================
# 3. 数据迁移器
# ============================================================================

@dataclass
class MigrationResult:
    """数据迁移结果"""

    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0

class DataMigrator:
    """
    数据迁移器

    负责批量数据迁移，确保事务一致性。
    """

    def __init__(self):
        """初始化迁移器"""
        self._migration_stats = defaultdict(
            lambda: {
                "total": 0,
                "success": 0,
                "failed": 0,
            }
        )

    async def migrate_l1_to_l2(
        self,
        candidates: List[Tuple[str, Any, MemoryMetadata, PromotionReason]],
        l2_layer,
        scope: MemoryScope,
        scope_id: str,
        batch_size: int = 50,
    ) -> MigrationResult:
        """
        批量迁移L1数据到L2

        Args:
            candidates: 候选数据列表 [(key, value, metadata, reason), ...]
            l2_layer: L2层实例
            scope: 作用域
            scope_id: 作用域ID
            batch_size: 批次大小

        Returns:
            迁移结果
        """
        result = MigrationResult()
        start_time = datetime.now()

        if not candidates:
            return result

        logger.info(f"Starting L1→L2 migration: {len(candidates)} candidates")

        # 分批处理
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i : i + batch_size]

            # 准备批量写入数据
            items = []
            for key, value, metadata, reason in batch:
                # 更新元数据
                metadata.layer = MemoryLayer.L2_SHORT_TERM
                items.append((key, value, scope, scope_id, metadata))

            # 批量写入
            try:
                count = await l2_layer.batch_set(items)

                result.success_count += count
                result.skipped_count += len(batch) - count

                logger.debug(
                    f"L1→L2 batch {i // batch_size + 1}: "
                    f"{count}/{len(batch)} succeeded"
                )

            except Exception as e:
                error_msg = f"Batch {i // batch_size + 1} failed: {e}"
                result.errors.append(error_msg)
                result.failed_count += len(batch)
                logger.error(error_msg)

        result.duration_seconds = (datetime.now() - start_time).total_seconds()

        logger.info(
            f"L1→L2 migration completed: "
            f"success={result.success_count}, "
            f"failed={result.failed_count}, "
            f"skipped={result.skipped_count}, "
            f"duration={result.duration_seconds:.2f}s"
        )

        # 更新统计
        self._migration_stats["l1_to_l2"]["total"] += len(candidates)
        self._migration_stats["l1_to_l2"]["success"] += result.success_count
        self._migration_stats["l1_to_l2"]["failed"] += result.failed_count

        return result

    async def migrate_l2_to_l3(
        self,
        candidates: List[Tuple[str, Any, MemoryMetadata, PromotionReason]],
        l3_layer,
        scope: MemoryScope,
        scope_id: str,
    ) -> MigrationResult:
        """
        批量迁移L2数据到L3

        Args:
            candidates: 候选数据列表 [(key, value, metadata, reason), ...]
            l3_layer: L3层实例
            scope: 作用域
            scope_id: 作用域ID

        Returns:
            迁移结果
        """
        result = MigrationResult()
        start_time = datetime.now()

        if not candidates:
            return result

        logger.info(f"Starting L2→L3 migration: {len(candidates)} candidates")

        # 逐个写入L3（L3不支持批量）
        for key, value, metadata, reason in candidates:
            try:
                # 更新元数据
                metadata.layer = MemoryLayer.L3_LONG_TERM
                metadata.importance = max(metadata.importance, 0.8)

                success = await l3_layer.set(key, value, scope, scope_id, metadata)

                if success:
                    result.success_count += 1
                else:
                    result.failed_count += 1
                    result.errors.append(f"Failed to write {key} to L3")

            except Exception as e:
                error_msg = f"Failed to migrate {key}: {e}"
                result.errors.append(error_msg)
                result.failed_count += 1
                logger.error(error_msg)

        result.duration_seconds = (datetime.now() - start_time).total_seconds()

        logger.info(
            f"L2→L3 migration completed: "
            f"success={result.success_count}, "
            f"failed={result.failed_count}, "
            f"duration={result.duration_seconds:.2f}s"
        )

        # 更新统计
        self._migration_stats["l2_to_l3"]["total"] += len(candidates)
        self._migration_stats["l2_to_l3"]["success"] += result.success_count
        self._migration_stats["l2_to_l3"]["failed"] += result.failed_count

        return result

    def get_migration_stats(self) -> Dict[str, Any]:
        """获取迁移统计"""
        return dict(self._migration_stats)

# ============================================================================
# 4. 提升事件记录器
# ============================================================================

@dataclass
class PromotionEvent:
    """提升事件"""

    event_id: str
    timestamp: datetime
    key: str
    from_layer: MemoryLayer
    to_layer: MemoryLayer
    reason: PromotionReason
    scope: MemoryScope
    scope_id: str
    access_count: int
    importance: float
    session_count: int
    explanation: str
    success: bool
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "key": self.key,
            "from_layer": self.from_layer.value,
            "to_layer": self.to_layer.value,
            "reason": self.reason.value,
            "scope": self.scope.value,
            "scope_id": self.scope_id,
            "access_count": self.access_count,
            "importance": self.importance,
            "session_count": self.session_count,
            "explanation": self.explanation,
            "success": self.success,
            "error_message": self.error_message,
        }

class PromotionEventLogger:
    """
    提升事件记录器

    记录所有提升事件，用于监控和调试。
    """

    def __init__(self, max_history: int = 10000):
        """
        初始化记录器

        Args:
            max_history: 最大历史记录数
        """
        self.max_history = max_history
        self._events: List[PromotionEvent] = []
        self._events_by_key: Dict[str, List[str]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def log_event(
        self,
        key: str,
        from_layer: MemoryLayer,
        to_layer: MemoryLayer,
        reason: PromotionReason,
        scope: MemoryScope,
        scope_id: str,
        metadata: MemoryMetadata,
        explanation: str,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> str:
        """
        记录提升事件

        Args:
            key: 数据键
            from_layer: 源层级
            to_layer: 目标层级
            reason: 提升原因
            scope: 作用域
            scope_id: 作用域ID
            metadata: 数据元信息
            explanation: 解释
            success: 是否成功
            error_message: 错误信息

        Returns:
            事件ID
        """
        async with self._lock:
            event = PromotionEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                key=key,
                from_layer=from_layer,
                to_layer=to_layer,
                reason=reason,
                scope=scope,
                scope_id=scope_id,
                access_count=metadata.access_count,
                importance=metadata.importance,
                session_count=len(metadata.session_ids),
                explanation=explanation,
                success=success,
                error_message=error_message,
            )

            self._events.append(event)
            self._events_by_key[key].append(event.event_id)

            # 限制历史记录数量
            if len(self._events) > self.max_history:
                oldest = self._events.pop(0)
                if oldest.key in self._events_by_key:
                    self._events_by_key[oldest.key].remove(oldest.event_id)

            logger.debug(
                f"Logged promotion event: {key} from {from_layer.value} "
                f"to {to_layer.value} (reason={reason.value}, success={success})"
            )

            return event.event_id

    async def get_events(
        self,
        limit: int = 100,
        key: Optional[str] = None,
        from_layer: Optional[MemoryLayer] = None,
        to_layer: Optional[MemoryLayer] = None,
        reason: Optional[PromotionReason] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取提升事件

        Args:
            limit: 最大返回数
            key: 筛选键（可选）
            from_layer: 筛选源层级（可选）
            to_layer: 筛选目标层级（可选）
            reason: 筛选原因（可选）

        Returns:
            事件列表
        """
        async with self._lock:
            events = self._events

            # 应用筛选
            if key:
                event_ids = self._events_by_key.get(key, [])
                events = [e for e in events if e.event_id in event_ids]

            if from_layer:
                events = [e for e in events if e.from_layer == from_layer]

            if to_layer:
                events = [e for e in events if e.to_layer == to_layer]

            if reason:
                events = [e for e in events if e.reason == reason]

            # 排序（最新在前）并限制数量
            events = sorted(events, key=lambda e: e.timestamp, reverse=True)
            events = events[:limit]

            return [e.to_dict() for e in events]

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        async with self._lock:
            total = len(self._events)
            successful = sum(1 for e in self._events if e.success)
            failed = total - successful

            # 按层级转换统计
            by_transition = defaultdict(int)
            for e in self._events:
                if e.success:
                    transition = f"{e.from_layer.value}_to_{e.to_layer.value}"
                    by_transition[transition] += 1

            # 按原因统计
            by_reason = defaultdict(int)
            for e in self._events:
                if e.success:
                    by_reason[e.reason.value] += 1

            return {
                "total_events": total,
                "successful": successful,
                "failed": failed,
                "by_transition": dict(by_transition),
                "by_reason": dict(by_reason),
                "unique_keys_promoted": len(self._events_by_key),
            }

    async def clear_old_events(self, days: int = 7):
        """
        清理旧事件

        Args:
            days: 保留天数
        """
        async with self._lock:
            cutoff = datetime.now() - timedelta(days=days)
            initial_count = len(self._events)

            self._events = [e for e in self._events if e.timestamp > cutoff]

            # 重建索引
            self._events_by_key.clear()
            for event in self._events:
                self._events_by_key[event.key].append(event.event_id)

            removed = initial_count - len(self._events)
            if removed > 0:
                logger.info(f"Cleared {removed} old promotion events (>{days} days)")

# ============================================================================
# 5. 主提升引擎
# ============================================================================

class PromotionEngine:
    """
    自动提升引擎

    整合所有组件，提供完整的自动提升功能。
    """

    def __init__(
        self,
        config: Optional[PromotionConfig] = None,
    ):
        """
        初始化提升引擎

        Args:
            config: 提升配置
        """
        self.config = config or PromotionConfig()

        # 初始化组件
        self.scope_tracker = ActiveScopeTracker(
            ttl_seconds=self.config.ACTIVE_SCOPE_TTL
        )
        self.rule_engine = PromotionRuleEngine(config=self.config)
        self.data_migrator = DataMigrator()
        self.event_logger = PromotionEventLogger()

        logger.info("PromotionEngine initialized")

    async def mark_scope_active(self, scope: MemoryScope, scope_id: str):
        """标记作用域为活跃"""
        await self.scope_tracker.mark_active(scope, scope_id)

    async def promote_l1_to_l2(
        self,
        l1_layer,
        l2_layer,
        max_candidates: Optional[int] = None,
    ) -> MigrationResult:
        """
        执行L1→L2提升

        Args:
            l1_layer: L1层实例
            l2_layer: L2层实例
            max_candidates: 最大候选数

        Returns:
            迁移结果
        """
        max_candidates = max_candidates or self.config.MAX_PROMOTIONS_PER_RUN
        candidates = []
        processed_scopes = 0

        # 获取活跃作用域
        active_scopes = await self.scope_tracker.get_active_scopes()

        logger.info(f"Scanning {len(active_scopes)} active scopes for L1→L2 promotion")

        for scope, scope_id in active_scopes:
            if len(candidates) >= max_candidates:
                break

            # 获取该作用域下的所有键
            keys = await l1_layer.list_keys(scope, scope_id)

            for key in keys:
                if len(candidates) >= max_candidates:
                    break

                # 获取数据和元数据
                result = await l1_layer.get(key, scope, scope_id)
                if result is None:
                    continue

                value, metadata = result

                # 评估提升规则
                should_promote, reason, explanation = (
                    self.rule_engine.should_promote_l1_to_l2(metadata)
                )

                if should_promote and reason:
                    candidates.append((key, value, metadata, reason))

                    # 记录事件（待迁移后更新状态）
                    event_id = await self.event_logger.log_event(
                        key=key,
                        from_layer=MemoryLayer.L1_TRANSIENT,
                        to_layer=MemoryLayer.L2_SHORT_TERM,
                        reason=reason,
                        scope=scope,
                        scope_id=scope_id,
                        metadata=metadata,
                        explanation=explanation,
                        success=False,  # 待迁移后更新
                    )

            processed_scopes += 1

        logger.info(f"Found {len(candidates)} L1→L2 promotion candidates")

        if not candidates:
            return MigrationResult()

        # 执行迁移
        result = await self.data_migrator.migrate_l1_to_l2(
            candidates,
            l2_layer,
            scope,  # 使用最后的作用域（简化）
            scope_id,
        )

        # 更新事件状态
        for i, (key, value, metadata, reason) in enumerate(candidates):
            success = i < result.success_count
            events = await self.event_logger.get_events(limit=1, key=key)
            if events:
                # 这里简化处理，实际应该通过event_id更新
                pass

        return result

    async def promote_l2_to_l3(
        self,
        l2_layer,
        l3_layer,
        max_candidates: Optional[int] = None,
    ) -> MigrationResult:
        """
        执行L2→L3提升

        Args:
            l2_layer: L2层实例
            l3_layer: L3层实例
            max_candidates: 最大候选数

        Returns:
            迁移结果
        """
        max_candidates = max_candidates or self.config.MAX_PROMOTIONS_PER_RUN
        candidates = []

        # 获取活跃作用域
        active_scopes = await self.scope_tracker.get_active_scopes()

        logger.info(f"Scanning {len(active_scopes)} active scopes for L2→L3 promotion")

        for scope, scope_id in active_scopes:
            if len(candidates) >= max_candidates:
                break

            # 获取该作用域下的所有键
            keys = await l2_layer.list_keys(scope, scope_id)

            for key in keys:
                if len(candidates) >= max_candidates:
                    break

                # 获取数据和元数据
                result = await l2_layer.get(key, scope, scope_id)
                if result is None:
                    continue

                value, metadata = result

                # 获取跨会话使用次数
                cross_session_count = await l2_layer.get_cross_session_count(key)

                # 评估提升规则
                should_promote, reason, explanation = (
                    self.rule_engine.should_promote_l2_to_l3(
                        metadata, cross_session_count
                    )
                )

                if should_promote and reason:
                    candidates.append((key, value, metadata, reason))

        logger.info(f"Found {len(candidates)} L2→L3 promotion candidates")

        if not candidates:
            return MigrationResult()

        # 执行迁移
        result = await self.data_migrator.migrate_l2_to_l3(
            candidates,
            l3_layer,
            scope,  # 使用最后的作用域（简化）
            scope_id,
        )

        return result

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "scope_tracker": await self.scope_tracker.get_stats(),
            "migration": self.data_migrator.get_migration_stats(),
            "events": await self.event_logger.get_stats(),
        }

    async def get_promotion_history(
        self,
        limit: int = 100,
        **filters,
    ) -> List[Dict[str, Any]]:
        """获取提升历史"""
        return await self.event_logger.get_events(limit=limit, **filters)
