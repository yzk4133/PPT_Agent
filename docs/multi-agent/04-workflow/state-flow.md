# 状态流转详解

## 📋 概述

本文档详细说明 LangGraph 工作流中的状态流转机制。

## 🔄 状态传递机制

### LangGraph 状态传递

LangGraph 使用自动状态传递机制：

1. **状态累积**: 每个节点返回更新后的状态
2. **自动合并**: LangGraph 自动合并更新
3. **类型安全**: 使用 TypedDict 确保类型正确

### 状态类层次结构

```
PPTGenerationState
├── InputState          # 初始输入
├── RequirementState   # 需求解析后填充
├── FrameworkState     # 框架设计后填充
├── ResearchState      # 研究后填充
├── ContentState       # 内容生成后填充
└── OutputState        # 渲染后填充
```

## 📊 状态变化时间线

```
初始状态 (0%)
├── user_input: "..."
├── task_id: "..."
├── structured_requirements: {}
├── ppt_framework: {}
├── research_results: []
├── content_materials: []
└── ppt_output: {}

         │
         ▼

需求解析完成 (15%)
├── structured_requirements: {...}
└── current_stage: "requirement_parsing"

         │
         ▼

框架设计完成 (30%)
├── ppt_framework: {...}
└── current_stage: "framework_design"

         │
         ▼
    ┌────┴────┐
    │ need_   │
    │ research?│
    └────┬────┘
    YES │    │ NO
    ▼    │    │
研究完成 │    │
(30%→50%) │   │
├── research_results: [...] │
└── current_stage: "research" │
         │    │
         └────┬┘
              ▼
    内容生成完成 (80%)
    ├── content_materials: [...]
    └── current_stage: "content_generation"

              │
              ▼
    渲染完成 (100%)
    ├── ppt_output: {...}
    └── current_stage: "template_renderer"
```

## 🔗 节点间通信

### 直接通信

节点之间通过状态直接通信：

```python
# requirement_agent 写入
state["structured_requirements"] = {...}

# framework_agent 读取
requirement = state.get("structured_requirements")
```

### 状态验证

每个节点执行前验证前置条件：

```python
# 验证函数
def validate_state_for_stage(state, stage) -> tuple[bool, List[str]]

# 在节点中使用
is_valid, errors = validate_state_for_stage(state, "research")
if not is_valid:
    raise ValueError(f"State validation failed: {errors}")
```

## 📝 状态更新模式

### 1. 完整替换

```python
# 直接设置整个字段
state["structured_requirements"] = {...}
```

### 2. 部分更新

```python
# 使用辅助函数更新
update_state_progress(state, "research", 45)
```

### 3. 追加

```python
# 追加到列表
state["messages"].append(message)
```

## 🔐 状态保护

### 只读字段

某些字段在特定阶段后不应被修改：

| 字段 | 写入节点 | 只读后 |
|------|---------|--------|
| `user_input` | 初始 | 始终只读 |
| `structured_requirements` | requirement_agent | framework_design 后 |
| `ppt_framework` | framework_agent | content_generation 后 |
| `research_results` | research_agent | content_generation 后 |
| `content_materials` | content_agent | rendering 后 |
| `ppt_output` | renderer_agent | - |

### 状态验证规则

```python
# 禁止修改只读字段的验证逻辑（可选实现）
def validate_state_immutability(
    old_state: PPTGenerationState,
    new_state: PPTGenerationState,
    current_stage: str
) -> bool:
    # 检查只读字段是否被修改
    ...
```

## 🔄 状态回滚

### 错误处理中的状态

当节点失败时，状态不会自动回滚：

```python
try:
    # 执行节点逻辑
    result = await agent.process(state)
    state.update(result)
except Exception as e:
    # 设置错误状态
    state["error"] = str(e)
    state["current_stage"] = "failed"
    return state  # 返回错误状态，不回滚
```

## 📊 状态监控

### 进度跟踪

每个节点完成后更新进度：

```python
update_state_progress(state, stage_name, progress_value)
```

### 阶段名称

| 阶段 | 名称 |
|------|------|
| 初始 | `init` |
| 需求解析 | `requirement_parsing` |
| 框架设计 | `framework_design` |
| 研究 | `research` |
| 内容生成 | `content_generation` |
| 渲染 | `template_renderer` |
| 失败 | `failed` |

## 🔗 相关文档

- [error-handling.md](error-handling.md): 错误处理机制
- [performance.md](performance.md): 性能优化
- [../01-models/state.py.md](../01-models/state.py.md): 状态模型定义
