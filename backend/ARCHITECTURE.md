# Backend Architecture Documentation

> **MultiAgentPPT 后端架构文档**
>
> **版本**: 2.0 (7层分层架构)
> **最后更新**: 2026-02-02

---

## 📐 架构概览

MultiAgentPPT 后端采用 **8层分层架构**，遵循 **DDD (Domain-Driven Design)** 和 **Clean Architecture** 原则。

### 架构层次

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                            │  ← HTTP接口
│                    (FastAPI Routes)                         │
├─────────────────────────────────────────────────────────────┤
│                      Services Layer                         │  ← 业务编排
│                 (Business Orchestration)                    │
├─────────────────────────────────────────────────────────────┤
│                   Orchestrator Layer                        │  ← 工作流编排
│         (Workflow Definitions & Execution Engine)           │
├─────────────────────────────────────────────────────────────┤
│                       Agents Layer                          │  ← Agent实现
│        (Planning, Research, Generation + Unified Tools)     │
├─────────────────────────────────────────────────────────────┤
│                     Domain Layer                           │  ← 领域模型
│              (Domain Models + Interfaces)                  │
├─────────────────────────────────────────────────────────────┤
│                    Cognition Layer                          │  ← AI认知能力
│          (Prompts, Memory, Planning Algorithms)            │
├─────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                     │  ← 技术设施
│            (LLM Factory, Config, MCP Loader)               │
├─────────────────────────────────────────────────────────────┤
│                        Utils Layer                          │  ← 通用工具
│                 (Common Utilities)                         │
└─────────────────────────────────────────────────────────────┘
```

### 依赖原则

**单向依赖**: 上层依赖下层，下层不依赖上层

```
API → Services → Orchestrator → Agents → Domain → Cognition → Infrastructure
                                                          ↓
                                                        Utils
```

---

## 📦 各层详解

### 1. API Layer (`api/`)

**职责**: 定义HTTP接口，处理请求和响应

```
api/
├── routes/
│   └── presentation.py      # 演示文稿路由
├── schemas/
│   ├── requests.py          # 请求模式（Pydantic）
│   └── responses.py         # 响应模式（Pydantic）
└── middleware/
    └── [待实现]             # 中间件
```

**示例**:
```python
# api/routes/presentation.py
@router.post("/create")
async def create_presentation(request: PresentationCreateRequest):
    service = PresentationService()
    presentation = await service.create_presentation(request)
    return PresentationCreateResponse(**presentation.to_dict())
```

---

### 2. Services Layer (`services/`)

**职责**: 业务逻辑编排，协调多个Agent完成复杂任务

```
services/
├── presentation_service.py    # 演示文稿服务
└── outline_service.py         # 大纲服务
```

**示例**:
```python
# services/presentation_service.py
class PresentationService:
    async def generate_presentation(self, request):
        # Stage 1: 拆分主题
        topics = await self.split_agent.run(request.outline)

        # Stage 2: 并行研究
        research = await self.research_agent.run_parallel(topics)

        # Stage 3: 生成PPT
        ppt = await self.writer_agent.run(research)

        return ppt
```

---

### 3. Orchestrator Layer (`agents/orchestrator/`, `agents/workflows/`)

**职责**: 定义和执行多Agent工作流

```
agents/
├── workflows/
│   ├── ppt_generation_workflow.py    # PPT生成工作流定义
│   └── outline_generation_workflow.py # 大纲生成工作流定义
└── orchestrator/
    └── workflow_executor.py          # 工作流执行引擎
```

**示例**:
```python
# agents/workflows/ppt_generation_workflow.py
workflow = PPTGenerationWorkflow()
executor = WorkflowExecutor()
results = await executor.execute(workflow, context)
```

---

### 4. Agents Layer (`agents/`)

**职责**: 实现各种Agent，封装LLM调用逻辑

```
agents/
├── core/
│   ├── planning/
│   │   └── topic_splitter_agent.py      # 主题拆分Agent
│   ├── research/
│   │   └── parallel_research_agent.py   # 并行研究Agent
│   ├── generation/
│   │   └── slide_writer_agent.py        # 幻灯片写入Agent
│   ├── base/                             # 基础Agent类
│   └── factory/                          # Agent工厂
├── tools/                                # 统一工具层
│   ├── registry/
│   │   └── unified_registry.py          # 统一工具注册表
│   ├── search/
│   │   └── document_search.py           # 文档搜索
│   ├── media/
│   │   └── image_search.py              # 图片搜索
│   ├── skills/                          # 技能框架
│   └── mcp/                             # MCP工具适配器
└── applications/                         # FastAPI应用入口
    ├── ppt_generator/
    └── outline_generator/
