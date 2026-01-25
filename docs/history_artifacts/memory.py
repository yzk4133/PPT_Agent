"""上下文记忆模块

维护Agent之间的对话历史和上下文信息
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json


@dataclass
class MemoryItem:
    """记忆项"""
    id: str
    agent_name: str
    content: Dict[str, Any]
    timestamp: datetime
    ttl: Optional[int] = None  # 生存时间（秒）
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return datetime.now() > self.timestamp + timedelta(seconds=self.ttl)


class ContextMemory:
    """上下文记忆管理器"""

    def __init__(self, max_size: int = 1000):
        self.memories: Dict[str, MemoryItem] = {}
        self.agent_memories: Dict[str, List[str]] = {}  # agent -> memory_ids
        self.max_size = max_size

    def add(
        self,
        agent_name: str,
        content: Dict[str, Any],
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """添加记忆

        Args:
            agent_name: Agent名称
            content: 记忆内容
            ttl: 生存时间（秒）
            metadata: 元数据

        Returns:
            记忆ID
        """
        # 清理过期记忆
        self._cleanup_expired()

        # 检查容量
        if len(self.memories) >= self.max_size:
            self._evict_oldest()

        import uuid
        memory_id = str(uuid.uuid4())

        memory = MemoryItem(
            id=memory_id,
            agent_name=agent_name,
            content=content,
            timestamp=datetime.now(),
            ttl=ttl,
            metadata=metadata or {}
        )

        self.memories[memory_id] = memory

        # 按Agent索引
        if agent_name not in self.agent_memories:
            self.agent_memories[agent_name] = []
        self.agent_memories[agent_name].append(memory_id)

        return memory_id

    def get(self, memory_id: str) -> Optional[MemoryItem]:
        """获取记忆"""
        memory = self.memories.get(memory_id)
        if memory and memory.is_expired():
            self.remove(memory_id)
            return None
        return memory

    def get_by_agent(self, agent_name: str, limit: int = 10) -> List[MemoryItem]:
        """获取Agent的记忆列表"""
        memory_ids = self.agent_memories.get(agent_name, [])
        memories = []

        for mid in memory_ids[-limit:]:  # 获取最近的N条
            memory = self.get(mid)
            if memory:
                memories.append(memory)

        return memories

    def search(
        self,
        query: Dict[str, Any],
        agent_name: Optional[str] = None
    ) -> List[MemoryItem]:
        """搜索记忆

        Args:
            query: 搜索条件
            agent_name: 限定Agent（可选）

        Returns:
            匹配的记忆列表
        """
        results = []

        for memory in self.memories.values():
            # 检查是否过期
            if memory.is_expired():
                continue

            # 检查Agent过滤
            if agent_name and memory.agent_name != agent_name:
                continue

            # 检查查询条件
            match = True
            for key, value in query.items():
                if key == "content":
                    # 简单的内容匹配
                    if str(value) not in str(memory.content):
                        match = False
                        break
                elif key in memory.metadata:
                    if memory.metadata[key] != value:
                        match = False
                        break
                else:
                    match = False
                    break

            if match:
                results.append(memory)

        return results

    def remove(self, memory_id: str) -> bool:
        """删除记忆"""
        memory = self.memories.pop(memory_id, None)
        if memory:
            # 从Agent索引中删除
            if memory.agent_name in self.agent_memories:
                self.agent_memories[memory.agent_name].remove(memory_id)
            return True
        return False

    def clear_agent(self, agent_name: str):
        """清空Agent的所有记忆"""
        memory_ids = self.agent_memories.get(agent_name, [])
        for mid in memory_ids:
            self.memories.pop(mid, None)
        self.agent_memories[agent_name] = []

    def _cleanup_expired(self):
        """清理过期记忆"""
        expired_ids = [
            mid for mid, mem in self.memories.items()
            if mem.is_expired()
        ]
        for mid in expired_ids:
            self.remove(mid)

    def _evict_oldest(self):
        """淘汰最旧的记忆"""
        if not self.memories:
            return

        oldest = min(self.memories.items(), key=lambda x: x[1].timestamp)
        self.remove(oldest[0])

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_memories": len(self.memories),
            "agents": len(self.agent_memories),
            "memories_by_agent": {
                agent: len(ids)
                for agent, ids in self.agent_memories.items()
            }
        }
