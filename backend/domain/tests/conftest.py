"""
Domain 层测试配置文件

提供 pytest fixtures 和测试工具
"""

import pytest
from datetime import datetime
from typing import Dict, Any

# ============================================================================
# 基础 Fixtures
# ============================================================================

@pytest.fixture
def current_time():
    """获取当前时间"""
    return datetime.now()

@pytest.fixture
def sample_task_id():
    """示例任务ID"""
    return "test_task_001"

@pytest.fixture
def sample_user_id():
    """示例用户ID"""
    return "test_user_001"

# ============================================================================
# Task Fixtures
# ============================================================================

@pytest.fixture
def sample_task(sample_task_id):
    """创建示例任务"""
    from domain.entities.task import Task
    return Task(
        id=sample_task_id,
        raw_input="生成一份AI技术介绍PPT"
    )

@pytest.fixture
def pending_task(sample_task_id):
    """创建待处理任务"""
    from domain.entities.task import Task
    return Task(
        id=sample_task_id,
        raw_input="生成PPT"
    )

@pytest.fixture
def in_progress_task(sample_task_id):
    """创建进行中的任务"""
    from domain.entities.task import Task, TaskStage
    task = Task(
        id=sample_task_id,
        raw_input="生成PPT"
    )
    task.start_stage(TaskStage.REQUIREMENT_PARSING)
    return task

@pytest.fixture
def completed_task(sample_task_id):
    """创建已完成的任务"""
    from domain.entities.task import Task, TaskStage
    task = Task(
        id=sample_task_id,
        raw_input="生成PPT"
    )
    for stage in TaskStage:
        task.start_stage(stage)
        task.complete_stage(stage)
    task.mark_completed()
    return task

# ============================================================================
# Requirement Fixtures
# ============================================================================

@pytest.fixture
def sample_requirement():
    """创建示例需求"""
    from domain.value_objects.requirement import Requirement, SceneType, TemplateType
    return Requirement(
        ppt_topic="AI技术介绍",
        page_num=10,
        scene=SceneType.BUSINESS_REPORT,
        template_type=TemplateType.BUSINESS,
        industry="科技",
        audience="技术人员",
        keywords=["AI", "人工智能", "机器学习"]
    )

@pytest.fixture
def minimal_requirement():
    """创建最小需求（仅必填字段）"""
    from domain.value_objects.requirement import Requirement
    return Requirement(
        ppt_topic="测试主题",
        page_num=5
    )

@pytest.fixture
def business_requirement():
    """创建商务汇报需求"""
    from domain.value_objects.requirement import Requirement, SceneType, TemplateType
    return Requirement.with_defaults(
        ppt_topic="2025年销售计划",
        scene=SceneType.BUSINESS_REPORT,
        page_num=15
    )

@pytest.fixture
def campus_defense_requirement():
    """创建校园答辩需求"""
    from domain.value_objects.requirement import Requirement, SceneType
    return Requirement.with_defaults(
        ppt_topic="AI在图像识别中的应用",
        scene=SceneType.CAMPUS_DEFENSE,
        page_num=20
    )

# ============================================================================
# Framework Fixtures
# ============================================================================

@pytest.fixture
def sample_framework():
    """创建示例框架"""
    from domain.value_objects.framework import PPTFramework, PageDefinition
    return PPTFramework(
        total_page=5,
        pages=[
            PageDefinition(
                page_no=1,
                title="封面",
                page_type="cover",
                core_content="AI技术介绍"
            ),
            PageDefinition(
                page_no=2,
                title="目录",
                page_type="directory",
                core_content="1. 背景 2. 核心技术 3. 应用"
            ),
            PageDefinition(
                page_no=3,
                title="背景介绍",
                page_type="content",
                core_content="AI发展历史"
            ),
            PageDefinition(
                page_no=4,
                title="核心技术",
                page_type="content",
                core_content="机器学习、深度学习"
            ),
            PageDefinition(
                page_no=5,
                title="应用场景",
                page_type="content",
                core_content="医疗、教育、金融"
            ),
        ]
    )

# ============================================================================
# 异常数据 Fixtures
# ============================================================================

@pytest.fixture
def invalid_requirements_list():
    """无效需求列表"""
    return [
        {
            "description": "空主题",
            "data": {"ppt_topic": "", "page_num": 10},
            "expected_errors": ["PPT主题不能为空"]
        },
        {
            "description": "页数为0",
            "data": {"ppt_topic": "测试", "page_num": 0},
            "expected_errors": ["页数必须大于0"]
        },
        {
            "description": "页数超过100",
            "data": {"ppt_topic": "测试", "page_num": 101},
            "expected_errors": ["页数不能超过100"]
        },
        {
            "description": "负数页数",
            "data": {"ppt_topic": "测试", "page_num": -1},
            "expected_errors": ["页数必须大于0"]
        },
    ]

@pytest.fixture
def boundary_page_numbers():
    """边界页数"""
    return [0, 1, 2, 10, 50, 99, 100, 101]

# ============================================================================
# 测试数据工厂
# ============================================================================

class TaskFactory:
    """任务测试数据工厂"""

    @staticmethod
    def create_task(task_id: str = "test_task_001", **kwargs) -> Any:
        """创建任务"""
        from domain.entities.task import Task
        return Task(
            id=task_id,
            raw_input=kwargs.get("raw_input", "生成PPT"),
            **{k: v for k, v in kwargs.items() if k != "raw_input"}
        )

    @staticmethod
    def create_with_stages(task_id: str = "test_task_001", stages: list = None) -> Any:
        """创建带有指定阶段的任务"""
        from domain.entities.task import Task, TaskStage
        task = Task(id=task_id, raw_input="生成PPT")

        if stages:
            for stage in stages:
                task.start_stage(stage)
                task.complete_stage(stage)

        return task

class RequirementFactory:
    """需求测试数据工厂"""

    @staticmethod
    def create_requirement(**kwargs) -> Any:
        """创建需求"""
        from domain.value_objects.requirement import Requirement
        return Requirement(
            ppt_topic=kwargs.get("ppt_topic", "测试主题"),
            page_num=kwargs.get("page_num", 10),
            **{k: v for k, v in kwargs.items() if k not in ["ppt_topic", "page_num"]}
        )

    @staticmethod
    def create_with_defaults(**kwargs) -> Any:
        """创建带默认值的需求"""
        from domain.value_objects.requirement import Requirement
        return Requirement.with_defaults(**kwargs)

@pytest.fixture
def task_factory():
    """任务工厂fixture"""
    return TaskFactory

@pytest.fixture
def requirement_factory():
    """需求工厂fixture"""
    return RequirementFactory

# ============================================================================
# pytest 配置
# ============================================================================

def pytest_configure(config):
    """pytest配置"""
    config.addinivalue_line(
        "markers",
        "domain: 标记domain层测试"
    )
    config.addinivalue_line(
        "markers",
        "unit: 单元测试"
    )
    config.addinivalue_line(
        "markers",
        "integration: 集成测试"
    )
    config.addinivalue_line(
        "markers",
        "p0: P0优先级测试（核心功能）"
    )
    config.addinivalue_line(
        "markers",
        "p1: P1优先级测试（重要功能）"
    )
    config.addinivalue_line(
        "markers",
        "p2: P2优先级测试（辅助功能）"
    )
