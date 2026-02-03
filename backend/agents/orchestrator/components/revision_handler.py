"""
Revision Handler

修订处理器，支持选择性重跑受影响的阶段。

支持的修订类型：
1. 修改模板 → 仅重跑 template_renderer
2. 修改文字 → 仅重跑 content_material + template_renderer
3. 补充数据 → 仅重跑 research + content_material + template_renderer
4. 增减页数 → 重跑 framework_designer + 后续所有
"""

import asyncio
import json
import logging
import os
import sys
from typing import Optional, Dict, Any, List, Set
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# 导入基础设施
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# 导入领域模型
from domain.models import Task, TaskStage

logger = logging.getLogger(__name__)


class RevisionType(str, Enum):
    """修订类型"""
    TEMPLATE_CHANGE = "template_change"      # 修改模板
    TEXT_CHANGE = "text_change"              # 修改文字
    DATA_SUPPLEMENT = "data_supplement"      # 补充数据
    PAGE_COUNT_CHANGE = "page_count_change"  # 增减页数
    REQUIREMENT_CHANGE = "requirement_change"  # 需求变更


@dataclass
class RevisionPlan:
    """
    修订计划

    Attributes:
        revision_type: 修订类型
        affected_stages: 受影响的阶段列表
        new_requirements: 新的需求（如果有）
        new_framework: 新的框架（如果有）
        additional_data: 额外数据（如果有）
    """
    revision_type: RevisionType
    affected_stages: List[TaskStage]
    new_requirements: Optional[Dict[str, Any]] = None
    new_framework: Optional[Dict[str, Any]] = None
    additional_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "revision_type": self.revision_type.value,
            "affected_stages": [stage.value for stage in self.affected_stages],
            "new_requirements": self.new_requirements,
            "new_framework": self.new_framework,
            "additional_data": self.additional_data
        }


@dataclass
class RevisionResult:
    """
    修订结果

    Attributes:
        task_id: 任务ID
        success: 是否成功
        updated_stages: 已更新的阶段列表
        new_output: 新的输出
        error: 错误信息
    """
    task_id: str
    success: bool
    updated_stages: List[TaskStage]
    new_output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "success": self.success,
            "updated_stages": [stage.value for stage in self.updated_stages],
            "new_output": self.new_output,
            "error": self.error
        }


