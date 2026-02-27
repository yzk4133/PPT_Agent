# MultiAgentPPT 项目架构文档

**版本**: 2.0.0
**更新日期**: 2026-02-09
**架构模式**: 分层架构 + LangChain Agent 系统

---

## 一、项目概览

### 项目定位
基于 LangChain 的多 Agent PPT 自动生成系统

### 核心理念
- **多 Agent 协作**: 不同 Agent 负责不同任务
- **状态驱动**: 通过 State 管理整个生成流程
- **检查点机制**: 支持断点续传
- **降级处理**: LLM 调用失败时的备用方案

---

## 二、整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        前端（Frontend）                       │
│                     (React / Vue / 其他)                      │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP Request
                               ↓
┌─────────────────────────────────────────────────────────────┐
│                       API 层 (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  api/main.py                                          │   │
│  │  - 启动配置                                            │   │
│  │  - 中间件注册                                          │   │
│  │  - CORS 处理                                           │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  api/routes/ppt_generation.py                         │   │
│  │  - POST /api/ppt/generate                            │   │
│  │  - POST /api/ppt/slides/generate                     │   │
│  │  - 参数验证                                           │   │
│  │  - 调用 MasterGraph                                   │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │ 调用
                               ↓
┌─────────────────────────────────────────────────────────────┐
│                   Agent 协调层 (Coordinator)                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  agents/coordinator/master_graph.py                   │   │
│  │  - MasterGraph (LangGraph)                            │   │
│  │  - 定义工作流: Research → Content → Render            │   │
│  │  - 状态管理: State                                     │   │
│  │  - 检查点: CheckpointManager                           │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  agents/coordinator/                                  │   │
│  │  - progress_tracker.py    # 进度跟踪                   │   │
│  │  - revision_handler.py    # 修订处理                   │   │
│  │  - page_pipeline.py       # 页面流水线                 │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │ 调用
                               ↓
┌─────────────────────────────────────────────────────────────┐
│                    Agent 核心 (Core Agents)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  agents/core/planning/framework_agent.py              │   │
│  │  - 功能: 设计 PPT 框架（大纲、主题、结构）              │   │
│  │  - 输入: 用户需求                                       │   │
│  │  - 输出: Framework（框架定义）                         │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  agents/core/research/research_agent.py               │   │
│  │  - 功能: 研究主题，收集信息                             │   │
│  │  - 输入: Framework, Topic                             │   │
│  │  - 输出: ResearchData（研究数据）                      │   │
│  │  - 工具: WebSearch, WebFetcher                        │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  agents/core/generation/content_agent.py              │   │
│  │  - 功能: 生成具体页面内容                              │   │
│  │  - 输入: Framework, PageConfig                        │   │
│  │  - 输出: PageContent（页面内容）                       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  agents/core/rendering/renderer_agent.py              │   │
│  │  - 功能: 渲染最终 PPT                                   │   │
│  │  - 输入: PageContent集合                               │   │
│  │  - 输出: PPT文件（.pptx）                              │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │ 使用
                               ↓
┌─────────────────────────────────────────────────────────────┐
│                   基础设施层 (Infrastructure)                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  infrastructure/config/common_config.py               │   │
│  │  - 环境变量管理                                        │   │
│  │  - 模型提供商配置                                      │   │
│  │  - Agent 配置                                         │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  infrastructure/checkpoint/                          │   │
│  │  - checkpoint_manager.py     # 检查点管理器           │   │
│  │  - database_backend.py      # 数据库后端接口         │   │
│  │  - 支持断点续传                                        │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  infrastructure/llm/fallback/                        │   │
│  │  - JSONFallbackParser        # JSON 解析降级         │   │
│  │  - LLM 返回非 JSON 时的备用解析                       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  infrastructure/middleware/                          │   │
│  │  - error_handler.py          # 全局异常处理           │   │
│  │  - rate_limit_middleware.py  # 速率限制               │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  infrastructure/exceptions/                          │   │
│  │  - BaseAPIException          # API 异常基类           │   │
│  │  - RateLimitExceededException                       │   │
│  │  - ValidationException                              │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │ 使用
                               ↓
┌─────────────────────────────────────────────────────────────┐
│                      数据模型层 (Models)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  models/execution_mode.py                            │   │
│  │  - ExecutionMode 枚举: SEQUENTIAL, PARALLEL          │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  models/checkpoint.py                                │   │
│  │  - Checkpoint 数据类                                  │   │
│  │  - 检查点状态存储结构                                  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  agents/models/                                      │   │
│  │  - state.py                    # Agent 状态          │   │
│  │  - framework.py               # 框架定义             │   │
│  │  - research.py                 # 研究数据             │   │
│  │  - content.py                  # 内容定义             │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │ 使用
                               ↓
┌─────────────────────────────────────────────────────────────┐
│                       工具层 (Utils)                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  utils/context_compressor.py                         │   │
│  │  - ContextCompressor                                 │   │
│  │  - 压缩 LLM 上下文，减少 token 使用                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、数据流向

### 完整的 PPT 生成流程

```
1. 用户请求
   ↓
   POST /api/ppt/generate
   { "topic": "人工智能", "requirements": "..." }

2. API 层接收
   ↓
   api/routes/ppt_generation.py
   - 验证参数
   - 创建初始 State

3. 启动 MasterGraph
   ↓
   agents/coordinator/master_graph.py
   - 创建 LangGraph StateGraph
   - 设置检查点
   - 开始执行工作流

4. 工作流执行
   ↓
   ┌─────────────────────────────────────────────┐
   │ Step 1: FrameworkAgent (规划)               │
   │ 输入: user_requirements                     │
   │ 输出: framework (大纲、主题、结构)           │
   └─────────────────────────────────────────────┘
   ↓
   ┌─────────────────────────────────────────────┐
   │ Step 2: ResearchAgent (研究)                │
   │ 输入: framework, topics                     │
   │ 输出: research_data (收集的信息)             │
   │ 工具: WebSearch, WebFetcher                │
   └─────────────────────────────────────────────┘
   ↓
   ┌─────────────────────────────────────────────┐
   │ Step 3: ContentAgent (内容生成)             │
   │ 输入: framework, research_data              │
   │ 输出: page_contents (每页的详细内容)         │
   │ 循环: 对每个页面执行                         │
   └─────────────────────────────────────────────┘
   ↓
   ┌─────────────────────────────────────────────┐
   │ Step 4: RendererAgent (渲染)                │
   │ 输入: page_contents, template               │
   │ 输出: ppt_file (.pptx)                       │
   └─────────────────────────────────────────────┘

5. 返回结果
   ↓
   { "ppt_path": "output.pptx", "status": "success" }
```

---

## 四、关键组件详解

### 4.1 MasterGraph (核心工作流)

**位置**: `agents/coordinator/master_graph.py`

**职责**:
- 定义 Agent 执行顺序
- 管理 State 传递
- 处理分支和循环
- 支持检查点（断点续传）

**关键代码**:
```python
from agents.coordinator.master_graph import MasterGraph, create_master_graph

# 创建工作流
graph = create_master_graph()

# 执行
result = graph.invoke({
    "topic": "人工智能",
    "requirements": "生成一个关于 AI 的 PPT"
})
```

---

### 4.2 State（状态管理）

**位置**: `agents/models/state.py`

**State 结构**:
```python
class AgentState(TypedDict):
    # 输入
    topic: str                    # 主题
    requirements: str             # 用户需求

    # 中间状态
    framework: Optional[dict]     # 框架定义
    research_data: Optional[dict] # 研究数据
    page_contents: List[dict]     # 页面内容

    # 输出
    ppt_path: Optional[str]       # PPT 文件路径
    error: Optional[str]          # 错误信息
```

**State 流转**:
```
Initial State
    ↓ [FrameworkAgent]
State + framework
    ↓ [ResearchAgent]
State + framework + research_data
    ↓ [ContentAgent] (循环每页)
State + framework + research_data + page_contents
    ↓ [RendererAgent]
State + ppt_path (最终结果)
```

---

### 4.3 检查点机制

**位置**: `infrastructure/checkpoint/`

**用途**:
- 保存执行状态
- 支持断点续传
- 防止长时间任务丢失

**使用**:
```python
from infrastructure.checkpoint import CheckpointManager

manager = CheckpointManager()
checkpoint = manager.save(
    task_id="task-123",
    state=current_state
)

# 恢复
restored = manager.restore("task-123")
```

---

### 4.4 降级处理

**位置**: `infrastructure/llm/fallback/`

**用途**:
- LLM 返回非标准 JSON 时
- 解析失败时的备用方案

**使用**:
```python
from infrastructure.llm.fallback import JSONFallbackParser

parser = JSONFallbackParser()
data = parser.parse(llm_response)  # 即使格式错误也能尝试解析
```

---

## 五、目录结构速查

```
backend/
│
├── api/                          # API 层
│   ├── main.py                   # FastAPI 应用入口
│   └── routes/
│       └── ppt_generation.py     # PPT 生成路由
│
├── agents/                       # Agent 系统
│   ├── coordinator/              # 协调器
│   │   ├── master_graph.py       # ⭐ 核心工作流
│   │   ├── progress_tracker.py   # 进度跟踪
│   │   ├── revision_handler.py   # 修订处理
│   │   └── page_pipeline.py      # 页面流水线
│   │
│   ├── core/                     # 核心 Agents
│   │   ├── planning/             # 规划 Agent
│   │   │   └── framework_agent.py
│   │   ├── research/             # 研究 Agent
│   │   │   └── research_agent.py
│   │   ├── generation/           # 生成 Agent
│   │   │   └── content_agent.py
│   │   └── rendering/            # 渲染 Agent
│   │       └── renderer_agent.py
│   │
│   ├── memory/                   # 记忆系统
│   ├── models/                   # 数据模型
│   ├── tools/                    # Agent 工具
│   └── tests/                    # 测试
│
├── infrastructure/               # 基础设施层
│   ├── checkpoint/               # 检查点管理
│   ├── config/                   # 配置管理
│   ├── exceptions/               # 异常定义
│   ├── llm/fallback/             # LLM 降级
│   └── middleware/               # 中间件
│
├── models/                       # 全局数据模型
│   ├── execution_mode.py
│   └── checkpoint.py
│
├── utils/                        # 工具函数
│   └── context_compressor.py
│
├── archive/                      # 历史归档（保留）
│
├── requirements.txt              # Python 依赖
├── pytest.ini                    # 测试配置
├── .env                          # 环境变量
└── __init__.py                   # 包导出
```

---

## 六、问题定位指南

### 6.1 按层级定位

| 症状 | 可能层级 | 检查位置 |
|------|---------|---------|
| 服务器无法启动 | Infrastructure / API | 依赖导入、配置文件 |
| API 返回 500 | API / Agent | 路由逻辑、Agent 调用 |
| Agent 不执行 | Agent / Coordinator | MasterGraph 定义、State 结构 |
| LLM 调用失败 | Infrastructure | API Key、模型配置 |
| PPT 生成错误 | Renderer Agent | 模板、渲染逻辑 |

### 6.2 常见问题

**问题 1: 服务器启动失败**
```bash
# 检查
python -c "from api.main import app"

# 可能原因:
# 1. 依赖缺失 → pip install -r requirements.txt
# 2. 导入错误 → 检查 __init__.py 导出
# 3. 配置错误 → 检查 .env 文件
```

**问题 2: Agent 执行失败**
```bash
# 检查 Agent 是否能创建
python -c "
from agents import create_master_graph
graph = create_master_graph()
print(graph)
"

# 可能原因:
# 1. LLM 配置错误 → 检查 API Key
# 2. State 结构不匹配 → 检查 agents/models/state.py
# 3. 工具未注册 → 检查 agents/tools/
```

**问题 3: 检查点保存失败**
```bash
# 检查
python -c "
from infrastructure.checkpoint import CheckpointManager
mgr = CheckpointManager()
print(mgr)
"

# 可能原因:
# 1. 数据库未连接 → 检查数据库配置
# 2. 权限问题 → 检查文件/目录权限
```

---

## 七、开发指南

### 7.1 添加新的 Agent

1. 在 `agents/core/` 下创建新文件
2. 继承或使用 LangChain Agent 模式
3. 定义输入输出 State
4. 在 `master_graph.py` 中注册

### 7.2 添加新的 API 端点

1. 在 `api/routes/` 下创建新文件
2. 定义路由和参数验证
3. 调用相应的 Agent 或服务
4. 在 `api/main.py` 中注册路由

### 7.3 修改工作流

1. 编辑 `agents/coordinator/master_graph.py`
2. 添加/移除/调整 Agent 节点
3. 更新 State 结构
4. 测试工作流执行

---

## 八、配置说明

### 8.1 环境变量 (.env)

```bash
# LLM 配置
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=xxx-xxx

# 应用配置
JWT_SECRET_KEY=your-secret-key
ENVIRONMENT=development

# 数据库（可选）
DATABASE_URL=sqlite:///./data.db
```

### 8.2 模型配置

**位置**: `infrastructure/config/common_config.py`

```python
class AgentConfig(BaseModel):
    provider: ModelProvider = ModelProvider.OPENAI
    model: str = "gpt-4"
    temperature: float = 0.7
```

---

## 九、测试指南

### 9.1 运行测试

```bash
# 运行所有测试
cd backend
pytest

# 运行特定测试
pytest agents/tests/test_base_agent.py

# 带覆盖率
pytest --cov=agents --cov-report=html
```

### 9.2 测试 API

```bash
# 启动服务器
python -m uvicorn api.main:app --reload

# 访问文档
http://localhost:8000/docs

# 测试健康检查
curl http://localhost:8000/api/health
```

---

## 十、附录

### A. 重要文件索引

| 文件 | 重要性 | 说明 |
|------|-------|------|
| `agents/coordinator/master_graph.py` | ⭐⭐⭐ | 核心工作流定义 |
| `api/routes/ppt_generation.py` | ⭐⭐⭐ | API 入口 |
| `infrastructure/config/common_config.py` | ⭐⭐⭐ | 配置管理 |
| `agents/models/state.py` | ⭐⭐ | State 定义 |
| `infrastructure/checkpoint/checkpoint_manager.py` | ⭐⭐ | 检查点管理 |

### B. 依赖关系图

```
API 层
  ↓ 依赖
Agent 层 (Coordinator + Core Agents)
  ↓ 依赖
Infrastructure 层 (Config, Checkpoint, Exceptions)
  ↓ 依赖
Models 层
  ↓ 依赖
Utils 层
```

---

**文档版本**: 2.0.0
**最后更新**: 2026-02-09
**维护者**: MultiAgentPPT Team
