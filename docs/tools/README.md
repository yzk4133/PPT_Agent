# 🛠️ 工具系统文档索引

欢迎来到 MultiAgentPPT 工具系统文档！本索引帮助你快速找到所需的文档。

---

## 📚 文档导航

### 🚀 快速开始

| 文档 | 说明 | 适合人群 |
|------|------|----------|
| [⚡ 快速参考](./QUICK_REFERENCE.md) | 5分钟上手，常用代码片段 | 所有人 |
| [📊 工具系统总览](./tools_overview.md) | 系统架构和核心概念 | 新用户 |

### 📝 最新变更

| 文档 | 说明 | 适合人群 |
|------|------|----------|
| [📋 变更日志](./REFACTORING_CHANGELOG.md) | v2.0 重构详细记录 | 所有用户 |
| [🔄 迁移指南](./REFACTORING_CHANGELOG.md#迁移指南) | 从旧工具迁移到新工具 | 现有用户 |

### 🏗️ 架构与设计

| 文档 | 说明 | 适合人群 |
|------|------|----------|
| [🏗️ 工具系统架构](./tools_architecture.md) | 详细的架构设计 | 架构师、开发者 |
| [📚 外部工具设计指南](./external_tools_guide.md) | MCP 工具设计规范 | 工具开发者 |

### 🎯 Skills 框架

| 文档 | 说明 | 适合人群 |
|------|------|----------|
| [🎭 Skills 框架指南](./skills_framework.md) | Skills 框架详解 | 所有用户 |
| [💡 Prompt 设计指南](./prompt_design_guide.md) | 提示词编写最佳实践 | 提示词工程师 |

### 🛠️ 开发指南

| 文档 | 说明 | 适合人群 |
|------|------|----------|
| [📖 工具参考手册](./tools_reference.md) | 所有工具的完整列表 | 所有用户 |
| [🔧 工具开发指南](./tools_development.md) | 如何创建新工具 | 开发者 |

### 📁 详细文档

| 文档 | 说明 | 适合人群 |
|------|------|----------|
| [📁 主 README](../../backend/agents/tools/README.md) | 工具系统完整文档 | 所有用户 |

---

## 🗂️ 按主题查找

### 我想了解...

#### **新工具系统是什么？**
1. 先看 [快速参考](./QUICK_REFERENCE.md)
2. 再看 [工具系统总览](./tools_overview.md)

#### **如何使用 MCP 工具？**
1. [快速参考 - MCP 工具](./QUICK_REFERENCE.md#mcp-工具-速查表)
2. [变更日志 - 新增功能](./REFACTORING_CHANGELOG.md#新增功能)
3. [主 README - MCP 工具参考](../../backend/agents/tools/README.md#-mcp-tools-reference)

#### **如何从旧工具迁移？**
1. [变更日志 - 迁移指南](./REFACTORING_CHANGELOG.md#迁移指南)
2. [快速参考 - 迁移对照表](./QUICK_REFERENCE.md#-迁移对照表)

#### **如何创建新的 Skill？**
1. [技能框架指南](./skills_framework.md)
2. [Prompt 设计指南](./prompt_design_guide.md)
3. [主 README - 创建 Skills](../../backend/agents/tools/README.md#-创建一个新的-skill)

#### **如何开发新的 MCP 工具？**
1. [工具开发指南](./tools_development.md)
2. [外部工具设计指南](./external_tools_guide.md)
3. [主 README - 开发指南](../../backend/agents/tools/README.md#-development)

---

## 📊 文档结构

```
docs/tools/
├── README.md                           # 本文件 - 文档索引
├── QUICK_REFERENCE.md                  # ⚡ 快速参考（NEW）
├── REFACTORING_CHANGELOG.md           # 📝 变更日志（NEW）
├── tools_overview.md                   # 📊 工具系统总览
├── tools_architecture.md               # 🏗️ 工具系统架构
├── tools_reference.md                  # 📖 工具参考手册
├── tools_development.md                # 🔧 工具开发指南
├── skills_framework.md                 # 🎭 Skills 框架指南
├── prompt_design_guide.md              # 💡 Prompt 设计指南
└── external_tools_guide.md             # 📚 外部工具设计指南
```

---

## 🎯 根据你的角色

### 👨‍💻 作为开发者

**必读文档**：
1. [快速参考](./QUICK_REFERENCE.md) - 了解新工具
2. [迁移指南](./REFACTORING_CHANGELOG.md#迁移指南) - 更新现有代码
3. [工具开发指南](./tools_development.md) - 开发新工具

**进阶阅读**：
- [工具系统架构](./tools_architecture.md)
- [外部工具设计指南](./external_tools_guide.md)

### 👨‍🔬 作为研究者

**必读文档**：
1. [工具系统总览](./tools_overview.md) - 理解整体架构
2. [Skills 框架指南](./skills_framework.md) - 如何使用 Skills
3. [Prompt 设计指南](./prompt_design_guide.md) - 编写有效提示词

### 📊 作为架构师

**必读文档**：
1. [变更日志](./REFACTORING_CHANGELOG.md) - 了解所有变化
2. [工具系统架构](./tools_architecture.md) - 深入理解架构
3. [外部工具设计指南](./external_tools_guide.md) - 设计规范

### 🔍 作为新用户

**推荐路径**：
1. **开始**: [快速参考](./QUICK_REFERENCE.md) - 5分钟上手
2. **理解**: [工具系统总览](./tools_overview.md) - 核心概念
3. **实践**: [工具参考手册](./tools_reference.md) - 查看所有工具
4. **深入**: 根据需要阅读其他文档

---

## 📖 术语表

| 术语 | 说明 |
|------|------|
| **MCP 工具** | 外部 API 集成工具（如 web_search, fetch_url） |
| **Skills** | 可复用的能力封装 |
| **提示词型 Skills** | Markdown 格式的知识封装 |
| **函数型 Skills** | Python 类的可执行能力 |
| **UnifiedToolRegistry** | 统一的工具和技能注册中心 |
| **SkillManager** | 高层技能管理 API |

---

## 🔗 相关资源

- **项目主页**: [MultiAgentPPT](../../)
- **后端文档**: [Backend Architecture](../backend-architecture.md)
- **多智能体文档**: [MultiAgent System](../multiagent/)
- **记忆系统**: [Memory System](../memory-system/)

---

## 💬 获取帮助

如果文档没有解答你的问题：

1. **查看 FAQ**: [变更日志 - 常见问题](./REFACTORING_CHANGELOG.md#常见问题)
2. **阅读示例**: [主 README](../../backend/agents/tools/README.md)
3. **查看测试**: [backend/agents/tools/tests/](../../backend/agents/tools/tests/)

---

## 📝 文档版本

- **当前版本**: v2.0.0
- **最后更新**: 2025-02-03
- **维护者**: MultiAgentPPT Team

---

**🚀 [开始使用](./QUICK_REFERENCE.md)** | **📖 [查看变更](./REFACTORING_CHANGELOG.md)** | **🏗️ [了解架构](./tools_overview.md)**
