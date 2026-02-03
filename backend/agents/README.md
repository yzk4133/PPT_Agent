# Agents 模块文档

> **最后更新**: 2026-02-03
>
> 本文档说明 MultiAgentPPT 的智能体架构和记忆系统集成

## 概述

Agents 模块采用 **1主5子** 架构，通过 MasterCoordinator 协调5个专业子智能体完成PPT生成任务。

**v2.1 新增**: 记忆系统深度集成，实现研究缓存、用户偏好学习、跨Agent数据共享等功能。

---

## 🏗️ 架构设计

### 1主5子架构

```
┌─────────────────────────────────────────────────────────────┐
│                  MasterCoordinator                          │
│                    主协调智能体                              │
│            - 任务调度与分发                                  │
│            - 阶段协调与状态管理                              │
│            - 容错与降级处理                                  │
└──────────────────┬──────────────────────────────────────────┘
                   │
     ┌─────────────┼─────────────┬─────────────┬─────────────┐
     │             │             │             │             │
     ▼             ▼             ▼             ▼             ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│需求解析  │ │框架设计  │ │研究Agent│ │内容生成  │ │模板渲染  │
│         │ │         │ │         │ │         │ │         │
│Parser   │ │Designer │ │Research │ │Material │ │Renderer │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

### 记忆系统集成

```
┌─────────────────────────────────────────────────────────────┐
│                  Application Layer                           │
│              MasterCoordinator + 5 Agents                    │
├─────────────────────────────────────────────────────────────┤
│              🔌 Agent Memory Adapter Layer                   │
│           AgentMemoryMixin (记忆适配器)                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ • remember/recall/forget (基础记忆)                  │    │
│  │ • share_data/get_shared_data (共享工作空间)          │    │
│  │ • get_user_preferences (用户偏好)                    │    │
│  │ • record_decision (决策记录)                         │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                   Memory System Layer                        │
│     L1 (内存) → L2 (Redis) → L3 (数据库)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 目录结构

```
agents/
├── core/                           # 核心Agent实现
│   ├── base_agent_with_memory.py   # 记忆适配器（v2.1新增）
│   │
│   ├── planning/                   # 规划层Agent
│   │   ├── framework_designer_agent.py
│   │   └── requirements/
│   │       ├── requirement_parser_agent.py
│   │       └── requirement_parser_agent_with_memory.py (v2.1)
│   │
│   ├── research/                   # 研究Agent
│   │   ├── research_agent.py
│   │   ├── research_agent_with_memory.py (v2.1)
│   │   └── parallel_research_agent.py
│   │
│   ├── generation/                 # 生成Agent
│   │   ├── content_material_agent.py
│   │   ├── content_material_agent_with_memory.py (v2.1)
│   │   └── slide_writer_agent.py
│   │
│   ├── rendering/                  # 渲染Agent
│   │   └── template_renderer_agent.py
│   │
│   └── quality/                    # 质量控制Agent
│       └── quality_agent.py
│
├── orchestrator/                   # 编排层
│   ├── agents/
│   │   ├── master_coordinator.py
│   │   ├── master_coordinator_with_memory.py (v2.1)
│   │   ├── flat_root_agent.py (已废弃)
│   │   └── flat_outline_agent.py (已废弃)
│   │
│   └── components/                 # 支持组件
│       ├── agent_gateway.py        # Agent网关
│       ├── progress_tracker.py     # 进度跟踪
│       ├── revision_handler.py     # 修订处理
│       └── page_pipeline.py        # 页面流水线
│
├── tools/                          # 工具层
│   ├── search/
│   │   └── document_search.py
│   └── media/
│       └── image_search.py
│
├── tests/                          # 测试
│   └── test_agent_memory_integration.py (v2.1新增)
│
└── README_MEMORY_INTEGRATION.md    # 记忆系统使用指南
```

---

## 🤖 智能体说明

