"""
Checkpoint Model

Defines the checkpoint data structure for saving and resuming
PPT generation workflow at intermediate stages.
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator, model_validator

from .execution_mode import ExecutionMode


class Checkpoint(BaseModel):
    """
    Execution Checkpoint

    Used for saving intermediate states during PPT generation,
    supporting two-phase execution:
    1. Save checkpoint after phase 1 completion (outline generation complete)
    2. User updates checkpoint after editing outline
    3. Phase 2 resumes from checkpoint to continue PPT generation

    Attributes:
        task_id: Unique task identifier
        user_id: User ID
        execution_mode: Execution mode
        phase: Current phase (1-5)
        raw_user_input: Original user input
        structured_requirements: Structured requirements
        ppt_framework: PPT framework (outline)
        created_at: Creation timestamp
        updated_at: Last update timestamp
        status: Status (editing, completed, expired, deleted)
        version: Version number (supports outline modification)
        parent_task_id: Parent task ID (for traceability)
        metadata: Additional metadata
    """

    task_id: str = Field(min_length=1, description="Unique task identifier")
    user_id: str = Field(min_length=1, description="User ID")
    execution_mode: ExecutionMode = Field(description="Execution mode")
    phase: int = Field(ge=1, le=5, description="Current phase (1-5)")
    raw_user_input: str = Field(min_length=1, description="Original user input")
    structured_requirements: Dict[str, Any] = Field(default_factory=dict, description="Structured requirements")
    ppt_framework: Dict[str, Any] = Field(default_factory=dict, description="PPT framework (outline)")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    status: str = Field(default="editing", description="Status (editing, completed, expired, deleted)")
    version: int = Field(default=1, ge=1, description="Version number")
    parent_task_id: Optional[str] = Field(default=None, description="Parent task ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """验证状态值"""
        valid_statuses = ["editing", "completed", "expired", "deleted"]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}. Must be one of {valid_statuses}")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for JSON serialization)"""
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
        """Ensure data is JSON serializable"""
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
        """Create instance from dictionary"""
        # Handle execution_mode
        execution_mode = data.get("execution_mode", "full")
        if isinstance(execution_mode, str):
            execution_mode = ExecutionMode(execution_mode)

        # Handle dates
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
        Update PPT framework (after user modifies outline)

        Args:
            new_framework: New PPT framework
        """
        self.ppt_framework = new_framework
        self.updated_at = datetime.now()
        self.version += 1
        self.metadata["framework_updated_at"] = self.updated_at.isoformat()

    def mark_completed(self) -> None:
        """Mark checkpoint as completed"""
        self.status = "completed"
        self.updated_at = datetime.now()
        self.metadata["completed_at"] = self.updated_at.isoformat()

    def mark_expired(self, ttl_hours: int = 24) -> bool:
        """
        Mark checkpoint as expired (if past TTL)

        Args:
            ttl_hours: Time to live in hours

        Returns:
            Whether checkpoint was marked as expired
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
        """Check if checkpoint is editable"""
        return self.status == "editing"

    def is_expired(self, ttl_hours: int = 24) -> bool:
        """Check if checkpoint is expired"""
        age_hours = (datetime.now() - self.created_at).total_seconds() / 3600
        return age_hours > ttl_hours and self.status != "completed"

    def get_summary(self) -> Dict[str, Any]:
        """Get checkpoint summary"""
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
        Create checkpoint from phase 1 completion state

        Args:
            task_id: Task ID
            user_id: User ID
            raw_input: Original input
            requirements: Structured requirements
            framework: PPT framework

        Returns:
            Checkpoint instance
        """
        return cls(
            task_id=task_id,
            user_id=user_id,
            execution_mode=ExecutionMode.PHASE_1,
            phase=2,  # Phase 2 completed
            raw_user_input=raw_input,
            structured_requirements=requirements,
            ppt_framework=framework,
            status="editing"
        )


class CheckpointSummary(BaseModel):
    """
    Checkpoint Summary

    Lightweight checkpoint information for list display
    """

    task_id: str = Field(min_length=1, description="Unique task identifier")
    user_id: str = Field(min_length=1, description="User ID")
    phase: int = Field(ge=1, le=5, description="Current phase")
    status: str = Field(description="Status")
    version: int = Field(ge=1, description="Version number")
    total_pages: int = Field(ge=0, description="Total pages in framework")
    ppt_topic: str = Field(description="PPT topic/title")
    created_at: str = Field(description="Creation timestamp (ISO format)")
    updated_at: str = Field(description="Update timestamp (ISO format)")
    age_hours: float = Field(ge=0, description="Age in hours")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """验证状态值"""
        valid_statuses = ["editing", "completed", "expired", "deleted"]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}. Must be one of {valid_statuses}")
        return v

    @classmethod
    def from_checkpoint(cls, checkpoint: Checkpoint) -> "CheckpointSummary":
        """Create summary from Checkpoint"""
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
    # Test code
    print("Testing Checkpoint")
    print("=" * 60)

    # Create test data
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

    # Create checkpoint
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

    # Test serialization
    print("\n" + "=" * 60)
    print("Testing serialization:")
    checkpoint_dict = checkpoint.to_dict()
    print(json.dumps(checkpoint_dict, indent=2, ensure_ascii=False)[:500] + "...")

    # Test deserialization
    print("\n" + "=" * 60)
    print("Testing deserialization:")
    restored = Checkpoint.from_dict(checkpoint_dict)
    print(f"Restored task_id: {restored.task_id}")
    print(f"Restored phase: {restored.phase}")

    # Test framework update
    print("\n" + "=" * 60)
    print("Testing framework update:")
    old_version = checkpoint.version
    checkpoint.update_framework(framework)
    print(f"Old version: {old_version}, New version: {checkpoint.version}")
    print(f"Updated at: {checkpoint.updated_at}")

    # Test summary
    print("\n" + "=" * 60)
    print("Testing summary:")
    summary = checkpoint.get_summary()
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    # Test CheckpointSummary
    print("\n" + "=" * 60)
    print("Testing CheckpointSummary:")
    summary_obj = CheckpointSummary.from_checkpoint(checkpoint)
    print(f"Topic: {summary_obj.ppt_topic}")
    print(f"Total pages: {summary_obj.total_pages}")
    print(f"Age: {summary_obj.age_hours:.2f} hours")
