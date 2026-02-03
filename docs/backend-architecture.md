# MultiAgentPPT Backend Architecture

> **版本**: 2.0
> **更新日期**: 2025-02-03
> **架构类型**: 8层分层架构 + 多Agent工作流

---

## 📋 目录

- [架构概览](#架构概览)
- [文件夹结构](#文件夹结构)
- [各层详解](#各层详解)
- [核心概念](#核心概念)
- [请求流程](#请求流程)
- [导入指南](#导入指南)
- [扩展指南](#扩展指南)
- [设计原则](#设计原则)
- [技术栈](#技术栈)

---

## 📐 架构概览

MultiAgentPPT 后端采用 **8层分层架构**，遵循 **DDD (Domain-Driven Design)** 和 **Clean Architecture** 原则，实现了一个可扩展、可维护的多Agent PPT生成系统。

### 架构层次图

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                            │  HTTP接口
│                    (FastAPI Routes + Schemas)               │
├─────────────────────────────────────────────────────────────┤
│                      Services Layer                         │  业务编排
│                 (Business Orchestration)                    │
├─────────────────────────────────────────────────────────────┤
│                   Orchestrator Layer                        │  工作流编排
│         (Workflow Definitions & Execution Engine)           │
├─────────────────────────────────────────────────────────────┤
│                       Agents Layer                          │  Agent实现
│        (Planning + Research + Generation + Tools)           │
├─────────────────────────────────────────────────────────────┤
│                     Domain Layer                           │  领域模型
│              (Domain Models + Interfaces)                   │
├─────────────────────────────────────────────────────────────┤
│                    Cognition Layer                          │  AI认知能力
│          (Prompts + Memory + Planning Logic)               │
├─────────────────────────────────────────────────────────────┤
│                 Infrastructure Layer                         │  技术设施
│            (LLM Factory + Config + MCP + Logging)           │
├─────────────────────────────────────────────────────────────┤
│                      Utils Layer                            │  通用工具
│                 (Common Utilities)                          │
└─────────────────────────────────────────────────────────────┘
```

### 依赖方向

```
┌─────────────────────────────────────────────────────┐
│  API ──> Services ──> Orchestrator ──> Agents        │
│                       ↓                │                │
│                    Domain ───────────┘                │
│                       ↓                                │
│                   Cognition                          │
│                       ↓                                │
│                Infrastructure                         │
│                       ↓                                │
│                     Utils                             │
└─────────────────────────────────────────────────────┘
```

**设计原则**: 单向依赖，上层依赖下层，下层不依赖上层

---

## 📁 文件夹结构

```
backend/
├── 🤖 agents/                          # Agent实现层
│   ├── applications/                   # FastAPI应用入口
│   │   ├── outline_generator/          # 大纲生成服务
│   │   │   ├── main_api.py             # FastAPI主入口
│   │   │   └── agents/                # 应用级Agent
│   │   └── ppt_generator/             # PPT生成服务
│   │       ├── main_api.py             # FastAPI主入口
│   │       └── agents/                # 应用级Agent
│   │
│   ├── core/                          # 核心Agent实现
│   │   ├── planning/                  # 规划Agent
│   │   │   └── topic_splitter_agent.py # 主题拆分Agent
│   │   ├── research/                  # 研究Agent
│   │   │   └── parallel_research_agent.py # 并行研究Agent
│   │   ├── generation/                # 生成Agent
│   │   │   └── slide_writer_agent.py  # 幻灯片生成Agent
│   │   ├── base/                      # 基础Agent类
│   │   └── factory/                   # Agent工厂
│   │
│   ├── tools/                         # ✨ 统一工具层
│   │   ├── registry/                  # 工具注册中心
│   │   │   ├── unified_registry.py     # 统一注册表（tools + skills）
│   │   │   └── tool_registry.py        # 原工具注册表（保留兼容）
│   │   ├── search/                    # 搜索工具
│   │   │   └── document_search.py      # 文档搜索
│   │   ├── media/                     # 媒体工具
│   │   │   └── image_search.py        # 图片搜索
│   │   ├── skills/                    # 技能框架（已合并）
│   │   │   ├── skill_wrapper.py       # 技能包装器
│   │   │   ├── skill_decorator.py     # @Skill装饰器
│   │   │   ├── skill_loaders.py       # 技能加载器
│   │   │   ├── skill_metadata.py      # 技能元数据
│   │   │   ├── skill_registry.py      # 技能注册表
│   │   │   └── managers/              # 技能管理器
│   │   └── mcp/                       # MCP工具适配
│   │       └── mcp_integration.py     # MCP集成
│   │
│   ├── workflows/                     # ✨ 工作流定义
│   │   └── ppt_generation_workflow.py # PPT生成工作流
│   │
│   └── orchestrator/                  # ✨ 工作流编排
│       └── workflow_executor.py       # 工作流执行引擎
│
├── 🧠 cognition/                      # ✨ AI认知能力层
│   ├── prompts/                       # 提示词管理
│   │   ├── templates/                 # 提示词模板
│   │   │   ├── planning_prompts.py    # 规划提示词
│   │   │   ├── research_prompts.py    # 研究提示词
│   │   │   └── generation_prompts.py  # 生成提示词
│   │   └── prompt_manager.py          # 提示词管理器
│   │
│   └── memory/                        # 记忆管理
│       ├── core/                      # 分层记忆
│       │   ├── core/                  # 核心组件
│       │   │   ├── hierarchical_memory_manager.py # 分层记忆管理器
│       │   │   ├── database.py         # 数据库管理
│       │   │   ├── redis_cache.py      # Redis缓存
│       │   │   └── models.py           # 数据模型
│       │   ├── services/              # 记忆服务
│       │   │   ├── agent_decision_service.py    # Agent决策服务
│       │   │   ├── context_optimizer.py         # 上下文优化器
│       │   │   ├── shared_workspace_service.py  # 共享工作空间
│       │   │   ├── tool_feedback_service.py      # 工具反馈服务
│       │   │   ├── user_preference_service.py    # 用户偏好服务
│       │   │   └── vector_memory_service.py       # 向量记忆服务
│       │   └── migrations/             # 数据迁移
│       └── basic/                     # 基础记忆
│
├── 📦 domain/                         # ✨ 领域层（原core/）
│   ├── models/                        # 领域模型
│   │   ├── presentation.py            # 演示文稿模型
│   │   ├── topic.py                   # 主题模型
│   │   ├── research.py                # 研究结果模型
│   │   └── slide.py                   # 幻灯片模型
│   └── interfaces/                    # 抽象接口
│       ├── agent.py                   # Agent接口
│       └── repository.py              # 仓储接口
│
├── 🔌 api/                            # API层
│   ├── routes/                        # 路由定义
│   │   └── presentation.py            # 演示文稿路由
│   ├── schemas/                       # 数据模式
│   │   ├── requests.py                # 请求模式
│   │   └── responses.py               # 响应模式
│   └── middleware/                    # 中间件
│
├── 💼 services/                       # 服务层
│   ├── presentation_service.py         # 演示文稿服务
│   └── outline_service.py             # 大纲服务
│
├── 🏗️ infrastructure/                 # 基础设施层
│   ├── config/                        # 配置管理
│   │   └── settings.py                # 配置设置
│   ├── llm/                           # LLM工厂
│   │   └── model_factory.py            # 模型工厂
│   ├── mcp/                           # MCP工具加载
│   ├── database/                      # 数据库
│   └── logging/                       # 日志
│
├── 🛠️ utils/                          # 工具层
│   └── common/                        # 通用工具
│       ├── config.py                  # 配置管理
│       ├── model_factory.py           # 模型工厂
│       ├── context_compressor.py     # 上下文压缩器
│       ├── retry_decorator.py         # 重试装饰器
│       ├── fallback/                  # 降级策略
│       └── tool_manager.py            # 工具管理器
│
├── 🧪 tests/                          # 测试
│   ├── unit/                          # 单元测试
│   ├── integration/                   # 集成测试
│   └── fixtures/                      # 测试夹具
│
├── 📚 docs/                           # 文档
│   └── backend/                       # 后端文档
│
└── 🗄️ archive/                        # 归档模块
```

---

## 📚 各层详解

### 1. API Layer (`api/`)

**职责**: 定义HTTP接口，处理请求和响应

#### 关键文件

- **`routes/presentation.py`**: 演示文稿相关的API路由
  - `POST /presentation/create` - 创建演示文稿
  - `GET /presentation/progress/{presentation_id}` - 查询生成进度
  - `GET /presentation/detail/{presentation_id}` - 查询演示文稿详情

- **`schemas/requests.py`**: 请求模式（Pydantic）
  - `PresentationCreateRequest`
  - `ProgressQueryRequest`

- **`schemas/responses.py`**: 响应模式（Pydantic）
  - `PresentationCreateResponse`
  - `PresentationDetailResponse`
  - `PresentationProgressResponse`

#### 示例代码

```python
from fastapi import APIRouter, BackgroundTasks
from api.schemas.requests import PresentationCreateRequest
from services import PresentationService

router = APIRouter(prefix="/presentation", tags=["presentation"])

@router.post("/create")
async def create_presentation(
    request: PresentationCreateRequest,
    background_tasks: BackgroundTasks
):
    service = PresentationService()
    presentation = await service.create_presentation(request)
    return {"presentation_id": presentation.id}
```

---

### 2. Services Layer (`services/`)

**职责**: 业务逻辑编排，协调多个Agent完成复杂任务

#### 关键文件

- **`presentation_service.py`**: 演示文稿服务
  - `create_presentation()` - 创建演示文稿
  - `generate_presentation()` - 三阶段生成流程

- **`outline_service.py`**: 大纲服务
  - `generate_outline()` - 生成大纲

#### 服务层工作流程

```python
class PresentationService:
    async def generate_presentation(self, presentation, context):
        # Stage 1: 主题拆分
        topics = await self._stage1_split_topics(presentation, context)

        # Stage 2: 并行研究
        research = await self._stage2_parallel_research(presentation, context, topics)

        # Stage 3: PPT生成
        ppt = await self._stage3_generate_ppt(presentation, context, research)

        return ppt
```

---

### 3. Orchestrator Layer (`agents/orchestrator/`, `agents/workflows/`)

**职责**: 定义和执行多Agent工作流

#### 关键文件

- **`workflows/ppt_generation_workflow.py`**: PPT生成工作流定义
  - 定义Agent执行顺序
  - 定义Agent间依赖关系
  - 支持串行、并行、DAG执行模式

- **`orchestrator/workflow_executor.py`**: 工作流执行引擎
  - 执行工作流定义
  - 处理并行执行
  - 错误处理和重试
  - 进度跟踪

#### 工作流定义示例

```python
class PPTGenerationWorkflow:
    """PPT生成工作流"""

    def __init__(self, execution_mode=ExecutionMode.SEQUENTIAL):
        self.execution_mode = execution_mode
        self._steps = [
            WorkflowStep(
                name="split_topics",
                agent_class=TopicSplitterAgent,
                description="拆分主题"
            ),
            WorkflowStep(
                name="research",
                agent_class=ParallelResearchAgent,
                description="并行研究",
                depends_on=["split_topics"]
            ),
            WorkflowStep(
                name="generate_slides",
                agent_class=SlideWriterAgent,
                description="生成幻灯片",
                depends_on=["research"]
            ),
        ]
```

#### 工作流执行示例

```python
async def generate_ppt(outline: str, num_slides: int):
    workflow = PPTGenerationWorkflow()
    executor = WorkflowExecutor()

    context = {
        "outline": outline,
        "num_slides": num_slides,
        "language": "EN-US"
    }

    results = await executor.execute(workflow, context)
    return results
```

---

### 4. Agents Layer (`agents/`)

**职责**: 实现各种Agent，封装LLM调用逻辑

#### 4.1 核心Agent (`agents/core/`)

##### Planning Agent - 主题拆分

```python
# agents/core/planning/topic_splitter_agent.py
from cognition.prompts import PromptManager

SPLIT_TOPIC_AGENT_PROMPT = PromptManager.get_split_topic_prompt()

split_topic_agent = Agent(
    name="SplitTopicAgent",
    model=create_model_with_fallback_simple(
        model="deepseek-chat",
        provider="deepseek"
    ),
    instruction=SPLIT_TOPIC_AGENT_PROMPT,
    output_key="split_topics"
)
```

**职责**: 将大纲拆分为3-8个独立的研究主题

**输出示例**:
```json
{
    "topics": [
        {
            "id": 1,
            "title": "主题标题",
            "description": "主题描述",
            "keywords": ["关键词1", "关键词2"],
            "research_focus": "研究重点"
        }
    ]
}
```

##### Research Agent - 并行研究

```python
# agents/core/research/parallel_research_agent.py
from cognition.prompts import PromptManager

RESEARCH_TOPIC_AGENT_PROMPT = PromptManager.get_research_topic_prompt()

class DynamicParallelSearchAgent(ParallelAgent):
    """动态并行搜索Agent"""

    async def _run_async_impl(self, ctx: InvocationContext):
        topics_output = ctx.session.state.get("split_topics", {})
        topic_list = json.loads(topics_output).get("topics", [])

        # 为每个主题动态创建子Agent
        dynamic_sub_agents = []
        for topic in topic_list:
            agent = Agent(
                model=research_model,
                instruction=f"{RESEARCH_TOPIC_AGENT_PROMPT}\n\n{topic}",
                tools=[DocumentSearch]
            )
            dynamic_sub_agents.append(agent)

        # 并行运行
        await _merge_agent_run([
            sub_agent.run_async(ctx)
            for sub_agent in dynamic_sub_agents
        ])
```

**职责**: 并行研究多个主题，每个主题独立执行

**工具**: `DocumentSearch(keyword: str, number: int)`

##### Generation Agent - 幻灯片生成

```python
# agents/core/generation/slide_writer_agent.py
from cognition.prompts import PromptManager

XML_PPT_AGENT_NEXT_PAGE_PROMPT = PromptManager.get_xml_ppt_generation_prompt

ppt_generator_loop_agent = LoopAgent(
    name="PPTGeneratorLoopAgent",
    max_iterations=100,
    sub_agents=[
        ppt_writer_sub_agent,
        ppt_checker_agent,
        SlideLoopConditionAgent(name="SlideCounter")
    ]
)
```

**职责**: 逐页生成PPT幻灯片，包含质量检查和重试机制

**工具**: `SearchImage(query: str)`

#### 4.2 工具层 (`agents/tools/`)

##### 统一工具注册表

```python
# agents/tools/registry/unified_registry.py
class UnifiedToolRegistry:
    """统一的工具和技能注册表"""

    def register(self, metadata: ToolMetadata, tool_func=None):
        """注册工具或技能"""
        self._tools[metadata.name] = ToolRegistration(
            metadata=metadata,
            tool_func=tool_func
        )

    def get_tool(self, tool_name: str):
        """获取工具"""
        return self._tools.get(tool_name)

    def list_tools(self, category=None):
        """列出工具"""
        if category:
            return self._categories.get(category, [])
        return list(self._tools.keys())
```

##### 可用工具

| 工具名称 | 类别 | 描述 | 文件位置 |
|---------|------|------|---------|
| DocumentSearch | SEARCH | 根据关键词搜索文档 | `agents/tools/search/document_search.py` |
| SearchImage | MEDIA | 根据关键词搜索图片 | `agents/tools/media/image_search.py` |

#### 4.3 技能框架 (`agents/tools/skills/`)

技能框架提供了动态加载和管理Agent技能的能力：

```python
# agents/tools/skills/skill_decorator.py
@Skill(
    name="web_search",
    description="搜索网络信息",
    category=SkillCategory.EXTERNAL,
    version="1.0.0"
)
async def web_search_tool(query: str) -> str:
    """搜索网络信息"""
    # 实现逻辑
    pass

# 技能会自动注册到UnifiedToolRegistry
```

---

### 5. Domain Layer (`domain/`)

**职责**: 定义领域模型和业务接口，与具体实现解耦

#### 5.1 领域模型 (`domain/models/`)

##### Presentation - 演示文稿模型

```python
# domain/models/presentation.py
@dataclass
class Presentation:
    """演示文稿模型"""

    id: str
    title: str
    outline: str
    status: PresentationStatus
    topics: Optional[TopicList]
    research_results: Optional[ResearchResults]
    slides: Optional[SlideList]
    metadata: PresentationMetadata
    generated_content: str
    created_at: datetime
    completed_at: Optional[datetime]

    def mark_generating(self):
        """标记为生成中"""
        self.status = PresentationStatus.GENERATING

    def mark_completed(self):
        """标记为已完成"""
        self.status = PresentationStatus.COMPLETED
        self.completed_at = datetime.now()
```

##### TopicList - 主题列表

```python
# domain/models/topic.py
@dataclass
class TopicList:
    """主题列表"""
    topics: List[Topic]
    total_count: int = field(init=False)

    def to_dict(self):
        return {
            "topics": [t.to_dict() for t in self.topics],
            "total_count": len(self.topics)
        }
```

##### ResearchResults - 研究结果

```python
# domain/models/research.py
@dataclass
class ResearchResults:
    """研究结果集合"""
    results: List[ResearchResult]
    success_count: int
    total_count: int

    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count
```

##### SlideList - 幻灯片列表

```python
# domain/models/slide.py
@dataclass
class SlideList:
    """幻灯片列表"""
    slides: List[Slide]
    total_count: int = field(init=False)
```

#### 5.2 接口定义 (`domain/interfaces/`)

##### Agent接口

```python
# domain/interfaces/agent.py
class IAgent(ABC):
    """Agent接口"""

    @abstractmethod
    def get_name(self) -> str:
        """获取Agent名称"""
        pass

    @abstractmethod
    async def run(self, context: AgentContext, input_data: Any) -> AgentResult:
        """执行Agent任务"""
        pass

class ITopicSplitterAgent(IAgent):
    """主题拆分Agent接口"""

    @abstractmethod
    async def split_topics(self, context: AgentContext, outline: str) -> List[Dict]:
        """拆分大纲为多个主题"""
        pass

class ISlideWriterAgent(IAgent):
    """幻灯片写入Agent接口"""

    @abstractmethod
    async def generate_slide(self, context: AgentContext, page_number: int,
                            research_content: str) -> str:
        """生成单张幻灯片"""
        pass
```

---

### 6. Cognition Layer (`cognition/`)

**职责**: 核心AI认知能力，包括提示词管理、记忆管理、规划算法

#### 6.1 提示词管理 (`cognition/prompts/`)

##### PromptManager - 提示词管理器

```python
# cognition/prompts/prompt_manager.py
class PromptManager:
    """集中式提示词管理"""

    _prompts = {
        "planning": {
            "v1": "...",  # 从planning_prompts.py加载
            "v2": "...",  # 未来版本
        },
        "research": {
            "v1": "...",  # 从research_prompts.py加载
        },
        "generation": {
            "v1": "...",  # 从generation_prompts.py加载
            "checker_v1": "...",
        }
    }

    @classmethod
    def get_prompt(cls, category: str, version: str = "v1", **kwargs):
        """获取提示词（支持模板变量）"""
        prompt = cls._prompts.get(category, {}).get(version, "")
        if kwargs:
            prompt = prompt.format(**kwargs)
        return prompt

    @classmethod
    def get_split_topic_prompt(cls):
        """便捷方法：获取主题拆分提示词"""
        return cls.get_prompt("planning", "v1")
```

##### 使用示例

```python
# 旧方式（硬编码）
SPLIT_TOPIC_AGENT_PROMPT = """
你是一位专业的主题划分专家...
"""

# 新方式（集中管理）
from cognition.prompts import PromptManager

SPLIT_TOPIC_AGENT_PROMPT = PromptManager.get_split_topic_prompt()

# 支持模板变量
prompt = PromptManager.get_prompt(
    "generation",
    page_num="3/10",
    research_doc=doc_content,
    language="EN-US"
)
```

#### 6.2 记忆管理 (`cognition/memory/`)

##### 分层记忆管理器

```python
# cognition/memory/core/hierarchical_memory_manager.py
class HierarchicalMemoryManager:
    """分层记忆管理器"""

    def __init__(self):
        self.l1_transient = L1TransientLayer()  # 瞬时记忆
        self.l2_short_term = L2ShortTermLayer()   # 短期记忆
        self.l3_longterm = L3LongTermLayer()      # 长期记忆

    async def store(self, key: str, value: Any,
                    level: MemoryLevel = MemoryLevel.SHORT_TERM):
        """存储记忆"""
        if level == MemoryLevel.TRANSIENT:
            self.l1_transient.store(key, value)
        elif level == MemoryLevel.SHORT_TERM:
            await self.l2_short_term.store(key, value)
        elif level == MemoryLevel.LONG_TERM:
            await self.l3_longterm.store(key, value)

    async def retrieve(self, key: str) -> Optional[Any]:
        """检索记忆（从L1到L3逐层查找）"""
        # L1: 瞬时记忆
        value = self.l1_transient.retrieve(key)
        if value:
            return value

        # L2: 短期记忆
        value = await self.l2_short_term.retrieve(key)
        if value:
            # 提升到L1
            self.l1_transient.store(key, value)
            return value

        # L3: 长期记忆
        value = await self.l3_longterm.retrieve(key)
        if value:
            # 提升到L2
            await self.l2_short_term.store(key, value)
            self.l1_transient.store(key, value)
            return value

        return None
```

##### 记忆服务

| 服务 | 文件 | 职责 |
|-----|------|------|
| AgentDecisionService | agent_decision_service.py | Agent决策记忆 |
| ContextOptimizer | context_optimizer.py | 上下文优化 |
| SharedWorkspaceService | shared_workspace_service.py | 共享工作空间 |
| ToolFeedbackService | tool_feedback_service.py | 工具反馈记忆 |
| UserPreferenceService | user_preference_service.py | 用户偏好管理 |
| VectorMemoryService | vector_memory_service.py | 向量记忆检索 |

---

### 7. Infrastructure Layer (`infrastructure/`)

**职责**: 提供技术基础设施

#### 7.1 配置管理

```python
# infrastructure/config/settings.py
class Settings(BaseSettings):
    """应用配置"""
    app_name: str = "MultiAgentPPT"
    debug: bool = False

    # LLM配置
    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-chat"
    llm_api_key: str

    # 数据库配置
    database_url: str

    class Config:
        env_file = ".env"

def get_agent_config(agent_name: str) -> AgentConfig:
    """获取Agent配置"""
    config = get_config()
    return getattr(config, f"{agent_name}_agent")
```

#### 7.2 LLM工厂

```python
# infrastructure/llm/model_factory.py
def create_model_with_fallback_simple(
    model: str,
    provider: str,
    fallback_model: Optional[str] = None
):
    """创建带降级的模型"""
    agent_config = AgentConfig(
        model=model,
        provider=ModelProvider(provider),
        enable_fallback=bool(fallback_model),
        fallback_model=fallback_model
    )
    return create_model_with_fallback(agent_config)
```

---

### 8. Utils Layer (`utils/`)

**职责**: 通用工具函数

#### 8.1 配置管理 (`utils/common/config.py`)

```python
class AppConfig(BaseSettings):
    """应用配置"""
    deepseek_api_key: str
    openai_api_key: Optional[str] = None

    # Agent配置
    split_topic_agent: AgentConfig
    research_agent: AgentConfig
    slide_writer_agent: AgentConfig

def get_config() -> AppConfig:
    """获取配置实例"""
    return AppConfig()
```

#### 8.2 模型工厂 (`utils/common/model_factory.py`)

```python
def create_model_with_fallback_simple(
    model: str,
    provider: str,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    fallback_model: Optional[str] = None
):
    """创建模型（简化接口）"""
    agent_config = AgentConfig(
        model=model,
        provider=ModelProvider(provider),
        temperature=temperature,
        max_tokens=max_tokens,
        enable_fallback=bool(fallback_model),
        fallback_model=fallback_model
    )
    return create_model_with_fallback(agent_config)
```

#### 8.3 上下文压缩器 (`utils/common/context_compressor.py`)

```python
class ContextCompressor:
    """上下文压缩器"""

    def compress_history(
        self,
        all_slides: List[str],
        current_index: int
    ) -> str:
        """压缩历史幻灯片内容"""
        # 提取关键信息
        compressed = []
        for slide in all_slides[:current_index]:
            compressed.append(self._extract_key_info(slide))

        return "\n\n".join(compressed)

    def get_token_savings(self, original: int, compressed: int):
        """计算token节省"""
        saved = original - compressed
        return {
            "original_chars": original,
            "compressed_chars": compressed,
            "saved_percentage": (saved / original * 100),
            "estimated_saved_tokens": saved / 4  # 粗略估计
        }
```

#### 8.4 重试装饰器 (`utils/common/retry_decorator.py`)

```python
@retry_with_exponential_backoff(
    max_retries=3,
    initial_delay=1.0,
    max_delay=10.0,
    backoff_multiplier=2.0
)
async def call_llm_api(prompt: str):
    """调用LLM API（带重试）"""
    # 实现逻辑
    pass
```

---

## 🔄 核心概念

### 1. 多Agent协作模式

系统采用**多Agent协作模式**，每个Agent负责特定任务：

1. **TopicSplitterAgent** - 拆分主题
2. **ParallelResearchAgent** - 并行研究
3. **SlideWriterAgent** - 生成幻灯片
4. **PPTCheckerAgent** - 质量检查

### 2. 工作流编排

```
┌─────────────────────────────────────────────────────┐
│  用户请求: "生成一个关于AI的PPT，10页"              │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│  WorkflowExecutor                                  │
│  ├─ 1. TopicSplitterAgent                         │
│  │    └─ 拆分为5个主题                              │
│  ├─ 2. ParallelResearchAgent (并行)                │
│  │    ├─ ResearchAgent#1 → 主题1研究                │
│  │    ├─ ResearchAgent#2 → 主题2研究                │
│  │    ├─ ResearchAgent#3 → 主题3研究                │
│  │    └─ ResearchAgent#4 → 主题4研究                │
│  └─ 3. SlideWriterAgent (循环10次)                 │
│     └─ PPTCheckerAgent (每页检查)                  │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│  生成完整的PPT XML                                  │
└─────────────────────────────────────────────────────┘
```

### 3. 提示词版本管理

提示词支持版本控制，便于A/B测试和迭代：

```python
# 使用v1版本
prompt_v1 = PromptManager.get_prompt("planning", "v1")

# 使用v2版本
prompt_v2 = PromptManager.get_prompt("planning", "v2")

# 列出所有版本
versions = PromptManager.list_versions("planning")
# ["v1", "v2"]
```

### 4. 工具与技能统一

工具和技能现在统一在 `UnifiedToolRegistry` 中管理：

```python
from agents.tools.registry import UnifiedToolRegistry

registry = UnifiedToolRegistry()

# 注册工具
registry.register(
    metadata=ToolMetadata(
        name="DocumentSearch",
        category=ToolCategory.SEARCH,
        description="搜索文档"
    ),
    tool_func=DocumentSearch
)

# 注册技能
registry.register_skill_wrapper(skill_wrapper)

# 获取所有工具
all_tools = registry.list_tools()

# 获取ADK工具
adk_tools = registry.get_adk_tools(include_skills=True)
```

---

## 🌊 请求流程

### 完整的PPT生成流程

```
1. 用户请求
   │
   └─> POST /presentation/create
       {
         "outline": "人工智能的发展历程",
         "num_slides": 10,
         "language": "EN-US"
       }

2. API层处理
   │
   └─> presentation_service.create_presentation()
       创建Presentation对象

3. 服务层编排
   │
   └─> presentation_service.generate_presentation()
       │
       ├─> Stage 1: 主题拆分
       │   │
       │   └─> split_topic_agent.run()
       │       输出: {"topics": [{id: 1, title: "...", ...}]}
       │
       ├─> Stage 2: 并行研究
       │   │
       │   └─> parallel_search_agent._run_async_impl()
       │       │
       │       ├─> 动态创建5个ResearchAgent
       │       │
       │       └─> 并行执行
       │           ├─> ResearchAgent#1 + DocumentSearch
       │           ├─> ResearchAgent#2 + DocumentSearch
       │           ├─> ResearchAgent#3 + DocumentSearch
       │           └─> ...
       │
       └─> Stage 3: PPT生成
           │
           └─> ppt_generator_loop_agent._run_async_impl()
               │
               ├─> 循环10次 (每次生成一页)
               │   │
               │   ├─> ppt_writer_sub_agent
               │   │   └─> 使用PromptManager获取提示词
               │   │   └─> 使用SearchImage搜索图片
               │   │   └─> 生成XML格式幻灯片
               │   │
               │   └─> ppt_checker_agent
               │       └─> 检查质量
               │           ├─> 合格 → 继续
               │           └─> 不合格 → 重写（最多3次）
               │
               └─> 汇总所有幻灯片

4. 返回结果
   │
   └─> <PRESENTATION>...</PRESENTATION>
       完整的PPT XML内容
```

---

## 📥 导入指南

### 基础导入

```python
# 领域模型
from domain.models import Presentation, PresentationRequest, TopicList
from domain.interfaces import IAgent, AgentContext

# 提示词管理
from cognition.prompts import PromptManager

# 工具注册
from agents.tools.registry import UnifiedToolRegistry, ToolCategory

# 工作流
from agents.workflows import PPTGenerationWorkflow
from agents.orchestrator import WorkflowExecutor

# Agent
from agents.core.planning.topic_splitter_agent import split_topic_agent
from agents.core.research.parallel_research_agent import parallel_search_agent
from agents.core.generation.slide_writer_agent import ppt_generator_loop_agent

# 工具
from agents.tools.search import DocumentSearch
from agents.tools.media import SearchImage

# 服务
from services.presentation_service import PresentationService

# 配置
from utils.common.config import get_config
from utils.common.model_factory import create_model_with_fallback_simple
```

### 迁移指南

| 旧导入路径 | 新导入路径 |
|-----------|-----------|
| `from core.models` | `from domain.models` |
| `from core.interfaces` | `from domain.interfaces` |
| `from tools.registry` | `from agents.tools.registry` |
| `from tools.search` | `from agents.tools.search` |
| `from memory.core` | `from cognition.memory.core` |
| `from common.config` | `from utils.common.config` |

---

## 🔧 扩展指南

### 添加新的Agent

#### 步骤1: 创建Agent文件

```python
# agents/core/my_category/my_agent.py
from google.adk.agents.llm_agent import Agent
from utils.common.model_factory import create_model_with_fallback_simple
from cognition.prompts import PromptManager

MY_AGENT_PROMPT = PromptManager.get_prompt("my_category", "v1")

my_agent = Agent(
    name="MyAgent",
    model=create_model_with_fallback_simple(
        model="deepseek-chat",
        provider="deepseek"
    ),
    instruction=MY_AGENT_PROMPT,
    output_key="my_result"
)
```

#### 步骤2: 添加提示词模板

```python
# cognition/prompts/templates/my_category_prompts.py
MY_AGENT_PROMPT = """
你是一个专业的...
"""
```

#### 步骤3: 注册到PromptManager

```python
# cognition/prompts/prompt_manager.py
from .templates.my_category_prompts import MY_AGENT_PROMPT

cls._prompts["my_category"] = {
    "v1": MY_AGENT_PROMPT
}
```

#### 步骤4: 在工作流中使用

```python
# agents/workflows/my_workflow.py
from agents.core.my_category.my_agent import my_agent

class MyWorkflow:
    def __init__(self):
        self._steps = [
            WorkflowStep(
                name="my_step",
                agent_class=my_agent.__class__,
                description="我的Agent步骤"
            )
        ]
```

### 添加新的工具

#### 步骤1: 实现工具函数

```python
# agents/tools/my_category/my_tool.py
from google.adk.tools import ToolContext

async def MyTool(param: str, tool_context: ToolContext) -> str:
    """工具描述"""
    # 实现逻辑
    return f"Result: {param}"
```

#### 步骤2: 注册工具

```python
# agents/tools/my_category/__init__.py
from .my_tool import MyTool

__all__ = ["MyTool"]
```

#### 步骤3: 在Agent中使用

```python
from agents.tools.my_category import MyTool

my_agent = Agent(
    name="MyAgent",
    model=...,
    instruction=...,
    tools=[MyTool]  # 添加工具
)
```

### 添加新的技能

#### 步骤1: 使用@Skill装饰器

```python
# agents/tools/skills/my_skills.py
from agents.tools.skills.skill_decorator import Skill
from agents.tools.skills.skill_metadata import SkillCategory

@Skill(
    name="my_skill",
    description="我的技能",
    category=SkillCategory.EXTERNAL,
    version="1.0.0",
    tags=["custom", "tool"]
)
async def my_skill_function(param: str) -> str:
    """技能实现"""
    return f"Skill result: {param}"
```

#### 步骤2: 技能会自动注册

技能会通过技能框架自动注册到 `UnifiedToolRegistry`。

---

## 🎯 设计原则

### 1. 单一职责原则 (SRP)
每个模块只负责一个明确的职责：
- **API层**: 只处理HTTP请求/响应
- **Service层**: 只编排业务逻辑
- **Agent层**: 只执行AI任务
- **Domain层**: 只定义业务模型

### 2. 依赖倒置原则 (DIP)
高层模块不依赖低层模块，都依赖抽象：
- Service层依赖 `domain.interfaces.IAgent`
- Agent实现依赖 `domain.models`

### 3. 开闭原则 (OCP)
对扩展开放，对修改关闭：
- 新增Agent: 在 `agents/core/` 添加
- 新增工具: 在 `agents/tools/` 添加并注册
- 新增提示词: 在 `cognition/prompts/templates/` 添加

### 4. 接口隔离原则 (ISP)
客户端不依赖不需要的接口

---

## 🛠️ 技术栈

### 核心框架
- **FastAPI**: Web框架
- **Google ADK**: Agent开发框架
- **Pydantic**: 数据验证
- **AsyncIO**: 异步编程

### LLM集成
- **DeepSeek**: 主LLM提供商
- **OpenAI**: 备用LLM提供商
- **降级策略**: 自动故障转移

### 数据存储
- **PostgreSQL**: 关系型数据库
- **Redis**: 缓存和会话存储
- **向量数据库**: 语义检索（可选）

### 工具库
- **Pydantic Settings**: 配置管理
- **Python-dotenv**: 环境变量管理
- **Logging**: 日志记录

---

## 📝 最佳实践

### 1. 错误处理

```python
from agents.core.base import AgentError

try:
    result = await agent.run(context, input_data)
except AgentError as e:
    logger.error(f"Agent执行失败: {e}")
    # 处理错误
```

### 2. 日志记录

```python
import logging

logger = logging.getLogger(__name__)

logger.info("开始生成PPT")
logger.debug(f"主题数量: {len(topics)}")
logger.warning("重试第3次")
logger.error("生成失败", exc_info=True)
```

### 3. 配置管理

```python
# 使用环境变量
import os
from pydantic import Field

class Settings(BaseSettings):
    api_key: str = Field(default=..., env="API_KEY")

    class Config:
        env_file = ".env"

settings = Settings()
```

### 4. 异步编程

```python
import asyncio

async def main():
    # 并行执行多个任务
    results = await asyncio.gather(
        task1(),
        task2(),
        task3()
    )

    # 超时控制
    result = await asyncio.wait_for(task(), timeout=30.0)
```

### 5. 资源清理

```python
async with async_session() as session:
    yield session
    # 自动清理
```

---

## 🐛 故障排查

### 常见问题

#### 1. 导入错误

**问题**: `ModuleNotFoundError: No module named 'core.models'`

**解决**: 使用新的导入路径
```python
# 错误
from core.models import Presentation

# 正确
from domain.models import Presentation
```

#### 2. Agent执行失败

**问题**: `TypeError: 'Agent' object is not callable`

**解决**: Agent对象不是函数，需要通过runner执行
```python
# 错误
result = agent(input_data)

# 正确
invocation_context = InvocationContext(...)
result = await agent.run_async(invocation_context)
```

#### 3. 提示词未更新

**问题**: Agent使用旧版提示词

**解决**: 确保使用 `PromptManager`
```python
from cognition.prompts import PromptManager

prompt = PromptManager.get_prompt("planning", "v2")
```

---

## 📚 相关文档

- [ARCHITECTURE.md](../backend/ARCHITECTURE.md) - 后端架构文档（旧版）
- [README.md](../README.md) - 项目说明
- [API Documentation](./api/) - API接口文档

---

## 📞 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。

**维护者**: MultiAgentPPT Team
**版本**: 2.0
**最后更新**: 2025-02-03
