"""
Task Domain Model

任务领域模型，用于跟踪PPT生成的完整任务生命周期。
"""

from typing import List, Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from domain.models.presentation import Presentation

# For runtime, we'll use Optional and check at runtime
Presentation = None  # type: ignore

# Import event types
from ..events.task_events import TaskEvent

class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    PARSING_REQUIREMENTS = "parsing_requirements"
    DESIGNING_FRAMEWORK = "designing_framework"
    RESEARCHING = "researching"
    GENERATING_CONTENT = "generating_content"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"
    REVISION_PENDING = "revision_pending"

class TaskStage(str, Enum):
    """任务阶段"""
    REQUIREMENT_PARSING = "requirement_parsing"
    FRAMEWORK_DESIGN = "framework_design"
    RESEARCH = "research"
    CONTENT_GENERATION = "content_generation"
    TEMPLATE_RENDERING = "template_rendering"

@dataclass
class StageProgress:
    """
    阶段进度

    Attributes:
        stage: 阶段名称
        status: 阶段状态
        progress: 进度百分比 (0-100)
        started_at: 开始时间
        completed_at: 完成时间
        error: 错误信息（如果失败）
        retry_count: 重试次数
    """

    stage: TaskStage
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.value,
            "status": self.status.value,
            "progress": self.progress,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "retry_count": self.retry_count
        }

@dataclass
class TaskMetadata:
    """
    任务元数据

    Attributes:
        user_id: 用户ID
        session_id: 会话ID
        created_at: 创建时间
        updated_at: 更新时间
        completed_at: 完成时间
        total_duration: 总耗时（秒）
        revision_count: 修订次数
    """

    user_id: str = "anonymous"
    session_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_duration: float = 0.0
    revision_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_duration": self.total_duration,
            "revision_count": self.revision_count
        }

