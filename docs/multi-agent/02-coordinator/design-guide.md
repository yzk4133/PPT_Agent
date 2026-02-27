# Coordinator 层设计指南

> 本文档说明 `backend/agents_langchain/coordinator/` 目录的设计思路和文件组织方式。

---

## 目录

1. [Coordinator 层概述](#coordinator-层概述)
2. [文件结构](#文件结构)
3. [各文件职责](#各文件职责)
4. [为什么需要这样组织](#为什么需要这样组织)
5. [协作关系](#协作关系)
6. [与 Models 层的关系](#与-models-层的关系)

---

## Coordinator 层概述

Coordinator 层是 LangChain 多 Agent 系统的**指挥协调层**，负责：

- 📋 定义和执行工作流
- ⚡ 管理并行任务执行
- 📊 追踪实时进度
- ✏️ 处理用户修订请求

**核心思想**：将"指挥中心"、"执行器"、"监控器"、"编辑器"分离，各司其职。

---

## 文件结构

```
coordinator/
├── master_graph.py       # 主工作流图 - "指挥中心"
├── page_pipeline.py      # 页面流水线 - "并行执行器"
├── progress_tracker.py   # 进度追踪 - "进度显示"
├── revision_handler.py   # 修订处理 - "修改专家"
└── __init__.py          # 模块导出
```

---

## 各文件职责

### 1. master_graph.py - 主工作流图（指挥中心）

**作用**：定义整个 PPT 生成的工作流程，协调所有 agent 节点

```python
# 核心职责：
- 使用 LangGraph StateGraph 定义工作流图
- 添加节点：requirement_parser → framework_designer → research → content_generation → template_renderer
- 添加条件边：根据状态决定下一步（是否需要研究、是否需要改进）
- 执行工作流并管理状态流转
```

**为什么需要**：
- 如果没有它 → 各 agent 各自为战，没有统一调度
- 就像：没有指挥的乐团，每个人都在演奏自己的节奏

**形象比喻**：音乐指挥家 → 决定谁先演奏、谁后演奏、何时合唱

**工作流示意**：

```
entry → requirement_parser → framework_designer
        → [need_research?]
            → YES: research → content_generation
            → NO: content_generation
        → [quality_check?] (可选)
            → below_threshold: refine → quality_check (循环)
            → ok: template_renderer
        → END
```

---

### 2. page_pipeline.py - 页面流水线（并行执行器）

**作用**：处理页面级任务的并行执行

```python
# 核心职责：
- 使用 asyncio.Semaphore 控制并发数
- 并行执行多个页面（研究、内容生成）
- 重试失败的页面
- 进度跟踪和回调
```

**为什么需要**：
- 如果没有它 → 100页 PPT 需要串行处理，耗时极长
- 性能提升：30%-60%（相比串行执行）

**形象比喻**：工厂流水线 → 多个工人同时工作，而不是一个人干完所有活

**执行对比**：

```python
# 串行执行（慢）
[页面1] → [页面2] → [页面3] → ... → [页面100]
耗时：100页 × 2秒/页 = 200秒

# 并行执行（快）
[页面1,2,3] → [页面4,5,6] → ...  (并发度=3)
耗时：⌈100/3⌉ × 2秒/页 ≈ 68秒  (提升66%)
```

---

### 3. progress_tracker.py - 进度追踪（进度显示）

**作用**：实时跟踪和报告工作流进度

```python
# 核心职责：
- 记录每个阶段的进度百分比
- 触发进度回调（通知前端）
- 记录阶段耗时
- 错误处理和通知
```

**为什么需要**：
- 如果没有它 → 用户不知道任务进行到哪了，只能干等
- 用户体验：实时反馈比黑盒处理好得多

**形象比喻**：外卖订单状态 → "已下单" → "制作中" → "配送中" → "已送达"

**进度映射**：

```
阶段                    进度范围
─────────────────────────────────
requirement_parser      0%  → 10%
framework_designer     10%  → 30%
research               30%  → 50%
content_generation     50%  → 75%
quality_check          75%  → 85%
template_renderer      85%  → 100%
```

---

### 4. revision_handler.py - 修订处理（修改专家）

**作用**：处理用户对已生成 PPT 的修改请求

```python
# 核心职责：
- 解析修订请求（content/style/structure/research）
- 应用修改到特定页面或全部页面
- 跟踪修订历史
```

**为什么需要**：
- 如果没有它 → 用户不满意只能从头生成，无法局部修改
- 场景：用户只想改第3页的内容，不需要重新生成整个 PPT

**形象比喻**：文档编辑模式 → 可以修改特定段落，而不需要重写整篇文章

**修订类型**：

| 类型 | 说明 | 示例 |
|------|------|------|
| content | 内容修订 | "把第3页的内容改得更简洁" |
| style | 风格修订 | "把整体风格改得更正式" |
| structure | 结构修订 | "在第5页后增加一页" |
| research | 研究修订 | "为第7页补充更多资料" |

---

## 为什么需要这样组织？

### 1. 职责分离（Single Responsibility）

| 文件 | 唯一职责 | 变更影响 |
|------|----------|----------|
| master_graph.py | 定义工作流结构 | 工作流程改变 |
| page_pipeline.py | 处理并行执行 | 并发策略改变 |
| progress_tracker.py | 追踪进度 | 进度报告方式改变 |
| revision_handler.py | 处理修改 | 修订逻辑改变 |

**好处**：
- ✅ 每个文件可以独立修改
- ✅ 每个文件可以独立测试
- ✅ 每个文件可以单独复用

---

### 2. 依赖方向清晰

```
            ┌─────────────┐
            │   models    │  ← 最底层，被所有人依赖
            └─────────────┘
                   ↑
                   │
            ┌─────────────┐
            │ coordinator │  ← 中间层，依赖 models
            └─────────────┘
                   ↑
                   │
            ┌─────────────┐
            │    agents   │  ← 最上层，使用 coordinator
            └─────────────┘
```

**原则**：
- 高层模块可以依赖低层模块
- 低层模块不应该依赖高层模块
- 依赖方向要单向，避免循环依赖

---

### 3. 易于扩展

需要添加新功能时：

| 需求 | 修改文件 | 影响范围 |
|------|----------|----------|
| 添加新阶段 | master_graph.py | 仅工作流 |
| 改进并行策略 | page_pipeline.py | 仅性能 |
| 增强进度报告 | progress_tracker.py | 仅显示 |
| 新增修订类型 | revision_handler.py | 仅修改 |

**好处**：修改局部化，不会影响其他部分

---

## 协作关系

### 文件间协作图

```
                    ┌──────────────────────────────────────┐
                    │         master_graph.py              │
                    │    (主工作流 - 指挥中心)              │
                    │                                      │
                    │  - 定义工作流图                       │
                    │  - 协调所有 agent                    │
                    │  - 使用 page_pipeline 处理并行       │
                    │  - 使用 progress_tracker 报告进度    │
                    │  - 使用 revision_handler 处理修改    │
                    └──────────────────────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
         ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐
         │ page_pipeline.py │  │progress_     │  │revision_handler  │
         │                  │  │tracker.py    │  │                  │
         │ - 并行执行页面    │  │              │  │ - 处理修订请求    │
         │ - 控制并发数      │  │ - 追踪进度   │  │ - 修改内容/风格  │
         │ - 重试失败页面    │  │ - 触发回调   │  │ - 记录修订历史    │
         │ - 进度回调        │  │ - 记录耗时   │  │                  │
         └──────────────────┘  └──────────────┘  └──────────────────┘
```

### 调用关系示例

```python
# master_graph.py 如何使用其他文件

class MasterGraph:
    async def generate(self, user_input, task_id, user_id):
        # 1. 创建进度跟踪器
        tracker = create_progress_tracker(
            state=initial_state,
            on_progress=lambda update: print(f"Progress: {update.progress}%")
        )

        # 2. 执行工作流（使用 page_pipeline）
        for stage in stages:
            tracker.update_stage(stage, progress, f"Processing {stage}")

            if stage == "research":
                # 使用 page_pipeline 并行执行研究
                await self.page_pipeline.execute_research_pipeline(state, research_agent)

            elif stage == "content_generation":
                # 使用 page_pipeline 并行生成内容
                await self.page_pipeline.execute_content_pipeline(state, content_agent)

        # 3. 处理修订（如果需要）
        if needs_revision:
            await self.revision_handler.handle_revision_request(state, revision_request)
```

---

## 与 Models 层的关系

### 依赖关系

| Coordinator 文件 | 依赖的 Models |
|------------------|---------------|
| master_graph.py | `state.py`（状态定义） |
| page_pipeline.py | `state.py` + `framework.py`（状态和框架） |
| progress_tracker.py | `state.py`（状态） |
| revision_handler.py | `state.py`（状态） |

### 数据流向

```
┌─────────────────────────────────────────────────────────┐
│                      Models 层                          │
│  ┌──────────────┐         ┌──────────────┐             │
│  │  state.py    │────────▶│ framework.py │             │
│  │ (工作流状态)  │         │  (PPT结构)   │             │
│  └──────────────┘         └──────────────┘             │
└─────────────────────────────────────────────────────────┘
                         │ 提供数据结构
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   Coordinator 层                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │master_graph  │  │page_pipeline │  │progress_     │ │
│  │              │  │              │  │tracker       │ │
│  │使用状态流转   │  │使用框架定义  │  │使用状态更新   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 核心区别

```
models/（数据定义）──────→ coordinator/（逻辑控制）
     ↓                           ↓
 "是什么"                    "怎么做"
 "数据结构"                  "工作流程"
 "静态定义"                  "动态执行"
```

---

## 总结

### 文件职责速查表

| 文件 | 核心职责 | 输入 | 输出 |
|------|----------|------|------|
| master_graph.py | 定义工作流 | user_input | final_state |
| page_pipeline.py | 并行执行 | pages + executor | results |
| progress_tracker.py | 追踪进度 | stage + progress | callbacks |
| revision_handler.py | 处理修改 | state + request | updated_state |

### 设计原则

1. **单一职责**：每个文件只做一件事
2. **依赖倒置**：高层依赖低层，低层不依赖高层
3. **开闭原则**：对扩展开放，对修改封闭
4. **接口隔离**：提供清晰的公共接口

### 形象总结

| 文件 | 形象比喻 | 一句话描述 |
|------|----------|-----------|
| master_graph.py | 乐团指挥 | 协调所有 agent 按流程执行 |
| page_pipeline.py | 流水线工人 | 并行处理多个页面任务 |
| progress_tracker.py | 进度条 | 实时显示工作进度 |
| revision_handler.py | 编辑工具 | 处理用户的修改请求 |

---

## 相关文档

- [实施指南](./implementation-guide.md) - 如何书写这些文件
- [ProgressTracker 文档](./progress_tracker.py.md) - 进度追踪详解
- [RevisionHandler 文档](./revision_handler.py.md) - 修订处理详解
- [Models 层设计指南](../01-models/design-guide.md) - 数据模型设计
