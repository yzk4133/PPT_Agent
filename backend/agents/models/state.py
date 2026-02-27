"""
LangChain 多Agent PPT 生成状态模型

本模块定义了 LangGraph 工作流中使用的状态结构。
状态在节点之间传递，并在流水线中累积结果。
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from typing_extensions import Required
from langchain_core.messages import BaseMessage


class InputState(TypedDict):
    """输入状态 - 仅包含用户输入"""
    user_input: Required[str]
    task_id: str


class RequirementState(TypedDict):
    """需求解析输出状态"""
    structured_requirements: Dict[str, Any]


class FrameworkState(TypedDict):
    """框架设计输出状态"""
    ppt_framework: Dict[str, Any]


class ResearchState(TypedDict):
    """研究输出状态"""
    research_results: List[Dict[str, Any]]


class ContentState(TypedDict):
    """内容生成输出状态"""
    content_materials: List[Dict[str, Any]]


class OutputState(TypedDict):
    """最终输出状态"""
    ppt_output: Dict[str, Any]


class PPTGenerationState(InputState, RequirementState, FrameworkState,
                          ResearchState, ContentState, OutputState):
    """
    PPT 生成工作流的主状态

    此状态在流水线中累积所有信息：
    - 来自用户的输入
    - 来自需求解析器的结构化需求
    - 来自框架设计器的 PPT 框架
    - 来自研究智能体的研究结果
    - 来自内容生成器的内容素材
    - 来自模板渲染器的最终 PPT 输出

    状态在 LangGraph 工作流的节点之间自动传递。
    """

    # 额外的元数据
    current_stage: str
    progress: int
    messages: List[BaseMessage]
    error: Optional[str]

    # 执行元数据
    start_time: str
    user_id: str
    session_id: str


# 状态管理辅助函数


def create_initial_state(
    user_input: str,
    task_id: str,
    user_id: str = "anonymous"
) -> PPTGenerationState:
    """
    创建 PPT 生成的初始状态

    Args:
        user_input: 用户的自然语言输入
        task_id: 唯一的任务标识符
        user_id: 用户标识符

    Returns:
        所有字段已初始化的初始 PPTGenerationState
    """
    from datetime import datetime

    return PPTGenerationState(
        # 输入状态
        user_input=user_input,
        task_id=task_id,

        # 需求状态（初始为空）
        structured_requirements={},

        # 框架状态（初始为空）
        ppt_framework={},

        # 研究状态（初始为空）
        research_results=[],

        # 内容状态（初始为空）
        content_materials=[],

        # 输出状态（初始为空）
        ppt_output={},

        # 元数据
        current_stage="init",
        progress=0,
        messages=[],
        error=None,
        start_time=datetime.now().isoformat(),
        user_id=user_id,
        session_id=task_id,
    )


def update_state_progress(
    state: PPTGenerationState,
    stage: str,
    progress: int
) -> PPTGenerationState:
    """
    使用新的进度信息更新状态

    Args:
        state: 当前状态
        stage: 当前阶段名称
        progress: 进度百分比 (0-100)

    Returns:
        更新后的状态
    """
    state["current_stage"] = stage
    state["progress"] = max(0, min(100, progress))
    return state


def add_message_to_state(
    state: PPTGenerationState,
    message: BaseMessage
) -> PPTGenerationState:
    """
    向状态历史添加消息

    Args:
        state: 当前状态
        message: 要添加的消息

    Returns:
        更新后的状态
    """
    if "messages" not in state:
        state["messages"] = []
    state["messages"].append(message)
    return state


def set_state_error(
    state: PPTGenerationState,
    error: str
) -> PPTGenerationState:
    """
    在状态中设置错误

    Args:
        state: 当前状态
        error: 错误消息

    Returns:
        已设置错误的更新后状态
    """
    state["error"] = error
    return state


def get_requirement_field(
    state: PPTGenerationState,
    field: str,
    default=None
) -> Any:
    """
    安全地从 structured_requirements 获取字段

    Args:
        state: 当前状态
        field: 要检索的字段名
        default: 如果字段未找到时的默认值

    Returns:
        字段值或默认值
    """
    return state.get("structured_requirements", {}).get(field, default)


def get_framework_pages(
    state: PPTGenerationState
) -> List[Dict[str, Any]]:
    """
    从 PPT 框架获取页面列表

    Args:
        state: 当前状态

    Returns:
        页面定义列表
    """
    framework = state.get("ppt_framework", {})
    return framework.get("ppt_framework", [])


def get_total_pages(state: PPTGenerationState) -> int:
    """
    从框架获取总页数

    Args:
        state: 当前状态

    Returns:
        总页数
    """
    framework = state.get("ppt_framework", {})
    return framework.get("total_page", 0)


def needs_research(state: PPTGenerationState) -> bool:
    """
    根据需求检查是否需要研究

    Args:
        state: 当前状态

    Returns:
        如果需要研究则返回 True
    """
    return get_requirement_field(state, "need_research", False)


def get_research_pages(state: PPTGenerationState) -> List[int]:
    """
    获取需要研究的页面索引

    Args:
        state: 当前状态

    Returns:
        需要研究的页码列表
    """
    framework = state.get("ppt_framework", {})
    return framework.get("research_page_indices", [])


def validate_state_for_stage(
    state: PPTGenerationState,
    stage: str
) -> tuple[bool, List[str]]:
    """
    验证状态是否包含给定阶段所需的必要数据

    Args:
        state: 当前状态
        stage: 要验证的阶段名称

    Returns:
        (是否有效, 错误消息列表) 元组
    """
    errors = []

    if stage == "framework_design":
        if not state.get("structured_requirements"):
            errors.append("框架设计缺少 structured_requirements")

    elif stage == "research":
        if not state.get("ppt_framework"):
            errors.append("研究缺少 ppt_framework")
        if not needs_research(state):
            errors.append("根据需求不需要研究")

    elif stage == "content_generation":
        if not state.get("ppt_framework"):
            errors.append("内容生成缺少 ppt_framework")

    elif stage == "template_rendering":
        if not state.get("ppt_framework"):
            errors.append("渲染缺少 ppt_framework")
        if not state.get("content_materials"):
            errors.append("渲染缺少 content_materials")

    return len(errors) == 0, errors


if __name__ == "__main__":
    # 测试状态创建
    test_state = create_initial_state(
        user_input="创建一个关于 AI 的 PPT",
        task_id="test_001"
    )

    print("初始状态已创建：")
    print(f"  任务 ID: {test_state['task_id']}")
    print(f"  用户输入: {test_state['user_input']}")
    print(f"  阶段: {test_state['current_stage']}")
    print(f"  进度: {test_state['progress']}%")

    # 测试状态更新
    test_state = update_state_progress(test_state, "requirement_parsing", 15)
    test_state["structured_requirements"] = {
        "ppt_topic": "AI 简介",
        "page_num": 10,
        "need_research": True
    }

    print("\n更新后的状态：")
    print(f"  阶段: {test_state['current_stage']}")
    print(f"  进度: {test_state['progress']}%")
    print(f"  主题: {test_state['structured_requirements']['ppt_topic']}")
    print(f"  需要研究: {needs_research(test_state)}")

    # 测试验证
    is_valid, errors = validate_state_for_stage(test_state, "framework_design")
    print(f"\n框架设计验证: {is_valid}")
    if not is_valid:
        print(f"  错误: {errors}")
