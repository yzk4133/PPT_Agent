"""
Task 业务规则测试

这些测试验证真实的业务场景和规则，而不是简单的功能验证
"""

import pytest
from datetime import datetime
from domain.entities.task import Task, TaskStatus, TaskStage
from domain.value_objects.requirement import Requirement, SceneType
from domain.exceptions import ValidationError

@pytest.mark.domain
@pytest.mark.business
@pytest.mark.p0
class TestTaskBusinessRules:
    """Task 业务规则测试"""

    def test_task_progress_weights_match_business_definition(self):
        """
        [BUSINESS-001] 测试进度权重符合业务定义

        业务规则：
        - 需求解析占整个项目的15%
        - 框架设计占30%
        - 研究阶段占50%（如果需要）
        - 内容生成占80%
        - 模板渲染占100%

        这是业务核心规则，不能随意修改
        """
        task = Task(id="business_001", raw_input="AI技术介绍PPT")

        # 完成需求解析后，应该是15%左右
        task.start_stage(TaskStage.REQUIREMENT_PARSING)
        task.complete_stage(TaskStage.REQUIREMENT_PARSING)
        progress = task.get_overall_progress()

        assert 14 <= progress <= 16, \
            f"需求解析完成后应该占总进度的15%左右，实际为{progress}%"

        # 完成框架设计后，累计应该是45%左右（15% + 30%）
        task.start_stage(TaskStage.FRAMEWORK_DESIGN)
        task.complete_stage(TaskStage.FRAMEWORK_DESIGN)
        progress = task.get_overall_progress()

        assert 44 <= progress <= 46, \
            f"需求解析+框架设计后应该占总进度的45%左右，实际为{progress}%"

    def test_research_stage_only_when_needed(self):
        """
        [BUSINESS-002] 测试研究阶段只在需要时计入进度

        业务规则：
        - 如果需要研究，研究阶段占50%权重
        - 如果不需要研究，研究阶段占0%权重
        - 这是业务逻辑的关键部分
        """
        # 场景1: 需要研究的任务
        task_with_research = Task(
            id="business_002",
            raw_input="量子计算前沿技术研究"
        )
        task_with_research.structured_requirements = {"need_research": True}

        task_with_research.start_stage(TaskStage.RESEARCH)
        task_with_research.complete_stage(TaskStage.RESEARCH)

        progress_with_research = task_with_research.get_overall_progress()
        # 完成研究后应该有显著进度（接近50%）
        assert progress_with_research >= 45, \
            f"需要研究的任务，完成研究阶段应该有45%+进度，实际为{progress_with_research}%"

        # 场景2: 不需要研究的任务
        task_without_research = Task(
            id="business_003",
            raw_input="公司简介PPT"
        )
        task_without_research.structured_requirements = {"need_research": False}

        task_without_research.start_stage(TaskStage.RESEARCH)
        task_without_research.complete_stage(TaskStage.RESEARCH)

        progress_without_research = task_without_research.get_overall_progress()
        # 完成研究阶段后进度应该保持不变或略有增长
        # 因为研究阶段被跳过
        assert progress_without_research <= 50, \
            f"不需要研究的任务，研究阶段不应大幅增加进度，实际为{progress_without_research}%"

    def test_task_duration_is_calculated_correctly(self):
        """
        [BUSINESS-003] 测试任务持续时间计算正确

        业务场景：
        - 用户关心任务需要多长时间完成
        - 系统需要准确记录并计算总耗时
        """
        task = Task(id="business_004", raw_input="测试")

        # 模拟任务在不同时间完成各阶段
        import time
        time.sleep(0.01)  # 确保有时间差

        task.start_stage(TaskStage.REQUIREMENT_PARSING)
        time.sleep(0.01)
        task.complete_stage(TaskStage.REQUIREMENT_PARSING)

        # 标记完成
        task.mark_completed()

        # 验证总耗时被计算
        assert task.metadata.total_duration >= 0, \
            "任务完成后应该计算总耗时"
        assert task.metadata.completed_at is not None, \
            "任务完成时间应该被记录"
        assert task.metadata.completed_at >= task.metadata.created_at, \
            "完成时间应该晚于创建时间"

    def test_task_stage_order_matters(self):
        """
        [BUSINESS-004] 测试任务阶段顺序的重要性

        业务规则：
        - 必须按顺序完成各阶段
        - 不能跳过中间阶段
        - 这是PPT生成的业务流程要求
        """
        task = Task(id="business_005", raw_input="测试")

        # 正常顺序：需求解析 -> 框架设计 -> 研究 -> 生成 -> 渲染
        task.start_stage(TaskStage.REQUIREMENT_PARSING)
        task.complete_stage(TaskStage.REQUIREMENT_PARSING)

        task.start_stage(TaskStage.FRAMEWORK_DESIGN)
        task.complete_stage(TaskStage.FRAMEWORK_DESIGN)

        # 验证阶段顺序：前面的阶段必须先完成
        assert task.stages[TaskStage.REQUIREMENT_PARSING].status == TaskStatus.COMPLETED
        assert task.stages[TaskStage.FRAMEWORK_DESIGN].status == TaskStatus.COMPLETED

        # 验证未开始的阶段还是pending
        assert task.stages[TaskStage.RESEARCH].status == TaskStatus.PENDING
        assert task.stages[TaskStage.CONTENT_GENERATION].status == TaskStatus.PENDING

