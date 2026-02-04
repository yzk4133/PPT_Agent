"""
Presentation Domain Model

演示文稿领域模型，用于表示完整的PPT演示文稿。
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .slide import Slide, SlideList
from .topic import TopicList
from .research import ResearchResults

class PresentationStatus(str, Enum):
    """演示文稿状态"""
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"

@dataclass
class PresentationMetadata:
    """
    演示文稿元数据

    Attributes:
        user_id: 用户ID
        language: 语言代码
        num_slides: 幻灯片数量
        theme: 主题
        style: 风格
        created_at: 创建时间
        updated_at: 更新时间
    """

    user_id: str = "anonymous"
    language: str = "EN-US"
    num_slides: int = 10
    theme: str = ""
    style: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "language": self.language,
            "num_slides": self.num_slides,
            "theme": self.theme,
            "style": self.style,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

@dataclass
class Presentation:
    """
    演示文稿模型

    表示完整的PPT演示文稿。

    Attributes:
        id: 演示文稿唯一标识符
        title: 标题
        outline: 大纲内容
        topics: 主题列表
        research_results: 研究结果
        slides: 幻灯片列表
        status: 状态
        metadata: 元数据
        generated_content: 生成的完整内容（XML格式）
        created_at: 创建时间
        completed_at: 完成时间
    """

    id: str
    title: str
    outline: str = ""
    topics: Optional[TopicList] = None
    research_results: Optional[ResearchResults] = None
    slides: Optional[SlideList] = None
    status: PresentationStatus = PresentationStatus.DRAFT
    metadata: PresentationMetadata = field(default_factory=PresentationMetadata)
    generated_content: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def mark_generating(self) -> None:
        """标记为生成中"""
        self.status = PresentationStatus.GENERATING

    def mark_completed(self) -> None:
        """标记为已完成"""
        self.status = PresentationStatus.COMPLETED
        self.completed_at = datetime.now()
        if self.metadata:
            self.metadata.updated_at = datetime.now()

    def mark_failed(self) -> None:
        """标记为失败"""
        self.status = PresentationStatus.FAILED
        self.completed_at = datetime.now()

    def get_progress(self) -> Dict[str, Any]:
        """
        获取生成进度

        Returns:
            包含进度信息的字典
        """
        progress = {
            "status": self.status.value if isinstance(self.status, PresentationStatus) else self.status,
            "stages": {}
        }

        # 主题拆分进度
        if self.topics:
            progress["stages"]["topics"] = {
                "completed": True,
                "count": self.topics.total_count
            }
        else:
            progress["stages"]["topics"] = {"completed": False}

        # 研究进度
        if self.research_results:
            progress["stages"]["research"] = {
                "completed": True,
                "total": self.research_results.total_count,
                "success": self.research_results.success_count,
                "success_rate": self.research_results.get_success_rate()
            }
        else:
            progress["stages"]["research"] = {"completed": False}

        # 幻灯片生成进度
        if self.slides:
            progress["stages"]["slides"] = {
                "completed": True,
                "total": self.slides.total_count
            }
        else:
            progress["stages"]["slides"] = {"completed": False}

        return progress

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "title": self.title,
            "outline": self.outline,
            "topics": self.topics.to_dict() if self.topics else None,
            "research_results": self.research_results.to_dict() if self.research_results else None,
            "slides": self.slides.to_dict() if self.slides else None,
            "status": self.status.value if isinstance(self.status, PresentationStatus) else self.status,
            "metadata": self.metadata.to_dict() if self.metadata else {},
            "generated_content": self.generated_content,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.get_progress()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Presentation":
        """从字典创建实例"""
        metadata_dict = data.get("metadata", {})
        metadata = PresentationMetadata(
            user_id=metadata_dict.get("user_id", "anonymous"),
            language=metadata_dict.get("language", "EN-US"),
            num_slides=metadata_dict.get("num_slides", 10),
            theme=metadata_dict.get("theme", ""),
            style=metadata_dict.get("style", "")
        )

        status_str = data.get("status", "draft")
        status = PresentationStatus(status_str) if isinstance(status_str, str) else status_str

        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            outline=data.get("outline", ""),
            topics=TopicList.from_dict(data["topics"]) if data.get("topics") else None,
            research_results=ResearchResults.from_dict(data["research_results"]) if data.get("research_results") else None,
            slides=SlideList.from_dict(data["slides"]) if data.get("slides") else None,
            status=status,
            metadata=metadata,
            generated_content=data.get("generated_content", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        )

    def __str__(self) -> str:
        return f"Presentation(id='{self.id}', title='{self.title}', status={self.status.value})"

@dataclass
class PresentationRequest:
    """
    演示文稿生成请求模型

    Attributes:
        outline: 大纲内容
        num_slides: 幻灯片数量
        language: 语言
        user_id: 用户ID
        theme: 主题
        style: 风格
        metadata: 额外的元数据
    """

    outline: str
    num_slides: int = 10
    language: str = "EN-US"
    user_id: str = "anonymous"
    theme: str = ""
    style: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outline": self.outline,
            "num_slides": self.num_slides,
            "language": self.language,
            "user_id": self.user_id,
            "theme": self.theme,
            "style": self.style,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PresentationRequest":
        return cls(
            outline=data.get("outline", ""),
            num_slides=data.get("numSlides", data.get("num_slides", 10)),
            language=data.get("language", "EN-US"),
            user_id=data.get("user_id", "anonymous"),
            theme=data.get("theme", ""),
            style=data.get("style", ""),
            metadata=data.get("metadata", {})
        )

if __name__ == "__main__":
    # 测试代码
    request = PresentationRequest(
        outline="人工智能的发展历程",
        num_slides=10,
        language="EN-US"
    )
    print(request.to_dict())
