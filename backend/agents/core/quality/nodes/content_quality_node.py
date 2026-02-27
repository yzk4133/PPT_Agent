"""
内容质量检查节点 - LangGraph 集成

该模块为集成到 LangGraph 工作流提供质量检查节点。
"""

import logging
from typing import Any, Dict, List, Optional

from ....models.state import PPTGenerationState

# Import from existing quality system
try:
    from archive.agents_google_adk_20250208.core.quality.feedback_loop import (
        QualityAssessor,
        RuleBasedAssessor,
        QualityDimension,
        QualityAssessment,
    )
    _QUALITY_AVAILABLE = True
except ImportError:
    _QUALITY_AVAILABLE = False
    # Create placeholder types if not available
    QualityAssessor = None  # type: ignore
    RuleBasedAssessor = None  # type: ignore
    QualityDimension = None  # type: ignore
    QualityAssessment = None  # type: ignore
    logging.warning("Quality feedback loop module not available")

logger = logging.getLogger(__name__)


async def check_content_quality(
    state: PPTGenerationState,
    assessor: Optional[QualityAssessor] = None,
    threshold: float = 0.8,
    check_dimensions: Optional[List[QualityDimension]] = None,
) -> PPTGenerationState:
    """
    LangGraph 节点：检查内容质量

    评估生成内容素材的质量，并将评估结果存储在状态中用于条件路由。

    Args:
        state: 当前 LangChain 状态
        assessor: 可选的质量评估器（如果为 None 则创建默认评估器）
        threshold: 质量阈值 (0.0 - 1.0)
        check_dimensions: 要检查的维度列表（如果为 None 则检查所有）

    Returns:
        包含质量评估的更新后状态
    """
    logger.info("[QualityCheckNode] Starting content quality check")

    # Create default assessor if needed
    if assessor is None:
        if not _QUALITY_AVAILABLE:
            logger.warning(
                "[QualityCheckNode] Quality system unavailable, skipping check"
            )
            state["quality_assessment"] = {
                "overall_score": 1.0,  # Pass by default
                "passes_threshold": True,
                "threshold": threshold,
                "system_available": False,
            }
            return state

        assessor = RuleBasedAssessor(threshold=threshold)

    # Get content materials from state
    content_materials = state.get("content_materials", [])

    if not content_materials:
        logger.warning("[QualityCheckNode] No content materials to check")
        state["quality_assessment"] = {
            "overall_score": 0.0,
            "passes_threshold": False,
            "threshold": threshold,
            "error": "No content materials",
        }
        return state

    # Define dimensions to check
    if check_dimensions is None:
        check_dimensions = [
            QualityDimension.COMPLETENESS,
            QualityDimension.CLARITY,
            QualityDimension.LENGTH,
        ]

    # Assess each content material
    all_assessments: List[QualityAssessment] = []
    all_scores: List[float] = []
    all_issues: List[str] = []

    for idx, material in enumerate(content_materials):
        content = material.get("content", "")

        # Build context for assessment
        context = {
            "min_length": 100,
            "max_length": 2000,
            "required_fields": material.get("required_fields", []),
            "page_index": idx,
        }

        try:
            assessment = await assessor.assess(
                content=content,
                context=context,
                dimensions=check_dimensions,
            )

            all_assessments.append(assessment)
            all_scores.append(assessment.overall_score)

            # Collect issues
            for score in assessment.dimension_scores:
                all_issues.extend([
                    f"[Page {idx}] {score.dimension.value}: {issue}"
                    for issue in score.issues
                ])

            logger.debug(
                f"[QualityCheckNode] Page {idx} score: {assessment.overall_score:.3f}"
            )

        except Exception as e:
            logger.error(
                f"[QualityCheckNode] Error assessing page {idx}: {e}",
                exc_info=True,
            )
            all_scores.append(0.0)

    # Calculate overall score
    overall_score = (
        sum(all_scores) / len(all_scores) if all_scores else 0.0
    )

    passes_threshold = overall_score >= threshold

    # Store assessment in state
    state["quality_assessment"] = {
        "overall_score": overall_score,
        "passes_threshold": passes_threshold,
        "threshold": threshold,
        "page_scores": all_scores,
        "issues": all_issues,
        "assessment_count": len(all_assessments),
        "dimensions_checked": [d.value for d in check_dimensions],
        "system_available": _QUALITY_AVAILABLE,
    }

    logger.info(
        f"[QualityCheckNode] Quality check complete: "
        f"score={overall_score:.3f}, passes={passes_threshold}"
    )

    return state


