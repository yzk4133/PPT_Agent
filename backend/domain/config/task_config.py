"""
Domain Configuration for Task

Provides configuration for task progress weights and task behavior.
"""

from dataclasses import dataclass, field

@dataclass
class TaskProgressWeights:
    """
    Progress weights for task stages

    Defines how much each stage contributes to the overall task progress.
    """

    REQUIREMENT_PARSING: int = 15
    FRAMEWORK_DESIGN: int = 30
    RESEARCH: int = 50
    CONTENT_GENERATION: int = 80
    TEMPLATE_RENDERING: int = 100

    def get_weight(self, stage_name: str) -> int:
        """
        Get progress weight for a stage

        Args:
            stage_name: Name of the stage

        Returns:
            Progress weight (0-100)
        """
        stage_map = {
            "requirement_parsing": self.REQUIREMENT_PARSING,
            "framework_design": self.FRAMEWORK_DESIGN,
            "research": self.RESEARCH,
            "content_generation": self.CONTENT_GENERATION,
            "template_rendering": self.TEMPLATE_RENDERING,
        }
        return stage_map.get(stage_name.lower(), 0)

@dataclass
class TaskConfig:
    """
    Task domain configuration

    Provides configuration for task behavior including progress weights,
    retry limits, and timeouts.
    """

    progress_weights: TaskProgressWeights = field(default_factory=TaskProgressWeights)
    max_retries: int = 3
    default_timeout: int = 300
    checkpoint_interval: int = 60  # seconds
    enable_checkpointing: bool = True

    def get_stage_weight(self, stage: str) -> int:
        """
        Get progress weight for a stage

        Args:
            stage: Stage name

        Returns:
            Progress weight
        """
        return self.progress_weights.get_weight(stage)

# Default singleton instance
default_task_config = TaskConfig()
