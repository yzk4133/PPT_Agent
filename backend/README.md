# Backend 目录说明

> **最后更新**: 2026-02-03
>
> 本文档说明后端目录结构。项目已完成**目录结构归档整理**和**API/Service层架构重构**，采用标准前后端分离架构。

---

## 🎉 架构重构（v2.0）

**重大更新**: 后端已完成架构重构，采用标准前后端分离设计：

### 核心改进

- ✅ **强类型Agent通信**: 使用`AgentContext`替代`session.state`字典
- ✅ **依赖注入**: 使用`dependency-injector`管理所有依赖
- ✅ **统一异常处理**: 标准化的API错误响应
- ✅ **Agent网关层**: 统一Agent调用接口，支持降级策略
- ✅ **移除旧架构**: 统一使用1主5子MasterCoordinator架构

### 快速了解新架构

- 📘 [QUICKSTART.md](./QUICKSTART.md) - 5分钟快速开始
- 📖 [API_SERVICE_DESIGN.md](./API_SERVICE_DESIGN.md) - 完整架构设计（93页）
- 📝 [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - 实施总结

---

## 📁 目录结构概览

项目采用**统一的7层分层架构**（v2.0重构），提供清晰的代码组织、依赖管理和可扩展性。

### 核心目录结构

```
backend/
├── 📦 agents/              # ✨ 统一Agent管理
│   ├── core/               # Agent核心层实现
│   │   ├── planning/       # 规划层（需求解析、框架设计）
│   │   │   └── requirements/  # 需求解析
│   │   ├── research/       # 研究Agent
│   │   ├── generation/     # 生成Agent
│   │   ├── rendering/      # 渲染Agent
│   │   └── quality/        # 质量控制
│   └── orchestrator/       # 编排层（推荐使用 Master Coordinator）
│       ├── agents/         # 编排Agents
│       │   ├── master_coordinator.py  # 主协调器（推荐）
│       │   ├── flat_root_agent.py      # PPT生成（已废弃）
│       │   └── flat_outline_agent.py   # 大纲生成（已废弃）
│       ├── components/     # 支持组件
│       │   ├── agent_gateway.py       # Agent网关
│       │   ├── progress_tracker.py    # 进度跟踪
│       │   ├── revision_handler.py    # 修订处理
│       │   └── page_pipeline.py       # 页面流水线
│       └── deprecated/     # 已废弃的代码
│
├── 📦 domain/              # ✨ 核心层 - 领域模型和接口
│   ├── models/             # 领域模型（新增agent_context.py, agent_result.py）
│   └── interfaces/         # 接口定义
│
├── 📦 api/                 # ✨ API层 - HTTP接口
│   ├── routes/             # 路由定义
│   ├── endpoints/          # 端点实现
│   ├── schemas/            # Pydantic Schema
│   ├── middleware/         # 中间件（新增error_handler.py）
│   └── dependencies.py     # FastAPI依赖注入（新增）
│
├── 📦 services/            # ✨ 服务层 - 业务编排
│   ├── presentation_service.py  # 演示文稿服务
│   └── outline_service.py       # 大纲服务
│
├── 📦 infrastructure/      # ✨ 基础设施层
│   ├── di/                 # 依赖注入容器（新增）
│   ├── config/             # 配置管理
│   ├── database/           # 数据库
│   ├── llm/                # LLM提供者
│   └── logging/            # 日志
│
├── 📦 tools/               # ✨ 工具层
│
├── 📁 memory/              # ✅ 统一记忆管理
│   ├── core/               # 核心记忆（原 persistent_memory）
│   └── basic/              # 基础记忆（原 memory）
│
├── 📁 skills/              # ✅ 技能框架（原 skill_framework）
├── 📁 utils/               # ✅ 通用工具
├── 📁 tests/               # ✅ 测试
├── 📁 docs/                # ✅ 文档
│
├── 📄 README.md            # 主文档
├── 📄 QUICKSTART.md        # 快速开始（新增）
├── 📄 API_SERVICE_DESIGN.md # 架构设计（新增）
├── 📄 IMPLEMENTATION_SUMMARY.md # 实施总结（新增）
├── 📄 ARCHITECTURE.md      # 架构文档
├── 📄 docker-compose.yml   # Docker配置
├── 📄 requirements.txt     # 依赖配置
└── 📄 env_template         # 环境变量模板
```

> **📦 归档目录**: 旧模块已移至 `archive/` 目录（8个模块）

### 🎯 7层分层架构（v2.0重构）

| 层级                 | 目录                   | 职责                         | 状态        |
| -------------------- | ---------------------- | ---------------------------- | ----------- |
| **API层**            | `api/`                 | HTTP接口、依赖注入、异常处理 | ✅ 重构完成 |
| **Services层**       | `services/`            | 业务逻辑编排、事务管理       | 🚧 重构中   |
| **Agent网关层**      | `agents/orchestrator/` | 统一Agent调用、降级策略      | ✅ 新增     |
| **Agents层**         | `agents/core/`         | Agent核心实现                | ✅ 统一     |
| **Domain层**         | `domain/`              | 领域模型、强类型上下文       | ✅ 重构完成 |
| **Infrastructure层** | `infrastructure/`      | 技术基础设施、依赖注入       | ✅ 重构完成 |
| **Tools层**          | `tools/`               | 可重用工具                   | ✅ 统一     |

### 🧠 记忆系统集成（v2.1新增）

**重大更新**: 已完成记忆系统与多Agent架构的深度集成，实现三层记忆能力：

#### 核心功能

| 功能 | Agent | 收益 |
|------|-------|------|
| **研究缓存** | ResearchAgent | API调用减少30%，响应速度提升50-90% |
| **用户偏好学习** | RequirementParserAgent | 自动适配用户习惯 |
| **共享工作空间** | ResearchAgent → ContentMaterialAgent | 跨Agent数据流转 |
| **任务状态追踪** | MasterCoordinator | 进度监控与恢复 |

#### 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  MasterCoordinator + 5 Sub-Agents                           │
├─────────────────────────────────────────────────────────────┤
│              🔌 Agent Memory Adapter Layer                   │
│  AgentMemoryMixin (base_agent_with_memory.py)                │
│  - remember/recall/forget                                   │
│  - share_data/get_shared_data                               │
│  - get_user_preferences/update_user_preferences             │
│  - record_decision/get_similar_decisions                    │
├─────────────────────────────────────────────────────────────┤
│                   Memory System Layer                        │
│  L1 (Transient) → L2 (Short-term) → L3 (Long-term)          │
└─────────────────────────────────────────────────────────────┘
```

#### 快速使用

```python
# 启用记忆系统（默认）
export USE_AGENT_MEMORY=true

# 自动使用带记忆的Agent
from agents.orchestrator import master_coordinator_agent
result = await master_coordinator_agent.run_async(ctx)
```

#### 详细文档

- 📘 [agents/README_MEMORY_INTEGRATION.md](./agents/README_MEMORY_INTEGRATION.md) - 完整使用指南
- 📊 [MEMORY_INTEGRATION_SUMMARY.md](../MEMORY_INTEGRATION_SUMMARY.md) - 实施总结

### 🚀 快速开始

#### 新架构使用示例

```python
# 使用强类型上下文和Agent网关
from domain.models.agent_context import AgentContext, Requirement
from agents.orchestrator.agent_gateway import AgentGateway

# 创建上下文
context = AgentContext(
    request_id="req_123",
    requirement=Requirement(topic="AI", num_slides=10)
)

# 调用Agent网关
gateway = AgentGateway(llm_provider=llm)
result = await gateway.execute_master_coordinator(context)
```

详细教程请查看 [QUICKSTART.md](./QUICKSTART.md)

### 🚀 使用应用

#### PPT生成

```bash
# 推荐：使用 Master Coordinator 架构
cd backend
python -m api.routes.ppt_generation

# 备选：使用 Flat 架构（已废弃）
python -m backend.api.agents.presentation_api --port 10012
```

#### 大纲生成

```bash
# 备选：使用 Flat 架构（已废弃）
python -m backend.api.agents.outline_api --port 10002
```

#### 导入模块

```python
# 导入领域模型
from core.models import Presentation, Topic, Slide

# 导入Agent（新路径）
from agents.core.planning import split_topic_agent
from agents.core.research import parallel_search_agent
from agents.core.generation import ppt_generator_loop_agent

# 导入工具
from tools import DocumentSearch, SearchImage, get_tool_registry

# 导入服务
from services import PresentationService

# 导入配置
from infrastructure.config import get_config
from infrastructure.llm import create_agent_model

# 导入记忆（新路径）
from memory.core import PersistentMemory
from memory.basic import BasicMemory
```

### 📊 架构优势

| 特性       | 归档前   | 归档后            |
| ---------- | -------- | ----------------- |
| 顶层目录数 | 23个     | 12个 ✅           |
| Agent管理  | 分散3处  | 统一到 agents/ ✅ |
| Memory管理 | 分散2处  | 统一到 memory/ ✅ |
| 工具管理   | 分散多处 | 统一到 utils/ ✅  |
| 目录清晰度 | 混乱     | 极清晰 ✅         |
| 临时文档   | 6个      | 0个 ✅            |

### 📦 归档内容

**8个模块已移至 `archive/` 目录：**

| 模块                | 类型     | 说明               |
| ------------------- | -------- | ------------------ |
| `slide_agent/`      | 旧架构   | 旧分层架构PPT生成  |
| `slide_outline/`    | 旧架构   | 旧大纲生成         |
| `simplePPT/`        | 实验性   | 简化版PPT生成      |
| `simpleOutline/`    | 实验性   | 简化版大纲生成     |
| `super_agent/`      | 开发中   | 文字版多智能体系统 |
| `ppt_api/`          | 开发中   | 旧PPT生成API       |
| `hostAgentAPI/`     | 协调模块 | A2A主机Agent API   |
| `multiagent_front/` | 协调模块 | 前端界面           |

> 📝 详见归档说明：[archive/README_ARCHIVE.md](./archive/README_ARCHIVE.md)

---

## 📋 核心模块说明

### Agent层（统一管理）

| 目录                                                | 功能              | 状态              |
| --------------------------------------------------- | ----------------- | ----------------- |
| `agents/core/base_agent_with_memory.py`             | 记忆适配器层      | ✅ **新增(v2.1)** |
| `agents/core/planning/`                             | 需求解析、框架设计 | ✅ 核心          |
| `agents/core/planning/requirements/`                | 需求解析（+记忆）  | ✅ 核心          |
| `agents/core/research/`                             | 研究Agent（+记忆） | ✅ 核心          |
| `agents/core/generation/`                           | 生成Agent（+记忆） | ✅ 核心          |
| `agents/core/rendering/`                            | 渲染Agent         | ✅ 核心          |
| `agents/core/quality/`                              | 质量控制           | ✅ 核心          |
| `agents/orchestrator/agents/master_coordinator.py`  | 主协调器（+记忆）  | ✅ **推荐使用**  |
| `agents/orchestrator/agents/flat_root_agent.py`     | PPT生成（Flat）    | ⚠️ 已废弃        |
| `agents/orchestrator/agents/flat_outline_agent.py`  | 大纲生成（Flat）   | ⚠️ 已废弃        |
| `agents/orchestrator/components/`                   | 支持组件           | ✅ 编排支持      |
| `agents/tests/test_agent_memory_integration.py`     | 记忆集成测试       | ✅ **新增(v2.1)** |

> **💡 记忆集成**: 所有核心Agent现已支持记忆功能，通过环境变量 `USE_AGENT_MEMORY` 控制

### Memory层（统一管理）

| 目录            | 功能                           | 状态    |
| --------------- | ------------------------------ | ------- |
| `memory/core/`  | 持久化记忆（数据库、向量存储） | ✅ 核心 |
| `memory/basic/` | 基础记忆管理                   | ✅ 保留 |

### 支持模块

| 目录              | 功能                           | 状态      |
| ----------------- | ------------------------------ | --------- |
| `skills/`         | 技能框架（原 skill_framework） | ✅ 重命名 |
| `utils/save_ppt/` | PPT保存功能                    | ✅ 整合   |
| `utils/common/`   | 通用配置                       | ✅ 整合   |

### 文档和配置

| 目录/文件            | 说明         |
| -------------------- | ------------ |
| `docs/`              | 文档目录     |
| `tests/`             | 测试目录     |
| `ARCHITECTURE.md`    | 架构文档     |
| `docker-compose.yml` | Docker配置   |
| `requirements.txt`   | 依赖配置     |
| `env_template`       | 环境变量模板 |

---

## 📦 依赖安装

```bash
pip install -r requirements.txt
```

---

## 🔧 LLM 模型配置

**注意：** Gemini 目前最适配（第一次一定要用 Gemini 试验）。

配置环境变量（复制 `env_template` 为 `.env`）：

```bash
# 在 .env 文件中配置
MODEL_PROVIDER=google
GOOGLE_API_KEY=your_api_key_here
```

---

## 🗄️ 归档模块使用

如需使用已归档的模块（如 A2A 框架、前端界面等），请参考：

- **归档目录**: `backend/archive/`
- **归档说明**: [archive/README_ARCHIVE.md](./archive/README_ARCHIVE.md)

**恢复模块示例**:

```bash
# 恢复 A2A 前端
mv backend/archive/multiagent_front backend/
mv backend/archive/hostAgentAPI backend/

# 恢复旧架构
mv backend/archive/slide_agent backend/
```

---

## 💡 开发指南

### Agent 开发

每个 Agent 的描述必须清晰，因为系统根据 Agent 任务描述确定输入信息。

### 代码规范

- 新功能应基于新架构（7层分层）开发
- 优先使用 `agents/core/` 中的共享Agent
- 避免重复代码，充分利用工具层和服务层

---

## 📚 相关文档

### 架构与设计
- [ARCHITECTURE.md](./ARCHITECTURE.md) - 架构设计文档
- [archive/README_ARCHIVE.md](./archive/README_ARCHIVE.md) - 归档模块说明
- [QUICKSTART.md](./QUICKSTART.md) - 5分钟快速开始
- [API_SERVICE_DESIGN.md](./API_SERVICE_DESIGN.md) - 完整架构设计（93页）
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - 实施总结

### 记忆系统
- [agents/README_MEMORY_INTEGRATION.md](./agents/README_MEMORY_INTEGRATION.md) - 记忆系统使用指南
- [MEMORY_INTEGRATION_SUMMARY.md](../MEMORY_INTEGRATION_SUMMARY.md) - 记忆集成实施总结
- [cognition/memory/core/README.md](./cognition/memory/core/README.md) - 记忆系统架构文档
