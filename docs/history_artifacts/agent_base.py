"""Agent基类定义

所有Agent的父类，定义统一接口和通用功能
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
import uuid


@dataclass
class AgentMessage:
    """Agent消息数据结构"""
    id: str
    from_agent: str
    to_agent: str
    content: Dict[str, Any]
    timestamp: float

    @classmethod
    def create(cls, from_agent: str, to_agent: str, content: Dict[str, Any]):
        """创建新消息"""
        return cls(
            id=str(uuid.uuid4()),
            from_agent=from_agent,
            to_agent=to_agent,
            content=content,
           =timestamp()
        )


@dataclass
class AgentConfig:
    """Agent配置"""
    name: str
    role: str
    model_provider: str
    max_retries: int = 3
    timeout: int = 30


class BaseAgent(ABC):
    """Agent基类"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.message_history = []

    @abstractmethod
    async def process(self, message: AgentMessage) -> AgentMessage:
        """处理消息的核心方法（子类必须实现）"""
        pass

    async def send_message(self, to_agent: str, content: Dict[str, Any]) -> AgentMessage:
        """发送消息到其他Agent"""
        message = AgentMessage.create(
            from_agent=self.config.name,
            to_agent=to_agent,
            content=content
        )
        self.message_history.append(message)
        return message

    def get_history(self, limit: int = 10) -> list:
        """获取历史消息"""
        return self.message_history[-limit:]
