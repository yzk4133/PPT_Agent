# OpenCode 架构总览

## 设计理念

OpenCode 是一个基于多 Agent 架构的 AI 辅助开发工具。其核心理念是通过**专业化分工**和**协作式执行**来提高开发效率。

### 核心设计原则

1. **专业化分工**: 不同 Agent 擅长不同任务，各司其职
2. **层级协作**: Primary Agent 统筹规划，Subagent 专注执行
3. **权限隔离**: 每个独立的 Agent 会话具有独立的权限和状态
4. **工具抽象**: 所有功能通过标准化的工具接口实现
5. **异步并行**: 支持多个 Agent 并行工作，提高效率

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户交互层                                │
│                    (CLI / Web UI / API)                         │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Session Manager                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  主会话      │  │  子会话 1    │  │  子会话 2    │          │
│  │ Primary      │  │ Subagent A   │  │ Subagent B   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Communication                         │
│                         Protocol (ACP)                           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Tool Registry                             │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐      │
│  │Read │ │Edit │ │Bash │ │Grep │ │Glob │ │ LSP │ │Task │      │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      文件系统 / 操作系统 / 网络                   │
└─────────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. Agent 系统

Agent 是架构的核心执行单元，具有以下特征：

- **独立性**: 每个 Agent 有独立的上下文、状态和权限
- **专业化**: 不同 Agent 针对不同任务优化
- **协作性**: Agent 之间可以相互调用和通信

```typescript
// Agent 定义结构
interface Agent {
  name: string;              // Agent 名称
  description: string;       // 功能描述
  mode: 'primary' | 'subagent';  // 运行模式
  permission: Ruleset;       // 权限配置
  model: ModelConfig;        // 使用的模型
  tools: Tool[];            // 可用工具集
}
```

### 2. 会话管理

会话 (Session) 是 Agent 的执行环境：

- **层级结构**: 支持父子会话关系
- **消息流**: 处理用户输入和 AI 响应的流式传输
- **状态管理**: 维护会话的快照和恢复

### 3. Agent Communication Protocol (ACP)

ACP 定义了 Agent 之间的通信标准：

- 消息格式规范
- 会话创建和管理
- 工具调用协调
- 权限验证

### 4. 工具系统

工具是 Agent 与外部世界交互的唯一途径：

- **标准化接口**: 统一的工具定义和调用方式
- **动态注册**: 运行时动态加载和卸载工具
- **权限控制**: 基于规则的工具访问控制

### 5. 权限系统

精细的权限管理确保安全性和可控性：

- **规则引擎**: 基于模式的权限评估
- **作用域**: 文件路径、命令、工具类型的细粒度控制
- **用户交互**: 敏感操作需要用户确认

## 工作流程

### 典型的多 Agent 协作流程

```
用户请求
    │
    ▼
Primary Agent (规划)
    │
    ├──► 分析任务
    │
    ├──► 创建 Subagent A (探索代码库)
    │       │
    │       └──► 返回结果
    │
    ├──► 创建 Subagent B (执行修改)
    │       │
    │       └──► 返回结果
    │
    └──► 整合结果并响应
```

### 示例场景：代码重构

1. **用户**: "重构这个函数"

2. **Primary Agent**:
   - 分析当前代码
   - 调用 Explore Agent 查找相关文件
   - 调用 General Agent 执行重构
   - 整合结果并展示

3. **Explore Agent** (子会话):
   - 使用只读工具 (Grep, Glob, Read)
   - 返回相关文件和依赖关系

4. **General Agent** (子会话):
   - 使用完整工具权限 (Edit, Bash)
   - 执行代码修改
   - 返回变更摘要

## 关键特性

### 1. 会话隔离

每个 Agent 运行在独立的会话中：

```typescript
// 父会话
const primarySession = await session.create({
  agent: "primary"
});

// 子会话
const subagentSession = await session.create({
  agent: "explore",
  parent: primarySession.id
});

// 子会话的状态不会影响父会话
```