```

**示例**:
```python
# agents/core/planning/topic_splitter_agent.py
from cognition.prompts import PromptManager

split_topic_agent = Agent(
    name="SplitTopicAgent",
    model=create_agent_model("split_topic"),
    instruction=PromptManager.get_split_topic_prompt(),
    output_key="split_topics"
)
```

---

### 5. Domain Layer (`domain/`)

**职责**: 定义领域模型和业务接口，与具体实现解耦

```
domain/
├── models/
│   ├── topic.py              # 主题领域模型
│   ├── research.py           # 研究结果领域模型
│   ├── slide.py              # 幻灯片领域模型
│   └── presentation.py       # 演示文稿领域模型
└── interfaces/
    ├── agent.py              # Agent接口
    └── repository.py         # 数据仓库接口
```

**示例**:
```python
# domain/models/presentation.py
@dataclass
class Presentation:
    id: str
    title: str
    outline: str
    status: PresentationStatus
    topics: Optional[TopicList]
    research_results: Optional[ResearchResults]
    slides: Optional[SlideList]
```

---

### 6. Cognition Layer (`cognition/`)

**职责**: 核心AI认知能力，包括提示词管理、记忆管理、规划算法

```
cognition/
├── prompts/
│   ├── templates/
│   │   ├── planning_prompts.py        # 规划相关提示词
│   │   ├── research_prompts.py        # 研究相关提示词
│   │   └── generation_prompts.py      # 生成相关提示词
│   └── prompt_manager.py              # 提示词管理器
├── memory/
│   ├── core/
│   │   ├── hierarchical_memory_manager.py
│   │   └── database.py
│   └── basic/
└── planning/                           # 规划算法（待实现）
```

**示例**:
```python
# cognition/prompts/prompt_manager.py
from cognition.prompts import PromptManager

prompt = PromptManager.get_prompt(
    "planning",
    version="v1",
    outline="My outline"
)
```

---

### 7. Infrastructure Layer (`infrastructure/`)

**职责**: 提供技术基础设施和服务

**设计原则**:
- 与业务逻辑无关的技术组件
- 提供可配置的技术能力
- 可替换的实现（如LLM提供商、数据库）

```
infrastructure/
├── config/                     # ✅ 配置管理
│   ├── common_config.py        # 统一配置
│   └── settings.py             # 环境变量配置
├── llm/                        # ✅ LLM集成
│   ├── common_model_factory.py # 模型工厂（降级、熔断）
│   ├── model_factory.py        # Agent模型工厂
│   ├── retry_decorator.py      # 重试装饰器
│   └── fallback/               # 降级策略框架
│       ├── __init__.py
│       └── ...
├── tools/                      # ✅ 工具管理
│   ├── tool_manager.py         # 工具管理器
│   └── a2a_client.py           # A2A客户端
├── utils/                      # ✅ Infrastructure工具
│   └── context_compressor.py   # 上下文压缩器
├── mcp/                        # ✅ MCP工具
│   └── mcp_loader.py           # MCP工具加载器
├── logging/                    # 日志配置
└── database/                   # 数据库连接
```

**导入路径**:
```python
# 配置
from infrastructure.config import get_config, AppConfig
from infrastructure import get_agent_config

# LLM
from infrastructure.llm import create_model_with_fallback, create_agent_model
from infrastructure.llm import retry_with_exponential_backoff, RetryableError
from infrastructure.llm.fallback import JSONFallbackParser, PartialSuccessHandler, FallbackChain