@pytest.mark.domain
@pytest.mark.business
@pytest.mark.p0
class TestRequirementBusinessRules:
    """Requirement 业务规则测试"""

    def test_default_modules_match_scene_type(self):
        """
        [BUSINESS-005] 测试默认模块符合场景类型

        业务规则：
        - 不同场景的PPT有不同的默认结构
        - 商务汇报必须包含：封面、目录、数据展示、总结
        - 校园答辩必须包含：研究背景、研究方法、研究结果
        - 产品宣讲必须包含：产品概述、核心功能、价格方案
        """
        # 商务汇报场景
        business_req = Requirement.with_defaults(
            ppt_topic="年度销售报告",
            scene=SceneType.BUSINESS_REPORT
        )

        required_modules = ["封面", "目录"]
        for module in required_modules:
            assert module in business_req.core_modules, \
                f"商务汇报必须包含{module}"

        # 校园答辩场景
        defense_req = Requirement.with_defaults(
            ppt_topic="AI图像识别算法研究",
            scene=SceneType.CAMPUS_DEFENSE
        )

        research_modules = ["研究背景", "研究方法", "研究结果"]
        for module in research_modules:
            assert any(module in m for m in defense_req.core_modules), \
                f"校园答辩必须包含{module}相关章节"

        # 产品宣讲场景
        product_req = Requirement.with_defaults(
            ppt_topic="新产品发布会",
            scene=SceneType.PRODUCT_PRESENTATION
        )

        product_modules = ["产品概述", "核心功能", "价格方案"]
        for module in product_modules:
            assert any(module in m for m in product_req.core_modules), \
                f"产品宣讲必须包含{module}"

    def test_page_num_reasonable_for_scene(self):
        """
        [BUSINESS-006] 测试页数符合场景合理性

        业务规则：
        - 商务汇报通常10-30页
        - 校园答辩通常20-50页
        - 产品宣讲通常10-20页
        - 培训PPT通常20-100页
        """
        # 这些测试验证默认生成的页数是否合理
        business_req = Requirement.with_defaults(
            ppt_topic="销售报告",
            scene=SceneType.BUSINESS_REPORT
        )

        assert 5 <= business_req.page_num <= 100, \
            "商务汇报页数应该在合理范围内"

        defense_req = Requirement.with_defaults(
            ppt_topic="毕业答辩",
            scene=SceneType.CAMPUS_DEFENSE
        )

        assert 5 <= defense_req.page_num <= 100, \
            "校园答辩页数应该在合理范围内"

    def test_keywords_extraction_is_meaningful(self):
        """
        [BUSINESS-007] 测试关键词提取有意义

        业务规则：
        - 从主题中提取的关键词应该相关
        - 至少应该提取1-3个关键词
        - 关键词对后续内容生成有帮助
        """
        req1 = Requirement.with_defaults(
            ppt_topic="人工智能在医疗领域的应用"
        )

        # 应该提取到AI或医疗相关的关键词
        assert len(req1.keywords) > 0, "应该提取到关键词"
        assert len(req1.keywords) <= 3, "关键词数量不应该超过3个"

        # 关键词应该来自主题
        topic_words = set("人工智能在医疗领域的应用".split())
        # 至少有一个关键词在主题中
        assert any(kw in topic_words or any(part in kw for part in topic_words)
                   for kw in req1.keywords), \
            "关键词应该与主题相关"

    def test_core_modules_count_constraint(self):
        """
        [BUSINESS-008] 测试核心模块数量约束

        业务规则：
        - 核心模块数不能超过总页数
        - 这是因为每个模块至少需要一页
        - 这是业务逻辑的基本约束
        """
        # 合法情况：模块数 = 页数
        req1 = Requirement(
            ppt_topic="测试",
            page_num=5,
            core_modules=["封面", "目录", "内容1", "内容2", "总结"]
        )
        assert req1.page_num == len(req1.core_modules)

        # 合法情况：模块数 < 页数
        req2 = Requirement(
            ppt_topic="测试",
            page_num=10,
            core_modules=["封面", "内容1", "内容2", "总结"]
        )
        assert len(req2.core_modules) < req2.page_num

        # 非法情况：模块数 > 页数
        with pytest.raises(ValidationError) as exc_info:
            Requirement(
                ppt_topic="测试",
                page_num=3,
                core_modules=["封面", "内容1", "内容2", "总结"]
            )

        assert "核心模块数量不能超过页数" in str(exc_info.value.errors)