### 2. 动态工具分配

不同 Agent 根据任务需求分配不同的工具集：

| Agent    | 工具集                          | 用途           |
|----------|---------------------------------|----------------|
| Primary  | 全部工具                        | 通用开发       |
| Explore  | Read, Grep, Glob (只读)         | 代码探索       |
| Build    | Bash, Edit, Write (构建相关)    | 构建和测试     |
| Plan     | Read, Grep (受限)               | 规划和分析     |

### 3. 并行执行

支持多个 Agent 并行工作：

```typescript
// 并行创建多个子 Agent
const results = await Promise.all([
  agent.create({ type: 'explore', task: 'find component' }),
  agent.create({ type: 'explore', task: 'find tests' }),
  agent.create({ type: 'general', task: 'update docs' })
]);
```

### 4. 权限继承与覆盖

```typescript
// 基础权限规则
const baseRuleset = {
  bash: { ask: ['rm -rf', 'sudo'] },
  edit: { allow: ['**/*.ts'] }
};

// Agent 可以继承和覆盖
const agent = {
  permission: {
    ...baseRuleset,
    edit: { allow: ['**/*.js'] }  // 覆盖
  }
};
```

## 技术优势

### 与单 Agent 架构的对比

| 特性           | 单 Agent         | 多 Agent (OpenCode)       |
|----------------|------------------|--------------------------|
| 任务专注度     | 低（需要切换模式）| 高（专业化分工）          |
| 并行能力       | 有限             | 强（独立会话）            |
| 权限控制       | 粗粒度           | 细粒度（按 Agent 配置）   |
| 可扩展性       | 一般             | 强（易于添加新 Agent）    |
| 上下文隔离     | 无               | 完全隔离                 |
| 错误影响范围   | 全局             | 局部（子会话失败不影响主会话） |

### 可扩展性

添加新 Agent 非常简单：

```typescript
// 定义新 Agent
const docWriter = {
  name: 'doc-writer',
  description: '专门生成文档',
  mode: 'subagent',
  permission: {
    read: { allow: ['**/*'] },
    write: { allow: ['**/*.md'] }
  },
  prompt: '你是一个文档编写专家...'
};

// 注册即可使用
```

## 设计模式

### 1. 策略模式 (Strategy Pattern)

不同 Agent 实现不同的任务执行策略：

```typescript
interface TaskStrategy {
  execute(task: Task): Promise<Result>;
}

class ExploreStrategy implements TaskStrategy { }
class BuildStrategy implements TaskStrategy { }
class GeneralStrategy implements TaskStrategy { }
```

### 2. 工厂模式 (Factory Pattern)

动态创建不同类型的 Agent：

```typescript
class AgentFactory {
  static create(type: string, config: Config): Agent {
    switch (type) {
      case 'explore': return new ExploreAgent(config);
      case 'build': return new BuildAgent(config);
      default: return new GeneralAgent(config);
    }
  }
}
```

### 3. 观察者模式 (Observer Pattern)

会话状态变化通知：

```typescript
session.on('message', (msg) => {
  // 处理消息
});

session.on('tool-call', (call) => {
  // 记录工具调用
});
```

## 性能考虑

### 1. 懒加载

Agent 和工具按需加载，减少内存占用。

### 2. 连接池

复用模型连接，提高响应速度。

### 3. 缓存机制

缓存文件读取和搜索结果，避免重复操作。

### 4. 并行限制

控制并行 Agent 数量，避免资源耗尽。

## 安全性

### 1. 权限隔离

每个 Agent 有独立的权限配置，互不影响。

### 2. 沙箱执行

危险操作需要用户确认。

### 3. 审计日志

记录所有 Agent 的操作，便于追踪和调试。

## 后续文档

- [Agent 系统详解](./02-agent-system.md) - 深入了解 Agent 的定义和实现
- [会话管理机制](./03-session-management.md) - 会话的生命周期管理
- [通信协议](./04-communication.md) - ACP 协议规范
