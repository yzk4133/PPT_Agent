# OpenCode 多 Agent 架构文档

本目录包含 OpenCode 项目多 Agent 架构的详细技术文档。

## 文档目录

### 入门指南
- [01-architecture-overview.md](./01-architecture-overview.md) - 架构总览和设计理念

### 核心系统
- [02-agent-system.md](./02-agent-system.md) - Agent 系统详解
- [03-session-management.md](./03-session-management.md) - 会话管理机制
- [04-communication.md](./04-communication.md) - Agent 通信协议 (ACP)

### 功能模块
- [05-task-execution.md](./05-task-execution.md) - 任务执行流程
- [06-tools-system.md](./06-tools-system.md) - 工具系统
- [07-permission-system.md](./07-permission-system.md) - 权限管理系统

### 实践指南
- [08-built-in-agents.md](./08-built-in-agents.md) - 内置 Agent 详解
- [09-custom-agent.md](./09-custom-agent.md) - 自定义 Agent 开发指南

## 快速开始

建议按照以下顺序阅读文档：

1. 首先阅读 [架构总览](./01-architecture-overview.md) 了解整体设计
2. 然后阅读 [Agent 系统](./02-agent-system.md) 理解核心概念
3. 根据需要深入阅读其他模块文档

## 核心概念

### Agent 类型
- **Primary Agent**: 主要 Agent，直接响应用户输入，可以创建子 Agent
- **Subagent**: 子 Agent，专门处理特定任务，由 Primary Agent 创建或手动调用

### 会话模型
- **父会话**: 主 Agent 的会话
- **子会话**: Subagent 的独立会话，与父会话隔离
- **会话分叉**: 从现有会话创建新分支的能力

### 工具系统
- 所有功能通过工具 (Tools) 实现
- Agent 可以根据权限配置访问不同的工具集
- 工具调用支持异步、并行和重试

## 技术栈

- **语言**: TypeScript
- **运行时**: Node.js / Bun
- **AI 模型**: 支持 Anthropic Claude 等多种模型
- **协议**: Agent Communication Protocol (ACP)

## 代码结构

```
packages/opencode/src/
├── agent/           # Agent 核心实现
├── session/         # 会话管理
├── tool/            # 工具系统
├── acp/             # Agent Communication Protocol
├── permission/      # 权限管理
└── cli/             # CLI 接口
```

## 贡献指南

如果您想参与开发，请阅读相关模块文档并查看源码：

- Agent 实现: `packages/opencode/src/agent/agent.ts`
- 会话处理: `packages/opencode/src/session/processor.ts`
- 工具注册: `packages/opencode/src/tool/registry.ts`
