"""
Page State Domain Models

Defines state management models for page-level pipeline parallel execution.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class PageStatus(str, Enum):
    """页面处理状态"""
    PENDING = "pending"
    RESEARCHING = "researching"
    CONTENT_GENERATING = "content_generating"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class PageState:
    """
    单页处理状态

    用于跟踪页面在流水线并行执行中的状态。

    Attributes:
        page_no: 页码
        status: 页面状态
        research_result: 研究结果
        content_material: 内容素材
        error: 错误信息
        research_progress: 研究进度 (0-100)
        content_progress: 内容生成进度 (0-100)
        started_at: 开始时间
        completed_at: 完成时间
        metadata: 附加元数据
    """

    page_no: int
    status: PageStatus = PageStatus.PENDING
    research_result: Optional[Dict[str, Any]] = None
    content_material: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    research_progress: float = 0.0
    content_progress: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_research_progress(self, progress: float) -> None:
        """
        更新研究进度

        Args:
            progress: 进度值 (0-100)
        """
        self.research_progress = max(0, min(100, progress))
        if self.research_progress >= 100:
            # 研究完成，进入内容生成阶段
            if self.status == PageStatus.RESEARCHING:
                self.status = PageStatus.CONTENT_GENERATING

    def update_content_progress(self, progress: float) -> None:
        """
        更新内容生成进度

        Args:
            progress: 进度值 (0-100)
        """
        self.content_progress = max(0, min(100, progress))
        if self.content_progress >= 100:
            self.status = PageStatus.COMPLETED
            self.completed_at = datetime.now()

    def mark_researching(self) -> None:
        """标记为正在研究"""
        self.status = PageStatus.RESEARCHING
        if self.started_at is None:
            self.started_at = datetime.now()

    def mark_content_generating(self) -> None:
        """标记为正在生成内容"""
        self.status = PageStatus.CONTENT_GENERATING
        if self.started_at is None:
            self.started_at = datetime.now()

    def mark_completed(self) -> None:
        """标记为已完成"""
        self.status = PageStatus.COMPLETED
        self.research_progress = 100
        self.content_progress = 100
        self.completed_at = datetime.now()

    def mark_failed(self, error: str) -> None:
        """标记为失败"""
        self.status = PageStatus.FAILED
        self.error = error
        self.completed_at = datetime.now()

    def mark_skipped(self, reason: str = "") -> None:
        """标记为跳过"""
        self.status = PageStatus.SKIPPED
        self.metadata["skip_reason"] = reason
        self.completed_at = datetime.now()

    def get_overall_progress(self) -> float:
        """
        获取总体进度

        Returns:
            进度百分比 (0-100)
        """
        return (self.research_progress + self.content_progress) / 2

    def is_pending(self) -> bool:
        """是否待处理"""
        return self.status == PageStatus.PENDING

    def is_in_progress(self) -> bool:
        """是否正在处理"""
        return self.status in (PageStatus.RESEARCHING, PageStatus.CONTENT_GENERATING)

    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status == PageStatus.COMPLETED

    def is_failed(self) -> bool:
        """是否失败"""
        return self.status == PageStatus.FAILED

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "page_no": self.page_no,
            "status": self.status.value if isinstance(self.status, PageStatus) else self.status,
            "research_result": self.research_result,
            "content_material": self.content_material,
            "error": self.error,
            "research_progress": self.research_progress,
            "content_progress": self.content_progress,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "overall_progress": self.get_overall_progress(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PageState":
        """从字典创建实例"""
        status = data.get("status", "pending")
        if isinstance(status, str):
            status = PageStatus(status)

        started_at = data.get("started_at")
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)

        completed_at = data.get("completed_at")
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        return cls(
            page_no=data["page_no"],
            status=status,
            research_result=data.get("research_result"),
            content_material=data.get("content_material"),
            error=data.get("error"),
            research_progress=data.get("research_progress", 0.0),
            content_progress=data.get("content_progress", 0.0),
            started_at=started_at,
            completed_at=completed_at,
            metadata=data.get("metadata", {})
        )

class PageStateManager:
    """
    页面状态管理器

    管理多个页面的处理状态，计算总体进度。
    """

    def __init__(self, total_pages: int):
        """
        初始化页面状态管理器

        Args:
            total_pages: 总页数
        """
        self.total_pages = total_pages
        self.page_states: Dict[int, PageState] = {
            i: PageState(page_no=i, status=PageStatus.PENDING)
            for i in range(1, total_pages + 1)
        }
        self.created_at = datetime.now()

    def get_state(self, page_no: int) -> Optional[PageState]:
        """
        获取页面状态

        Args:
            page_no: 页码

        Returns:
            PageState对象，如果页码不存在则返回None
        """
        return self.page_states.get(page_no)

    def set_state(self, page_no: int, state: PageState) -> None:
        """
        设置页面状态

        Args:
            page_no: 页码
            state: PageState对象
        """
        self.page_states[page_no] = state

    def get_all_states(self) -> List[PageState]:
        """获取所有页面状态"""
        return list(self.page_states.values())

    def get_pending_pages(self) -> List[PageState]:
        """获取待处理的页面"""
        return [s for s in self.page_states.values() if s.is_pending()]

    def get_in_progress_pages(self) -> List[PageState]:
        """获取正在处理的页面"""
        return [s for s in self.page_states.values() if s.is_in_progress()]

    def get_completed_pages(self) -> List[PageState]:
        """获取已完成的页面"""
        return [s for s in self.page_states.values() if s.is_completed()]

    def get_failed_pages(self) -> List[PageState]:
        """获取失败的页面"""
        return [s for s in self.page_states.values() if s.is_failed()]

    def get_overall_progress(self) -> float:
        """
        计算总体进度

        Returns:
            总体进度百分比 (0-100)
        """
        if not self.page_states:
            return 0.0

        total_progress = sum(
            state.get_overall_progress()
            for state in self.page_states.values()
        )
        return total_progress / self.total_pages

    def get_status_summary(self) -> Dict[str, int]:
        """
        获取状态摘要

        Returns:
            各状态的数量统计
        """
        summary = {status.value: 0 for status in PageStatus}

        for state in self.page_states.values():
            summary[state.status.value] += 1

        return summary

    def get_completion_percentage(self) -> float:
        """
        获取完成百分比

        Returns:
            完成的页面百分比 (0-100)
        """
        completed = len(self.get_completed_pages())
        return (completed / self.total_pages) * 100 if self.total_pages > 0 else 0

    def has_failures(self) -> bool:
        """是否有失败"""
        return len(self.get_failed_pages()) > 0

    def is_all_completed(self) -> bool:
        """是否全部完成"""
        return len(self.get_completed_pages()) == self.total_pages

    def get_elapsed_time(self) -> float:
        """
        获取已用时间（秒）

        Returns:
            从创建到现在的秒数
        """
        return (datetime.now() - self.created_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_pages": self.total_pages,
            "overall_progress": self.get_overall_progress(),
            "completion_percentage": self.get_completion_percentage(),
            "status_summary": self.get_status_summary(),
            "elapsed_time": self.get_elapsed_time(),
            "pages": [s.to_dict() for s in self.page_states.values()]
        }

@dataclass
class PagePipelineConfig:
    """
    页面流水线配置

    Attributes:
        max_concurrency: 最大并发数
        enable_research: 是否启用研究阶段
        enable_content_generation: 是否启用内容生成
        timeout_per_page: 每页超时时间（秒）
        retry_limit: 重试次数
    """

    max_concurrency: int = 3
    enable_research: bool = True
    enable_content_generation: bool = True
    timeout_per_page: int = 300
    retry_limit: int = 2

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "max_concurrency": self.max_concurrency,
            "enable_research": self.enable_research,
            "enable_content_generation": self.enable_content_generation,
            "timeout_per_page": self.timeout_per_page,
            "retry_limit": self.retry_limit
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PagePipelineConfig":
        """从字典创建实例"""
        return cls(
            max_concurrency=data.get("max_concurrency", 3),
            enable_research=data.get("enable_research", True),
            enable_content_generation=data.get("enable_content_generation", True),
            timeout_per_page=data.get("timeout_per_page", 300),
            retry_limit=data.get("retry_limit", 2)
        )

@dataclass
class PagePipelineResult:
    """
    页面流水线执行结果

    Attributes:
        success: 是否成功
        total_pages: 总页数
        completed_pages: 完成的页数
        failed_pages: 失败的页数
        skipped_pages: 跳过的页数
        total_time: 总耗时（秒）
        page_states: 所有页面状态
        errors: 错误列表
    """

    success: bool
    total_pages: int
    completed_pages: int
    failed_pages: int
    skipped_pages: int
    total_time: float
    page_states: List[PageState]
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "total_pages": self.total_pages,
            "completed_pages": self.completed_pages,
            "failed_pages": self.failed_pages,
            "skipped_pages": self.skipped_pages,
            "completion_rate": (self.completed_pages / self.total_pages * 100) if self.total_pages > 0 else 0,
            "total_time": self.total_time,
            "avg_time_per_page": (self.total_time / self.total_pages) if self.total_pages > 0 else 0,
            "errors": self.errors,
            "page_states": [s.to_dict() for s in self.page_states]
        }

    @classmethod
    def from_manager(cls, manager: PageStateManager, total_time: float, errors: List[str] = None) -> "PagePipelineResult":
        """从PageStateManager创建结果"""
        completed = len(manager.get_completed_pages())
        failed = len(manager.get_failed_pages())
        skipped = len([s for s in manager.page_states.values() if s.status == PageStatus.SKIPPED])

        return cls(
            success=failed == 0,
            total_pages=manager.total_pages,
            completed_pages=completed,
            failed_pages=failed,
            skipped_pages=skipped,
            total_time=total_time,
            page_states=manager.get_all_states(),
            errors=errors or []
        )

if __name__ == "__main__":
    # 测试代码
    print("Testing PageState and PageStateManager")
    print("=" * 60)

    # 创建页面状态管理器
    manager = PageStateManager(total_pages=10)

    # 模拟页面处理
    print("\n1. Simulating page processing...")

    # 页面1-3: 正在研究
    for i in range(1, 4):
        state = manager.get_state(i)
        state.mark_researching()
        state.update_research_progress(50)
        manager.set_state(i, state)

    # 页面4-6: 正在生成内容
    for i in range(4, 7):
        state = manager.get_state(i)
        state.mark_researching()
        state.update_research_progress(100)
        state.mark_content_generating()
        state.update_content_progress(50)
        manager.set_state(i, state)

    # 页面7-9: 已完成
    for i in range(7, 10):
        state = manager.get_state(i)
        state.mark_completed()
        manager.set_state(i, state)

    # 页面10: 失败
    state = manager.get_state(10)
    state.mark_failed("网络错误")
    manager.set_state(10, state)

    # 获取统计
    print(f"\n2. Progress statistics:")
    print(f"   Overall progress: {manager.get_overall_progress():.1f}%")
    print(f"   Completion percentage: {manager.get_completion_percentage():.1f}%")
    print(f"   Status summary: {manager.get_status_summary()}")

    # 获取各状态页面
    print(f"\n3. Page counts by status:")
    print(f"   Pending: {len(manager.get_pending_pages())}")
    print(f"   In progress: {len(manager.get_in_progress_pages())}")
    print(f"   Completed: {len(manager.get_completed_pages())}")
    print(f"   Failed: {len(manager.get_failed_pages())}")

    # 创建流水线结果
    print(f"\n4. Pipeline result:")
    result = PagePipelineResult.from_manager(manager, total_time=45.5)
    print(f"   Success: {result.success}")
    print(f"   Completion rate: {result.to_dict()['completion_rate']:.1f}%")
    print(f"   Avg time per page: {result.to_dict()['avg_time_per_page']:.2f}s")

    # 测试配置
    print(f"\n5. Pipeline config:")
    config = PagePipelineConfig(max_concurrency=5, timeout_per_page=600)
    print(f"   {config.to_dict()}")