# 工具
from infrastructure.tools import UnifiedToolManager, get_tool_manager

# 工具函数
from infrastructure.utils import ContextCompressor

# MCP
from infrastructure.mcp import load_mcp_tools, get_mcp_manager
```

---

### 8. Utils Layer (`utils/`)

**职责**: 通用工具函数（纯函数、无状态）

**特征**:
- 无状态的纯函数
- 不依赖配置、不涉及外部服务
- 高度可复用的业务无关计算

```
utils/
├── save_ppt/                   # ✅ PPT文件操作
│   ├── main_api.py
│   ├── ppt_generator.py
│   └── look_master.py
└── common/                     # ⚠️ 已弃用（迁移到 infrastructure）
    └── __init__.py             # 仅保留向后兼容
```

**迁移说明**:
- `utils.common` 已弃用，请使用 `infrastructure` 模块
- `utils.save_ppt` 保留用于PPT文件操作
- 参见 `utils/common/__init__.py` 中的详细迁移路径

---

## 🔄 请求流程

### 完整的PPT生成流程

```
┌─────────────┐
│   User      │ 发送PPT生成请求
└──────┬──────┘
       ↓
┌─────────────────────────────────────┐
│   API Layer (FastAPI Endpoint)      │  接收HTTP请求
│   POST /presentation/create         │
└──────┬──────────────────────────────┘
       ↓
┌─────────────────────────────────────┐
│   Services Layer                    │  业务编排
│   PresentationService               │
└──────┬──────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│   Orchestrator Layer                 │  工作流定义和执行
│   PPTGenerationWorkflow              │
│   WorkflowExecutor                   │
└──────┬───────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│   Agents Layer (3个Agent)            │
│   ├─ split_topic_agent             │  Stage 1: 拆分主题
│   ├─ parallel_search_agent         │  Stage 2: 并行研究
│   └─ ppt_generator_loop_agent      │  Stage 3: 生成PPT
└──────┬───────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│   Domain Layer (Domain Models)      │  数据模型
│   Presentation, Topic, Slide        │
└──────┬───────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│   Cognition Layer                    │  提示词和记忆
│   PromptManager, Memory              │
└──────┬───────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│   Agents Tools                       │  工具调用
│   DocumentSearch, SearchImage       │
└──────┬───────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│   Infrastructure Layer              │  技术支持
│   LLM Factory, Config, MCP          │
└──────┬───────────────────────────────┘
       ↓
┌─────────────┐
│   User      │ 接收PPT内容
└─────────────┘
```

---

## 🔄 请求流程

### 完整的PPT生成流程

```
┌─────────────┐
│   User      │ 发送PPT生成请求
└──────┬──────┘
       ↓
┌─────────────────────────────────────┐
│   API Layer (FastAPI Endpoint)      │  接收HTTP请求
│   POST /presentation/create         │
└──────┬──────────────────────────────┘
       ↓
┌─────────────────────────────────────┐
│   Services Layer                    │  业务编排
│   PresentationService               │
│   ├─ create_presentation()         │
│   └─ generate_presentation()       │
└──────┬──────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│   Agents Layer (3个Agent)            │
│   ├─ split_topic_agent             │  Stage 1: 拆分主题
│   ├─ parallel_search_agent         │  Stage 2: 并行研究
│   └─ ppt_generator_loop_agent      │  Stage 3: 生成PPT
└──────┬───────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│   Core Layer (Domain Models)        │  数据模型
│   Presentation, Topic, Slide        │
└──────┬───────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│   Infrastructure Layer              │  技术支持
│   LLM Factory, Config, MCP          │
└──────┬───────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│   Tools Layer                       │  工具调用
│   DocumentSearch, SearchImage       │
└──────────────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│   Memory Layer                      │  数据存储
│   User Prefs, Vector Store          │
└──────────────────────────────────────┘
       ↓
