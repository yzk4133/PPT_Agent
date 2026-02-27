# LangChain 多Agent PPT 生成架构文档

## 📖 文档概述

本文档详细说明了基于 LangChain/LangGraph 的多Agent PPT 生成系统的架构设计、实现细节和使用方法。

## 🏗️ 架构概览

本系统采用声明式工作流设计，使用 LangGraph 的 StateGraph 构建了一个清晰的、可扩展的 PPT 生成流程。

### 主要组件

- **模型层 (Models)**: 定义状态和领域模型
- **协调器层 (Coordinator)**: 工作流编排和页面级流水线
- **核心智能体层 (Core Agents)**: 各个处理阶段的智能体

### 工作流程

```
用户输入 → 需求解析 → 框架设计 → [研究?] → 内容生成 → 模板渲染 → PPT输出
```

## 📁 文档结构

| 文档 | 描述 |
|------|------|
| [00-architecture-overview.md](00-architecture-overview.md) | 架构总览 |
| [01-models/state.py.md](01-models/state.py.md) | 状态模型详解 |
| [01-models/framework.py.md](01-models/framework.py.md) | 框架模型详解 |
| [02-coordinator/master_graph.py.md](02-coordinator/master_graph.py.md) | 主工作流图详解 |
| [02-coordinator/page_pipeline.py.md](02-coordinator/page_pipeline.py.md) | 页面流水线详解 |
| [03-core-agents/requirement_agent.py.md](03-core-agents/requirement_agent.py.md) | 需求解析智能体详解 |
| [03-core-agents/framework_agent.py.md](03-core-agents/framework_agent.py.md) | 框架设计智能体详解 |
| [03-core-agents/research_agent.py.md](03-core-agents/research_agent.py.md) | 研究智能体详解 |
| [03-core-agents/content_agent.py.md](03-core-agents/content_agent.py.md) | 内容生成智能体详解 |
| [03-core-agents/renderer_agent.py.md](03-core-agents/renderer_agent.py.md) | 渲染智能体详解 |
| [04-workflow/state-flow.md](04-workflow/state-flow.md) | 状态流转详解 |
| [04-workflow/error-handling.md](04-workflow/error-handling.md) | 错误处理详解 |
| [04-workflow/performance.md](04-workflow/performance.md) | 性能优化详解 |
| [05-examples/basic-usage.md](05-examples/basic-usage.md) | 基础用法 |
| [05-examples/advanced-usage.md](05-examples/advanced-usage.md) | 高级用法 |

## 🚀 快速开始

### 基本用法

```python
from agents_langchain import create_master_graph

# 创建工作流图
graph = create_master_graph()

# 生成 PPT
result = await graph.generate("创建一份关于人工智能的PPT，10页")

# 查看结果
print(f"输出文件: {result['ppt_output']['file_path']}")
print(f"总页数: {result['ppt_framework']['total_page']}")
```

## 🔧 配置

系统支持通过环境变量进行配置：

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | - |
| `OPENAI_BASE_URL` | API 基础 URL | - |
| `LLM_MODEL` | 使用的模型名称 | `gpt-4o-mini` |
| `PAGE_PIPELINE_CONCURRENCY` | 页面流水线并发数 | `3` |

## 📊 架构特点

1. **声明式工作流**: 使用 LangGraph 的 StateGraph 声明工作流
2. **状态管理**: 集中式状态管理，状态在节点间自动传递
3. **并行处理**: 页面级流水线支持并行执行
4. **降级策略**: 每个 Agent 都有 fallback 机制
5. **可扩展性**: 易于添加新的 Agent 或修改工作流

## 🔗 相关链接

- [LangChain 文档](https://python.langchain.com/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [原始架构文档](../README.md)
