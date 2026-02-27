# master_graph.py 详解

> 主工作流图 - 基于 LangGraph 的多 Agent 协调器

---

## 目录

1. [概述](#概述)
2. [LangGraph 基础](#langgraph-基础)
3. [MasterGraph 类详解](#mastergraph-类详解)
4. [工作流构建](#工作流构建)
5. [条件判断](#条件判断)
6. [执行模式](#执行模式)
7. [使用示例](#使用示例)
8. [错误处理](#错误处理)
9. [最佳实践](#最佳实践)
10. [常见问题](#常见问题)

---

## 概述

### 作用

`master_graph.py` 实现基于 LangGraph 的主工作流图，负责编排所有 Agent 的执行，是整个系统的指挥中心。

### 为什么需要

- ❌ **没有它**：各 Agent 各自为战，没有统一调度
- ✅ **有它**：定义清晰的工作流程，协调所有 Agent 协作

### 核心功能

| 功能 | 说明 |
|------|------|
| **工作流定义** | 使用 LangGraph StateGraph 定义工作流 |
| **Agent 编排** | 管理所有核心 Agent 的生命周期 |
| **条件路由** | 根据状态动态决定执行路径 |
| **进度跟踪** | 实时报告工作流进度 |
| **错误处理** | 捕获并处理执行过程中的异常 |

---

## LangGraph 基础

### 什么是 LangGraph？

LangGraph 是 LangChain 的一个库，用于构建有状态的多角色应用程序（即 agent 工作流）。

### 核心概念

#### 1. StateGraph（状态图）

定义工作流的结构和状态流转：

```python
from langgraph.graph import StateGraph, END

# 创建状态图
builder = StateGraph(PPTGenerationState)

# 添加节点
builder.add_node("node1", node1_function)
builder.add_node("node2", node2_function)

# 添加边（连接节点）
builder.add_edge("node1", "node2")

# 添加条件边（分支）
builder.add_conditional_edges(
    "node2",
    condition_function,  # 判断函数
    {"node3": "node3", "end": END}  # 路由映射
)

# 编译图
graph = builder.compile()

# 执行
result = await graph.ainvoke(initial_state)
```

#### 2. Node（节点）

节点是工作流中的处理单元，接收状态并返回更新后的状态：

```python
async def my_node(state: PPTGenerationState) -> PPTGenerationState:
    """节点函数"""
    # 处理状态
    state["some_field"] = "new_value"
    return state

# 添加到图
builder.add_node("my_node", my_node)
```

#### 3. Edge（边）

边定义节点之间的连接关系：

```python
# 普通边：无条件执行
builder.add_edge("node1", "node2")

# 条件边：根据状态决定下一步
builder.add_conditional_edges(
    "node2",
    lambda state: "node3" if state["condition"] else "end",
    {
        "node3": "node3",
        "end": END
    }
)
```

---

## MasterGraph 类详解

### 初始化

```python
class MasterGraph:
    def __init__(
        self,
        requirement_agent: Optional[RequirementParserAgent] = None,
        framework_agent: Optional[FrameworkDesignerAgent] = None,
        research_agent: Optional[ResearchAgent] = None,
        content_agent: Optional[ContentMaterialAgent] = None,
        renderer_agent: Optional[TemplateRendererAgent] = None,
        page_pipeline: Optional[PagePipeline] = None,
        model: Optional[ChatOpenAI] = None,
        # Quality control parameters
        enable_quality_checks: bool = True,
        quality_threshold: float = 0.8,
        max_refinements: int = 3,
    ):
        """
        初始化主工作流图

        Args:
            requirement_agent: 需求解析智能体
            framework_agent: 框架设计智能体
            research_agent: 研究智能体
            content_agent: 内容生成智能体
            renderer_agent: 渲染智能体
            page_pipeline: 页面流水线
            model: 共享的LLM模型
            enable_quality_checks: 是否启用质量检查
            quality_threshold: 质量阈值（0.0-1.0）
            max_refinements: 最大改进次数
        """
```

**初始化流程**：

```python
def __init__(self, ...):
    # 1. 保存质量控制参数
    self.enable_quality_checks = enable_quality_checks
    self.quality_threshold = quality_threshold
    self.max_refinements = max_refinements

    # 2. 创建或使用提供的模型
    self.model = model or self._create_default_model()

    # 3. 创建或使用提供的智能体
    self.requirement_agent = requirement_agent or create_requirement_parser(self.model)
    self.framework_agent = framework_agent or create_framework_designer(self.model)
    self.research_agent = research_agent or create_research_agent(self.model)
    self.content_agent = content_agent or create_content_agent(self.model)
    self.renderer_agent = renderer_agent or create_renderer_agent(self.model)

    # 4. 创建页面流水线
    self.page_pipeline = page_pipeline or create_page_pipeline(
        max_concurrency=int(os.getenv("PAGE_PIPELINE_CONCURRENCY", "3"))
    )

    # 5. 构建状态图
    self.graph = self._build_graph()

    logger.info("[MasterGraph] Initialized with all agents")
```

---

### 核心方法

#### 1. _create_default_model()

**创建默认 LLM 模型**

```python
def _create_default_model(self) -> ChatOpenAI:
    """创建默认LLM模型"""
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL")
    model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")

    if not api_key:
        logger.warning("[MasterGraph] No API key found, using mock mode")
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key="sk-mock-key",
            temperature=0.0,
        )

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0.0,
    )
```

**环境变量配置**：

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | - |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | - |
| `OPENAI_BASE_URL` | API 基础 URL | - |
| `DEEPSEEK_BASE_URL` | DeepSeek 基础 URL | - |
| `LLM_MODEL` | 模型名称 | `gpt-4o-mini` |
| `PAGE_PIPELINE_CONCURRENCY` | 页面流水线并发数 | `3` |

---

#### 2. _build_graph()

**构建状态图（核心方法）**

```python
def _build_graph(self) -> StateGraph:
    """
    构建状态图

    Returns:
        StateGraph 实例
    """
    # 1. 创建状态图
    builder = StateGraph(PPTGenerationState)

    # 2. 添加节点
    builder.add_node("requirement_parser", self.requirement_agent.run_node)
    builder.add_node("framework_designer", self.framework_agent.run_node)
    builder.add_node("research", self.research_agent.run_node)
    builder.add_node("content_generation", self.content_agent.run_node)
    builder.add_node("template_renderer", self.renderer_agent.run_node)

    # 3. 添加质量控制节点（如果启用）
    if self.enable_quality_checks:
        from ..core.quality.nodes import check_content_quality, refine_content

        builder.add_node("quality_check", quality_check_with_threshold)
        builder.add_node("refine_content", refine_content_with_model)

    # 4. 设置入口点
    builder.set_entry_point("requirement_parser")

    # 5. 添加边 - 需求解析 → 框架设计
    builder.add_edge("requirement_parser", "framework_designer")

    # 6. 添加条件边 - 框架设计 → [研究 or 内容生成]
    builder.add_conditional_edges(
        "framework_designer",
        self._should_research,
        {"research": "research", "content": "content_generation"},
    )

    # 7. 添加边 - 研究 → 内容生成
    builder.add_edge("research", "content_generation")

    # 8. 添加边 - 内容生成 → (质量检查 or 直接渲染)
    if self.enable_quality_checks:
        builder.add_edge("content_generation", "quality_check")

        # 质量检查 → (改进 or 渲染)
        builder.add_conditional_edges(
            "quality_check",
            self._should_refine,
            {"refine": "refine_content", "proceed": "template_renderer"},
        )

        # 改进 → 质量检查（循环）
        builder.add_edge("refine_content", "quality_check")
    else:
        # 跳过质量检查，直接渲染
        builder.add_edge("content_generation", "template_renderer")

    # 9. 添加边 - 模板渲染 → END
    builder.add_edge("template_renderer", END)

    # 10. 编译图
    graph = builder.compile()

    logger.info("[MasterGraph] State graph built successfully")
    return graph
```

**工作流图示**：

```
┌─────────────────────────────────────────────────────────────┐
│                     工作流结构                                │
└─────────────────────────────────────────────────────────────┘

entry_point
    │
    ▼
┌───────────────────┐
│ requirement_parser│  需求解析
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│framework_designer │  框架设计
└─────────┬─────────┘
          │
          ▼
    ┌─────────────┐
    │ _should_    │
    │ research?   │  条件判断
    └──┬──────┬───┘
       │YES   │NO
       │      │
       ▼      ▼
    ┌──────┐  │
    │research  │
    └───┬───┘  │
        │      │
        └──┬───┘
           ▼
┌───────────────────┐
│content_generation │  内容生成
└─────────┬─────────┘
          │
          ▼
    ┌─────────────┐
    │ enable_     │
    │ quality_    │  是否启用质量控制？
    │ checks?     │
    └──┬──────┬───┘
       │YES   │NO
       │      │
       ▼      │
┌──────────────┐│
│quality_check ││
└──────┬───────┘│
       │        │
       ▼        │
    ┌─────────┐ │
    │_should_ │ │
    │refine?  │ │  质量判断
    └┬────┬───┘│
     │YES │NO  │
     │    │    │
     ▼    │    │
  ┌──────┐│    │
  │refine ││    │
  └───┬──┘│    │
      └──┼────┘
         │
         ▼
┌───────────────────┐
│template_renderer  │  模板渲染
└─────────┬─────────┘
          │
          ▼
         END
```

---

## 工作流构建

### 节点定义

每个节点对应一个 Agent 的 `run_node` 方法：

```python
# 节点函数签名
async def run_node(self, state: PPTGenerationState) -> PPTGenerationState:
    """
    节点函数

    Args:
        state: 当前状态

    Returns:
        更新后的状态

    工作流程：
    1. 从状态中读取输入
    2. 执行处理逻辑
    3. 更新状态中的相应字段
    4. 返回状态
    """
```

### 边的类型

#### 1. 普通边（Edge）

无条件连接两个节点：

```python
# 执行完 node1 后，总是执行 node2
builder.add_edge("node1", "node2")
```

#### 2. 条件边（ConditionalEdge）

根据状态决定下一步：

```python
builder.add_conditional_edges(
    "node1",
    condition_function,        # 判断函数
    {
        "node2": "node2",      # 返回 "node2" 时执行 node2
        "node3": "node3",      # 返回 "node3" 时执行 node3
        END: END,              # 返回 "end" 时结束
    }
)
```

**条件函数签名**：

```python
def condition_function(state: PPTGenerationState) -> str:
    """
    条件判断函数

    Args:
        state: 当前状态

    Returns:
        下一个节点的名称（必须在路由映射中）
    """
    if some_condition:
        return "node2"
    else:
        return "node3"
```

---

## 条件判断

### _should_research()

**判断是否需要研究**

```python
def _should_research(
    self,
    state: PPTGenerationState
) -> Literal["research", "content"]:
    """
    条件判断：是否需要研究

    Args:
        state: 当前状态

    Returns:
        下一个节点名称 ("research" 或 "content")
    """
    if needs_research(state):
        logger.info("[MasterGraph] Research needed, routing to research node")
        return "research"
    else:
        logger.info("[MasterGraph] No research needed, routing to content_generation node")
        return "content"
```

**判断逻辑**：

```python
def needs_research(state: PPTGenerationState) -> bool:
    """检查是否需要研究"""
    return get_requirement_field(state, "need_research", False)
```

### _should_refine()

**判断是否需要改进内容**

```python
def _should_refine(
    self,
    state: PPTGenerationState
) -> Literal["refine", "proceed"]:
    """
    条件判断：是否需要改进内容

    Args:
        state: 当前状态

    Returns:
        下一个节点名称 ("refine" 或 "proceed")
    """
    # 检查是否超过最大改进次数
    refinement_count = state.get("refinement_count", 0)

    if refinement_count >= self.max_refinements:
        logger.warning(
            f"[MasterGraph] Max refinements reached ({self.max_refinements}), proceeding to render"
        )
        return "proceed"

    # 使用质量评估结果决定
    from ..core.quality.nodes import should_refine_content

    decision = should_refine_content(state)

    if decision == "refine":
        logger.info(
            f"[MasterGraph] Quality below threshold, routing to refinement "
            f"(iteration {refinement_count + 1}/{self.max_refinements})"
        )
    else:
        logger.info(f"[MasterGraph] Quality threshold met, proceeding to render")

    return decision
```

**判断流程**：

```
1. 检查改进次数
   ├─ 超过最大次数 → proceed（避免无限循环）
   └─ 未超过 → 继续

2. 检查质量分数
   ├─ 低于阈值 → refine（需要改进）
   └─ 高于阈值 → proceed（质量合格）
```

---

## 执行模式

### 1. generate() - 基本执行

**最简单的执行方式**

```python
async def generate(
    self,
    user_input: str,
    task_id: Optional[str] = None,
    user_id: str = "anonymous",
) -> PPTGenerationState:
    """
    生成PPT（主入口）

    Args:
        user_input: 用户输入
        task_id: 任务ID（可选，自动生成）
        user_id: 用户ID

    Returns:
        最终状态
    """
    # 1. 生成任务ID
    if not task_id:
        task_id = f"task_{uuid.uuid4().hex[:8]}"

    logger.info(f"[MasterGraph] Starting PPT generation: task_id={task_id}")

    # 2. 创建初始状态
    initial_state = create_initial_state(
        user_input=user_input,
        task_id=task_id,
        user_id=user_id
    )

    try:
        # 3. 执行工作流
        final_state = await self.graph.ainvoke(initial_state)

        # 4. 检查是否有错误
        if final_state.get("error"):
            logger.error(f"[MasterGraph] Generation completed with error")
        else:
            logger.info(f"[MasterGraph] Generation completed successfully")

        return final_state

    except Exception as e:
        logger.error(f"[MasterGraph] Generation failed: {e}", exc_info=True)

        # 5. 更新状态中的错误
        final_state = initial_state
        final_state["error"] = str(e)
        final_state["current_stage"] = "failed"

        return final_state
```

**使用示例**：

```python
# 创建工作流
graph = create_master_graph()

# 生成 PPT
result = await graph.generate(
    user_input="创建一份关于人工智能的PPT，10页",
    task_id="task_001",
    user_id="user123"
)

# 检查结果
if result.get("error"):
    print(f"生成失败: {result['error']}")
else:
    print(f"生成成功:")
    print(f"  文件: {result['ppt_output']['file_path']}")
    print(f"  页数: {result['ppt_framework']['total_page']}")
```

---

### 2. generate_with_callbacks() - 带回调执行

**实时进度报告**

```python
async def generate_with_callbacks(
    self,
    user_input: str,
    on_stage_complete: Optional[callable] = None,
    on_progress: Optional[callable] = None,
    on_error: Optional[callable] = None,
    task_id: Optional[str] = None,
    user_id: str = "anonymous",
) -> PPTGenerationState:
    """
    带流式回掉的生成

    使用 LangGraph 的 streaming 功能实现实时进度更新。

    Args:
        user_input: 用户输入
        on_stage_complete: 阶段完成回调 (stage_name, state)
        on_progress: 进度回调 (progress, message)
        on_error: 错误回调 (stage_name, error)
        task_id: 任务ID
        user_id: 用户ID

    Returns:
        最终状态
    """
    # 1. 生成任务ID
    if not task_id:
        task_id = f"task_{uuid.uuid4().hex[:8]}"

    # 2. 创建初始状态
    initial_state = create_initial_state(
        user_input=user_input,
        task_id=task_id,
        user_id=user_id
    )

    # 3. 创建进度跟踪器
    from .progress_tracker import create_progress_tracker

    tracker = create_progress_tracker(
        state=initial_state,
        on_progress=lambda update: (
            on_progress(update.progress, update.message) if on_progress else None
        ),
        on_stage_complete=on_stage_complete,
        on_error=on_error,
    )

    # 4. 初始化进度
    tracker.update_stage("init", 0, "Initializing workflow")

    try:
        # 5. 使用 LangGraph streaming
        final_state = None
        async for event in self.graph.astream(initial_state):
            # event 格式: {"node_name": {...}} 或 {"__end__": final_state}
            for node_name, node_output in event.items():
                if node_name == "__end__":
                    # 工作流完成
                    final_state = node_output
                    break

                # 更新进度
                progress = self._get_stage_progress(node_name)
                tracker.update_stage(node_name, progress, f"Processing {node_name}")

                # 触发阶段完成回调
                if on_stage_complete:
                    try:
                        if asyncio.iscoroutinefunction(on_stage_complete):
                            await on_stage_complete(node_name, node_output)
                        else:
                            on_stage_complete(node_name, node_output)
                    except Exception as cb_error:
                        logger.error(f"[MasterGraph] Stage complete callback error: {cb_error}")

        # 6. 确保返回最终状态
        if final_state is None:
            final_state = initial_state

        # 7. 标记完成
        tracker.stage_complete("complete", final_state)

        logger.info(f"[MasterGraph] Streaming generation completed")
        return final_state

    except Exception as e:
        logger.error(f"[MasterGraph] Streaming generation failed: {e}", exc_info=True)
        tracker.error("generation", e)
        raise
```

**使用示例**：

```python
# 定义回调函数
def on_progress(progress, message):
    print(f"[{progress}%] {message}")

def on_stage_complete(stage, state):
    print(f"阶段完成: {stage}")

def on_error(stage, error):
    print(f"阶段 {stage} 出错: {error}")

# 生成 PPT（带进度）
result = await graph.generate_with_callbacks(
    user_input="创建一份关于人工智能的PPT",
    on_progress=on_progress,
    on_stage_complete=on_stage_complete,
    on_error=on_error,
)

# 输出示例：
# [0%] Initializing workflow
# [10%] Processing requirement_parser
# 阶段完成: requirement_parser
# [30%] Processing framework_designer
# 阶段完成: framework_designer
# ...
```

---

## 使用示例

### 1. 基本使用

```python
from backend.agents_langchain.coordinator.master_graph import (
    create_master_graph,
)

# 创建工作流图
graph = create_master_graph()

# 生成 PPT
result = await graph.generate(
    user_input="创建一份关于人工智能的PPT，10页"
)

# 检查结果
print(f"状态: {result['current_stage']}")
print(f"进度: {result['progress']}%")
print(f"文件: {result['ppt_output'].get('file_path')}")
```

### 2. 自定义模型

```python
from langchain_openai import ChatOpenAI

# 创建自定义模型
model = ChatOpenAI(
    model="gpt-4",
    api_key="your-api-key",
    temperature=0.7,
)

# 使用自定义模型
graph = create_master_graph(model=model)
result = await graph.generate(user_input="...")
```

### 3. 调整质量控制

```python
# 启用质量控制，设置阈值和最大改进次数
graph = create_master_graph(
    enable_quality_checks=True,
    quality_threshold=0.85,   # 更高的阈值
    max_refinements=5,         # 更多改进次数
)
```

### 4. 禁用质量控制（快速模式）

```python
# 禁用质量控制，加快速度
graph = create_master_graph(
    enable_quality_checks=False,
)
result = await graph.generate(user_input="...")
```

### 5. 实时进度跟踪

```python
import asyncio

async def generate_with_realtime_progress():
    """实时进度跟踪示例"""

    async def on_progress(progress, message):
        print(f"进度: {progress}% - {message}")

    async def on_stage_complete(stage, state):
        print(f"✓ {stage} 完成")

    async def on_error(stage, error):
        print(f"✗ {stage} 失败: {error}")

    # 创建工作流
    graph = create_master_graph()

    # 生成（带回调）
    result = await graph.generate_with_callbacks(
        user_input="创建一份关于量子计算的PPT，15页",
        on_progress=on_progress,
        on_stage_complete=on_stage_complete,
        on_error=on_error,
    )

    return result

# 运行
result = await generate_with_realtime_progress()
```

---

## 错误处理

### 错误层次

```
┌─────────────────────────────────────────┐
│          错误处理层次                    │
└─────────────────────────────────────────┘

1. 节点级错误
   ├─ Agent 执行失败
   ├─ 状态更新失败
   └─ 节点内部捕获

2. 工作流级错误
   ├─ 条件判断失败
   ├─ 状态转换失败
   └─ MasterGraph 捕获

3. 系统级错误
   ├─ LLM API 调用失败
   ├─ 文件系统错误
   └─ 顶级异常处理
```

### 错误处理策略

```python
# 节点级错误处理（在 Agent 内部）
async def run_node(self, state: PPTGenerationState) -> PPTGenerationState:
    try:
        # 执行处理逻辑
        result = await self.process(state)
        state["output"] = result
        return state
    except Exception as e:
        logger.error(f"[Agent] Error: {e}")
        state["error"] = str(e)
        return state

# 工作流级错误处理（在 MasterGraph 中）
async def generate(self, ...):
    try:
        final_state = await self.graph.ainvoke(initial_state)
        return final_state
    except Exception as e:
        logger.error(f"[MasterGraph] Generation failed: {e}")
        final_state = initial_state
        final_state["error"] = str(e)
        final_state["current_stage"] = "failed"
        return final_state
```

---

## 最佳实践

### 1. 资源管理

```python
# 使用完毕后清理资源
async with create_master_graph() as graph:
    result = await graph.generate(user_input="...")
    # 资源自动清理
```

### 2. 超时控制

```python
import asyncio

# 设置超时
try:
    result = await asyncio.wait_for(
        graph.generate(user_input="..."),
        timeout=300.0  # 最多等5分钟
    )
except asyncio.TimeoutError:
    logger.error("Generation timed out")
```

### 3. 重试策略

```python
# 在应用层实现重试
async def generate_with_retry(graph, user_input, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await graph.generate(user_input)
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(2 ** attempt)  # 指数退避
            else:
                raise
```

### 4. 状态验证

```python
# 验证最终状态
result = await graph.generate(user_input="...")

# 检查必需字段
if not result.get("ppt_output"):
    raise ValueError("Missing ppt_output in final state")

if result.get("error"):
    raise Exception(f"Generation failed: {result['error']}")
```

---

## 调试技巧

### 1. 启用详细日志

```python
import logging

# 启用 MasterGraph 详细日志
logging.getLogger("backend.agents_langchain.coordinator.master_graph").setLevel(logging.DEBUG)

# 现在可以看到每个节点的执行详情
```

### 2. 可视化工作流

```python
# LangGraph 支持生成工作流图（需要安装 pygraphviz）
from IPython.display import Image, display

# 生成工作流图
png_data = graph.graph.get_graph().draw_mermaid_png()
display(Image(png_data))
```

### 3. 单步执行

```python
# 手动执行每个节点（调试用）
state = create_initial_state(user_input="...", task_id="test")

state = await graph.requirement_agent.run_node(state)
print(f"After requirement_parser: {state['structured_requirements']}")

state = await graph.framework_agent.run_node(state)
print(f"After framework_designer: {state['ppt_framework']}")

# ... 继续其他节点
```

---

## 常见问题

### Q1: 如何修改工作流的执行顺序？

A: 修改 `_build_graph()` 方法中的边定义：

```python
# 原始顺序
builder.add_edge("requirement_parser", "framework_designer")

# 修改为（例如：跳过框架设计）
builder.add_edge("requirement_parser", "content_generation")
```

### Q2: 如何添加新的节点？

A: 三步骤：

```python
# 1. 创建 Agent
class MyCustomAgent:
    async def run_node(self, state):
        # 处理逻辑
        return state

# 2. 在 __init__ 中初始化
self.custom_agent = MyCustomAgent()

# 3. 在 _build_graph 中添加节点
builder.add_node("custom_node", self.custom_agent.run_node)
builder.add_edge("framework_designer", "custom_node")
builder.add_edge("custom_node", "content_generation")
```

### Q3: 如何实现动态的工作流？

A: 使用条件边：

```python
def dynamic_routing(state):
    """根据状态动态路由"""
    if state.get("use_research"):
        return "research"
    elif state.get("use_custom_agent"):
        return "custom_agent"
    else:
        return "content_generation"

builder.add_conditional_edges(
    "framework_designer",
    dynamic_routing,
    {
        "research": "research",
        "custom_agent": "custom_agent",
        "content_generation": "content_generation",
    }
)
```

---

## 相关文档

- [设计指南](./design-guide.md) - Coordinator 层设计
- [实施指南](./implementation-guide.md) - 如何实现 master_graph
- [PagePipeline 文档](./page_pipeline.py.md) - 页面流水线详解
- [ProgressTracker 文档](./progress_tracker.py.md) - 进度跟踪详解
