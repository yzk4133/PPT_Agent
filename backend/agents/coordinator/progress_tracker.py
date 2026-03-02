"""
LangGraph 协调器的进度跟踪器

为 PPT 生成提供实时进度跟踪和回调。
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from ..models.state import PPTGenerationState

logger = logging.getLogger(__name__)


class ProgressUpdate(BaseModel):
    """
    进度更新数据结构

    属性：
        stage: 当前阶段名称
        progress: 进度百分比 (0-100)
        message: 进度消息
        timestamp: 更新时间戳
        metadata: 额外元数据
    """

    stage: str = Field(description="当前阶段名称")
    progress: int = Field(ge=0, le=100, description="进度百分比 (0-100)")
    message: str = Field(description="进度消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="更新时间戳")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "stage": self.stage,
            "progress": self.progress,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProgressUpdate":
        """从字典创建实例（向后兼容）"""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            stage=data.get("stage", ""),
            progress=data.get("progress", 0),
            message=data.get("message", ""),
            timestamp=timestamp or datetime.now(),
            metadata=data.get("metadata", {})
        )


class ProgressTracker:
    """
    PPT 生成工作流的进度跟踪器

    通过阶段跟踪进度，并为实时更新提供回调。
    """

    # Stage definitions
    STAGE_INIT = "init"
    STAGE_REQUIREMENT_PARSING = "requirement_parsing"
    STAGE_FRAMEWORK_DESIGN = "framework_design"
    STAGE_RESEARCH = "research"
    STAGE_CONTENT_GENERATION = "content_generation"
    STAGE_QUALITY_CHECK = "quality_check"
    STAGE_REFINEMENT = "refinement"
    STAGE_TEMPLATE_RENDERING = "template_rendering"
    STAGE_COMPLETE = "complete"

    def __init__(
        self,
        task_id: str,
        on_progress: Optional[Callable[[ProgressUpdate], None]] = None,
        on_stage_complete: Optional[Callable[[str, PPTGenerationState], None]] = None,
        on_error: Optional[Callable[[str, Exception], None]] = None,
    ):
        """
        初始化进度跟踪器

        参数：
            task_id: 任务标识符
            on_progress: 进度回调 (progress_update)
            on_stage_complete: 阶段完成回调 (stage_name, state)
            on_error: 错误回调 (stage_name, error)
        """
        self.task_id = task_id
        self.on_progress = on_progress
        self.on_stage_complete = on_stage_complete
        self.on_error = on_error

        # Progress tracking
        self._current_stage = self.STAGE_INIT
        self._current_progress = 0
        self._start_time = datetime.now()
        self._stage_start_times: Dict[str, datetime] = {}

        # History
        self._progress_history: List[ProgressUpdate] = []

        logger.debug(f"[ProgressTracker] Initialized for task {task_id}")

    def update_stage(
        self,
        stage: str,
        progress: int,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        更新进度并触发回调

        参数：
            stage: 当前阶段名称
            progress: 进度百分比 (0-100)
            message: 进度消息
            metadata: 可选元数据
        """
        # Clamp progress
        progress = max(0, min(100, progress))

        # Track stage timing
        if stage != self._current_stage:
            if self._current_stage in self._stage_start_times:
                elapsed = datetime.now() - self._stage_start_times[self._current_stage]
                logger.debug(
                    f"[ProgressTracker] Stage '{self._current_stage}' completed in {elapsed.total_seconds():.2f}s"
                )

            self._stage_start_times[stage] = datetime.now()
            self._current_stage = stage

        self._current_progress = progress

        # Create update
        update = ProgressUpdate(
            stage=stage,
            progress=progress,
            message=message or f"Processing {stage}",
            timestamp=datetime.now(),
            metadata=metadata or {},
        )

        self._progress_history.append(update)

        # Trigger callback
        if self.on_progress:
            try:
                self.on_progress(update)
            except Exception as e:
                logger.error(f"[ProgressTracker] Progress callback error: {e}")

        logger.debug(f"[ProgressTracker] [{self.task_id}] {stage}: {progress}% - {message}")

    def stage_complete(
        self,
        stage: str,
        state: PPTGenerationState,
    ):
        """
        标记阶段为完成并触发回调

        参数：
            stage: 阶段名称
            state: 当前状态
        """
        update = ProgressUpdate(
            stage=stage,
            progress=100,
            message=f"{stage} completed",
            timestamp=datetime.now(),
            metadata={"stage_complete": True},
        )

        self._progress_history.append(update)

        # Trigger callback
        if self.on_stage_complete:
            try:
                self.on_stage_complete(stage, state)
            except Exception as e:
                logger.error(f"[ProgressTracker] Stage complete callback error: {e}")

        logger.info(f"[ProgressTracker] [{self.task_id}] Stage '{stage}' complete")

    def error(
        self,
        stage: str,
        error: Exception,
    ):
        """
        处理错误并触发回调

        参数：
            stage: 发生错误的阶段
            error: 异常
        """
        update = ProgressUpdate(
            stage=stage,
            progress=self._current_progress,
            message=f"Error in {stage}: {str(error)}",
            timestamp=datetime.now(),
            metadata={"error": True, "error_type": type(error).__name__},
        )

        self._progress_history.append(update)

        # Trigger callback
        if self.on_error:
            try:
                self.on_error(stage, error)
            except Exception as e:
                logger.error(f"[ProgressTracker] Error callback error: {e}")

        logger.error(f"[ProgressTracker] [{self.task_id}] Error in {stage}: {error}")

    def get_elapsed_time(self) -> float:
        """获取经过的时间（秒）"""
        return (datetime.now() - self._start_time).total_seconds()

    def get_stage_elapsed_time(self, stage: str) -> Optional[float]:
        """获取特定阶段的经过时间"""
        if stage in self._stage_start_times:
            return (datetime.now() - self._stage_start_times[stage]).total_seconds()
        return None

    def get_history(self) -> List[Dict[str, Any]]:
        """获取进度历史"""
        return [update.to_dict() for update in self._progress_history]

    def get_summary(self) -> Dict[str, Any]:
        """获取进度摘要"""
        return {
            "task_id": self.task_id,
            "current_stage": self._current_stage,
            "current_progress": self._current_progress,
            "elapsed_time_seconds": self.get_elapsed_time(),
            "total_updates": len(self._progress_history),
        }


