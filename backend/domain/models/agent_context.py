"""
强类型Agent上下文模型

替代原来的 session.state 字典，提供类型安全的数据传递
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ExecutionMode(str, Enum):
    """执行模式"""

    FULL = "full"  # 完整执行所有阶段
    PHASE_1 = "phase_1"  # 仅执行阶段1-2（需求解析+框架设计）
    PHASE_2 = "phase_2"  # 从checkpoint继续执行阶段3-5


class AgentStage(str, Enum):
    """Agent执行阶段"""

    REQUIREMENT_PARSING = "requirement_parsing"
    FRAMEWORK_DESIGN = "framework_design"
    RESEARCH = "research"
    CONTENT_GENERATION = "content_generation"
    PAGE_RENDERING = "page_rendering"
    QUALITY_CHECK = "quality_check"


@dataclass
class Requirement:
    """需求数据模型"""

    topic: str
    num_slides: int
    language: str = "中文"
    style: str = "professional"
    industry: Optional[str] = None
    target_audience: Optional[str] = None
    key_points: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "topic": self.topic,
            "num_slides": self.num_slides,
            "language": self.language,
            "style": self.style,
            "industry": self.industry,
            "target_audience": self.target_audience,
            "key_points": self.key_points,
        }


@dataclass
class PPTFramework:
    """PPT框架模型"""

    title: str
    outline: List[Dict[str, Any]]
    total_slides: int
    structure_type: str = "linear"  # "linear", "hierarchical", "matrix"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "title": self.title,
            "outline": self.outline,
            "total_slides": self.total_slides,
            "structure_type": self.structure_type,
        }


@dataclass
class ResearchResult:
    """研究结果模型"""

    topic: str
    content: str
    sources: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "topic": self.topic,
            "content": self.content,
            "sources": self.sources,
            "images": self.images,
            "confidence": self.confidence,
        }


@dataclass
class SlideContent:
    """幻灯片内容模型"""

    slide_number: int
    title: str
    content: str
    layout_type: str
    images: List[str] = field(default_factory=list)
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "slide_number": self.slide_number,
            "title": self.title,
            "content": self.content,
            "layout_type": self.layout_type,
            "images": self.images,
            "notes": self.notes,
        }


@dataclass
class AgentContext:
    """
    强类型Agent上下文

    替代原来的 session.state 字典，提供类型安全的数据传递

    使用示例:
        >>> context = AgentContext(
        ...     request_id="req_123",
        ...     requirement=Requirement(topic="AI", num_slides=10)
        ... )
        >>> context.framework = PPTFramework(title="AI发展", outline=[...], total_slides=10)
        >>> print(context.framework.title)  # IDE会提供自动补全
    """

    # 基础信息
    request_id: str
    execution_mode: ExecutionMode = ExecutionMode.FULL
    current_stage: Optional[AgentStage] = None

    # 阶段数据（强类型）
    requirement: Optional[Requirement] = None
    framework: Optional[PPTFramework] = None
    research_results: List[ResearchResult] = field(default_factory=list)
    slide_contents: List[SlideContent] = field(default_factory=list)
    final_ppt_path: Optional[str] = None

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # 错误和重试
    errors: List[str] = field(default_factory=list)
    retry_count: int = 0

    # 扩展字段（向后兼容，用于存储不常用的数据）
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典（用于序列化/存储）

        Returns:
            字典表示
        """
        return {
            "request_id": self.request_id,
            "execution_mode": self.execution_mode.value,
            "current_stage": self.current_stage.value if self.current_stage else None,
            "requirement": self.requirement.to_dict() if self.requirement else None,
            "framework": self.framework.to_dict() if self.framework else None,
            "research_results": [r.to_dict() for r in self.research_results],
            "slide_contents": [s.to_dict() for s in self.slide_contents],
            "final_ppt_path": self.final_ppt_path,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "errors": self.errors,
            "retry_count": self.retry_count,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentContext":
        """
        从字典创建实例（用于反序列化）

        Args:
            data: 字典数据

        Returns:
            AgentContext实例
        """
        context = cls(
            request_id=data["request_id"],
            execution_mode=ExecutionMode(data.get("execution_mode", "full")),
            current_stage=(
                AgentStage(data["current_stage"]) if data.get("current_stage") else None
            ),
            retry_count=data.get("retry_count", 0),
        )

        # 恢复强类型数据
        if data.get("requirement"):
            context.requirement = Requirement(**data["requirement"])

        if data.get("framework"):
            context.framework = PPTFramework(**data["framework"])

        if data.get("research_results"):
            context.research_results = [
                ResearchResult(**r) for r in data["research_results"]
            ]

        if data.get("slide_contents"):
            context.slide_contents = [SlideContent(**s) for s in data["slide_contents"]]

        context.final_ppt_path = data.get("final_ppt_path")
        context.errors = data.get("errors", [])
        context.extra = data.get("extra", {})

        if data.get("created_at"):
            context.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            context.updated_at = datetime.fromisoformat(data["updated_at"])

        return context

    def update_stage(self, stage: AgentStage):
        """更新当前阶段"""
        self.current_stage = stage
        self.updated_at = datetime.now()

    def add_error(self, error: str):
        """添加错误信息"""
        self.errors.append(error)
        self.updated_at = datetime.now()

    def add_research_result(self, result: ResearchResult):
        """添加研究结果"""
        self.research_results.append(result)
        self.updated_at = datetime.now()

    def add_slide_content(self, content: SlideContent):
        """添加幻灯片内容"""
        self.slide_contents.append(content)
        self.updated_at = datetime.now()