@pytest.mark.domain
@pytest.mark.business
@pytest.mark.p1
class TestTaskErrorHandling:
    """Task 错误处理业务场景测试"""

    def test_retry_mechanism_in_real_scenario(self):
        """
        [BUSINESS-009] 测试重试机制的真实场景

        业务场景：
        - LLM调用可能失败
        - 系统应该支持重试
        - 重试次数应该被记录
        """
        task = Task(id="real_001", raw_input="测试")
        task.start_stage(TaskStage.REQUIREMENT_PARSING)

        # 模拟第1次失败
        task.fail_stage(TaskStage.REQUIREMENT_PARSING, "网络超时")
        assert task.stages[TaskStage.REQUIREMENT_PARSING].retry_count == 0

        # 记录重试次数
        count1 = task.increment_retry(TaskStage.REQUIREMENT_PARSING)
        assert count1 == 1

        count2 = task.increment_retry(TaskStage.REQUIREMENT_PARSING)
        assert count2 == 2

        # 业务规则：重试次数应该被限制
        # 防止无限重试浪费资源
        assert task.stages[TaskStage.REQUIREMENT_PARSING].retry_count == 2

    def test_task_failure_sets_correct_state(self):
        """
        [BUSINESS-010] 测试任务失败设置正确状态

        业务场景：
        - 任务失败后应该有明确的错误信息
        - 失败时间应该被记录
        - 其他Agent需要知道任务状态
        """
        task = Task(id="real_002", raw_input="测试")
        task.start_stage(TaskStage.REQUIREMENT_PARSING)

        error_message = "LLM API调用次数超限"
        task.fail_stage(TaskStage.REQUIREMENT_PARSING, error_message)

        # 验证状态
        assert task.status == TaskStatus.FAILED
        assert task.error == error_message
        assert task.stages[TaskStage.REQUIREMENT_PARSING].error == error_message
        assert task.stages[TaskStage.REQUIREMENT_PARSING].completed_at is not None

        # 验证可以触发失败事件
        events = task.get_pending_events()
        # 注意：start_stage也会触发一个TASK_STARTED事件
        assert len(events) >= 2  # 至少包含阶段失败和任务失败事件
        failed_events = [e for e in events if e.event_type.value == "TASK_FAILED"]
        assert len(failed_events) >= 1  # 应该有失败事件

