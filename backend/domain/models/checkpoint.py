"""
Checkpoint Domain Model

Defines the checkpoint data structure for saving and resuming
PPT generation workflow at intermediate stages.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List

from .execution_mode import ExecutionMode


@dataclass
class Checkpoint:
    """
    执行检查点

    用于保存PPT生成过程中的中间状态，支持两阶段执行：
    1. 阶段1完成后保存checkpoint（大纲生成完成）
    2. 用户编辑大纲后更新checkpoint
    3. 阶段2从checkpoint恢复继续生成PPT

    Attributes:
        task_id: 任务唯一标识符
        user_id: 用户ID
        execution_mode: 执行模式
        phase: 当前阶段（1-5）
        raw_user_input: 原始用户输入
        structured_requirements: 结构化需求
        ppt_framework: PPT框架（大纲）
        created_at: 创建时间
        updated_at: 更新时间
        status: 状态 (editing, completed, expired, deleted)
        version: 版本号（支持大纲修改）
        parent_task_id: 父任务ID（用于追溯）
        metadata: 附加元数据
    """

    task_id: str
    user_id: str
    execution_mode: ExecutionMode
    phase: int
    raw_user_input: str
    structured_requirements: Dict[str, Any]
    ppt_framework: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: str = "editing"  # editing, completed, expired, deleted
    version: int = 1
    parent_task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于JSON序列化）"""
        return {
            "task_id": self.task_id,
            "user_id": self.user_id,
            "execution_mode": self.execution_mode.value if isinstance(self.execution_mode, ExecutionMode) else self.execution_mode,
            "phase": self.phase,
            "raw_user_input": self.raw_user_input,
            "structured_requirements": self._serialize_jsonable(self.structured_requirements),
            "ppt_framework": self._serialize_jsonable(self.ppt_framework),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status,
            "version": self.version,
            "parent_task_id": self.parent_task_id,
            "metadata": self._serialize_jsonable(self.metadata)
        }

    def _serialize_jsonable(self, data: Any) -> Any:
        """确保数据可JSON序列化"""
        if isinstance(data, dict):
            return {k: self._serialize_jsonable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_jsonable(item) for item in data]
        elif hasattr(data, 'to_dict'):
            return data.to_dict()
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        else:
            return str(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        """从字典创建实例"""
        # 处理execution_mode
        execution_mode = data.get("execution_mode", "full")
        if isinstance(execution_mode, str):
            execution_mode = ExecutionMode(execution_mode)

        # 处理日期
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif updated_at is None:
            updated_at = datetime.now()

        return cls(
            task_id=data["task_id"],
            user_id=data["user_id"],
            execution_mode=execution_mode,
            phase=data["phase"],
            raw_user_input=data["raw_user_input"],
            structured_requirements=data.get("structured_requirements", {}),
            ppt_framework=data.get("ppt_framework", {}),
            created_at=created_at,
            updated_at=updated_at,
            status=data.get("status", "editing"),
            version=data.get("version", 1),
            parent_task_id=data.get("parent_task_id"),
            metadata=data.get("metadata", {})
        )

    def update_framework(self, new_framework: Dict[str, Any]) -> None:
        """
        更新PPT框架（用户修改大纲后）

        Args:
            new_framework: 新的PPT框架
        """
        self.ppt_framework = new_framework
        self.updated_at = datetime.now()
        self.version += 1
        self.metadata["framework_updated_at"] = self.updated_at.isoformat()

    def mark_completed(self) -> None:
        """标记checkpoint为已完成"""
        self.status = "completed"
        self.updated_at = datetime.now()
        self.metadata["completed_at"] = self.updated_at.isoformat()

    def mark_expired(self, ttl_hours: int = 24) -> bool:
        """
        标记checkpoint为过期（如果超过TTL）

        Args:
            ttl_hours: 生存时间（小时）

        Returns:
            是否被标记为过期
        """
        if self.status == "completed":
            return False

        age_hours = (datetime.now() - self.created_at).total_seconds() / 3600
        if age_hours > ttl_hours:
            self.status = "expired"
            self.updated_at = datetime.now()
            return True
        return False

    def is_editable(self) -> bool:
        """是否可编辑"""
        return self.status == "editing"

    def is_expired(self, ttl_hours: int = 24) -> bool:
        """是否已过期"""
        age_hours = (datetime.now() - self.created_at).total_seconds() / 3600
        return age_hours > ttl_hours and self.status != "completed"

    def get_summary(self) -> Dict[str, Any]:
        """获取checkpoint摘要信息"""
        framework = self.ppt_framework or {}
        pages = framework.get("ppt_framework", [])

        return {
            "task_id": self.task_id,
            "user_id": self.user_id,
            "phase": self.phase,
            "status": self.status,
            "version": self.version,
            "total_pages": framework.get("total_page", len(pages)),
            "has_research_pages": framework.get("has_research_pages", False),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "age_hours": (datetime.now() - self.created_at).total_seconds() / 3600
        }

    @classmethod
    def create_from_phase_1(
        cls,
        task_id: str,
        user_id: str,
        raw_input: str,
        requirements: Dict[str, Any],
        framework: Dict[str, Any]
    ) -> "Checkpoint":
        """
        从阶段1完成后的状态创建checkpoint

        Args:
            task_id: 任务ID
            user_id: 用户ID
            raw_input: 原始输入
            requirements: 结构化需求
            framework: PPT框架

        Returns:
            Checkpoint实例
        """
        return cls(
            task_id=task_id,
            user_id=user_id,
            execution_mode=ExecutionMode.PHASE_1,
            phase=2,  # 已完成阶段2
            raw_user_input=raw_input,
            structured_requirements=requirements,
            ppt_framework=framework,
            status="editing"
        )


@dataclass
class CheckpointSummary:
    """
    Checkpoint摘要

    用于列表展示的轻量级checkpoint信息
    """

    task_id: str
    user_id: str
    phase: int
    status: str
    version: int
    total_pages: int
    ppt_topic: str
    created_at: str
    updated_at: str
    age_hours: float

    @classmethod
    def from_checkpoint(cls, checkpoint: Checkpoint) -> "CheckpointSummary":
        """从Checkpoint创建摘要"""
        framework = checkpoint.ppt_framework or {}
        requirements = checkpoint.structured_requirements or {}

        return cls(
            task_id=checkpoint.task_id,
            user_id=checkpoint.user_id,
            phase=checkpoint.phase,
            status=checkpoint.status,
            version=checkpoint.version,
            total_pages=framework.get("total_page", 0),
            ppt_topic=requirements.get("ppt_topic", "未命名"),
            created_at=checkpoint.created_at.isoformat(),
            updated_at=checkpoint.updated_at.isoformat(),
            age_hours=(datetime.now() - checkpoint.created_at).total_seconds() / 3600
        )


if __name__ == "__main__":
    # 测试代码
    print("Testing Checkpoint")
    print("=" * 60)

    # 创建测试数据
    task_id = "task_20240203_143022_abc123"
    user_id = "user_001"
    raw_input = "做一份AI技术介绍PPT，15页"

    requirements = {
        "ppt_topic": "AI技术介绍",
        "scene": "business_report",
        "page_num": 15,
        "template_type": "business_template",
        "need_research": True
    }

    framework = {
        "total_page": 15,
        "ppt_framework": [
            {"page_no": 1, "title": "封面", "page_type": "cover"},
            {"page_no": 2, "title": "目录", "page_type": "directory"}
        ],
        "has_research_pages": True
    }

    # 创建checkpoint
    checkpoint = Checkpoint.create_from_phase_1(
        task_id=task_id,
        user_id=user_id,
        raw_input=raw_input,
        requirements=requirements,
        framework=framework
    )

    print(f"\nCreated checkpoint: {checkpoint.task_id}")
    print(f"Execution mode: {checkpoint.execution_mode.value}")
    print(f"Phase: {checkpoint.phase}")
    print(f"Status: {checkpoint.status}")
    print(f"Is editable: {checkpoint.is_editable()}")

    # 测试序列化
    print("\n" + "=" * 60)
    print("Testing serialization:")
    checkpoint_dict = checkpoint.to_dict()
    print(json.dumps(checkpoint_dict, indent=2, ensure_ascii=False)[:500] + "...")

    # 测试反序列化
    print("\n" + "=" * 60)
    print("Testing deserialization:")
    restored = Checkpoint.from_dict(checkpoint_dict)
    print(f"Restored task_id: {restored.task_id}")
    print(f"Restored phase: {restored.phase}")

    # 测试框架更新
    print("\n" + "=" * 60)
    print("Testing framework update:")
    old_version = checkpoint.version
    checkpoint.update_framework(framework)
    print(f"Old version: {old_version}, New version: {checkpoint.version}")
    print(f"Updated at: {checkpoint.updated_at}")

    # 测试摘要
    print("\n" + "=" * 60)
    print("Testing summary:")
    summary = checkpoint.get_summary()
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    # 测试CheckpointSummary
    print("\n" + "=" * 60)
    print("Testing CheckpointSummary:")
    summary_obj = CheckpointSummary.from_checkpoint(checkpoint)
    print(f"Topic: {summary_obj.ppt_topic}")
    print(f"Total pages: {summary_obj.total_pages}")
    print(f"Age: {summary_obj.age_hours:.2f} hours")
