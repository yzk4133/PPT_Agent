"""
三层内存架构的抽象基类和核心接口定义

L1 (Transient Memory): 瞬时内存 - 任务级生命周期，纯内存存储
L2 (Short-term Memory): 短期内存 - 会话级生命周期，Redis存储
L3 (Long-term Memory): 长期内存 - 用户级永久存储，PostgreSQL+pgvector
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MemoryLayer(Enum):
    """内存层级枚举"""

    L1_TRANSIENT = "transient"  # 瞬时内存 (seconds)
    L2_SHORT_TERM = "short_term"  # 短期内存 (hours)
    L3_LONG_TERM = "long_term"  # 长期内存 (permanent)


class MemoryScope(Enum):
    """内存作用域枚举"""

    TASK = "task"  # 单个任务范围
    SESSION = "session"  # 单个会话范围
    AGENT = "agent"  # 单个Agent范围
    WORKSPACE = "workspace"  # 多Agent工作区范围
    USER = "user"  # 用户级全局范围


class PromotionReason(Enum):
    """数据提升原因"""

    HIGH_ACCESS_FREQUENCY = "high_access_frequency"  # 高访问频率
    HIGH_IMPORTANCE_SCORE = "high_importance_score"  # 高重要性分数
    CROSS_SESSION_USAGE = "cross_session_usage"  # 跨会话使用
    MANUAL_PROMOTION = "manual_promotion"  # 手动标记重要
    LONG_LIFETIME = "long_lifetime"  # 长期存在


class MemoryMetadata:
    """内存数据的元信息"""

    def __init__(
        self,
        key: str,
        layer: MemoryLayer,
        scope: MemoryScope,
        created_at: Optional[datetime] = None,
        importance: float = 0.5,
        access_count: int = 0,
        last_accessed: Optional[datetime] = None,
        session_ids: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ):
        self.key = key
        self.layer = layer
        self.scope = scope
        self.created_at = created_at or datetime.now()
        self.importance = max(0.0, min(1.0, importance))  # 0-1范围
        self.access_count = access_count
        self.last_accessed = last_accessed or datetime.now()
        self.session_ids = session_ids or []
        self.tags = tags or []

    def increment_access(self):
        """增加访问计数"""
        self.access_count += 1
        self.last_accessed = datetime.now()

    def add_session_id(self, session_id: str):
        """添加访问会话ID"""
        if session_id not in self.session_ids:
            self.session_ids.append(session_id)

    def should_promote_to_l2(self) -> bool:
        """判断是否应该从L1提升到L2"""
        # 规则：访问次数≥3次 或 重要性≥0.7
        return self.access_count >= 3 or self.importance >= 0.7

    def should_promote_to_l3(self) -> bool:
        """判断是否应该从L2提升到L3"""
        # 规则：跨会话使用≥2次
        return len(self.session_ids) >= 2

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "key": self.key,
            "layer": self.layer.value,
            "scope": self.scope.value,
            "created_at": self.created_at.isoformat(),
            "importance": self.importance,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat(),
            "session_ids": self.session_ids,
            "tags": self.tags,
        }


class BaseMemoryLayer(ABC):
    """内存层抽象基类"""

    def __init__(self, layer_type: MemoryLayer):
        self.layer_type = layer_type
        self.logger = logging.getLogger(f"{__name__}.{layer_type.value}")

    @abstractmethod
    async def get(
        self, key: str, scope: MemoryScope, scope_id: str
    ) -> Optional[Tuple[Any, MemoryMetadata]]:
        """
        获取数据

        Args:
            key: 数据键
            scope: 作用域类型
            scope_id: 作用域ID (task_id/session_id/agent_id/user_id等)

        Returns:
            (数据值, 元信息) 或 None
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        scope: MemoryScope,
        scope_id: str,
        metadata: Optional[MemoryMetadata] = None,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """
        设置数据

        Args:
            key: 数据键
            value: 数据值
            scope: 作用域类型
            scope_id: 作用域ID
            metadata: 元信息
            ttl_seconds: 过期时间（秒），None表示使用层级默认值

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def delete(self, key: str, scope: MemoryScope, scope_id: str) -> bool:
        """删除数据"""
        pass

    @abstractmethod
    async def exists(self, key: str, scope: MemoryScope, scope_id: str) -> bool:
        """检查数据是否存在"""
        pass

    @abstractmethod
    async def list_keys(
        self, scope: MemoryScope, scope_id: str, pattern: Optional[str] = None
    ) -> List[str]:
        """列出符合条件的所有键"""
        pass

    @abstractmethod
    async def get_metadata(
        self, key: str, scope: MemoryScope, scope_id: str
    ) -> Optional[MemoryMetadata]:
        """获取数据的元信息"""
        pass

    @abstractmethod
    async def update_metadata(
        self, key: str, scope: MemoryScope, scope_id: str, metadata: MemoryMetadata
    ) -> bool:
        """更新数据的元信息"""
        pass

    @abstractmethod
    async def clear_scope(self, scope: MemoryScope, scope_id: str) -> int:
        """清空指定作用域的所有数据，返回清除的数量"""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """获取该层的统计信息"""
        pass

    def _build_full_key(self, key: str, scope: MemoryScope, scope_id: str) -> str:
        """构建完整的存储键"""
        return f"{self.layer_type.value}:{scope.value}:{scope_id}:{key}"

    def _parse_full_key(self, full_key: str) -> Optional[Tuple[str, MemoryScope, str]]:
        """解析完整的存储键"""
        try:
            parts = full_key.split(":", 3)
            if len(parts) != 4:
                return None
            layer, scope_str, scope_id, key = parts
            if layer != self.layer_type.value:
                return None
            scope = MemoryScope(scope_str)
            return key, scope, scope_id
        except (ValueError, IndexError):
            return None


class PromotionTracker:
    """数据提升追踪器"""

    def __init__(self):
        self.promotion_history: Dict[str, List[Dict[str, Any]]] = {}

    def record_promotion(
        self,
        key: str,
        from_layer: MemoryLayer,
        to_layer: MemoryLayer,
        reason: PromotionReason,
        metadata: MemoryMetadata,
    ):
        """记录数据提升事件"""
        if key not in self.promotion_history:
            self.promotion_history[key] = []

        self.promotion_history[key].append(
            {
                "timestamp": datetime.now().isoformat(),
                "from_layer": from_layer.value,
                "to_layer": to_layer.value,
                "reason": reason.value,
                "access_count": metadata.access_count,
                "importance": metadata.importance,
                "session_count": len(metadata.session_ids),
            }
        )

    def get_promotion_history(self, key: str) -> List[Dict[str, Any]]:
        """获取指定键的提升历史"""
        return self.promotion_history.get(key, [])

    def get_stats(self) -> Dict[str, Any]:
        """获取提升统计信息"""
        if not self.promotion_history:
            return {"total_promotions": 0, "by_reason": {}, "by_layer_transition": {}}

        by_reason = {}
        by_layer = {}

        for history_list in self.promotion_history.values():
            for event in history_list:
                reason = event["reason"]
                transition = f"{event['from_layer']}_to_{event['to_layer']}"

                by_reason[reason] = by_reason.get(reason, 0) + 1
                by_layer[transition] = by_layer.get(transition, 0) + 1

        return {
            "total_promotions": sum(len(h) for h in self.promotion_history.values()),
            "unique_keys_promoted": len(self.promotion_history),
            "by_reason": by_reason,
            "by_layer_transition": by_layer,
        }