┌─────────────┐
│   User      │ 接收PPT内容
└─────────────┘
```

---

## 🎯 设计原则

### 1. 单一职责原则 (SRP)
每层只负责一个明确的职责

### 2. 依赖倒置原则 (DIP)
高层模块不依赖低层模块，都依赖抽象（Core Layer的接口）

### 3. 开闭原则 (OCP)
对扩展开放，对修改关闭
- 新增Agent：在`agents/`添加，在`factory/`注册
- 新增工具：在`tools/`添加，在`registry/`注册

### 4. 接口隔离原则 (ISP)
客户端不依赖不需要的接口

---

## 🔧 扩展指南

### 添加新Agent

1. **实现Agent**
```python
# agents/core/my_category/my_agent.py
from cognition.prompts import PromptManager

my_agent = Agent(
    name="MyAgent",
    model=create_agent_model("my_agent"),
    instruction=PromptManager.get_prompt("my_category", "v1")
)
```

2. **注册到工厂**
```python
# agents/core/factory/agent_factory.py
def create_my_agent(config):
    return my_agent
```

3. **使用**
```python
from agents.core.factory import AgentFactory
agent = AgentFactory.create_my_agent(config)
```

### 添加新工具

1. **实现工具**
```python
# agents/tools/my_category/my_tool.py
async def my_tool(param: str):
    return result
```

2. **注册工具**
```python
from agents.tools.registry import register_tool, ToolCategory

register_tool(
    name="MyTool",
    category=ToolCategory.UTILITY,
    description="My tool description",
    tool_func=my_tool
)
```

3. **使用**
```python
from agents.tools.registry import get_tool
tool = get_tool("MyTool")
result = await tool.tool_func("param")
```

### 添加新提示词

1. **创建提示词模板**
```python
# cognition/prompts/templates/my_category_prompts.py
MY_AGENT_PROMPT = """
你是一个专业的...
"""
```

2. **注册到PromptManager**
```python
# cognition/prompts/prompt_manager.py
from .templates.my_category_prompts import MY_AGENT_PROMPT

cls._prompts["my_category"]["v1"] = MY_AGENT_PROMPT
```

3. **使用**
```python
from cognition.prompts import PromptManager

prompt = PromptManager.get_prompt("my_category", "v1")
```

---

## 📊 架构对比

### 旧架构 vs 新架构

| 方面 | 旧架构 | 新架构 |
|------|--------|--------|
| **目录结构** | 分散在各子项目 | 统一8层结构 |
| **代码复用** | ❌ 代码重复60% | ✅ 共享agents/tools |
| **依赖管理** | ❌ 循环依赖 | ✅ 单向依赖 |
| **Agent管理** | ❌ 分散在各子项目 | ✅ 统一工厂模式 |
| **工具管理** | ❌ 每个Agent自带工具 | ✅ 统一工具注册中心 |
| **提示词管理** | ❌ 硬编码在各Agent | ✅ PromptManager集中管理 |
| **工作流编排** | ❌ 分散在Services | ✅ WorkflowExecutor统一编排 |
| **记忆管理** | ❌ 顶层目录混乱 | ✅ 归属Cognition认知层 |
| **领域模型** | ⚠️ core命名过于通用 | ✅ domain符合DDD术语 |
| **可测试性** | ⚠️ 难以单元测试 | ✅ 各层独立测试 |
| **可扩展性** | ⚠️ 需修改多处 | ✅ 插件式扩展 |

---

## 🔍 关键文件说明

### 入口文件

| 文件 | 端口 | 说明 |
|------|------|------|
| `flat_slide_agent/main_api.py` | 10012 | **推荐** - 新架构PPT生成 |
| `flat_slide_outline/main_api.py` | 10002 | **推荐** - 新架构大纲生成 |
| `slide_agent/main_api.py` | 10011 | 旧架构PPT生成（保留） |
| `slide_outline/main_api.py` | 10001 | 旧架构大纲生成（保留） |

### 配置文件

| 文件 | 说明 |
|------|------|
| `infrastructure/config/common_config.py` | 统一配置管理（Pydantic Settings） |
| `infrastructure/llm/common_model_factory.py` | LLM模型工厂（支持多提供商） |
| `.env` | 环境变量配置 |

---

## ⚠️ 已知问题与解决方案

### 1. Pydantic版本兼容性

**问题**: `infrastructure/config/common_config.py` 使用 Pydantic v1 语法
```python
from pydantic import BaseSettings  # v1语法
```

**解决**: 安装 pydantic-settings
```bash
pip install pydantic-settings
```

或升级到 v2 语法：
```python
from pydantic_settings import BaseSettings  # v2语法
```

### 2. 导入路径

确保Python路径包含backend目录：
```python
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
```

**新的导入路径**:
```python
# 领域模型 (原 core.models)
from domain.models import Presentation, PresentationRequest

