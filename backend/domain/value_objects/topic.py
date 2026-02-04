"""
Topic Domain Model

研究主题领域模型，用于表示拆分后的研究主题。
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Topic:
    """
    研究主题模型

    表示一个独立的研究主题，包含标题、描述、关键词等信息。

    Attributes:
        id: 主题唯一标识符
        title: 主题标题
        description: 主题描述
        keywords: 关键词列表
        research_focus: 研究重点
        metadata: 额外的元数据
        created_at: 创建时间
    """

    id: int
    title: str
    description: str
    keywords: List[str] = field(default_factory=list)
    research_focus: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "keywords": self.keywords,
            "research_focus": self.research_focus,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Topic":
        """从字典创建实例"""
        return cls(
            id=data.get("id", 0),
            title=data.get("title", ""),
            description=data.get("description", ""),
            keywords=data.get("keywords", []),
            research_focus=data.get("research_focus", ""),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        )

    def __str__(self) -> str:
        return f"Topic(id={self.id}, title='{self.title}')"

@dataclass
class TopicList:
    """
    主题列表模型

    包含多个研究主题的集合。

    Attributes:
        topics: 主题列表
        total_count: 总主题数
        metadata: 额外的元数据
    """

    topics: List[Topic] = field(default_factory=list)
    total_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        if self.total_count == 0:
            self.total_count = len(self.topics)

    def add_topic(self, topic: Topic) -> None:
        """添加主题"""
        self.topics.append(topic)
        self.total_count += 1

    def get_topic_by_id(self, topic_id: int) -> Optional[Topic]:
        """根据ID获取主题"""
        for topic in self.topics:
            if topic.id == topic_id:
                return topic
        return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（JSON兼容）"""
        return {
            "topics": [topic.to_dict() for topic in self.topics],
            "total_count": self.total_count,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TopicList":
        """从字典创建实例"""
        topics = [Topic.from_dict(t) for t in data.get("topics", [])]
        return cls(
            topics=topics,
            total_count=data.get("total_count", len(topics)),
            metadata=data.get("metadata", {})
        )

# JSON Schema 兼容的工厂函数
def create_topic_from_json(data: Dict[str, Any]) -> Topic:
    """
    从JSON数据创建Topic实例

    这是用于解析Agent输出的辅助函数。
    兼容从Agent返回的JSON格式。

    Args:
        data: JSON字典数据

    Returns:
        Topic实例
    """
    return Topic(
        id=data.get("id", 0),
        title=data.get("title", ""),
        description=data.get("description", ""),
        keywords=data.get("keywords", []),
        research_focus=data.get("research_focus", "")
    )

if __name__ == "__main__":
    # 测试代码
    topic = Topic(
        id=1,
        title="人工智能",
        description="研究人工智能的发展历程",
        keywords=["AI", "机器学习", "深度学习"],
        research_focus="技术发展"
    )
    print(topic)
    print(topic.to_dict())