class StageProgressMapper:
    """
    将 LangGraph 阶段映射到进度百分比

    为标准工作流提供预定义的进度映射。
    """

    # Default stage weights (sums to 100)
    DEFAULT_STAGE_WEIGHTS = {
        "requirement_parser": 10,
        "framework_designer": 20,
        "research": 30,
        "content_generation": 25,
        "quality_check": 10,
        "template_renderer": 5,
    }

    @classmethod
    def get_progress_for_stage(
        cls,
        stage: str,
        stage_weights: Optional[Dict[str, int]] = None,
    ) -> int:
        """
        获取阶段的进度百分比

        参数：
            stage: 阶段名称
            stage_weights: 可选的自定义阶段权重

        返回：
            进度百分比
        """
        weights = stage_weights or cls.DEFAULT_STAGE_WEIGHTS

        # Calculate cumulative progress before this stage
        progress = 0
        for s, w in weights.items():
            if s == stage:
                # Return progress at start of this stage
                return progress
            progress += w

        return progress

    @classmethod
    def get_stage_progress_range(
        cls,
        stage: str,
        stage_weights: Optional[Dict[str, int]] = None,
    ) -> tuple[int, int]:
        """
        获取阶段的进度范围 (开始, 结束)

        参数：
            stage: 阶段名称
            stage_weights: 可选的自定义阶段权重

        返回：
            (start_progress, end_progress) 元组
        """
        weights = stage_weights or cls.DEFAULT_STAGE_WEIGHTS

        start = 0
        found = False

        for s, w in weights.items():
            if found:
                return (start, start + w)
            if s == stage:
                found = True
                start += w

        if found:
            return (start, 100)

        return (0, 0)


def create_progress_tracker(
    state: PPTGenerationState,
    on_progress: Optional[Callable[[ProgressUpdate], None]] = None,
    on_stage_complete: Optional[Callable[[str, PPTGenerationState], None]] = None,
    on_error: Optional[Callable[[str, Exception], None]] = None,
) -> ProgressTracker:
    """
    从状态创建进度跟踪器的工厂函数

    参数：
        state: LangChain 状态
        on_progress: 进度回调
        on_stage_complete: 阶段完成回调
        on_error: 错误回调

    返回：
        ProgressTracker 实例
    """
    task_id = state.get("task_id", "unknown")

    return ProgressTracker(
        task_id=task_id,
        on_progress=on_progress,
        on_stage_complete=on_stage_complete,
        on_error=on_error,
    )
