# Domain Layer（领域层）文档

## 目录

- [概述](#概述)
- [DDD 架构](#ddd-架构)
- [目录结构](#目录结构)
- [核心概念](#核心概念)
- [模块详解](#模块详解)
- [使用指南](#使用指南)
- [最佳实践](#最佳实践)
- [迁移指南](#迁移指南)
- [重要修复说明](#重要修复说明)

---

## 概述

Domain Layer（领域层）是 MultiAgentPPT 项目的核心业务逻辑层，采用 **Domain-Driven Design (DDD)** 方法论设计。它封装了 PPT 生成的所有业务规则、领域模型和领域服务，与基础设施层和应用层保持独立。

### 核心职责

- **定义领域模型**：实体（Entities）、值对象（Value Objects）
- **实现业务逻辑**：通过领域服务和领域事件
- **定义业务规则**：验证、状态转换、不变性约束
- **提供领域接口**：与外部系统交互的契约

### 设计原则

1. **单一职责**：每个类只负责一个明确的业务概念
2. **封装不变性**：通过值对象确保数据完整性
3. **事件驱动**：通过领域事件解耦业务流程
4. **依赖倒置**：依赖接口而非具体实现

---

## DDD 架构

### 战术模式

本项目实现了以下 DDD 战术模式：

#### 1. 实体（Entity）

具有唯一标识符的对象，通过 ID 而非属性判断相等性。

**示例**：`Task`, `Presentation`, `Checkpoint`

```python
@dataclass
class Task:
    id: str  # 唯一标识
    status: TaskStatus
    # ... 其他属性

    def __eq__(self, other):
        return isinstance(other, Task) and self.id == other.id
```

#### 2. 值对象（Value Object）

不可变的对象，通过属性值判断相等性。

**示例**：`Requirement`, `PPTFramework`, `ResearchResult`

```python
@dataclass(frozen=True)
class Requirement(ValueObject, Serializable):
    ppt_topic: str
    page_num: int
    # ... 其他属性

    def __post_init__(self):
        # 验证逻辑
        if self.page_num < 1:
            raise ValidationError("page_num must be positive")
```

#### 3. 聚合（Aggregate）

一组相关领域对象的集合，通过聚合根（Aggregate Root）统一管理。

**示例**：`Task` 是聚合根，管理 `StageProgress`、`TaskMetadata`

#### 4. 领域服务（Domain Service）

不属于特定实体或值对象的业务逻辑。

**示例**：`TaskProgressService`, `TaskValidationService`

#### 5. 领域事件（Domain Event）

表示领域内发生的重要事情，用于解耦和集成。

**示例**：`TaskCreatedEvent`, `StageCompletedEvent`

#### 6. 仓储接口（Repository Interface）

定义持久化抽象，由基础设施层实现。

**示例**：`ITaskRepository`, `IPresentationRepository`

---

## 目录结构

```
backend/domain/
├── __init__.py                      # 主导出模块（保持向后兼容）
├── DDD_RESTRUCTURE_SUMMARY.md       # DDD 重构总结
│
├── entities/                        # 实体（有身份标识）
│   ├── __init__.py
│   ├── base.py                      # 基础类
│   │   ├── Entity                   # 实体基类
│   │   ├── ValueObject              # 值对象基类
│   │   ├── Serializable              # 序列化混入类
│   │   └── AggregateRoot            # 聚合根基类
│   ├── task.py                      # Task 实体（聚合根）
│   ├── presentation.py              # Presentation 实体
│   ├── checkpoint.py                # Checkpoint 实体
│   └── state/                       # 状态模型
│       ├── __init__.py
│       ├── content_state.py         # 内容状态
│       ├── framework_state.py       # 框架状态
│       ├── requirement_state.py     # 需求状态
│       └── research_state.py        # 研究状态
│
├── value_objects/                   # 值对象（不可变）
│   ├── __init__.py
│   ├── requirement.py               # Requirement 需求值对象
│   ├── framework.py                 # PPTFramework 框架值对象
│   ├── research.py                  # ResearchResult 研究结果
│   ├── slide.py                     # Slide 幻灯片
│   ├── topic.py                     # Topic 主题
│   └── page_state.py                # PageState 页面状态
│
├── services/                        # 领域服务
│   ├── __init__.py
│   ├── task_progress_service.py     # 任务进度计算服务
│   ├── task_validation_service.py   # 任务验证服务
│   └── stage_transition_service.py  # 阶段转换服务
│
├── exceptions/                      # 领域异常
│   ├── __init__.py
│   └── domain_exceptions.py
│       ├── DomainError              # 基础领域异常
│       ├── ValidationError          # 验证失败
│       ├── InvalidStateTransitionError  # 无效状态转换
│       ├── InvalidTaskError         # 无效任务状态
│       └── TaskNotFoundError        # 任务未找到
│
├── events/                          # 领域事件
│   ├── __init__.py
│   └── task_events.py
│       ├── TaskEvent                # 事件基类
│       ├── TaskEventType            # 事件类型枚举
│       └── 工厂函数
│           ├── create_task_created_event()
│           ├── create_stage_started_event()
│           ├── create_stage_completed_event()
│           ├── create_stage_failed_event()
│           ├── create_task_failed_event()
│           └── create_task_completed_event()
│
├── communication/                   # Agent 通信模型
│   ├── __init__.py
│   ├── agent_context.py             # Agent 上下文
│   │   ├── AgentContext             # 强类型上下文
│   │   ├── Requirement              # 需求模型
│   │   ├── PPTFramework             # 框架模型
│   │   ├── ResearchResult           # 研究结果
│   │   ├── SlideContent             # 幻灯片内容
│   │   ├── ExecutionMode            # 执行模式
│   │   └── AgentStage               # Agent 阶段
│   └── agent_result.py              # Agent 结果
│       ├── AgentResult              # 通用结果（泛型）
│       ├── ResultStatus             # 结果状态
│       ├── ValidationResult         # 验证结果
│       └── ProgressEvent            # 进度事件
│
├── config/                          # 配置
│   ├── __init__.py
│   └── task_config.py
│       ├── TaskProgressWeights      # 进度权重配置
│       └── TaskConfig               # 任务配置
│
├── interfaces/                      # 接口定义
│   ├── __init__.py
│   ├── agent.py                     # Agent 接口
│   │   ├── IAgent                   # Agent 基础接口
│   │   ├── IAgentConfig             # 配置接口
│   │   ├── IAgentContext            # 上下文接口
│   │   ├── IAgentResult             # 结果接口
│   │   ├── ITopicSplitterAgent      # 主题拆分 Agent
│   │   ├── IResearchAgent           # 研究 Agent
│   │   ├── IContentGeneratorAgent   # 内容生成 Agent
│   │   ├── ISlideWriterAgent        # 幻灯片写入 Agent
│   │   ├── IQualityCheckerAgent     # 质量检查 Agent
│   │   └── IAgentFactory            # Agent 工厂接口
│   └── repository.py                # 仓储接口（待实现）
│
└── models/                          # 旧模型（保留以保持向后兼容）
    └── __init__.py                  # 标记为 DEPRECATED
```

---

## 核心概念

### 1. 实体 vs 值对象

| 特性 | 实体 (Entity) | 值对象 (Value Object) |
|------|--------------|---------------------|
| 身份标识 | 有 ID | 无 ID |
| 可变性 | 可变 | 不可变（frozen） |
| 相等性 | ID 相等 | 所有属性相等 |
| 生命周期 | 长期 | 临时 |
| 示例 | Task, Presentation | Requirement, Framework |

### 2. 聚合和聚合根

```
Task (聚合根)
  ├─ metadata: TaskMetadata
  ├─ stages: Dict[TaskStage, StageProgress]
  ├─ presentation: Presentation
  └─ _pending_events: List[TaskEvent]
```

**规则**：
- 外部只能通过聚合根访问聚合内部对象
- 聚合根负责保证内部对象的一致性
- 一次事务只更新一个聚合

### 3. 领域事件

```python
# 事件发布
task.start_stage(TaskStage.REQUIREMENT_PARSING)

# 事件消费
events = task.get_pending_events()
for event in events:
    # 处理事件（如：保存到事件存储、发送通知等）
    handle_event(event)
```

---

## 模块详解

### entities/ - 实体模块

#### Task 实体

**职责**：表示一个完整的 PPT 生成任务，是系统的核心聚合根。

**关键字段**：
```python
@dataclass
class Task:
    id: str                                    # 任务 ID
    status: TaskStatus                         # 任务状态
    metadata: TaskMetadata                     # 元数据
    stages: Dict[TaskStage, StageProgress]     # 各阶段进度
    presentation: Optional[Presentation]       # 关联的演示文稿
    raw_input: str                             # 原始输入
    structured_requirements: Optional[Dict]     # 结构化需求
    ppt_framework: Optional[Dict]              # PPT 框架
    research_results: Optional[List[Dict]]      # 研究结果
    content_material: Optional[List[Dict]]      # 内容素材
    final_output: Optional[Dict]               # 最终输出
    error: Optional[str]                       # 错误信息
```

**关键方法**：
```python
# 阶段管理
start_stage(stage: TaskStage) -> None
complete_stage(stage: TaskStage) -> None
fail_stage(stage: TaskStage, error: str) -> None
update_stage_progress(stage: TaskStage, progress: int) -> None

# 任务生命周期
mark_completed() -> None
increment_retry(stage: TaskStage) -> int

# 事件
get_pending_events() -> List[TaskEvent]

# 进度
get_overall_progress() -> int
```

**使用示例**：
```python
from domain.entities import Task, TaskStage, TaskStatus

# 创建任务
task = Task(
    id="task_001",
    raw_input="创建一个关于 AI 的 PPT"
)

# 开始阶段
task.start_stage(TaskStage.REQUIREMENT_PARSING)

# 更新进度
task.update_stage_progress(TaskStage.REQUIREMENT_PARSING, 50)

# 完成阶段
task.complete_stage(TaskStage.REQUIREMENT_PARSING)

# 获取事件
events = task.get_pending_events()
```

#### Presentation 实体

**职责**：表示生成的 PPT 演示文稿。

**状态枚举**：
```python
class PresentationStatus(str, Enum):
    DRAFT = "draft"           # 草稿
    GENERATING = "generating" # 生成中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
```

#### Checkpoint 实体

**职责**：保存任务执行快照，支持断点续传。

**阶段**：
- `PHASE_1`: 需求解析 + 框架设计
- `PHASE_2`: 研究 + 内容生成 + 渲染

---

### value_objects/ - 值对象模块

#### Requirement 值对象

**职责**：封装 PPT 生成需求。

**特性**：
- 不可变（frozen=True）
- 自动验证（__post_init__）
- 工厂方法（with_defaults）

**字段**：
```python
@dataclass(frozen=True)
class Requirement(ValueObject, Serializable):
    ppt_topic: str                    # PPT 主题
    scene: SceneType                  # 使用场景
    industry: str                     # 行业
    audience: str                     # 受众
    page_num: int                     # 页数
    template_type: TemplateType       # 模板类型
    core_modules: List[str]           # 核心模块
    need_research: bool               # 是否需要研究
    special_require: List[str]        # 特殊要求
    language: str                     # 语言
    keywords: List[str]               # 关键词
    style_preference: str             # 风格偏好
    color_scheme: str                 # 配色方案
```

**验证规则**：
- 主题不能为空
- 页数必须在 1-100 之间
- 核心模块数不能超过页数

**使用示例**：
```python
from domain.value_objects import Requirement, SceneType

# 方式1：直接创建
req = Requirement(
    ppt_topic="AI 发展历程",
    page_num=10,
    scene=SceneType.BUSINESS_REPORT
)

# 方式2：使用工厂方法（带默认值）
req = Requirement.with_defaults("AI 发展历程", page_num=10)
```

#### PPTFramework 值对象

**职责**：定义 PPT 的整体结构框架。

**组成**：
- `PageDefinition`: 单页定义
- `PPTFramework`: 完整框架

**页面类型**：
```python
class PageType(str, Enum):
    COVER = "cover"         # 封面
    DIRECTORY = "directory" # 目录
    CONTENT = "content"     # 内容页
    CHART = "chart"         # 图表页
    IMAGE = "image"         # 配图页
    SUMMARY = "summary"     # 总结
    THANKS = "thanks"       # 致谢
```

#### ResearchResult 值对象

**职责**：封装主题研究结果。

**字段**：
```python
@dataclass
class ResearchResult:
    topic_id: str                  # 主题 ID
    topic_title: str               # 主题标题
    content: str                   # 研究内容
    status: ResearchStatus         # 研究状态
    sources: List[str]             # 参考来源
    confidence: float              # 置信度 (0-1)
```

---

### services/ - 领域服务模块

#### TaskProgressService

**职责**：计算任务进度。

**方法**：
```python
class TaskProgressService:
    def calculate_overall_progress(
        self, stages: Dict[TaskStage, StageProgress]
    ) -> int:
        """计算总体进度 (0-100)"""

    def calculate_stage_progress(
        self, stage_name: str,
        completed_items: int,
        total_items: int
    ) -> int:
        """计算单阶段进度"""

    def get_incomplete_stages(
        self, stages: Dict[TaskStage, StageProgress]
    ) -> List[str]:
        """获取未完成的阶段"""
```

**进度权重**：
```python
REQUIREMENT_PARSING: 15%
FRAMEWORK_DESIGN: 30%
RESEARCH: 50%
CONTENT_GENERATION: 80%
TEMPLATE_RENDERING: 100%
```

#### TaskValidationService

**职责**：验证领域模型。

**方法**：
```python
class TaskValidationService:
    def validate_requirement(self, requirement) -> None:
        """验证需求"""

    def validate_framework(self, framework) -> None:
        """验证框架"""

    def validate_task_transition(
        self, current_status: str, new_status: str
    ) -> None:
        """验证状态转换"""

    def validate_research_result(self, research_result) -> None:
        """验证研究结果"""
```

#### StageTransitionService

**职责**：管理阶段转换。

**方法**：
```python
class StageTransitionService:
    def start_stage(self, task, stage_name: str) -> None:
        """开始阶段"""

    def complete_stage(self, task, stage_name: str) -> None:
        """完成阶段"""

    def fail_stage(self, task, stage_name: str, error: str) -> None:
        """失败阶段"""
```

---

### exceptions/ - 领域异常模块

**异常层次结构**：
```
DomainError (基类)
├── ValidationError
│   └── RequirementValidationError
│   └── FrameworkValidationError
│   └── ResearchValidationError
├── InvalidStateTransitionError
├── InvalidTaskError
└── TaskNotFoundError
```

**使用示例**：
```python
from domain.exceptions import ValidationError, InvalidStateTransitionError

try:
    requirement = Requirement(ppt_topic="", page_num=10)
except ValidationError as e:
    print(f"Validation failed: {e.errors}")
    # 输出: Validation failed: ['PPT主题不能为空']
```

---

### events/ - 领域事件模块

**事件类型**：
```python
class TaskEventType(str, Enum):
    # 任务生命周期
    TASK_CREATED = "TASK_CREATED"
    TASK_STARTED = "TASK_STARTED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"

    # 阶段事件
    REQUIREMENT_PARSED = "REQUIREMENT_PARSED"
    FRAMEWORK_DESIGNED = "FRAMEWORK_DESIGNED"
    RESEARCH_COMPLETED = "RESEARCH_COMPLETED"
    CONTENT_GENERATED = "CONTENT_GENERATED"
    PPT_RENDERED = "PPT_RENDERED"

    # Checkpoint 事件
    CHECKPOINT_SAVED = "CHECKPOINT_SAVED"
    CHECKPOINT_LOADED = "CHECKPOINT_LOADED"

    # 修订事件
    REQUIREMENT_MODIFIED = "REQUIREMENT_MODIFIED"
    FRAMEWORK_MODIFIED = "FRAMEWORK_MODIFIED"
```

**事件结构**：
```python
@dataclass
class TaskEvent:
    event_type: TaskEventType      # 事件类型
    version: int                    # 版本号
    data: Dict[str, Any]            # 事件数据
    timestamp: datetime             # 时间戳
    correlation_id: Optional[str]   # 关联 ID
    metadata: Dict[str, Any]        # 元数据
```

**工厂函数**：
```python
# 创建任务创建事件
event = create_task_created_event(
    version=1,
    task_id="task_001",
    raw_input="创建 PPT",
    user_id="user_001"
)

# 创建阶段完成事件
event = create_stage_completed_event(
    version=2,
    task_id="task_001",
    stage_name="requirement_parsing",
    result_data={"status": "completed"}
)
```

---

### communication/ - Agent 通信模块

#### AgentContext

**职责**：强类型的 Agent 上下文，替代原来的字典传递。

**字段**：
```python
@dataclass
class AgentContext:
    # 基础信息
    request_id: str
    execution_mode: ExecutionMode
    current_stage: Optional[AgentStage]

    # 阶段数据（强类型）
    requirement: Optional[Requirement]
    framework: Optional[PPTFramework]
    research_results: List[ResearchResult]
    slide_contents: List[SlideContent]
    final_ppt_path: Optional[str]

    # 元数据
    created_at: datetime
    updated_at: datetime
    errors: List[str]
    retry_count: int
```

**使用优势**：
- 类型安全（IDE 自动补全）
- 编译时检查
- 自文档化

#### AgentResult

**职责**：统一的 Agent 执行结果（泛型支持）。

**字段**：
```python
@dataclass
class AgentResult(Generic[T]):
    status: ResultStatus        # SUCCESS, PARTIAL, FAILURE, RETRY
    data: Optional[T]           # 结果数据
    message: str                # 消息
    errors: List[str]           # 错误列表

    # 降级信息
    fallback_used: bool
    fallback_reason: Optional[str]

    # 性能指标
    execution_time: float
    token_usage: int
```

**工厂方法**：
```python
# 成功
result = AgentResult.success(data=PPTFramework(...))

# 失败
result = AgentResult.failure(message="LLM 调用失败", errors=["超时"])

# 部分成功（降级）
result = AgentResult.partial(
    data=default_framework,
    fallback_reason="LLM 返回格式错误"
)
```

---

### interfaces/ - 接口模块

#### IAgent 接口

**职责**：定义 Agent 的基本契约。

```python
class IAgent(ABC):
    @abstractmethod
    def get_name(self) -> str: pass

    @abstractmethod
    def get_description(self) -> str: pass

    @abstractmethod
    async def run(
        self, context: IAgentContext, input_data: Any
    ) -> IAgentResult: pass

    @abstractmethod
    async def run_stream(
        self, context: IAgentContext, input_data: Any
    ) -> AsyncIterator[Any]: pass
```

#### IAgentFactory 接口

**职责**：创建不同类型的 Agent。

```python
class IAgentFactory(ABC):
    @abstractmethod
    def create_topic_splitter(
        self, config: IAgentConfig
    ) -> ITopicSplitterAgent: pass

    @abstractmethod
    def create_research_agent(
        self, config: IAgentConfig
    ) -> IResearchAgent: pass

    @abstractmethod
    def create_slide_writer(
        self, config: IAgentConfig
    ) -> ISlideWriterAgent: pass

    @abstractmethod
    def create_quality_checker(
        self, config: IAgentConfig
    ) -> IQualityCheckerAgent: pass
```

---

### config/ - 配置模块

#### TaskProgressWeights

**职责**：定义各阶段进度权重。

```python
@dataclass
class TaskProgressWeights:
    REQUIREMENT_PARSING: int = 15
    FRAMEWORK_DESIGN: int = 30
    RESEARCH: int = 50
    CONTENT_GENERATION: int = 80
    TEMPLATE_RENDERING: int = 100
```

#### TaskConfig

**职责**：任务行为配置。

```python
@dataclass
class TaskConfig:
    progress_weights: TaskProgressWeights
    max_retries: int = 3
    default_timeout: int = 300
    checkpoint_interval: int = 60
    enable_checkpointing: bool = True
```

---

## 使用指南

### 1. 创建和管理任务

```python
from domain.entities import Task, TaskStage, TaskStatus
from domain.services import stage_transition_service

# 创建任务
task = Task(
    id="task_001",
    raw_input="创建一个关于人工智能的 PPT，10页"
)

# 开始阶段
stage_transition_service.start_stage(task, "requirement_parsing")

# 更新进度
stage_transition_service.update_stage_progress(
    task, "requirement_parsing", 50
)

# 完成阶段
stage_transition_service.complete_stage(task, "requirement_parsing")

# 获取并处理事件
events = task.get_pending_events()
for event in events:
    print(f"Event: {event.event_type.value}")
```

### 2. 创建需求

```python
from domain.value_objects import Requirement, SceneType

# 方式1：直接创建（会验证）
req = Requirement(
    ppt_topic="AI 发展历程",
    page_num=10,
    scene=SceneType.BUSINESS_REPORT
)

# 方式2：使用工厂方法（带默认值）
req = Requirement.with_defaults("AI 发展历程", page_num=10)

# 转换为字典
data = req.to_dict()

# 从字典恢复
req2 = Requirement.from_dict(data)
```

### 3. 使用领域服务

```python
from domain.services import (
    task_progress_service,
    task_validation_service
)

# 计算进度
progress = task_progress_service.calculate_overall_progress(task.stages)
print(f"Overall progress: {progress}%")

# 验证需求
try:
    task_validation_service.validate_requirement(requirement)
except ValidationError as e:
    print(f"Validation failed: {e.errors}")
```

### 4. 监听领域事件

```python
from domain.entities import Task
from domain.events import TaskEventType

task = Task(id="task_001", raw_input="Create PPT")
task.start_stage(TaskStage.REQUIREMENT_PARSING)
task.complete_stage(TaskStage.REQUIREMENT_PARSING)

# 获取事件
events = task.get_pending_events()
for event in events:
    if event.event_type == TaskEventType.TASK_STARTED:
        print(f"Task started at {event.timestamp}")
    elif event.event_type == TaskEventType.TASK_COMPLETED:
        print(f"Stage completed: {event.data['stage']}")

# 持久化事件
for event in events:
    event_store.append(event)
```

### 5. Agent 通信

```python
from domain.communication import AgentContext, AgentResult, ResultStatus

# 创建上下文
context = AgentContext(
    request_id="req_001",
    execution_mode=ExecutionMode.FULL
)

# 设置阶段数据
context.requirement = Requirement.with_defaults("AI Intro", 10)
context.update_stage(AgentStage.REQUIREMENT_PARSING)

# 创建结果
result = AgentResult.success(
    data=PPTFramework(...),
    message="Framework designed successfully"
)

# 检查结果
if result.is_success:
    print(f"Data: {result.data}")
elif result.needs_retry:
    print(f"Retry needed: {result.message}")
```

---

## 最佳实践

### 1. 实体设计

**✅ 推荐做法**：
```python
# 实体通过 ID 判断相等性
@dataclass
class Task:
    id: str
    status: TaskStatus

    def __eq__(self, other):
        return isinstance(other, Task) and self.id == other.id

    def __hash__(self):
        return hash(self.id)
```

**❌ 错误做法**：
```python
# 不要用所有字段判断相等性（这是值对象的做法）
def __eq__(self, other):
    return (
        self.id == other.id and
        self.status == other.status
    )
```

### 2. 值对象设计

**✅ 推荐做法**：
```python
@dataclass(frozen=True)
class Requirement(ValueObject, Serializable):
    ppt_topic: str

    def __post_init__(self):
        # 验证
        if not self.ppt_topic:
            raise ValidationError("Topic cannot be empty")
```

**❌ 错误做法**：
```python
# 不要让值对象可变
@dataclass  # 缺少 frozen=True
class Requirement:
    ppt_topic: str

    # 不要有修改状态的方法
    def update_topic(self, new_topic: str):
        self.topic = new_topic  # ❌
```

### 3. 领域服务使用

**✅ 推荐做法**：
```python
# 将业务逻辑放在领域服务中
from domain.services import task_validation_service

try:
    task_validation_service.validate_requirement(requirement)
except ValidationError as e:
    # 处理验证错误
    pass
```

**❌ 错误做法**：
```python
# 不要在应用层或基础设施层实现业务逻辑
def validate_requirement_in_app_layer(req):
    if not req.ppt_topic:  # ❌ 业务逻辑应该在领域层
        return False
    return True
```

### 4. 事件处理

**✅ 推荐做法**：
```python
# 在状态变更时发出事件
def complete_stage(self, stage: TaskStage) -> None:
    self.stages[stage].status = TaskStatus.COMPLETED

    # 发出事件
    event = create_stage_completed_event(
        version=self.metadata.revision_count,
        task_id=self.id,
        stage_name=stage.value
    )
    self._add_event(event)
```

**❌ 错误做法**：
```python
# 不要在实体中直接处理事件（如发送邮件）
def complete_stage(self, stage: TaskStage) -> None:
    self.stages[stage].status = TaskStatus.COMPLETED

    # ❌ 不要在实体中调用基础设施
    email_service.send_notification(...)
    database.save(...)
```

### 5. 异常处理

**✅ 推荐做法**：
```python
from domain.exceptions import ValidationError

try:
    requirement = Requirement(ppt_topic="", page_num=10)
except ValidationError as e:
    logger.error(f"Validation failed: {e.errors}")
    # 返回错误信息给用户
    return {"error": e.errors}
```

**❌ 错误做法**：
```python
# 不要使用通用异常
try:
    requirement = Requirement(ppt_topic="", page_num=10)
except ValueError as e:  # ❌ 不够具体
    pass
except Exception as e:  # ❌ 太宽泛
    pass
```

### 6. 序列化

**✅ 推荐做法**：
```python
# 所有领域模型都应该支持序列化
requirement = Requirement.with_defaults("AI", 10)

# 转字典
data = requirement.to_dict()

# 从字典恢复
req2 = Requirement.from_dict(data)

# 两者相等
assert requirement == req2
```

---

## 迁移指南

### 从旧 models 迁移到新 DDD 结构

#### 旧代码
```python
from domain.models import Task, TaskStatus, Requirement
```

#### 新代码
```python
# 实体
from domain.entities import Task, TaskStatus

# 值对象
from domain.value_objects import Requirement

# 服务
from domain.services import task_progress_service

# 异常
from domain.exceptions import ValidationError

# 事件
from domain.events import create_task_created_event
```

### 常见迁移模式

#### 1. 模型导入

```python
# 旧代码
from domain.models.task import Task

# 新代码
from domain.entities import Task
# 或者
from domain import Task  # 通过 __init__.py 导入
```

#### 2. 验证逻辑

```python
# 旧代码
req = Requirement(ppt_topic="AI", page_num=10)
is_valid, errors = req.validate()
if not is_valid:
    print(errors)

# 新代码
from domain.exceptions import ValidationError
from domain.services import task_validation_service

try:
    req = Requirement(ppt_topic="AI", page_num=10)
except ValidationError as e:
    print(e.errors)

# 或者使用服务
try:
    task_validation_service.validate_requirement(req)
except ValidationError as e:
    print(e.errors)
```

#### 3. 进度计算

```python
# 旧代码
progress = task.get_overall_progress()

# 新代码（使用服务）
from domain.services import task_progress_service
progress = task_progress_service.calculate_overall_progress(task.stages)
```

#### 4. 事件监听

```python
# 新代码
# Task 现在支持事件
task.start_stage(TaskStage.REQUIREMENT_PARSING)
events = task.get_pending_events()
for event in events:
    # 处理事件
    handle_event(event)
```

---

## 常见问题（FAQ）

### Q1: 为什么有些类在 models/ 和 entities/ 都有？

**A**: 为了保持向后兼容。`models/` 文件夹标记为 DEPRECATED，但仍然导出所有内容。新代码应该使用 `entities/` 和 `value_objects/`。

### Q2: 值对象为什么要不可变？

**A**:
- **线程安全**：不可变对象天然线程安全
- **一致性**：创建后不会意外修改
- **简化理解**：不需要跟踪对象的状态变化
- **可缓存**：相同值的对象可以共享

### Q3: 什么时候使用领域服务？

**A**: 当业务逻辑：
- 不属于单个实体或值对象
- 涉及多个领域对象
- 需要访问基础设施（如：验证服务）

### Q4: 如何处理领域事件？

**A**:
```python
# 1. 实体发出事件
task.complete_stage(TaskStage.REQUIREMENT_PARSING)

# 2. 应用层获取事件
events = task.get_pending_events()

# 3. 事件处理器处理
for event in events:
    event_handler.handle(event)

# 4. 持久化事件
event_store.store(events)
```

### Q5: 如何扩展领域模型？

**A**:
```python
# 1. 在相应模块创建新类
# backend/domain/value_objects/custom_value.py
@dataclass(frozen=True)
class CustomValue(ValueObject, Serializable):
    field: str

    def __post_init__(self):
        # 验证
        pass

# 2. 在 __init__.py 中导出
# backend/domain/value_objects/__init__.py
from .custom_value import CustomValue

# 3. 在主 __init__.py 中导出
# backend/domain/__init__.py
from .value_objects import CustomValue
```

---

## 附录

### A. 类型别名

```python
# 常用类型别名
TaskID = str
PresentationID = str
Progress = int  # 0-100
```

### B. 常量

```python
# 默认值
DEFAULT_PAGE_NUM = 10
DEFAULT_LANGUAGE = "中文"
DEFAULT_TIMEOUT = 300

# 限制
MAX_SLIDES = 100
MAX_RETRIES = 3
```

### C. 相关文档

- [DDD 重构总结](../backend/domain/DDD_RESTRUCTURE_SUMMARY.md)
- [后端架构文档](./backend-architecture.md)
- [多Agent系统文档](./multiagent/README.md)

---

## 重要修复说明

### 重复定义问题（已修复）

在 DDD 重构过程中发现了重复定义问题，已于 2025-02-04 修复：

**问题描述**：
- `AgentContext` 在 `models/agent_context.py` 和 `communication/agent_context.py` 中重复定义
- `AgentResult` 在 `models/agent_result.py` 和 `communication/agent_result.py` 中重复定义
- `ExecutionMode` 在多处定义

**解决方案**：
1. **删除重复文件**：移除 `models/agent_context.py` 和 `models/agent_result.py`
2. **统一权威版本**：保留 `communication/` 中的定义作为权威版本
3. **向后兼容**：通过 `models/__init__.py` 从 `communication/` 重新导出

**修复后的导入规则**：
```python
# ✅ 推荐方式（新代码）
from domain.communication import AgentContext, AgentResult

# ✅ 向后兼容（旧代码）
from domain.models import AgentContext, AgentResult

# ✅ 通用导入
from domain import AgentContext, AgentResult
```

**详细说明**：参见 [Domain Layer Fixes](./domain-layer-fixes.md)

### models/ 文件夹状态

**当前状态**：
- `models/` 文件夹保留以提供向后兼容
- **不再包含新的类定义**
- 通过重新导出来提供兼容性

**models/__init__.py 的作用**：
```python
# 本地定义
from .task import Task, TaskStatus, TaskStage
from .requirement import Requirement
# ... 其他本地定义

# 从 communication/ 重新导出（避免重复定义）
from ..communication.agent_context import AgentContext, AgentResult
from ..communication.agent_result import ResultStatus, ValidationResult
```

---

## 更新日志

### v2.0.1 (2025-02-04) - 修复重复定义

- ✅ 删除 `models/agent_context.py` 和 `models/agent_result.py`（重复定义）
- ✅ 更新 `models/__init__.py` 从 `communication/` 重新导出
- ✅ 更新 `agent_gateway.py` 使用新的导入路径
- ✅ 验证所有导入路径工作正常
- ✅ 创建修复文档：`docs/domain-layer-fixes.md`

### v2.0.0 (2025-02-04) - DDD 重构

- ✅ 创建 DDD 目录结构（entities, value_objects, services, etc.）
- ✅ 实现基础类（Entity, ValueObject, Serializable）
- ✅ 重构值对象为不可变（frozen=True）
- ✅ 添加领域验证（__post_init__）
- ✅ 创建领域服务（TaskProgressService, TaskValidationService, etc.）
- ✅ 实现领域事件系统
- ✅ 添加领域异常层次
- ✅ 创建配置模块
- ✅ 保持向后兼容性

### v1.0.0 (2025-01-XX) - 初始版本

- 基础领域模型
- Agent 接口定义

---

**文档版本**: 2.0.1
**最后更新**: 2025-02-04
**维护者**: MultiAgentPPT Team

