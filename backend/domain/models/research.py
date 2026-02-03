"""
Research Result Domain Model

研究结果领域模型，用于表示单个主题的研究结果。
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ResearchStatus(str, Enum):
    """研究状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # 部分成功


@dataclass
class Reference:
    """
    参考文献模型

    Attributes:
        id: 参考文献ID
        title: 文献标题
        url: 文献链接
        source: 来源
        doc_id: 文档ID
    """

    id: int
    title: str
    url: str = ""
    source: str = ""
    doc_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "doc_id": self.doc_id
        }


@dataclass
class ResearchResult:
    """
    研究结果模型

    表示单个主题的研究结果，包含研究内容、参考文献等。

    Attributes:
        topic_id: 关联的主题ID
        topic_title: 主题标题
        content: 研究内容（Markdown格式）
        status: 研究状态
        references: 参考文献列表
        keywords: 提取的关键词
        summary: 研究摘要
        metadata: 额外的元数据
        created_at: 创建时间
        completed_at: 完成时间
    """

    topic_id: int
    topic_title: str
    content: str = ""
    status: ResearchStatus = ResearchStatus.PENDING
    references: List[Reference] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def mark_completed(self) -> None:
        """标记为已完成"""
        self.status = ResearchStatus.COMPLETED
        self.completed_at = datetime.now()

    def mark_failed(self) -> None:
        """标记为失败"""
        self.status = ResearchStatus.FAILED
        self.completed_at = datetime.now()

    def mark_partial(self) -> None:
        """标记为部分成功"""
        self.status = ResearchStatus.PARTIAL
        self.completed_at = datetime.now()

    def is_successful(self) -> bool:
        """是否成功（完全成功或部分成功）"""
        return self.status in [ResearchStatus.COMPLETED, ResearchStatus.PARTIAL]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "topic_id": self.topic_id,
            "topic_title": self.topic_title,
            "content": self.content,
            "status": self.status.value if isinstance(self.status, ResearchStatus) else self.status,
            "references": [ref.to_dict() for ref in self.references],
            "keywords": self.keywords,
            "summary": self.summary,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchResult":
        """从字典创建实例"""
        references = [Reference(**ref) for ref in data.get("references", [])]
        status_str = data.get("status", "pending")
        status = ResearchStatus(status_str) if isinstance(status_str, str) else status_str

        return cls(
            topic_id=data.get("topic_id", 0),
            topic_title=data.get("topic_title", ""),
            content=data.get("content", ""),
            status=status,
            references=references,
            keywords=data.get("keywords", []),
            summary=data.get("summary", ""),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        )

    def __str__(self) -> str:
        return f"ResearchResult(topic_id={self.topic_id}, status={self.status.value})"


@dataclass
class ResearchResults:
    """
    研究结果集合模型

    包含多个主题的研究结果。

    Attributes:
        results: 研究结果列表
        total_count: 总研究数
        success_count: 成功数量
        failed_count: 失败数量
        metadata: 额外的元数据
    """

    results: List[ResearchResult] = field(default_factory=list)
    total_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        if self.total_count == 0:
            self.total_count = len(self.results)
        self._update_counts()

    def _update_counts(self) -> None:
        """更新统计计数"""
        self.success_count = sum(1 for r in self.results if r.is_successful())
        self.failed_count = sum(1 for r in self.results if r.status == ResearchStatus.FAILED)

    def add_result(self, result: ResearchResult) -> None:
        """添加研究结果"""
        self.results.append(result)
        self.total_count += 1
        self._update_counts()

    def get_result_by_topic_id(self, topic_id: int) -> Optional[ResearchResult]:
        """根据主题ID获取研究结果"""
        for result in self.results:
            if result.topic_id == topic_id:
                return result
        return None

    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "results": [result.to_dict() for result in self.results],
            "total_count": self.total_count,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "success_rate": self.get_success_rate(),
            "metadata": self.metadata
        }


if __name__ == "__main__":
    # 测试代码
    result = ResearchResult(
        topic_id=1,
        topic_title="人工智能",
        content="# 人工智能研究\n\n这是一个测试内容...",
        status=ResearchStatus.COMPLETED,
        keywords=["AI", "机器学习"]
    )
    result.mark_completed()
    print(result)
    print(result.to_dict())
