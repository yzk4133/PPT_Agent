"""
Quality Feedback Loop for Agents

Provides self-assessment and iterative refinement capabilities for agents.
Includes quality metrics, assessment functions, and refinement strategies.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class QualityDimension(str, Enum):
    """Dimensions of quality to assess"""
    COMPLETENESS = "completeness"  # Is all required information present?
    COHERENCE = "coherence"  # Does the content flow logically?
    RELEVANCE = "relevance"  # Is it relevant to the input/request?
    ACCURACY = "accuracy"  # Is the information accurate?
    CLARITY = "clarity"  # Is the content clear and understandable?
    STRUCTURE = "structure"  # Is the structure appropriate?
    LENGTH = "length"  # Is the length appropriate?


@dataclass
class QualityScore:
    """
    Quality assessment score.

    Attributes:
        dimension: Quality dimension being assessed
        score: Score from 0.0 to 1.0
        details: Additional details about the score
        issues: List of specific issues found
        suggestions: Suggestions for improvement
    """
    dimension: QualityDimension
    score: float
    details: str = ""
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "dimension": self.dimension.value,
            "score": round(self.score, 3),
            "details": self.details,
            "issues": self.issues,
            "suggestions": self.suggestions
        }


@dataclass
class QualityAssessment:
    """
    Complete quality assessment for content.

    Attributes:
        overall_score: Overall quality score (0.0 - 1.0)
        passes_threshold: Whether the assessment meets the threshold
        dimension_scores: Scores for each dimension
        metadata: Additional metadata
    """
    overall_score: float
    passes_threshold: bool
    dimension_scores: List[QualityScore]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "overall_score": round(self.overall_score, 3),
            "passes_threshold": self.passes_threshold,
            "dimension_scores": [s.to_dict() for s in self.dimension_scores],
            "metadata": self.metadata
        }


@dataclass
class RefinementResult:
    """
    Result of a refinement iteration.

    Attributes:
        iteration: Iteration number
        content: Refined content
        assessment: Quality assessment of the refined content
        improved: Whether this iteration improved the quality
        changes: Description of changes made
    """
    iteration: int
    content: Any
    assessment: QualityAssessment
    improved: bool
    changes: str = ""


class QualityAssessor(ABC):
    """
    Abstract base class for quality assessors.

    Implement specific assessors for different content types.
    """

    @abstractmethod
    async def assess(
        self,
        content: Any,
        context: Dict[str, Any],
        dimensions: Optional[List[QualityDimension]] = None
    ) -> QualityAssessment:
        """
        Assess the quality of content.

        Args:
            content: Content to assess
            context: Additional context for assessment
            dimensions: Specific dimensions to assess (all if None)

        Returns:
            QualityAssessment object
        """
        pass


class RuleBasedAssessor(QualityAssessor):
    """
    Rule-based quality assessor.

    Uses heuristic rules to assess content quality.
    """

    def __init__(
        self,
        threshold: float = 0.8,
        dimension_weights: Optional[Dict[QualityDimension, float]] = None
    ):
        """
        Initialize the assessor.

        Args:
            threshold: Quality threshold (0.0 - 1.0)
            dimension_weights: Weights for each dimension
        """
        self.threshold = threshold
        self.dimension_weights = dimension_weights or {
            QualityDimension.COMPLETENESS: 0.2,
            QualityDimension.COHERENCE: 0.15,
            QualityDimension.RELEVANCE: 0.2,
            QualityDimension.ACCURACY: 0.15,
            QualityDimension.CLARITY: 0.15,
            QualityDimension.STRUCTURE: 0.1,
            QualityDimension.LENGTH: 0.05
        }

    async def assess(
        self,
        content: Any,
        context: Dict[str, Any],
        dimensions: Optional[List[QualityDimension]] = None
    ) -> QualityAssessment:
        """Assess quality using rules"""
        if dimensions is None:
            dimensions = list(QualityDimension)

        dimension_scores = []

        for dimension in dimensions:
            score = await self._assess_dimension(content, context, dimension)
            dimension_scores.append(score)

        # Calculate overall score
        overall = sum(
            s.score * self.dimension_weights.get(s.dimension, 1.0)
            for s in dimension_scores
        )

        return QualityAssessment(
            overall_score=overall,
            passes_threshold=overall >= self.threshold,
            dimension_scores=dimension_scores,
            metadata={
                "threshold": self.threshold,
                "assessor": "RuleBasedAssessor"
            }
        )

    async def _assess_dimension(
        self,
        content: Any,
        context: Dict[str, Any],
        dimension: QualityDimension
    ) -> QualityScore:
        """Assess a single dimension"""
        score = 0.0
        issues = []
        suggestions = []

        if isinstance(content, dict):
            # Dictionary content assessment
            if dimension == QualityDimension.COMPLETENESS:
                score, issues, suggestions = self._assess_completeness_dict(content, context)
            elif dimension == QualityDimension.STRUCTURE:
                score, issues, suggestions = self._assess_structure_dict(content, context)
            else:
                score = 0.7  # Default for unassessed dimensions

        elif isinstance(content, str):
            # String content assessment
            if dimension == QualityDimension.LENGTH:
                score, issues, suggestions = self._assess_length_string(content, context)
            elif dimension == QualityDimension.CLARITY:
                score, issues, suggestions = self._assess_clarity_string(content, context)
            else:
                score = 0.7

        elif isinstance(content, list):
            # List content assessment
            if dimension == QualityDimension.COMPLETENESS:
                score, issues, suggestions = self._assess_completeness_list(content, context)
            else:
                score = 0.7

        else:
            score = 0.5  # Unknown type
            issues.append(f"Unknown content type: {type(content)}")

        return QualityScore(
            dimension=dimension,
            score=score,
            issues=issues,
            suggestions=suggestions
        )

    def _assess_completeness_dict(
        self,
        content: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Assess completeness of dictionary content"""
        required_fields = context.get("required_fields", [])
        if not required_fields:
            return 1.0, [], []

        missing = [f for f in required_fields if f not in content]
        score = 1.0 - (len(missing) / len(required_fields))

        issues = [f"Missing field: {f}" for f in missing]
        suggestions = [f"Add field: {f}" for f in missing]

        return score, issues, suggestions

    def _assess_structure_dict(
        self,
        content: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Assess structure of dictionary content"""
        issues = []
        score = 1.0

        # Check for empty values
        empty_fields = [k for k, v in content.items() if not v]
        if empty_fields:
            score -= 0.1 * len(empty_fields)
            issues.append(f"Empty fields: {', '.join(empty_fields)}")

        return max(0.0, score), issues, []

    def _assess_length_string(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Assess length of string content"""
        min_length = context.get("min_length", 10)
        max_length = context.get("max_length", 10000)

        length = len(content)

        if min_length <= length <= max_length:
            return 1.0, [], []
        elif length < min_length:
            return (
                length / min_length,
                [f"Content too short: {length} < {min_length}"],
                [f"Expand content to at least {min_length} characters"]
            )
        else:
            return (
                max_length / length,
                [f"Content too long: {length} > {max_length}"],
                [f"Condense content to at most {max_length} characters"]
            )

    def _assess_clarity_string(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Assess clarity of string content"""
        issues = []
        suggestions = []
        score = 1.0

        # Check for very long sentences
        sentences = content.split('.')
        long_sentences = [s.strip() for s in sentences if len(s.strip()) > 200]
        if long_sentences:
            score -= 0.1 * len(long_sentences)
            issues.append(f"Found {len(long_sentences)} very long sentences")
            suggestions.append("Break long sentences into shorter ones")

        # Check for repeated words
        words = content.lower().split()
        if len(words) > 0:
            from collections import Counter
            word_counts = Counter(words)
            repeated = [w for w, c in word_counts.items() if c > 5 and len(w) > 3]
            if repeated:
                score -= 0.05 * len(repeated)
                issues.append(f"Repeated words: {', '.join(repeated[:5])}")

        return max(0.0, score), issues, suggestions

    def _assess_completeness_list(
        self,
        content: List[Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Assess completeness of list content"""
        min_items = context.get("min_items", 1)
        score = min(1.0, len(content) / min_items)

        issues = []
        suggestions = []

        if len(content) < min_items:
            issues.append(f"List too short: {len(content)} < {min_items}")
            suggestions.append(f"Add at least {min_items - len(content)} more items")

        return score, issues, suggestions


class FeedbackLoopAgent:
    """
    Agent with feedback loop capability.

    Automatically assesses and refines output until quality threshold is met.
    """

    def __init__(
        self,
        assessor: QualityAssessor,
        max_iterations: int = 3,
        threshold: float = 0.8,
        refinement_strategy: Optional[Callable[[Any, QualityAssessment], Any]] = None
    ):
        """
        Initialize the feedback loop agent.

        Args:
            assessor: Quality assessor to use
            max_iterations: Maximum refinement iterations
            threshold: Quality threshold to aim for
            refinement_strategy: Function to refine content based on assessment
        """
        self.assessor = assessor
        self.max_iterations = max_iterations
        self.threshold = threshold
        self.refinement_strategy = refinement_strategy or self._default_refinement

    async def execute_with_feedback(
        self,
        generator: Callable[[], Any],
        context: Dict[str, Any],
        dimensions: Optional[List[QualityDimension]] = None
    ) -> RefinementResult:
        """
        Execute with automatic feedback and refinement.

        Args:
            generator: Function that generates initial content
            context: Context for generation and assessment
            dimensions: Quality dimensions to assess

        Returns:
            Final refinement result
        """
        iteration = 0
        content = generator()
        last_score = 0.0

        while iteration < self.max_iterations:
            # Assess current content
            assessment = await self.assessor.assess(content, context, dimensions)

            logger.info(
                f"Iteration {iteration + 1}: Quality score = {assessment.overall_score:.3f}"
            )

            # Check if threshold met
            if assessment.overall_score >= self.threshold:
                logger.info(f"Quality threshold met at iteration {iteration + 1}")
                return RefinementResult(
                    iteration=iteration + 1,
                    content=content,
                    assessment=assessment,
                    improved=True,
                    changes=f"Met threshold on iteration {iteration + 1}"
                )

            # Check if no improvement
            if iteration > 0 and assessment.overall_score <= last_score:
                logger.warning("No improvement in quality, stopping refinement")
                break

            # Refine content
            last_score = assessment.overall_score
            content = self.refinement_strategy(content, assessment)
            iteration += 1

        # Max iterations reached
        final_assessment = await self.assessor.assess(content, context, dimensions)

        return RefinementResult(
            iteration=iteration,
            content=content,
            assessment=final_assessment,
            improved=final_assessment.overall_score > self.threshold,
            changes=f"Reached max iterations ({self.max_iterations})"
        )

    def _default_refinement(
        self,
        content: Any,
        assessment: QualityAssessment
    ) -> Any:
        """
        Default refinement strategy.

        In a real implementation, this would call an LLM to refine the content.
        For now, it returns the content unchanged.
        """
        logger.info("Using default refinement strategy (no changes)")
        return content


# Global assessor instance
_default_assessor: Optional[QualityAssessor] = None


def get_default_assessor() -> QualityAssessor:
    """Get the default quality assessor"""
    global _default_assessor
    if _default_assessor is None:
        _default_assessor = RuleBasedAssessor(threshold=0.8)
    return _default_assessor


if __name__ == "__main__":
    # Test quality assessment
    logging.basicConfig(level=logging.INFO)

    async def test_assessment():
        print("=== Testing Quality Assessment ===")

        assessor = RuleBasedAssessor(threshold=0.8)

        # Test 1: Complete dictionary
        print("\n--- Test 1: Complete Dictionary ---")
        content1 = {
            "title": "AI Presentation",
            "pages": 10,
            "template": "business",
            "author": "John Doe"
        }
        context1 = {
            "required_fields": ["title", "pages", "template"]
        }

        assessment1 = await assessor.assess(content1, context1)
        print(json.dumps(assessment1.to_dict(), indent=2, ensure_ascii=False))

        # Test 2: Incomplete dictionary
        print("\n--- Test 2: Incomplete Dictionary ---")
        content2 = {"title": "AI Presentation"}
        context2 = {
            "required_fields": ["title", "pages", "template", "author"]
        }

        assessment2 = await assessor.assess(content2, context2)
        print(json.dumps(assessment2.to_dict(), indent=2, ensure_ascii=False))

        # Test 3: String length
        print("\n--- Test 3: String Length ---")
        content3 = "Short"
        context3 = {"min_length": 10, "max_length": 100}

        assessment3 = await assessor.assess(content3, context3)
        print(json.dumps(assessment3.to_dict(), indent=2, ensure_ascii=False))

        # Test 4: Feedback loop
        print("\n--- Test 4: Feedback Loop ---")

        def mock_generator():
            return {"title": "AI Presentation"}

        agent = FeedbackLoopAgent(
            assessor=assessor,
            max_iterations=2,
            threshold=0.8
        )

        result = await agent.execute_with_feedback(
            generator=mock_generator,
            context={"required_fields": ["title", "pages"]}
        )

        print(f"Iterations: {result.iteration}")
        print(f"Final score: {result.assessment.overall_score:.3f}")
        print(f"Passed: {result.assessment.passes_threshold}")

    asyncio.run(test_assessment())