@dataclass
class Task:
    """
    任务模型

    表示一个完整的PPT生成任务。

    Attributes:
        id: 任务唯一标识符
        status: 任务状态
        metadata: 任务元数据
        stages: 各阶段进度
        presentation: 关联的演示文稿
        raw_input: 原始用户输入
        structured_requirements: 结构化需求（由需求解析智能体生成）
        ppt_framework: PPT框架（由框架设计智能体生成）
        research_results: 研究结果（由资料研究智能体生成）
        content_material: 内容素材（由内容素材智能体生成）
        final_output: 最终输出（文件路径+预览数据）
        error: 错误信息
    """

    id: str
    status: TaskStatus = TaskStatus.PENDING
    metadata: TaskMetadata = field(default_factory=TaskMetadata)
    stages: Dict[TaskStage, StageProgress] = field(default_factory=dict)
    presentation: Optional[Presentation] = None
    raw_input: str = ""
    structured_requirements: Optional[Dict[str, Any]] = None
    ppt_framework: Optional[Dict[str, Any]] = None
    research_results: Optional[List[Dict[str, Any]]] = None
    content_material: Optional[List[Dict[str, Any]]] = None
    final_output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    # Event support (not serialized in to_dict)
    _pending_events: List[TaskEvent] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """初始化阶段进度"""
        if not self.stages:
            for stage in TaskStage:
                self.stages[stage] = StageProgress(stage=stage)

    def _add_event(self, event: TaskEvent) -> None:
        """添加事件到待处理列表"""
        self._pending_events.append(event)

    def get_pending_events(self) -> List[TaskEvent]:
        """
        获取并清空待处理事件列表

        Returns:
            待处理的事件列表
        """
        events = self._pending_events
        self._pending_events = []
        return events

    def start_stage(self, stage: TaskStage) -> None:
        """开始一个阶段"""
        from ..events.task_events import create_stage_started_event

        self.stages[stage].status = TaskStatus.PARSING_REQUIREMENTS if stage == TaskStage.REQUIREMENT_PARSING else (
            TaskStatus.DESIGNING_FRAMEWORK if stage == TaskStage.FRAMEWORK_DESIGN else
            TaskStatus.RESEARCHING if stage == TaskStage.RESEARCH else
            TaskStatus.GENERATING_CONTENT if stage == TaskStage.CONTENT_GENERATION else
            TaskStatus.RENDERING
        )
        self.stages[stage].started_at = datetime.now()
        self.status = self.stages[stage].status
        self.metadata.updated_at = datetime.now()

        # Emit event
        event = create_stage_started_event(
            version=self.metadata.revision_count,
            task_id=self.id,
            stage_name=stage.value
        )
        self._add_event(event)

    def update_stage_progress(self, stage: TaskStage, progress: int) -> None:
        """更新阶段进度"""
        self.stages[stage].progress = max(0, min(100, progress))
        self.metadata.updated_at = datetime.now()

    def complete_stage(self, stage: TaskStage) -> None:
        """完成一个阶段"""
        from ..events.task_events import create_stage_completed_event

        self.stages[stage].status = TaskStatus.COMPLETED
        self.stages[stage].progress = 100
        self.stages[stage].completed_at = datetime.now()
        self.metadata.updated_at = datetime.now()

        # Emit event
        event = create_stage_completed_event(
            version=self.metadata.revision_count,
            task_id=self.id,
            stage_name=stage.value,
            result_data={"stage": stage.value, "status": "completed"}
        )
        self._add_event(event)

    def fail_stage(self, stage: TaskStage, error: str) -> None:
        """标记阶段失败"""
        from ..events.task_events import create_stage_failed_event, create_task_failed_event

        self.stages[stage].status = TaskStatus.FAILED
        self.stages[stage].error = error
        self.stages[stage].completed_at = datetime.now()
        self.status = TaskStatus.FAILED
        self.error = error
        self.metadata.updated_at = datetime.now()

        # Emit stage failed event
        event = create_stage_failed_event(
            version=self.metadata.revision_count,
            task_id=self.id,
            stage_name=stage.value,
            error=error
        )
        self._add_event(event)

        # Emit task failed event
        task_event = create_task_failed_event(
            version=self.metadata.revision_count,
            task_id=self.id,
            error=error
        )
        self._add_event(task_event)

    def increment_retry(self, stage: TaskStage) -> int:
        """增加重试次数"""
        self.stages[stage].retry_count += 1
        return self.stages[stage].retry_count

    def mark_completed(self) -> None:
        """标记任务完成"""
        from ..events.task_events import create_task_completed_event

        self.status = TaskStatus.COMPLETED
        self.metadata.completed_at = datetime.now()
        self.metadata.updated_at = datetime.now()
        if self.metadata.created_at:
            self.metadata.total_duration = (
                self.metadata.completed_at - self.metadata.created_at
            ).total_seconds()

        # Emit event
        event = create_task_completed_event(
            version=self.metadata.revision_count,
            task_id=self.id
        )
        self._add_event(event)

    def get_overall_progress(self) -> int:
        """
        获取总体进度百分比

        各阶段权重：
        - 需求解析: 15%
        - 框架设计: 30%
        - 资料研究: 50% (如果需要)
        - 内容生成: 80%
        - 模板渲染: 100%
        """
        weights = {
            TaskStage.REQUIREMENT_PARSING: 15,
            TaskStage.FRAMEWORK_DESIGN: 30,
            TaskStage.RESEARCH: 50,
            TaskStage.CONTENT_GENERATION: 80,
            TaskStage.TEMPLATE_RENDERING: 100
        }

        # 检查是否需要研究阶段
        need_research = False
        if self.structured_requirements:
            need_research = self.structured_requirements.get("need_research", False)

        total_progress = 0
        for stage, progress in self.stages.items():
            if stage == TaskStage.RESEARCH and not need_research:
                continue
            if progress.progress > 0:
                total_progress += (progress.progress / 100) * weights.get(stage, 0)

        return min(100, int(total_progress))

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "status": self.status.value,
            "metadata": self.metadata.to_dict(),
            "stages": {
                stage.value: progress.to_dict()
                for stage, progress in self.stages.items()
            },
            "presentation": self.presentation.to_dict() if self.presentation else None,
            "raw_input": self.raw_input,
            "structured_requirements": self.structured_requirements,
            "ppt_framework": self.ppt_framework,
            "research_results": self.research_results,
            "content_material": self.content_material,
            "final_output": self.final_output,
            "overall_progress": self.get_overall_progress(),
            "error": self.error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """从字典创建实例"""
        metadata_dict = data.get("metadata", {})
        metadata = TaskMetadata(
            user_id=metadata_dict.get("user_id", "anonymous"),
            session_id=metadata_dict.get("session_id", ""),
            created_at=datetime.fromisoformat(metadata_dict["created_at"]) if metadata_dict.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(metadata_dict["updated_at"]) if metadata_dict.get("updated_at") else None,
            completed_at=datetime.fromisoformat(metadata_dict["completed_at"]) if metadata_dict.get("completed_at") else None,
            total_duration=metadata_dict.get("total_duration", 0.0),
            revision_count=metadata_dict.get("revision_count", 0)
        )

        stages = {}
        for stage_str, progress_dict in data.get("stages", {}).items():
            stage = TaskStage(stage_str)
            stages[stage] = StageProgress(
                stage=stage,
                status=TaskStatus(progress_dict.get("status", "pending")),
                progress=progress_dict.get("progress", 0),
                started_at=datetime.fromisoformat(progress_dict["started_at"]) if progress_dict.get("started_at") else None,
                completed_at=datetime.fromisoformat(progress_dict["completed_at"]) if progress_dict.get("completed_at") else None,
                error=progress_dict.get("error"),
                retry_count=progress_dict.get("retry_count", 0)
            )

        status_str = data.get("status", "pending")
        status = TaskStatus(status_str) if isinstance(status_str, str) else status_str

        presentation = None
        if data.get("presentation"):
            from .presentation import Presentation
            presentation = Presentation.from_dict(data["presentation"])

        return cls(
            id=data.get("id", ""),
            status=status,
            metadata=metadata,
            stages=stages,
            presentation=presentation,
            raw_input=data.get("raw_input", ""),
            structured_requirements=data.get("structured_requirements"),
            ppt_framework=data.get("ppt_framework"),
            research_results=data.get("research_results"),
            content_material=data.get("content_material"),
            final_output=data.get("final_output"),
            error=data.get("error")
        )

    def __str__(self) -> str:
        return f"Task(id='{self.id}', status={self.status.value}, progress={self.get_overall_progress()}%)"

if __name__ == "__main__":
    # 测试代码
    task = Task(id="test_001", raw_input="生成一份AI介绍PPT")
    task.start_stage(TaskStage.REQUIREMENT_PARSING)
    task.update_stage_progress(TaskStage.REQUIREMENT_PARSING, 50)
    print(f"Task progress: {task.get_overall_progress()}%")
    print(task.to_dict())
