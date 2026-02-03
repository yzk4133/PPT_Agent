"""
三层内存架构的统一管理器

提供统一的get/set接口，自动管理数据在L1/L2/L3之间的流转：
- 自动路由：根据数据特征选择合适的存储层
- 透明提升：访问频繁或重要的数据自动提升到更持久的层
- 智能降级：过期或低价值数据自动清理
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from .memory_layer_base import (
    MemoryLayer,
    MemoryScope,
    MemoryMetadata,
    PromotionReason,
    PromotionTracker,
)
from .l1_transient_layer import L1TransientLayer
from .l2_short_term_layer import L2ShortTermLayer
from .l3_longterm_layer import L3LongtermLayer
from .promotion_engine import (
    PromotionEngine,
    PromotionConfig,
)

logger = logging.getLogger(__name__)


class HierarchicalMemoryManager:
    """三层内存架构的统一管理器"""

    def __init__(
        self,
        l1_capacity: int = 1000,
        l2_redis_url: Optional[str] = None,
        l3_db_manager: Optional[Any] = None,
        enable_auto_promotion: bool = True,
        promotion_config: Optional[PromotionConfig] = None,
    ):
        """
        初始化三层内存管理器

        Args:
            l1_capacity: L1层容量
            l2_redis_url: L2层Redis连接地址
            l3_db_manager: L3层数据库管理器
            enable_auto_promotion: 是否启用自动提升
            promotion_config: 提升配置
        """
        # 初始化三层
        self.l1 = L1TransientLayer(capacity=l1_capacity)
        self.l2 = L2ShortTermLayer(redis_url=l2_redis_url)
        self.l3 = L3LongtermLayer(db_manager=l3_db_manager)

        # 提升追踪器
        self.promotion_tracker = PromotionTracker()
        self.enable_auto_promotion = enable_auto_promotion

        # 初始化提升引擎
        self.promotion_engine = PromotionEngine(config=promotion_config) if enable_auto_promotion else None

        # 后台任务
        self._promotion_task = None
        self._cleanup_task = None

        logger.info("HierarchicalMemoryManager initialized")

    async def start_background_tasks(self):
        """启动后台任务"""
        await self.l1.start_cleanup_task()

        if self.enable_auto_promotion:
            self._promotion_task = asyncio.create_task(self._auto_promotion_loop())

        logger.info("Background tasks started")

    async def stop_background_tasks(self):
        """停止后台任务"""
        await self.l1.stop_cleanup_task()

        if self._promotion_task:
            self._promotion_task.cancel()
            try:
                await self._promotion_task
            except asyncio.CancelledError:
                pass

        logger.info("Background tasks stopped")

    async def get(
        self,
        key: str,
        scope: MemoryScope,
        scope_id: str,
        search_all_layers: bool = True,
    ) -> Optional[Tuple[Any, MemoryMetadata]]:
        """
        获取数据，自动搜索L1→L2→L3

        Args:
            key: 数据键
            scope: 作用域
            scope_id: 作用域ID
            search_all_layers: 是否搜索所有层（False时只查L1）

        Returns:
            (value, metadata) 或 None
        """
        # 优先从L1获取（最快）
        result = await self.l1.get(key, scope, scope_id)
        if result is not None:
            logger.debug(f"Memory hit in L1: {key}")
            return result

        if not search_all_layers:
            return None

        # L1未命中，尝试L2
        result = await self.l2.get(key, scope, scope_id)
        if result is not None:
            logger.debug(f"Memory hit in L2: {key}")
            value, metadata = result

            # 写回L1（热数据上浮）
            await self.l1.set(key, value, scope, scope_id, metadata)
            return result

        # L2未命中，尝试L3
        result = await self.l3.get(key, scope, scope_id)
        if result is not None:
            logger.debug(f"Memory hit in L3: {key}")
            value, metadata = result

            # 写回L2和L1
            await self.l2.set(key, value, scope, scope_id, metadata)
            await self.l1.set(key, value, scope, scope_id, metadata)
            return result

        return None

    async def set(
        self,
        key: str,
        value: Any,
        scope: MemoryScope,
        scope_id: str,
        importance: float = 0.5,
        target_layer: Optional[MemoryLayer] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        设置数据，自动选择存储层

        Args:
            key: 数据键
            value: 数据值
            scope: 作用域
            scope_id: 作用域ID
            importance: 重要性(0-1)
            target_layer: 指定目标层（None为自动选择）
            tags: 标签列表

        Returns:
            是否成功
        """
        # 标记作用域为活跃
        if self.promotion_engine:
            await self.promotion_engine.mark_scope_active(scope, scope_id)

        # 创建元数据
        metadata = MemoryMetadata(
            key=key,
            layer=MemoryLayer.L1_TRANSIENT,
            scope=scope,
            importance=importance,
            tags=tags or [],
        )

        # 自动选择目标层
        if target_layer is None:
            target_layer = self._determine_target_layer(importance, scope)

        # 根据目标层设置数据
        if target_layer == MemoryLayer.L3_LONG_TERM:
            # 直接写入L3（用户标记重要）
            metadata.layer = MemoryLayer.L3_LONG_TERM
            success = await self.l3.set(key, value, scope, scope_id, metadata)
            if success:
                self.promotion_tracker.record_promotion(
                    key,
                    MemoryLayer.L1_TRANSIENT,
                    MemoryLayer.L3_LONG_TERM,
                    PromotionReason.MANUAL_PROMOTION,
                    metadata,
                )
            return success

        elif target_layer == MemoryLayer.L2_SHORT_TERM:
            # 写入L2
            metadata.layer = MemoryLayer.L2_SHORT_TERM
            return await self.l2.set(key, value, scope, scope_id, metadata)

        else:
            # 默认写入L1
            return await self.l1.set(key, value, scope, scope_id, metadata)

    def _determine_target_layer(
        self, importance: float, scope: MemoryScope
    ) -> MemoryLayer:
        """根据重要性和作用域自动确定目标层"""
        # 高重要性 → L2或L3
        if importance >= 0.8:
            return MemoryLayer.L2_SHORT_TERM
        # 用户级作用域 → L2
        elif scope in (MemoryScope.USER, MemoryScope.WORKSPACE):
            return MemoryLayer.L2_SHORT_TERM
        # 默认 → L1
        else:
            return MemoryLayer.L1_TRANSIENT

    async def delete(
        self,
        key: str,
        scope: MemoryScope,
        scope_id: str,
        delete_all_layers: bool = True,
    ) -> bool:
        """
        删除数据

        Args:
            key: 数据键
            scope: 作用域
            scope_id: 作用域ID
            delete_all_layers: 是否删除所有层（False时只删L1）

        Returns:
            是否至少有一层成功删除
        """
        deleted = False

        # 从L1删除
        if await self.l1.delete(key, scope, scope_id):
            deleted = True

        if delete_all_layers:
            # 从L2删除
            if await self.l2.delete(key, scope, scope_id):
                deleted = True

            # 从L3删除
            if await self.l3.delete(key, scope, scope_id):
                deleted = True

        return deleted

    async def exists(self, key: str, scope: MemoryScope, scope_id: str) -> bool:
        """检查数据是否存在（任一层）"""
        if await self.l1.exists(key, scope, scope_id):
            return True
        if await self.l2.exists(key, scope, scope_id):
            return True
        if await self.l3.exists(key, scope, scope_id):
            return True
        return False

    async def clear_scope(
        self,
        scope: MemoryScope,
        scope_id: str,
        layers: Optional[List[MemoryLayer]] = None,
    ) -> Dict[str, int]:
        """
        清空指定作用域

        Args:
            scope: 作用域
            scope_id: 作用域ID
            layers: 要清理的层（None为全部）

        Returns:
            {"l1": count, "l2": count, "l3": count}
        """
        results = {}

        if layers is None or MemoryLayer.L1_TRANSIENT in layers:
            results["l1"] = await self.l1.clear_scope(scope, scope_id)

        if layers is None or MemoryLayer.L2_SHORT_TERM in layers:
            results["l2"] = await self.l2.clear_scope(scope, scope_id)

        if layers is None or MemoryLayer.L3_LONG_TERM in layers:
            results["l3"] = await self.l3.clear_scope(scope, scope_id)

        return results

    async def get_stats(self) -> Dict[str, Any]:
        """获取全局统计信息"""
        l1_stats = await self.l1.get_stats()
        l2_stats = await self.l2.get_stats()
        l3_stats = await self.l3.get_stats()
        promotion_stats = self.promotion_tracker.get_stats()

        stats = {
            "l1_transient": l1_stats,
            "l2_short_term": l2_stats,
            "l3_long_term": l3_stats,
            "promotion": promotion_stats,
            "total_data_count": (
                l1_stats.get("data_count", 0)
                + l2_stats.get("hits", 0)  # L2无法直接获取数量
                + l3_stats.get("total_records", 0)
            ),
        }

        # 添加提升引擎统计
        if self.promotion_engine:
            stats["promotion_engine"] = await self.promotion_engine.get_stats()

        return stats

    async def _auto_promotion_loop(self):
        """自动提升循环任务"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟执行一次
                await self._perform_auto_promotion()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto promotion error: {e}")

    async def _perform_auto_promotion(self):
        """执行自动提升"""
        if not self.promotion_engine:
            return

        # L1 → L2 提升
        l1_to_l2_result = await self._promote_l1_to_l2()

        # L2 → L3 提升
        l2_to_l3_result = await self._promote_l2_to_l3()

        if l1_to_l2_result.success_count > 0 or l2_to_l3_result.success_count > 0:
            logger.info(
                f"Auto promotion completed: "
                f"L1→L2={l1_to_l2_result.success_count}, L2→L3={l2_to_l3_result.success_count}"
            )

    async def _promote_l1_to_l2(self):
        """L1 → L2 提升"""
        if not self.promotion_engine:
            return type('obj', (object,), {'success_count': 0})()

        return await self.promotion_engine.promote_l1_to_l2(
            self.l1,
            self.l2,
        )

    async def _promote_l2_to_l3(self):
        """L2 → L3 提升"""
        if not self.promotion_engine:
            return type('obj', (object,), {'success_count': 0})()

        return await self.promotion_engine.promote_l2_to_l3(
            self.l2,
            self.l3,
        )

    async def promote_to_l3(
        self,
        key: str,
        scope: MemoryScope,
        scope_id: str,
        reason: PromotionReason = PromotionReason.MANUAL_PROMOTION,
    ) -> bool:
        """
        手动提升数据到L3

        用于用户标记重要的数据
        """
        # 从当前层获取数据
        result = await self.get(key, scope, scope_id)
        if result is None:
            return False

        value, metadata = result

        # 更新元数据
        metadata.layer = MemoryLayer.L3_LONG_TERM
        metadata.importance = max(metadata.importance, 0.8)

        # 写入L3
        success = await self.l3.set(key, value, scope, scope_id, metadata)

        if success:
            # 记录提升
            self.promotion_tracker.record_promotion(
                key,
                MemoryLayer.L1_TRANSIENT,
                MemoryLayer.L3_LONG_TERM,
                reason,
                metadata,
            )
            logger.info(f"Promoted to L3: {key} (reason={reason.value})")

        return success

    async def batch_flush_l1_to_l2(self, scope: MemoryScope, scope_id: str) -> int:
        """
        批量刷新L1高价值数据到L2

        在任务/会话结束时调用
        """
        # 获取需要刷新的数据
        to_flush = await self.l1.batch_flush_to_l2(scope, scope_id)

        if not to_flush:
            return 0

        # 批量写入L2
        items = []
        for key, value, metadata in to_flush:
            metadata.layer = MemoryLayer.L2_SHORT_TERM
            items.append((key, value, scope, scope_id, metadata))

        count = await self.l2.batch_set(items)

        if count > 0:
            logger.info(f"Flushed {count} items from L1 to L2")

        return count

    async def semantic_search(
        self,
        query_embedding: List[float],
        scope: MemoryScope,
        scope_id: str,
        limit: int = 10,
        min_importance: float = 0.3,
    ) -> List[Tuple[str, Any, float]]:
        """
        语义搜索（仅在L3层）

        Args:
            query_embedding: 查询向量
            scope: 作用域
            scope_id: 作用域ID
            limit: 返回数量
            min_importance: 最低重要性

        Returns:
            [(key, content, similarity), ...]
        """
        return await self.l3.semantic_search(
            query_embedding, scope, scope_id, limit, min_importance
        )

    async def get_promotion_history(
        self,
        limit: int = 100,
        **filters,
    ) -> List[Dict[str, Any]]:
        """
        获取提升历史

        Args:
            limit: 最大返回数
            **filters: 筛选条件

        Returns:
            事件列表
        """
        if self.promotion_engine:
            return await self.promotion_engine.get_promotion_history(limit, **filters)
        return []


# 全局单例（可选）
_global_memory_manager: Optional[HierarchicalMemoryManager] = None


def get_global_memory_manager() -> HierarchicalMemoryManager:
    """获取全局内存管理器实例"""
    global _global_memory_manager
    if _global_memory_manager is None:
        _global_memory_manager = HierarchicalMemoryManager()
    return _global_memory_manager


async def init_global_memory_manager(**kwargs):
    """初始化全局内存管理器"""
    global _global_memory_manager
    _global_memory_manager = HierarchicalMemoryManager(**kwargs)
    await _global_memory_manager.start_background_tasks()
    return _global_memory_manager


async def shutdown_global_memory_manager():
    """关闭全局内存管理器"""
    global _global_memory_manager
    if _global_memory_manager:
        await _global_memory_manager.stop_background_tasks()
        _global_memory_manager = None
