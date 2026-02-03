"""
统一的Agent结果封装

提供类型安全的结果返回，支持泛型
"""

from dataclasses import dataclass, field
from typing import Optional, Any, List, Generic, TypeVar
from enum import Enum

T = TypeVar("T")


class ResultStatus(str, Enum):
    """结果状态"""

    SUCCESS = "success"  # 完全成功
    PARTIAL = "partial"  # 部分成功（使用了降级策略）
    FAILURE = "failure"  # 失败
    RETRY = "retry"  # 需要重试


@dataclass
class AgentResult(Generic[T]):
    """
    统一的Agent执行结果

    使用泛型支持不同类型的数据

    使用示例:
        >>> # 成功情况
        >>> result = AgentResult(
        ...     status=ResultStatus.SUCCESS,
        ...     data=PPTFramework(...),
        ...     message="框架设计完成"
        ... )

        >>> # 失败情况
        >>> result = AgentResult(
        ...     status=ResultStatus.FAILURE,
        ...     message="LLM调用失败",
        ...     errors=["连接超时"]
        ... )

        >>> # 降级情况
        >>> result = AgentResult(
        ...     status=ResultStatus.PARTIAL,
        ...     data=default_framework,
        ...     fallback_used=True,
        ...     fallback_reason="LLM返回格式错误"
        ... )
    """

    status: ResultStatus
    data: Optional[T] = None
    message: str = ""
    errors: List[str] = field(default_factory=list)

    # 降级信息
    fallback_used: bool = False
    fallback_reason: Optional[str] = None

    # 性能指标
    execution_time: float = 0.0  # 执行时间（秒）
    token_usage: int = 0  # Token使用量

    # 元数据
    metadata: dict = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """是否成功（包括部分成功）"""
        return self.status in [ResultStatus.SUCCESS, ResultStatus.PARTIAL]

    @property
    def needs_retry(self) -> bool:
        """是否需要重试"""
        return self.status == ResultStatus.RETRY

    @property
    def is_failure(self) -> bool:
        """是否失败"""
        return self.status == ResultStatus.FAILURE

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "status": self.status.value,
            "data": self.data,
            "message": self.message,
            "errors": self.errors,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
            "execution_time": self.execution_time,
            "token_usage": self.token_usage,
            "metadata": self.metadata,
        }

    @classmethod
    def success(
        cls,
        data: T,
        message: str = "执行成功",
        execution_time: float = 0.0,
        token_usage: int = 0,
    ) -> "AgentResult[T]":
        """创建成功结果"""
        return cls(
            status=ResultStatus.SUCCESS,
            data=data,
            message=message,
            execution_time=execution_time,
            token_usage=token_usage,
        )

    @classmethod
    def failure(
        cls, message: str, errors: List[str] = None, execution_time: float = 0.0
    ) -> "AgentResult[T]":
        """创建失败结果"""
        return cls(
            status=ResultStatus.FAILURE,
            message=message,
            errors=errors or [],
            execution_time=execution_time,
        )

    @classmethod
    def partial(
        cls,
        data: T,
        fallback_reason: str,
        message: str = "使用降级策略",
        execution_time: float = 0.0,
    ) -> "AgentResult[T]":
        """创建部分成功结果（使用了降级）"""
        return cls(
            status=ResultStatus.PARTIAL,
            data=data,
            message=message,
            fallback_used=True,
            fallback_reason=fallback_reason,
            execution_time=execution_time,
        )

    @classmethod
    def retry(cls, message: str, errors: List[str] = None) -> "AgentResult[T]":
        """创建需要重试的结果"""
        return cls(status=ResultStatus.RETRY, message=message, errors=errors or [])


# 常用的特定类型结果
@dataclass
class ValidationResult:
    """验证结果"""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


@dataclass
class ProgressEvent:
    """进度事件（用于WebSocket推送）"""

    presentation_id: str
    stage: str
    progress: float  # 0-100
    message: str
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "presentation_id": self.presentation_id,
            "stage": self.stage,
            "progress": self.progress,
            "message": self.message,
            "timestamp": self.timestamp,
        }
