"""
Task Validation Service

Provides validation logic for task and related domain models.
"""

from typing import List, Optional
from domain.exceptions import ValidationError, InvalidStateTransitionError


class TaskValidationService:
    """
    Service for validating domain models

    Handles validation for requirements, tasks, and state transitions.
    """

    def validate_requirement(self, requirement) -> None:
        """
        Validate requirement data

        Args:
            requirement: Requirement object to validate

        Raises:
            ValidationError: If validation fails
        """
        errors: List[str] = []

        # Validate topic
        if not requirement.ppt_topic or len(requirement.ppt_topic.strip()) == 0:
            errors.append("PPT主题不能为空")

        # Validate page number
        if requirement.page_num < 1:
            errors.append("页数必须大于0")
        elif requirement.page_num > 100:
            errors.append("页数不能超过100")

        # Validate scene
        if hasattr(requirement, 'scene') and requirement.scene:
            from domain.models.requirement import SceneType
            if requirement.scene not in SceneType:
                errors.append(f"无效的场景类型: {requirement.scene}")

        # Validate template type
        if hasattr(requirement, 'template_type') and requirement.template_type:
            from domain.models.requirement import TemplateType
            if requirement.template_type not in TemplateType:
                errors.append(f"无效的模板类型: {requirement.template_type}")

        # Check core modules
        if hasattr(requirement, 'core_modules') and requirement.core_modules:
            if len(requirement.core_modules) > requirement.page_num:
                errors.append("核心模块数量不能超过页数")

        if errors:
            raise ValidationError("Requirement validation failed", errors=errors)

    def validate_framework(self, framework) -> None:
        """
        Validate framework data

        Args:
            framework: Framework object to validate

        Raises:
            ValidationError: If validation fails
        """
        errors: List[str] = []

        if not framework.title or len(framework.title.strip()) == 0:
            errors.append("框架标题不能为空")

        if not framework.outline or len(framework.outline) == 0:
            errors.append("大纲不能为空")

        if framework.total_slides < 1:
            errors.append("幻灯片总数必须大于0")

        if errors:
            raise ValidationError("Framework validation failed", errors=errors)

    def validate_task_transition(self, current_status: str, new_status: str) -> None:
        """
        Validate state transition for a task

        Args:
            current_status: Current task status
            new_status: Target status

        Raises:
            InvalidStateTransitionError: If transition is invalid
        """
        # Define valid transitions
        valid_transitions = {
            "pending": ["parsing_requirements", "failed"],
            "parsing_requirements": ["designing_framework", "failed"],
            "designing_framework": ["researching", "failed"],
            "researching": ["generating_content", "failed"],
            "generating_content": ["rendering", "failed"],
            "rendering": ["completed", "failed"],
            "failed": ["parsing_requirements", "revision_pending"],
            "revision_pending": ["parsing_requirements"],
            "completed": [],  # Terminal state
        }

        allowed_next = valid_transitions.get(current_status, [])

        if new_status not in allowed_next:
            raise InvalidStateTransitionError(
                f"Invalid state transition from {current_status} to {new_status}",
                current_state=current_status,
                target_state=new_status
            )

    def validate_research_result(self, research_result) -> None:
        """
        Validate research result data

        Args:
            research_result: ResearchResult object to validate

        Raises:
            ValidationError: If validation fails
        """
        errors: List[str] = []

        if not research_result.topic or len(research_result.topic.strip()) == 0:
            errors.append("研究主题不能为空")

        if not research_result.content or len(research_result.content.strip()) == 0:
            errors.append("研究内容不能为空")

        if hasattr(research_result, 'confidence'):
            if not 0 <= research_result.confidence <= 1:
                errors.append("置信度必须在0-1之间")

        if errors:
            raise ValidationError("Research result validation failed", errors=errors)


# Singleton instance
task_validation_service = TaskValidationService()