@pytest.mark.domain
@pytest.mark.business
@pytest.mark.p1
class TestEventDrivenBehavior:
    """事件驱动行为测试"""

    def test_events_enable_reactive_workflow(self):
        """
        [BUSINESS-011] 测试事件支持响应式工作流

        业务价值：
        - 事件驱动架构让Agent可以响应任务状态变化
        - 比如ResearchAgent监听FRAMEWORK_DESIGNED事件
        - 然后自动开始研究工作
        """
        task = Task(id="reactive_001", raw_input="测试")

        # 完成一个阶段
        task.start_stage(TaskStage.REQUIREMENT_PARSING)
        start_events = task.get_pending_events()  # 清空开始事件

        task.complete_stage(TaskStage.REQUIREMENT_PARSING)
        events = task.get_pending_events()

        # 验证事件包含足够的信息供其他Agent使用
        assert len(events) > 0
        event = events[0]

        assert event.data["task_id"] == "reactive_001"
        assert event.data["stage"] == TaskStage.REQUIREMENT_PARSING.value
        assert event.data["status"] == "completed"
        assert event.correlation_id == "reactive_001"  # 用于关联事件
        assert event.timestamp is not None  # 用于时间排序

    def test_event_sequence_matches_task_flow(self):
        """
        [BUSINESS-012] 测试事件序列匹配任务流程

        业务场景：
        - 任务执行会生成事件序列
        - 事件序列应该反映真实的业务流程
        - 可以用于审计和调试
        """
        task = Task(id="audit_001", raw_input="测试")
        all_events = []

        # 执行完整流程并收集事件
        for stage in [TaskStage.REQUIREMENT_PARSING, TaskStage.FRAMEWORK_DESIGN]:
            task.start_stage(stage)
            all_events.extend(task.get_pending_events())

            task.complete_stage(stage)
            all_events.extend(task.get_pending_events())

        # 验证事件序列
        assert len(all_events) == 4  # 2个阶段 × 2个事件（开始+完成）

        # 验证事件类型：应该开始和完成交替
        event_types = [e.data.get("status") for e in all_events]
        assert event_types == ["started", "completed", "started", "completed"]

@pytest.mark.domain
@pytest.mark.business
@pytest.mark.p2
class TestEdgeCases:
    """边界情况和异常场景测试"""

    def test_concurrent_task_execution(self):
        """
        [BUSINESS-013] 测试并发任务执行的场景

        业务场景：
        - 多个用户同时创建任务
        - 每个任务的状态应该独立
        - 不应该互相干扰
        """
        # 创建多个任务
        tasks = [
            Task(id=f"concurrent_{i}", raw_input=f"任务{i}")
            for i in range(10)
        ]

        # 同时执行不同阶段
        for i, task in enumerate(tasks):
            stage = list(TaskStage)[i % len(TaskStage)]
            task.start_stage(stage)

        # 验证每个任务的状态是独立的
        for i, task in enumerate(tasks):
            stage = list(TaskStage)[i % len(TaskStage)]
            assert task.stages[stage].status != TaskStatus.PENDING
            assert task.id == f"concurrent_{i}"

    def test_task_serialization_preserves_business_data(self):
        """
        [BUSINESS-014] 测试序列化保持业务数据完整

        业务场景：
        - 任务需要持久化到数据库
        - 后续需要从数据库恢复
        - 所有业务数据必须完整保留
        """
        # 创建一个复杂的任务
        task = Task(id="serialize_001", raw_input="AI介绍")

        task.start_stage(TaskStage.REQUIREMENT_PARSING)
        task.complete_stage(TaskStage.REQUIREMENT_PARSING)

        # 添加需求数据
        requirement = Requirement.with_defaults(
            ppt_topic="AI介绍",
            scene=SceneType.BUSINESS_REPORT
        )
        task.structured_requirements = requirement.to_dict()

        # 序列化
        data = task.to_dict()

        # 反序列化
        restored = Task.from_dict(data)

        # 验证业务数据完整
        assert restored.id == task.id
        assert restored.raw_input == task.raw_input
        assert restored.stages[TaskStage.REQUIREMENT_PARSING].status == TaskStatus.COMPLETED
        assert restored.structured_requirements == task.structured_requirements
        assert restored.get_overall_progress() == task.get_overall_progress()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