class RevisionHandler:
    """
    修订处理器

    支持的修订类型：
    1. 修改模板 → 仅重跑 template_renderer
    2. 修改文字 → 仅重跑 content_material + template_renderer
    3. 补充数据 → 仅重跑 research + content_material + template_renderer
    4. 增减页数 → 重跑 framework_designer + 后续所有
    """

    # 阶段依赖关系（DAG）
    STAGE_DEPENDENCIES = {
        TaskStage.REQUIREMENT_PARSING: [],
        TaskStage.FRAMEWORK_DESIGN: [TaskStage.REQUIREMENT_PARSING],
        TaskStage.RESEARCH: [TaskStage.FRAMEWORK_DESIGN],
        TaskStage.CONTENT_GENERATION: [TaskStage.RESEARCH, TaskStage.FRAMEWORK_DESIGN],
        TaskStage.TEMPLATE_RENDERING: [TaskStage.CONTENT_GENERATION, TaskStage.FRAMEWORK_DESIGN],
    }

    # 修订类型与受影响阶段的映射
    REVISION_STAGE_MAPPING = {
        RevisionType.TEMPLATE_CHANGE: [TaskStage.TEMPLATE_RENDERING],
        RevisionType.TEXT_CHANGE: [TaskStage.CONTENT_GENERATION, TaskStage.TEMPLATE_RENDERING],
        RevisionType.DATA_SUPPLEMENT: [TaskStage.RESEARCH, TaskStage.CONTENT_GENERATION, TaskStage.TEMPLATE_RENDERING],
        RevisionType.PAGE_COUNT_CHANGE: [
            TaskStage.FRAMEWORK_DESIGN,
            TaskStage.RESEARCH,
            TaskStage.CONTENT_GENERATION,
            TaskStage.TEMPLATE_RENDERING
        ],
        RevisionType.REQUIREMENT_CHANGE: [
            TaskStage.REQUIREMENT_PARSING,
            TaskStage.FRAMEWORK_DESIGN,
            TaskStage.RESEARCH,
            TaskStage.CONTENT_GENERATION,
            TaskStage.TEMPLATE_RENDERING
        ],
    }

    def __init__(self):
        """初始化修订处理器"""
        from agents.orchestrator.agents.master_coordinator import master_coordinator_agent
        self.master_coordinator = master_coordinator_agent
        from agents.orchestrator.components.progress_tracker import get_progress_tracker
        self.progress_tracker = get_progress_tracker()

    async def handle_revision(
        self,
        task_id: str,
        revision_request: Dict[str, Any]
    ) -> RevisionResult:
        """
        处理修订请求

        Args:
            task_id: 任务ID
            revision_request: 修订请求

        Returns:
            修订结果
        """
        try:
            logger.info(f"Handling revision for task {task_id}: {revision_request}")

            # 1. 分析修订类型
            revision_plan = self._analyze_revision(revision_request)

            logger.info(f"Revision plan: {revision_plan.to_dict()}")

            # 2. 获取原始任务状态
            # 注意：这里需要从状态存储中获取，简化实现中我们假设通过session传递
            # 在实际使用中，可能需要从数据库或其他存储中获取

            # 3. 重跑受影响的阶段
            updated_stages = []

            # 这里需要实际的上下文执行环境
            # 简化实现中，我们返回修订计划
            # 实际实现需要重新运行智能体

            for stage in revision_plan.affected_stages:
                # 执行阶段重跑
                await self._rerun_stage(task_id, stage, revision_plan)
                updated_stages.append(stage)

            # 4. 返回更新后的结果
            return RevisionResult(
                task_id=task_id,
                success=True,
                updated_stages=updated_stages,
                new_output={"revision_plan": revision_plan.to_dict()}
            )

        except Exception as e:
            logger.error(f"Revision failed: {e}", exc_info=True)
            return RevisionResult(
                task_id=task_id,
                success=False,
                updated_stages=[],
                error=str(e)
            )

    def _analyze_revision(self, revision_request: Dict[str, Any]) -> RevisionPlan:
        """
        分析修订请求，生成修订计划

        Args:
            revision_request: 修订请求

        Returns:
            修订计划
        """
        # 确定修订类型
        revision_type_str = revision_request.get("revision_type", "template_change")
        revision_type = RevisionType(revision_type_str)

        # 获取受影响的阶段
        affected_stages = self.REVISION_STAGE_MAPPING.get(revision_type, [])

        # 创建修订计划
        plan = RevisionPlan(
            revision_type=revision_type,
            affected_stages=affected_stages
        )

        # 根据修订类型添加额外信息
        if revision_type == RevisionType.REQUIREMENT_CHANGE:
            plan.new_requirements = revision_request.get("new_requirements")

        elif revision_type == RevisionType.PAGE_COUNT_CHANGE:
            plan.new_requirements = revision_request.get("new_requirements")

        elif revision_type == RevisionType.DATA_SUPPLEMENT:
            plan.additional_data = revision_request.get("additional_data")

        return plan

    async def _rerun_stage(
        self,
        task_id: str,
        stage: TaskStage,
        revision_plan: RevisionPlan
    ) -> None:
        """
        重跑单个阶段

        Args:
            task_id: 任务ID
            stage: 要重跑的阶段
            revision_plan: 修订计划
        """
        logger.info(f"Re-running stage {stage.value} for task {task_id}")

        # 在实际实现中，这里需要：
        # 1. 获取原始上下文
        # 2. 根据修订计划更新上下文
        # 3. 重新运行对应的智能体
        # 4. 更新状态存储

        # 简化实现：仅记录日志
        await asyncio.sleep(0.1)  # 模拟异步操作

    def get_affected_stages(self, revision_type: RevisionType) -> List[TaskStage]:
        """
        获取修订类型对应的受影响阶段

        Args:
            revision_type: 修订类型

        Returns:
            受影响的阶段列表
        """
        return self.REVISION_STAGE_MAPPING.get(revision_type, [])

    def get_revision_types(self) -> List[str]:
        """获取所有支持的修订类型"""
        return [rt.value for rt in RevisionType]

    def validate_revision_request(self, revision_request: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        校验修订请求

        Args:
            revision_request: 修订请求

        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []

        # 检查修订类型
        revision_type_str = revision_request.get("revision_type")
        if not revision_type_str:
            errors.append("缺少 revision_type 字段")
        else:
            try:
                RevisionType(revision_type_str)
            except ValueError:
                errors.append(f"无效的修订类型: {revision_type_str}")

        # 根据修订类型检查必需字段
        revision_type_str = revision_request.get("revision_type", "")
        if revision_type_str == RevisionType.REQUIREMENT_CHANGE.value:
            if not revision_request.get("new_requirements"):
                errors.append("requirement_change 修订需要 new_requirements 字段")

        elif revision_type_str == RevisionType.PAGE_COUNT_CHANGE.value:
            if not revision_request.get("new_requirements"):
                errors.append("page_count_change 修订需要 new_requirements 字段")

        return len(errors) == 0, errors


# 全局修订处理器实例
_global_revision_handler: Optional[RevisionHandler] = None


def get_revision_handler() -> RevisionHandler:
    """
    获取全局修订处理器实例

    Returns:
        RevisionHandler实例
    """
    global _global_revision_handler
    if _global_revision_handler is None:
        _global_revision_handler = RevisionHandler()
    return _global_revision_handler


if __name__ == "__main__":
    # 测试代码
    async def test_revision_handler():
        print(f"Testing RevisionHandler")
        print("=" * 60)

        handler = RevisionHandler()

        # 测试修订类型
        print(f"Supported revision types: {handler.get_revision_types()}")

        # 测试分析修订请求
        test_requests = [
            {"revision_type": "template_change"},
            {"revision_type": "text_change"},
            {"revision_type": "data_supplement", "additional_data": {"key": "value"}},
            {"revision_type": "page_count_change", "new_requirements": {"page_num": 15}},
        ]

        for req in test_requests:
            plan = handler._analyze_revision(req)
            print(f"\nRequest: {req['revision_type']}")
            print(f"Affected stages: {[s.value for s in plan.affected_stages]}")

        # 测试校验
        is_valid, errors = handler.validate_revision_request({"revision_type": "invalid_type"})
        print(f"\nValidation test: valid={is_valid}, errors={errors}")

    asyncio.run(test_revision_handler())