# 接口 (原 core.interfaces)
from domain.interfaces import AgentContext, IAgent

# 提示词管理 (新)
from cognition.prompts import PromptManager

# 工具注册 (原 tools)
from agents.tools.registry import UnifiedToolRegistry, register_tool, ToolCategory

# 工作流编排 (新)
from agents.workflows import PPTGenerationWorkflow
from agents.orchestrator import WorkflowExecutor
```

---

## 📚 相关文档

- [README.md](./README.md) - 目录结构说明
- [MIGRATION_PROGRESS.md](./MIGRATION_PROGRESS.md) - 迁移进度
- [MIGRATION_SUMMARY.md](./MIGRATION_SUMMARY.md) - 迁移总结

---

**维护者**: Claude Code
**版本**: 2.1 (新增"1主5子"架构)
**状态**: Phase 1-5 完成 ✅ | Phase 6 优化中 🚧 | 新架构实现完成 ✅

---

## 🆕 "1主5子"多智能体架构

### 架构概览

基于《PPT生成多智能体架构设计文档》，项目新增了一个完整的多智能体架构，实现设计文档中的功能。

```
┌─────────────────────────────────────────────────────────────┐
│                   主协调智能体 (Master)                       │
│  6大核心功能：任务建模、动态调度、信息中转、交叉校验、      │
│              容错兜底（3次重试）、进度管理                  │
├─────────────────────────────────────────────────────────────┤
│  子智能体1: 需求解析智能体 → 自然语言转结构化需求           │
│  子智能体2: 框架设计智能体 → PPT页序+每页定义                │
│  子智能体3: 资料研究智能体 → 外部资料检索+整理（可选）       │
│  子智能体4: 内容素材智能体 → 文字+图表+配图生成              │
│  子智能体5: PPT模板渲染智能体 → 基于模板填充和渲染          │
└─────────────────────────────────────────────────────────────┘
```

### 各智能体详细说明

#### 1. 主协调智能体 (Master Coordinator Agent)

**文件位置**: `backend/agents/orchestrator/master_coordinator.py`

**核心功能**:
1. **需求入口与分发**: 接收用户输入，生成任务ID
2. **任务建模与调度**: DAG方式调度5个子智能体
3. **信息中转**: 在各智能体间传递上下文数据
4. **全流程校验**: 交叉校验需求、框架、研究结果的一致性
5. **容错兜底**: 每个子智能体支持3次重试，失败后使用默认值
6. **进度管理**: 细粒度进度追踪（15% → 30% → 50% → 80% → 100%）

**使用方式**:
```python
from agents.orchestrator.master_coordinator import master_coordinator_agent

# 通过Master Coordinator执行完整流程
async for event in master_coordinator_agent.run_async(ctx):
    # 处理事件
    pass
