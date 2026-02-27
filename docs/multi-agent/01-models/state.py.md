# state.py - 状态模型详解

## 📋 文件概述

`backend/agents_langchain/models/state.py` 定义了 LangGraph 工作流中使用的状态结构。

## 🎯 主要功能

1. 定义工作流中的各种状态类型
2. 提供状态初始化和更新函数
3. 提供状态验证和辅助访问函数

## 📦 类定义

### InputState

**输入状态 - 仅包含用户输入**

```python
class InputState(TypedDict):
    user_input: Required[str]  # 用户的自然语言输入
    task_id: str              # 任务唯一标识符
```

### RequirementState

**需求解析输出状态**

```python
class RequirementState(TypedDict):
    structured_requirements: Dict[str, Any]  # 结构化的需求字典
```

### FrameworkState

**框架设计输出状态**

```python
class FrameworkState(TypedDict):
    ppt_framework: Dict[str, Any]  # PPT 框架字典
```

### ResearchState

**研究输出状态**

```python
class ResearchState(TypedDict):
    research_results: List[Dict[str, Any]]  # 研究结果列表
```

### ContentState

**内容生成输出状态**

```python
class ContentState(TypedDict):
    content_materials: List[Dict[str, Any]]  # 内容素材列表
```

### OutputState

**最终输出状态**

```python
class OutputState(TypedDict):
    ppt_output: Dict[str, Any]  # 最终输出字典
```

### PPTGenerationState

**主状态类 - 继承所有子状态**

```python
class PPTGenerationState(
    InputState, RequirementState, FrameworkState,
    ResearchState, ContentState, OutputState
):
    # 额外的元数据
    current_stage: str              # 当前阶段名称
    progress: int                   # 进度百分比 (0-100)
    messages: List[BaseMessage]     # 消息历史
    error: Optional[str]            # 错误信息（如果有）

    # 执行元数据
    start_time: str                 # 开始时间 (ISO 格式)
    user_id: str                    # 用户 ID
    session_id: str                 # 会话 ID
```

## 🔧 辅助函数

### create_initial_state()

**创建 PPT 生成的初始状态**

```python
def create_initial_state(
    user_input: str,
    task_id: str,
    user_id: str = "anonymous"
) -> PPTGenerationState
```

**参数**:
- `user_input`: 用户的自然语言输入
- `task_id`: 唯一的任务标识符
- `user_id`: 用户标识符

**返回**: 所有字段已初始化的初始 PPTGenerationState

**边界情况**:
- 自动生成 ISO 格式的时间戳
- 如果未提供 `user_id`，使用 "anonymous"

### update_state_progress()

**使用新的进度信息更新状态**

```python
def update_state_progress(
    state: PPTGenerationState,
    stage: str,
    progress: int
) -> PPTGenerationState
```

**参数**:
- `state`: 当前状态
- `stage`: 当前阶段名称
- `progress`: 进度百分比 (0-100)

**边界情况**:
- 自动将 progress 限制在 0-100 范围内: `max(0, min(100, progress))`

### add_message_to_state()

**向状态历史添加消息**

```python
def add_message_to_state(
    state: PPTGenerationState,
    message: BaseMessage
) -> PPTGenerationState
```

**边界情况**:
- 如果 "messages" 键不存在，自动创建空列表

### set_state_error()

**在状态中设置错误**

```python
def set_state_error(
    state: PPTGenerationState,
    error: str
) -> PPTGenerationState
```

### get_requirement_field()

**安全地从 structured_requirements 获取字段**

```python
def get_requirement_field(
    state: PPTGenerationState,
    field: str,
    default=None
) -> Any
```

**边界情况**:
- 使用嵌套的 `.get()` 方法，避免 KeyError
- 支持自定义默认值

### get_framework_pages()

**从 PPT 框架获取页面列表**

```python
def get_framework_pages(
    state: PPTGenerationState
) -> List[Dict[str, Any]]
```

**边界情况**:
- 框架不存在时返回空列表

### get_total_pages()

**从框架获取总页数**

```python
def get_total_pages(
    state: PPTGenerationState
) -> int
```

**边界情况**:
- 框架不存在时返回 0

### needs_research()

**根据需求检查是否需要研究**

```python
def needs_research(
    state: PPTGenerationState
) -> bool
```

**边界情况**:
- 默认返回 False

### get_research_pages()

**获取需要研究的页面索引**

```python
def get_research_pages(
    state: PPTGenerationState
) -> List[int]
```

**边界情况**:
- 框架不存在时返回空列表

### validate_state_for_stage()

**验证状态是否包含给定阶段所需的必要数据**

```python
def validate_state_for_stage(
    state: PPTGenerationState,
    stage: str
) -> tuple[bool, List[str]]
```

**验证规则**:

| 阶段 | 必需字段 |
|------|---------|
| `framework_design` | `structured_requirements` |
| `research` | `ppt_framework`, `need_research=True` |
| `content_generation` | `ppt_framework` |
| `template_rendering` | `ppt_framework`, `content_materials` |

**返回**: `(是否有效, 错误消息列表)` 元组

## 📊 进度映射

| 阶段 | 进度范围 |
|------|---------|
| `init` | 0% |
| `requirement_parsing` | 15% |
| `framework_design` | 30% |
| `research` | 30% → 50% |
| `content_generation` | 50% → 80% |
| `template_rendering` | 100% |

## 🔐 错误处理

所有辅助函数都采用了防御性编程：
- 使用 `.get()` 而不是直接访问
- 提供合理的默认值
- 限制数值范围

## 📝 使用示例

```python
# 创建初始状态
state = create_initial_state(
    user_input="创建一个关于 AI 的 PPT",
    task_id="task_001",
    user_id="user123"
)

# 更新进度
state = update_state_progress(state, "framework_design", 30)

# 添加字段
state["structured_requirements"] = {
    "ppt_topic": "AI 简介",
    "page_num": 10
}

# 验证状态
is_valid, errors = validate_state_for_stage(state, "research")
if not is_valid:
    print(f"验证失败: {errors}")
```

## 🔗 相关文件

- [`framework.py`](framework.py.md): 框架模型定义
- [`../coordinator/master_graph.py`](../02-coordinator/master_graph.py.md): 使用这些状态的主工作流