def should_refine_content(state: PPTGenerationState) -> str:
    """
    条件边函数：决定是否改进内容

    Args:
        state: 当前状态

    Returns:
        如果质量低于阈值则返回 "refine"，否则返回 "proceed"
    """
    assessment = state.get("quality_assessment", {})

    # Check if quality check passed
    passes = assessment.get("passes_threshold", True)

    # Check refinement count (prevent infinite loops)
    refinement_count = state.get("refinement_count", 0)
    max_refinements = 3

    if refinement_count >= max_refinements:
        logger.warning(
            f"[should_refine] Max refinements reached ({max_refinements}), proceeding"
        )
        return "proceed"

    if not passes:
        logger.info(
            f"[should_refine] Quality below threshold, routing to refinement "
            f"(score={assessment.get('overall_score', 0):.3f})"
        )
        return "refine"

    logger.info(
        f"[should_refine] Quality threshold met, proceeding "
        f"(score={assessment.get('overall_score', 0):.3f})"
    )
    return "proceed"


async def check_framework_quality(
    state: PPTGenerationState,
    assessor: Optional[QualityAssessor] = None,
    threshold: float = 0.8,
) -> PPTGenerationState:
    """
    LangGraph 节点：检查 PPT 框架质量

    评估生成的 PPT 框架结构的质量。

    Args:
        state: 当前 LangChain 状态
        assessor: 可选的质量评估器
        threshold: 质量阈值

    Returns:
        包含框架质量评估的更新后状态
    """
    logger.info("[QualityCheckNode] Starting framework quality check")

    if assessor is None:
        if not _QUALITY_AVAILABLE:
            state["framework_quality_assessment"] = {
                "overall_score": 1.0,
                "passes_threshold": True,
                "system_available": False,
            }
            return state
        assessor = RuleBasedAssessor(threshold=threshold)

    # Get framework from state
    framework = state.get("ppt_framework", {})
    pages = framework.get("ppt_framework", [])

    if not pages:
        logger.warning("[QualityCheckNode] No framework to check")
        state["framework_quality_assessment"] = {
            "overall_score": 0.0,
            "passes_threshold": False,
            "error": "No framework pages",
        }
        return state

    # Assess framework completeness
    required_fields = ["page_type", "title", "content_description"]
    missing_count = 0

    for page in pages:
        missing = [f for f in required_fields if f not in page or not page[f]]
        missing_count += len(missing)

    # Calculate score
    total_fields = len(pages) * len(required_fields)
    completeness_score = 1.0 - (missing_count / total_fields) if total_fields > 0 else 0.0

    # Assess page count
    expected_page_count = framework.get("total_page", len(pages))
    page_count_score = 1.0 if len(pages) >= expected_page_count else len(pages) / expected_page_count

    # Overall framework score
    overall_score = (completeness_score * 0.7) + (page_count_score * 0.3)

    passes_threshold = overall_score >= threshold

    state["framework_quality_assessment"] = {
        "overall_score": overall_score,
        "passes_threshold": passes_threshold,
        "threshold": threshold,
        "completeness_score": completeness_score,
        "page_count_score": page_count_score,
        "total_pages": len(pages),
        "missing_fields": missing_count,
        "system_available": _QUALITY_AVAILABLE,
    }

    logger.info(
        f"[QualityCheckNode] Framework quality check complete: "
        f"score={overall_score:.3f}, passes={passes_threshold}"
    )

    return state


def should_refine_framework(state: PPTGenerationState) -> str:
    """
    条件边：决定是否改进框架

    Args:
        state: 当前状态

    Returns:
        "refine" 或 "proceed"
    """
    assessment = state.get("framework_quality_assessment", {})
    passes = assessment.get("passes_threshold", True)

    if not passes:
        return "refine"
    return "proceed"