### MasterCoordinator（主协调器）

**推荐使用** - 新架构的核心协调器

**功能**:
- 任务调度与分发
- 阶段协调（5个阶段）
- 容错与重试（3次重试）
- 进度跟踪
- 支持三种执行模式：FULL, PHASE_1, PHASE_2

**使用方式**:
```python
from agents.orchestrator import master_coordinator_agent

# 自动选择带记忆的版本（通过环境变量控制）
result = await master_coordinator_agent.run_async(ctx)
```

**记忆功能（v2.1）**:
- 任务状态记忆
- 阶段进度追踪
- 任务恢复支持
- 性能统计

---

### RequirementParserAgent（需求解析）

**功能**: 将自然语言需求转化为结构化需求

**输入**: "做一份2025电商618销售复盘PPT，商务风模板，15页"

**输出**:
```json
{
  "ppt_topic": "2025电商618销售复盘",
  "scene": "BUSINESS_REPORT",
  "page_num": 15,
  "template_type": "BUSINESS",
  "need_research": true
}
```

**记忆功能（v2.1）**:
- 用户偏好学习（页数、语言、风格）
- 自动应用历史偏好
- 偏好计数统计

---

### FrameworkDesignerAgent（框架设计）

**功能**: 根据需求生成PPT大纲框架

**输出**: 每页的标题、类型、内容要求

**特点**:
- 智能分页
- 标注需要研究的页面
- 支持多种页面类型（封面、目录、内容页、总结）

---

### ResearchAgent（研究Agent）

**功能**: 为标注的页面搜索外部资料

**记忆功能（v2.1）**:
- **研究缓存**: 7天TTL，避免重复研究
- **共享工作空间**: 自动分享研究结果给ContentMaterialAgent
- **向量检索**: 支持语义相似研究复用

**预期收益**: API调用减少30%，响应速度提升50-90%

---

### ContentMaterialAgent（内容生成）

**功能**: 为每页生成具体内容素材

**记忆功能（v2.1）**:
- **共享研究获取**: 从工作空间获取ResearchAgent的研究结果
- **内容缓存**: 24小时TTL，加速重复内容生成
- **用户偏好应用**: 根据用户偏好调整内容风格

---

### TemplateRendererAgent（模板渲染）

**功能**: 应用模板生成最终PPT

**输出**: PPT文件或XML格式

---

## 🧠 记忆系统集成详解

### 启用记忆功能

```bash
# 默认启用
export USE_AGENT_MEMORY=true

# 禁用记忆功能
export USE_AGENT_MEMORY=false
```

### 记忆功能对比

| 功能 | 禁用记忆 | 启用记忆 |
|------|---------|---------|
| 研究缓存 | ❌ 每次都搜索 | ✅ 7天内复用 |
| 用户偏好 | ❌ 每次手动配置 | ✅ 自动学习 |
| 数据共享 | ❌ 通过ctx.state | ✅ 共享工作空间 |
| 任务追踪 | ❌ 无记录 | ✅ 完整追踪 |
| 决策分析 | ❌ 无记录 | ✅ 完整记录 |

### 配置选项

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `USE_AGENT_MEMORY` | true | 启用记忆功能 |
| `RESEARCH_CACHE_TTL_DAYS` | 7 | 研究缓存天数 |
| `ENABLE_CONTENT_CACHE` | true | 启用内容缓存 |
| `CONTENT_CACHE_TTL_HOURS` | 24 | 内容缓存小时数 |
| `ENABLE_PREFERENCE_LEARNING` | true | 启用偏好学习 |
| `MIN_SAMPLES_FOR_LEARNING` | 3 | 最小学习样本数 |

---

## 🚀 快速开始

### 基础使用

```python
from agents.orchestrator import master_coordinator_agent

# 执行完整PPT生成
result = await master_coordinator_agent.run_async(ctx)
```

### 分阶段执行

