# Coordinator 层实施指南

> 本文档说明 `backend/agents_langchain/coordinator/` 目录各文件的实施策略、书写顺序和实现要点。

---

## 目录

1. [书写顺序与考量](#书写顺序与考量)
2. [实施路线图](#实施路线图)
3. [各文件实现要点](#各文件实现要点)
4. [快速自检清单](#快速自检清单)

---

## 书写顺序与考量

### 推荐顺序

```
第1步：progress_tracker.py     ← 最简单、最基础
     ↓
第2步：page_pipeline.py        ← 独立性强、可并行测试
     ↓
第3步：revision_handler.py     ← 独立性强、业务逻辑清晰
     ↓
第4步：master_graph.py         ← 最复杂、依赖其他所有文件
```

### 考量因素

#### 1. 依赖关系

```
                        ┌──────────────────┐
                        │  master_graph.py │  ← 依赖所有人
                        └──────────────────┘
                                 ↑
                    ┌────────────┼────────────┐
                    │            │            │
         ┌──────────────────┐   │   ┌──────────────────┐
         │ page_pipeline.py │   │   │revision_handler  │
         └──────────────────┘   │   └──────────────────┘
                    │            │
                    └────────────┼────────────┘
                                 │
                    ┌──────────────────┐
                    │progress_tracker  │  ← 不依赖任何人
                    └──────────────────┘
```

**原则**：从底层到高层，先写被依赖的，再写依赖别人的

#### 2. 复杂度排序

| 文件 | 复杂度 | 理由 |
|------|--------|------|
| progress_tracker.py | ⭐ | 简单的记录和回调 |
| page_pipeline.py | ⭐⭐⭐ | 需要理解异步并发 |
| revision_handler.py | ⭐⭐⭐ | 需要处理多种修改类型 |
| master_graph.py | ⭐⭐⭐⭐⭐ | 需要理解 LangGraph 状态图 |

**原则**：先易后难，建立信心

#### 3. 可测试性排序

| 文件 | 可独立测试？ | 测试难度 |
|------|--------------|----------|
| progress_tracker.py | ✅ 完全独立 | 简单 |
| page_pipeline.py | ✅ 完全独立 | 中等 |
| revision_handler.py | ✅ 完全独立 | 中等 |
| master_graph.py | ❌ 依赖其他文件 | 困难 |

**原则**：先写能独立测试的，方便验证

---

## 实施路线图

### 阶段1：基础设施（1-2天）

```
┌──────────────────────────────────────────────────────┐
│ Day 1 上午：progress_tracker.py                      │
├──────────────────────────────────────────────────────┤
│  ├─ 定义 ProgressUpdate 数据类                        │
│  ├─ 实现 ProgressTracker 核心逻辑                     │
│  ├─ 实现 StageProgressMapper                         │
│  └─ 编写单元测试                                      │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ Day 1 下午：page_pipeline.py (开始)                   │
├──────────────────────────────────────────────────────┤
│  ├─ 定义 PagePipeline 类                              │
│  ├─ 实现 asyncio.Semaphore 并发控制                   │
│  └─ 基础测试                                          │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ Day 2 上午：page_pipeline.py (完成)                   │
├──────────────────────────────────────────────────────┤
│  ├─ 实现重试逻辑                                      │
│  ├─ 添加进度回调                                      │
│  ├─ 实现 execute_research_pipeline                   │
│  ├─ 实现 execute_content_pipeline                    │
│  └─ 集成测试                                          │
└──────────────────────────────────────────────────────┘
```

### 阶段2：业务逻辑（2-3天）

```
┌──────────────────────────────────────────────────────┐
│ Day 2 下午：revision_handler.py (开始)                │
├──────────────────────────────────────────────────────┤
│  ├─ 定义 RevisionRequest 数据类                       │
│  ├─ 实现 RevisionHandler 基础结构                     │
│  └─ 实现内容修订（_revise_content）                   │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ Day 3 全天：revision_handler.py (完成)                │
├──────────────────────────────────────────────────────┤
│  ├─ 实现风格修订（_revise_style）                     │
│  ├─ 实现结构修订（_revise_structure）                 │
│  ├─ 实现研究修订（_revise_research）                  │
│  ├─ 添加修订历史记录                                  │
│  ├─ 实现增量修订（apply_incremental_revision）       │
│  └─ 编写测试用例                                      │
└──────────────────────────────────────────────────────┘
```

### 阶段3：主工作流（3-4天）

```
┌──────────────────────────────────────────────────────┐
│ Day 4 全天：master_graph.py (基础)                    │
├──────────────────────────────────────────────────────┤
│  ├─ 学习 LangGraph StateGraph 基础                   │
│  ├─ 构建简单工作流（2-3个节点）                        │
│  ├─ 实现 _build_graph 基础版本                        │
│  ├─ 实现 generate 方法                                │
│  └─ 测试基本流程                                      │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ Day 5 全天：master_graph.py (完整流程)                │
├──────────────────────────────────────────────────────┤
│  ├─ 添加所有 agent 节点                               │
│  ├─ 实现条件边（_should_research）                    │
│  ├─ 集成 page_pipeline                                │
│  ├─ 测试完整工作流                                    │
│  └─ 调试错误处理                                      │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ Day 6 全天：master_graph.py (收尾)                    │
├──────────────────────────────────────────────────────┤
│  ├─ 集成 progress_tracker                             │
│  ├─ 实现 generate_with_callbacks                      │
│  ├─ 添加质量控制节点（可选）                           │
│  ├─ 实现条件边（_should_refine）                      │
│  ├─ 完善错误处理                                      │
│  ├─ 添加日志记录                                      │
│  └─ 端到端集成测试                                    │
└──────────────────────────────────────────────────────┘
```

---

## 各文件实现要点

### 第1步：progress_tracker.py

#### 为什么先写它？
- ✅ 最简单，建立信心
- ✅ 不依赖任何其他 coordinator 文件
- ✅ 其他文件都会用到它

#### 必须包含的内容

```python
# 1. 数据结构：进度更新
@dataclass
class ProgressUpdate:
    """进度更新数据结构"""
    stage: str           # 当前阶段
    progress: int        # 进度百分比 (0-100)
    message: str         # 进度消息
    timestamp: datetime  # 时间戳
    metadata: Dict       # 额外信息

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于序列化）"""

# 2. 核心类：进度跟踪器
class ProgressTracker:
    """PPT 生成工作流的进度跟踪器"""

    # 阶段常量定义
    STAGE_INIT = "init"
    STAGE_REQUIREMENT_PARSING = "requirement_parsing"
    STAGE_FRAMEWORK_DESIGN = "framework_design"
    STAGE_RESEARCH = "research"
    STAGE_CONTENT_GENERATION = "content_generation"
    STAGE_QUALITY_CHECK = "quality_check"
    STAGE_REFINEMENT = "refinement"
    STAGE_TEMPLATE_RENDERING = "template_rendering"
    STAGE_COMPLETE = "complete"

    def __init__(
        self,
        task_id: str,
        on_progress: Optional[Callable] = None,
        on_stage_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ):
        """初始化进度跟踪器"""

    def update_stage(
        self,
        stage: str,
        progress: int,
        message: str = "",
        metadata: Optional[Dict] = None,
    ):
        """更新进度并触发回调"""

    def stage_complete(self, stage: str, state: PPTGenerationState):
        """标记阶段为完成并触发回调"""

    def error(self, stage: str, error: Exception):
        """处理错误并触发回调"""

    def get_elapsed_time(self) -> float:
        """获取经过的时间（秒）"""

    def get_history(self) -> List[Dict]:
        """获取进度历史"""

# 3. 工具类：进度映射
class StageProgressMapper:
    """将 LangGraph 阶段映射到进度百分比"""

    DEFAULT_STAGE_WEIGHTS = {
        "requirement_parser": 10,
        "framework_designer": 20,
        "research": 30,
        "content_generation": 25,
        "quality_check": 10,
        "template_renderer": 5,
    }

    @classmethod
    def get_progress_for_stage(cls, stage: str) -> int:
        """获取阶段的进度百分比"""

    @classmethod
    def get_stage_progress_range(cls, stage: str) -> tuple[int, int]:
        """获取阶段的进度范围 (开始, 结束)"""

# 4. 工厂函数
def create_progress_tracker(
    state: PPTGenerationState,
    on_progress: Optional[Callable] = None,
    on_stage_complete: Optional[Callable] = None,
    on_error: Optional[Callable] = None,
) -> ProgressTracker:
    """从状态创建进度跟踪器的工厂函数"""
```

#### 实现检查清单

- [ ] 有 `@dataclass` 定义数据结构吗？
- [ ] 回调函数有异常处理吗？（避免回调报错影响主流程）
- [ ] 进度值有范围限制吗？（0-100）
- [ ] 有历史记录吗？（用于调试）
- [ ] 有便捷的工厂函数吗？
- [ ] 有单元测试吗？

---

### 第2步：page_pipeline.py

#### 为什么第二个写？
- ✅ 相对独立，只依赖 models
- ✅ 性能优化核心，需要重点测试
- ✅ master_graph 会用到它

#### 必须包含的内容

```python
# 1. 核心类：页面流水线
class PagePipeline:
    """页面级流水线 - 并行执行器"""

    def __init__(
        self,
        max_concurrency: int = 3,
        max_retries: int = 2,
        retry_delay: float = 1.0,
    ):
        """初始化页面流水线"""
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def execute_pages(
        self,
        pages: List[Dict[str, Any]],
        executor_func: Callable,
        progress_callback: Optional[Callable] = None,
    ) -> List[Dict[str, Any]]:
        """并行执行页面任务"""

    async def execute_research_pipeline(
        self,
        state: PPTGenerationState,
        research_agent,
    ) -> PPTGenerationState:
        """执行研究流水线"""

    async def execute_content_pipeline(
        self,
        state: PPTGenerationState,
        content_agent,
    ) -> PPTGenerationState:
        """执行内容生成流水线"""

    # 私有方法

    async def _process_page_with_semaphore(
        self,
        page: Dict[str, Any],
        executor_func: Callable,
        progress_callback: Optional[Callable],
        total_pages: int,
    ) -> Dict[str, Any]:
        """使用信号量控制并发的页面处理"""

    async def _process_page_with_retry(
        self,
        page: Dict[str, Any],
        executor_func: Callable,
        progress_callback: Optional[Callable],
        total_pages: int,
    ) -> Dict[str, Any]:
        """带重试的页面处理"""

# 2. 工厂函数
def create_page_pipeline(
    max_concurrency: int = 3,
    max_retries: int = 2,
    retry_delay: float = 1.0,
) -> PagePipeline:
    """创建页面流水线"""

# 3. 便捷函数
async def execute_page_pipeline(
    pages: List[Dict[str, Any]],
    executor_func: Callable,
    max_concurrency: int = 3,
) -> List[Dict[str, Any]]:
    """直接执行页面流水线（便捷函数）"""
```

#### 实现检查清单

- [ ] 使用了 `asyncio.Semaphore` 控制并发吗？
- [ ] 有重试机制吗？（失败页面）
- [ ] 有超时处理吗？（避免无限等待）
- [ ] 进度回调是线程安全的吗？
- [ ] 有日志记录吗？（每个页面的执行情况）
- [ ] 有单元测试吗？（并发测试）

#### 核心难点

```python
# 1. 并发控制
self.semaphore = asyncio.Semaphore(max_concurrency)

async with self.semaphore:
    # 同时最多只有 max_concurrency 个任务在运行
    result = await executor_func(page)

# 2. 异常处理
results = await asyncio.gather(*tasks, return_exceptions=True)
# 不会因为单个页面失败而中断整个流程

# 3. 重试逻辑
for attempt in range(max_retries + 1):
    try:
        return await executor_func(page)
    except Exception as e:
        if attempt < max_retries:
            await asyncio.sleep(retry_delay)
        else:
            raise
```

---

### 第3步：revision_handler.py

#### 为什么第三个写？
- ✅ 业务逻辑清晰，相对独立
- ✅ 不影响主流程
- ✅ 可以增量开发（先实现简单的，再扩展）

#### 必须包含的内容

```python
# 1. 数据结构：修订请求
@dataclass
class RevisionRequest:
    """Revision request data structure"""
    type: Literal["content", "style", "structure", "research"]
    target: Literal["page_index", "all", "section"]
    instructions: str
    page_indices: Optional[List[int]] = None
    section_name: Optional[str] = None

# 2. 核心类：修订处理器
class RevisionHandler:
    """Handles PPT revision requests"""

    def __init__(self, model: Optional[ChatOpenAI] = None):
        """Initialize revision handler"""

    async def handle_revision_request(
        self,
        state: PPTGenerationState,
        revision_request: Dict[str, Any],
    ) -> PPTGenerationState:
        """Handle a revision request（主入口）"""

    # 私有方法：各种修订类型

    async def _revise_content(
        self,
        state: PPTGenerationState,
        request: RevisionRequest,
    ) -> PPTGenerationState:
        """Revise content based on user feedback"""

    async def _revise_style(
        self,
        state: PPTGenerationState,
        request: RevisionRequest,
    ) -> PPTGenerationState:
        """Revise style/tone of content"""

    async def _revise_structure(
        self,
        state: PPTGenerationState,
        request: RevisionRequest,
    ) -> PPTGenerationState:
        """Revise PPT structure"""

    async def _revise_research(
        self,
        state: PPTGenerationState,
        request: RevisionRequest,
    ) -> PPTGenerationState:
        """Revise research results"""

    def _parse_revision_request(
        self,
        request: Dict[str, Any],
    ) -> RevisionRequest:
        """Parse revision request from dictionary"""

    async def apply_incremental_revision(
        self,
        state: PPTGenerationState,
        page_index: int,
        new_content: str,
    ) -> PPTGenerationState:
        """Apply incremental revision to a specific page"""

    def get_revision_summary(
        self,
        state: PPTGenerationState,
    ) -> Dict[str, Any]:
        """Get summary of revision history"""

# 3. 工厂函数（可选）
def create_revision_handler(model: Optional[ChatOpenAI] = None) -> RevisionHandler:
    """创建修订处理器"""
```

#### 实现检查清单

- [ ] 有请求验证吗？（防止非法参数）
- [ ] 有边界情况处理吗？（page_index 超出范围）
- [ ] 有修订历史吗？（用于审计）
- [ ] 支持增量修订吗？（直接提供新内容）
- [ ] 有错误恢复吗？（修订失败不影响原内容）
- [ ] 有单元测试吗？

---

### 第4步：master_graph.py

#### 为什么最后写？
- ⚠️ 依赖所有其他文件
- ⚠️ 最复杂，需要理解 LangGraph
- ⚠️ 需要先有 agents（虽然还没写，但可以预留接口）

#### 必须包含的内容

```python
# 1. 核心类：主工作流图
class MasterGraph:
    """主工作流图 - LangGraph 实现"""

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
        """初始化主工作流图"""
        # 创建或使用提供的智能体
        # 创建页面流水线
        # 构建状态图

    def _create_default_model(self) -> ChatOpenAI:
        """创建默认LLM模型"""

    def _build_graph(self) -> StateGraph:
        """构建状态图（核心方法）"""
        # 创建 StateGraph
        # 添加节点
        # 添加边
        # 添加条件边
        # 编译图

    def _should_research(self, state: PPTGenerationState) -> Literal["research", "content"]:
        """条件判断：是否需要研究"""

    def _should_refine(self, state: PPTGenerationState) -> Literal["refine", "proceed"]:
        """条件判断：是否需要改进内容"""

    async def generate(
        self,
        user_input: str,
        task_id: Optional[str] = None,
        user_id: str = "anonymous",
    ) -> PPTGenerationState:
        """生成PPT（主入口）"""
        # 创建初始状态
        # 执行工作流
        # 返回最终状态

    async def generate_with_callbacks(
        self,
        user_input: str,
        on_stage_complete: Optional[callable] = None,
        on_progress: Optional[callable] = None,
        on_error: Optional[callable] = None,
        task_id: Optional[str] = None,
        user_id: str = "anonymous",
    ) -> PPTGenerationState:
        """带流式回调的生成（使用 progress_tracker）"""
        # 创建进度跟踪器
        # 使用 LangGraph streaming
        # 触发回调

    def _get_stage_progress(self, stage: str) -> int:
        """获取阶段进度百分比"""

# 2. 工厂函数
def create_master_graph(
    model: Optional[ChatOpenAI] = None,
    max_concurrency: int = 3,
    enable_quality_checks: bool = True,
    quality_threshold: float = 0.8,
    max_refinements: int = 3,
) -> MasterGraph:
    """创建主工作流图"""

# 3. 便捷函数
async def generate_ppt(
    user_input: str,
    model: Optional[ChatOpenAI] = None,
    task_id: Optional[str] = None,
    user_id: str = "anonymous",
) -> Dict[str, Any]:
    """直接生成 PPT（便捷函数）"""
```

#### 实现检查清单

- [ ] 所有节点都添加到图了吗？
- [ ] 所有边都正确连接了吗？
- [ ] 条件边的逻辑正确吗？
- [ ] 有错误处理吗？（节点失败怎么办）
- [ ] 有日志记录吗？（每个节点的执行情况）
- [ ] 支持流式输出吗？（实时进度）
- [ ] 有集成测试吗？

#### 核心难点

```python
# 1. 构建状态图
builder = StateGraph(PPTGenerationState)

# 添加节点
builder.add_node("requirement_parser", self.requirement_agent.run_node)
builder.add_node("framework_designer", self.framework_agent.run_node)
builder.add_node("research", self.research_agent.run_node)
builder.add_node("content_generation", self.content_agent.run_node)
builder.add_node("template_renderer", self.renderer_agent.run_node)

# 添加普通边
builder.add_edge("requirement_parser", "framework_designer")

# 添加条件边（分支）
builder.add_conditional_edges(
    "framework_designer",
    self._should_research,  # 判断函数
    {
        "research": "research",
        "content": "content_generation"
    },  # 路由映射
)

# 添加边 - 研究 → 内容生成
builder.add_edge("research", "content_generation")

# 添加边 - 内容生成 → 渲染
builder.add_edge("content_generation", "template_renderer")

# 添加边 - 渲染 → END
builder.add_edge("template_renderer", END)

# 编译图
graph = builder.compile()

# 2. 执行工作流
final_state = await graph.ainvoke(initial_state)

# 3. 流式执行
async for event in self.graph.astream(initial_state):
    # event 格式: {"node_name": {...}} 或 {"__end__": final_state}
    for node_name, node_output in event.items():
        if node_name == "__end__":
            final_state = node_output
            break
        # 实时更新进度
        tracker.update_stage(node_name, progress, f"Processing {node_name}")
```

---

## 快速自检清单

### 每个文件完成后

| 问题 | 检查方式 |
|------|----------|
| **能独立运行吗？** | `python xxx.py` 不报错 |
| **有单元测试吗？** | pytest 通过所有用例 |
| **有日志吗？** | 关键操作都有日志输出 |
| **有异常处理吗？** | 不会因为异常而崩溃 |
| **有文档吗？** | 每个函数都有 docstring |
| **能集成吗？** | 能被其他模块正确调用 |

### 全部完成后

- [ ] 四个文件都能独立运行
- [ ] 所有单元测试通过
- [ ] 有集成测试验证协作
- [ ] 有端到端测试验证完整流程
- [ ] 代码有完整的文档字符串
- [ ] 有使用示例
- [ ] 性能测试通过（并发性能）

---

## 调试技巧

### 1. 使用日志

```python
import logging

logger = logging.getLogger(__name__)

# 关键步骤添加日志
logger.info(f"[MasterGraph] Starting PPT generation: task_id={task_id}")
logger.debug(f"[PagePipeline] Processing page {page_no}, attempt {attempt + 1}")
logger.error(f"[ProgressTracker] Error in {stage}: {error}")
```

### 2. 使用测试

```python
# 单元测试
async def test_progress_tracker():
    tracker = create_progress_tracker(state)
    tracker.update_stage("test", 50, "Testing")
    assert tracker._current_progress == 50

# 集成测试
async def test_page_pipeline():
    pipeline = create_page_pipeline(max_concurrency=2)
    results = await pipeline.execute_pages(test_pages, mock_executor)
    assert len(results) == len(test_pages)
```

### 3. 使用模拟

```python
# 模拟 agent（在 agent 还没实现时）
class MockRequirementAgent:
    async def run_node(self, state):
        state["structured_requirements"] = {"test": "data"}
        return state
```

---

## 相关文档

- [设计指南](./design-guide.md) - 为什么需要这些文件
- [ProgressTracker 文档](./progress_tracker.py.md) - 进度追踪详解
- [RevisionHandler 文档](./revision_handler.py.md) - 修订处理详解
- [Models 层实施指南](../01-models/design-guide.md) - 数据模型实现
