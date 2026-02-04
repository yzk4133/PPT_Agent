"""
Stage Transition Service

Provides logic for managing stage transitions in tasks.
"""

from datetime import datetime
from typing import Optional
from domain.events.task_events import create_stage_started_event, create_stage_completed_event, create_stage_failed_event
from domain.services.task_validation_service import task_validation_service

class StageTransitionService:
    """
    Service for managing stage transitions

    Handles starting, completing, and failing stages with validation
    and event emission.
    """

    def __init__(self):
        """Initialize stage transition service"""
        self.validation_service = task_validation_service

    def start_stage(self, task, stage_name: str) -> None:
        """
        Start a stage with validation

        Args:
            task: Task entity
            stage_name: Name of the stage to start
        """
        from domain.models.task import TaskStatus

        stage = task.stages.get(stage_name)
        if stage:
            stage.status = TaskStatus.PARSING_REQUIREMENTS if stage_name == "requirement_parsing" else TaskStatus.DESIGNING_FRAMEWORK if stage_name == "framework_design" else TaskStatus.RESEARCHING if stage_name == "research" else TaskStatus.GENERATING_CONTENT if stage_name == "content_generation" else TaskStatus.RENDERING
            stage.started_at = datetime.now()
            stage.progress = 0

    def complete_stage(self, task, stage_name: str) -> None:
        """
        Complete a stage with validation

        Args:
            task: Task entity
            stage_name: Name of the stage to complete
        """
        from domain.models.task import TaskStatus

        stage = task.stages.get(stage_name)
        if stage:
            stage.status = TaskStatus.COMPLETED
            stage.completed_at = datetime.now()
            stage.progress = 100

            # Update task overall status based on completed stage
            if stage_name == "requirement_parsing":
                task.status = TaskStatus.DESIGNING_FRAMEWORK
            elif stage_name == "framework_design":
                task.status = TaskStatus.RESEARCHING
            elif stage_name == "research":
                task.status = TaskStatus.GENERATING_CONTENT
            elif stage_name == "content_generation":
                task.status = TaskStatus.RENDERING

    def fail_stage(self, task, stage_name: str, error: str) -> None:
        """
        Fail a stage with error information

        Args:
            task: Task entity
            stage_name: Name of the stage that failed
            error: Error message
        """
        from domain.models.task import TaskStatus

        stage = task.stages.get(stage_name)
        if stage:
            stage.status = TaskStatus.FAILED
            stage.error = error
            stage.completed_at = datetime.now()

        task.status = TaskStatus.FAILED
        task.error = error

    def increment_retry(self, task, stage_name: str) -> None:
        """
        Increment retry count for a stage

        Args:
            task: Task entity
            stage_name: Name of the stage
        """
        stage = task.stages.get(stage_name)
        if stage:
            stage.retry_count += 1

    def update_stage_progress(self, task, stage_name: str, progress: int) -> None:
        """
        Update progress for a stage

        Args:
            task: Task entity
            stage_name: Name of the stage
            progress: Progress percentage (0-100)
        """
        stage = task.stages.get(stage_name)
        if stage:
            stage.progress = max(0, min(100, progress))

# Singleton instance
stage_transition_service = StageTransitionService()