```python
# PHASE_1: 仅生成大纲（阶段1-2）
ctx.session.state["execution_mode"] = "phase_1"
result = await master_coordinator_agent.run_async(ctx)

# PHASE_2: 从checkpoint继续生成（阶段3-5）
ctx.session.state["execution_mode"] = "phase_2"
ctx.session.state["task_id"] = "previous_task_id"
result = await master_coordinator_agent.run_async(ctx)
```

### 禁用记忆功能

```python
# 方式1: 环境变量
import os
os.environ["USE_AGENT_MEMORY"] = "false"

# 方式2: 直接使用原始版本
from agents.core.research import optimized_research_agent
agent = optimized_research_agent
```

---

## 📊 性能指标

### 记忆系统收益

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 研究API调用 | 100% | 70% | -30% |
| 缓存命中响应 | 100% | 10-50% | +50-90% |
| 重复用户输入 | 每次配置 | 自动应用 | 用户体验+ |

### 统计信息查看

```python
# ResearchAgent统计
print(f"缓存命中: {research_agent.stats['cache_hits']}")
print(f"新研究: {research_agent.stats['new_research']}")

# ContentMaterialAgent统计
print(f"共享研究使用: {content_agent.stats['shared_research_used']}")

# MasterCoordinator统计
print(f"总任务数: {coordinator.stats['total_tasks']}")
print(f"完成任务数: {coordinator.stats['completed_tasks']}")
```

---

## 🧪 测试

### 运行测试

```bash
cd backend
pytest agents/tests/test_agent_memory_integration.py -v
```

### 测试覆盖率

```bash
pytest agents/tests/test_agent_memory_integration.py --cov=agents --cov-report=html
```

---

## 📚 相关文档

### 记忆系统
- [README_MEMORY_INTEGRATION.md](./README_MEMORY_INTEGRATION.md) - 记忆系统完整使用指南
- [MEMORY_INTEGRATION_SUMMARY.md](../../MEMORY_INTEGRATION_SUMMARY.md) - 实施总结

### 架构设计
- [ARCHITECTURE.md](../ARCHITECTURE.md) - 整体架构文档
- [API_SERVICE_DESIGN.md](../API_SERVICE_DESIGN.md) - API/Service层设计

### 记忆系统底层
- [cognition/memory/core/README.md](../cognition/memory/core/README.md) - 记忆系统架构

---

## 🔄 版本历史

### v2.1 (2026-02-03)
- ✅ 新增 AgentMemoryMixin 记忆适配器层
- ✅ ResearchAgent 研究缓存功能
- ✅ RequirementParserAgent 用户偏好学习
- ✅ ContentMaterialAgent 共享工作空间集成
- ✅ MasterCoordinator 任务状态追踪
- ✅ 完整的单元测试和文档

### v2.0 (2025-xx-xx)
- ✅ 统一1主5子架构
- ✅ Agent网关层
- ✅ 强类型上下文
- ✅ 依赖注入

---

## 🤝 贡献指南

### 添加新Agent

1. 继承对应基类（LlmAgent/ParallelAgent/BaseAgent）
2. 如需记忆功能，继承 AgentMemoryMixin
3. 实现 `_run_async_impl` 方法
4. 添加单元测试
5. 更新文档

### 示例

```python
from agents.core.base_agent_with_memory import AgentMemoryMixin
from google.adk.agents.llm_agent import LlmAgent

class MyAgentWithMemory(AgentMemoryMixin, LlmAgent):
    def __init__(self, **kwargs):
        super().__init__(
            model="deepseek-chat",
            name="MyAgent",
            instruction="Your instruction",
            **kwargs
        )

    async def _run_async_impl(self, ctx):
        # 使用记忆功能
        await self.remember(key="test", value="data", scope="TASK")
        value = await self.recall(key="test", scope="TASK")
```

---

**文档版本**: v2.1
**最后更新**: 2026-02-03
