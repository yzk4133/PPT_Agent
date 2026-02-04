"""
Task Progress Service

Provides progress calculation logic for tasks.
"""

from typing import Dict, Any
from domain.config.task_config import TaskProgressWeights

class TaskProgressService:
    """
    Service for calculating task progress

    Extracts progress calculation logic from Task entity.
    """

    def __init__(self, weights: TaskProgressWeights = None):
        """
        Initialize task progress service

        Args:
            weights: Progress weights configuration (optional)
        """
        self.weights = weights or TaskProgressWeights()

    def calculate_overall_progress(self, stages: Dict[str, Any]) -> int:
        """
        Calculate overall task progress based on stage progress

        Args:
            stages: Dictionary of stage names to StageProgress objects

        Returns:
            Overall progress percentage (0-100)
        """
        if not stages:
            return 0

        total_progress = 0
        stage_count = len(stages)

        for stage_name, stage_progress in stages.items():
            # Get progress weight for this stage
            weight = self.weights.get_weight(stage_name)

            # Get current progress for this stage
            current_progress = getattr(stage_progress, 'progress', 0)

            # Calculate weighted contribution
            total_progress += (current_progress * weight) // 100

        # Normalize to 0-100
        return min(100, max(0, total_progress // max(1, stage_count)))

    def calculate_stage_progress(
        self,
        stage_name: str,
        completed_items: int,
        total_items: int
    ) -> int:
        """
        Calculate progress for a single stage

        Args:
            stage_name: Name of the stage
            completed_items: Number of completed items
            total_items: Total number of items

        Returns:
            Progress percentage (0-100)
        """
        if total_items == 0:
            return 0

        return (completed_items * 100) // total_items

    def is_stage_complete(self, stage_progress: Any) -> bool:
        """
        Check if a stage is complete

        Args:
            stage_progress: StageProgress object

        Returns:
            True if stage is complete (progress >= 100)
        """
        progress = getattr(stage_progress, 'progress', 0)
        return progress >= 100

    def get_incomplete_stages(self, stages: Dict[str, Any]) -> list:
        """
        Get list of incomplete stages

        Args:
            stages: Dictionary of stage names to StageProgress objects

        Returns:
            List of stage names that are not complete
        """
        incomplete = []

        for stage_name, stage_progress in stages.items():
            if not self.is_stage_complete(stage_progress):
                incomplete.append(stage_name)

        return incomplete

# Singleton instance with default weights
task_progress_service = TaskProgressService()