```

#### 2. 需求解析智能体 (Requirement Parser Agent)

**文件位置**: `backend/agents/core/requirements/requirement_parser_agent.py`

**核心功能**:
- 从自然语言中提取核心要素（主题、场景、行业、受众、页数、模板类型）
- 模糊需求补全（默认值）
- 需求结构化（输出标准化JSON）
- 自校验（完整性、合理性校验）

**输出格式**:
```json
{
  "ppt_topic": "PPT主题",
  "scene": "business_report",
  "industry": "所属行业",
  "audience": "目标受众",
  "page_num": 15,
  "template_type": "business_template",
  "core_modules": ["模块1", "模块2"],
  "need_research": true
}
```

#### 3. 框架设计智能体 (Framework Designer Agent)

**文件位置**: `backend/agents/core/planning/framework_designer_agent.py`

**核心功能**:
- 根据需求设计PPT页序（封面→目录→内容页→总结）
- 为每页定义标题、核心内容、是否需要图表/研究资料
- 模板布局适配（标注图表区、配图区）
- 自校验（页数匹配、逻辑连贯）

**输出格式**:
```json
{
  "total_page": 15,
  "ppt_framework": [
    {
      "page_no": 1,
      "title": "封面",
      "page_type": "cover",
      "is_need_chart": false,
      "is_need_research": false
    }
  ]
}
```

#### 4. 资料研究智能体 (Research Agent - 优化版)

**文件位置**: `backend/agents/core/research/research_agent.py`

**核心改进**:
- **精准匹配**: 仅研究框架中标注 `is_need_research=true` 的页面
- **权威来源**: 标注资料来源（如：艾瑞咨询）
- **结构化整理**: 按页码组织研究结果
- **可开关控制**: 根据 `need_research` 字段决定是否执行

#### 5. 内容素材智能体 (Content Material Agent)

**文件位置**: `backend/agents/core/generation/content_material_agent.py`

**核心功能**:
- 文字内容生成（融合研究结果）
- 图表生成（基于数据）
- 配图匹配（基于主题）
- 与PPT渲染分离，专注素材生成

#### 6. PPT模板渲染智能体 (Template Renderer Agent)

**文件位置**: `backend/agents/core/rendering/template_renderer_agent.py`

**核心功能**:
- 模板加载（根据 template_type）
- 页面扩容
- 内容与素材填充
- 基础优化（目录、页码）
- 文件生成与前端预览数据生成

### 修订机制

**文件位置**: `backend/agents/orchestrator/revision_handler.py`

支持的修订类型:
1. **修改模板** → 仅重跑 `template_renderer`
2. **修改文字** → 仅重跑 `content_material` + `template_renderer`
3. **补充数据** → 仅重跑 `research` + `content_material` + `template_renderer`
4. **增减页数** → 重跑 `framework_designer` + 后续所有

### 进度追踪器

**文件位置**: `backend/agents/orchestrator/progress_tracker.py`

功能:
- 细粒度进度追踪（每阶段独立进度）
- WebSocket实时进度推送支持
- 进度订阅/取消订阅机制

### 任务服务

**文件位置**: `backend/services/task_service.py`

功能:
- 任务创建
- 任务状态追踪
- 任务结果检索
- 任务修订处理

### 使用示例

```python
# 方式1: 直接使用Master Coordinator
from agents.orchestrator.master_coordinator import master_coordinator_agent

async for event in master_coordinator_agent.run_async(ctx):
    print(f"Progress: {event.content}")

# 方式2: 通过Task Service
from services.task_service import get_task_service

task_service = get_task_service()
task = await task_service.create_task(
    user_input="生成一份AI介绍PPT",
    user_id="user123"
)
result = await task_service.execute_task(task)

# 方式3: 使用修订机制
revision_result = await task_service.handle_revision(
    task_id="task_xxx",
    revision_request={
        "revision_type": "template_change",
        "new_template_type": "creative_template"
    }
)
```

### 新增领域模型

**文件位置**:
- `backend/domain/models/task.py` - 任务领域模型
- `backend/domain/models/requirement.py` - 需求领域模型
- `backend/domain/models/framework.py` - 框架领域模型

**主要类**:
```python
from domain.models import (
    Task, TaskStatus, TaskStage, StageProgress,
    Requirement, SceneType, TemplateType,
    PPTFramework, PageDefinition, PageType, ContentType
)
```

### 架构对比

| 方面 | 旧3阶段架构 | 新"1主5子"架构 |
|------|------------|----------------|
| **智能体数量** | 3个 | 6个（1主5子） |
| **输入方式** | 需要提供结构化大纲 | 支持自然语言输入 |
| **修订能力** | 不支持 | 支持选择性修订 |
| **内容专业性** | 依赖LLM生成 | 有资料研究支撑 |
| **进度可见性** | 简单进度 | 细粒度阶段进度 |
| **容错能力** | 基础重试 | 3次重试+降级策略 |
