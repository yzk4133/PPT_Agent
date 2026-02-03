# Backend 目录说明

> **最后更新**: 2026-02-02
>
> 本文档说明后端目录结构。项目已完成**目录结构归档整理**，保持简洁清晰的核心架构。

---

## 📁 目录结构概览

项目采用**统一的7层分层架构**，提供清晰的代码组织、依赖管理和可扩展性。

### 核心目录结构

```
backend/
├── 📦 agents/              # ✨ 统一Agent管理
│   ├── core/               # Agent核心层实现
│   │   ├── planning/       # 主题拆分Agent
│   │   ├── research/       # 研究Agent
│   │   └── generation/     # 生成Agent
│   └── applications/       # Agent应用
│       ├── ppt_generator/  # PPT生成（原 flat_slide_agent）
│       └── outline_generator/  # 大纲生成（原 flat_slide_outline）
│
├── 📦 core/                # ✨ 核心层 - 领域模型和接口
├── 📦 api/                 # ✨ API层 - HTTP接口
├── 📦 services/            # ✨ 服务层 - 业务编排
├── 📦 infrastructure/      # ✨ 基础设施层
├── 📦 tools/               # ✨ 工具层
│
├── 📁 memory/              # ✅ 统一记忆管理
│   ├── core/               # 核心记忆（原 persistent_memory）
│   └── basic/              # 基础记忆（原 memory）
│
├── 📁 skills/              # ✅ 技能框架（原 skill_framework）
├── 📁 utils/               # ✅ 通用工具
│   ├── save_ppt/           # PPT保存功能
│   └── common/             # 通用配置
│
├── 📁 tests/               # ✅ 测试
├── 📁 docs/                # ✅ 文档
│
├── 📄 README.md            # 主文档
├── 📄 ARCHITECTURE.md      # 架构文档
├── 📄 docker-compose.yml   # Docker配置
├── 📄 requirements.txt     # 依赖配置
└── 📄 env_template         # 环境变量模板
```

> **📦 归档目录**: 旧模块已移至 `archive/` 目录（8个模块）

### 🎯 7层分层架构

| 层级 | 目录 | 职责 | 状态 |
|------|------|------|------|
| **API层** | `api/` | HTTP接口定义 | ✅ 统一 |
| **Services层** | `services/` | 业务逻辑编排 | ✅ 统一 |
| **Agents层** | `agents/core/` | Agent核心实现 | ✅ 统一 |
| **Core层** | `core/` | 领域模型和接口 | ✅ 统一 |
| **Infrastructure层** | `infrastructure/` | 技术基础设施 | ✅ 统一 |
| **Tools层** | `tools/` | 可重用工具 | ✅ 统一 |
| **Memory层** | `memory/core/` | 持久化记忆管理 | ✅ 统一 |

### 🚀 使用应用

#### PPT生成
```bash
# 使用新的统一架构
cd agents/applications/ppt_generator
python main_api.py --port 10012
```

#### 大纲生成
```bash
# 使用新的统一架构
cd agents/applications/outline_generator
python main_api.py --port 10002
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

| 特性 | 归档前 | 归档后 |
|------|--------|--------|
| 顶层目录数 | 23个 | 12个 ✅ |
| Agent管理 | 分散3处 | 统一到 agents/ ✅ |
| Memory管理 | 分散2处 | 统一到 memory/ ✅ |
| 工具管理 | 分散多处 | 统一到 utils/ ✅ |
| 目录清晰度 | 混乱 | 极清晰 ✅ |
| 临时文档 | 6个 | 0个 ✅ |

### 📦 归档内容

**8个模块已移至 `archive/` 目录：**

| 模块 | 类型 | 说明 |
|------|------|------|
| `slide_agent/` | 旧架构 | 旧分层架构PPT生成 |
| `slide_outline/` | 旧架构 | 旧大纲生成 |
| `simplePPT/` | 实验性 | 简化版PPT生成 |
| `simpleOutline/` | 实验性 | 简化版大纲生成 |
| `super_agent/` | 开发中 | 文字版多智能体系统 |
| `ppt_api/` | 开发中 | 旧PPT生成API |
| `hostAgentAPI/` | 协调模块 | A2A主机Agent API |
| `multiagent_front/` | 协调模块 | 前端界面 |

> 📝 详见归档说明：[archive/README_ARCHIVE.md](./archive/README_ARCHIVE.md)

---

## 📋 核心模块说明

### Agent层（统一管理）

| 目录 | 功能 | 状态 |
|------|------|------|
| `agents/core/planning/` | 主题拆分Agent | ✅ 核心 |
| `agents/core/research/` | 研究Agent | ✅ 核心 |
| `agents/core/generation/` | 生成Agent | ✅ 核心 |
| `agents/applications/ppt_generator/` | PPT生成应用 | ✅ 应用 |
| `agents/applications/outline_generator/` | 大纲生成应用 | ✅ 应用 |

### Memory层（统一管理）

| 目录 | 功能 | 状态 |
|------|------|------|
| `memory/core/` | 持久化记忆（数据库、向量存储） | ✅ 核心 |
| `memory/basic/` | 基础记忆管理 | ✅ 保留 |

### 支持模块

| 目录 | 功能 | 状态 |
|------|------|------|
| `skills/` | 技能框架（原 skill_framework） | ✅ 重命名 |
| `utils/save_ppt/` | PPT保存功能 | ✅ 整合 |
| `utils/common/` | 通用配置 | ✅ 整合 |

### 文档和配置

| 目录/文件 | 说明 |
|----------|------|
| `docs/` | 文档目录 |
| `tests/` | 测试目录 |
| `ARCHITECTURE.md` | 架构文档 |
| `docker-compose.yml` | Docker配置 |
| `requirements.txt` | 依赖配置 |
| `env_template` | 环境变量模板 |

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

- [ARCHITECTURE.md](./ARCHITECTURE.md) - 架构设计文档
- [archive/README_ARCHIVE.md](./archive/README_ARCHIVE.md) - 归档模块说明
