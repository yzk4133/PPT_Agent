# Agent 系统详解

## 概述

Agent 是 OpenCode 架构的核心执行单元。每个 Agent 都是一个独立的 AI 实体，具有特定的角色、能力和权限配置。

## Agent 定义

### 核心结构

Agent 的定义位于 `packages/opencode/src/agent/agent.ts`:

```typescript
export namespace Agent {
  export const Info = z.object({
    name: z.string(),                    // Agent 唯一标识
    description: z.string().optional(),  // 功能描述
    mode: z.enum(["subagent", "primary", "all"]),  // 运行模式
    native: z.boolean().optional(),       // 是否为内置 Agent
    hidden: z.boolean().optional(),       // 是否在列表中隐藏
    topP: z.number().optional(),          // 模型 top_p 参数
    temperature: z.number().optional(),  // 模型温度参数
    color: z.string().optional(),        // UI 显示颜色
    permission: PermissionNext.Ruleset,  // 权限规则集
    model: z.object({                     // 模型配置
      modelID: z.string(),
      providerID: z.string(),
    }).optional(),
    variant: z.string().optional(),       // 模型变体
    prompt: z.string().optional(),        // 系统提示词
    options: z.record(z.string(), z.any()), // 额外选项
    steps: z.number().int().positive().optional(), // 最大步骤数
  })

  export type Info = z.infer<typeof Info>
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | Agent 的唯一标识符，用于引用和配置 |
| `description` | string | 人类可读的功能描述，显示在 UI 中 |
| `mode` | enum | `primary`: 主 Agent，直接响应用户<br>`subagent`: 子 Agent，被调用执行任务<br>`all`: 两种模式都支持 |
| `native` | boolean | 标识是否为系统内置的 Agent |
| `hidden` | boolean | 是否在 Agent 列表中隐藏（不显示给用户） |
| `permission` | Ruleset | 定义 Agent 可以执行的操作权限 |
| `model` | object | 指定使用的 AI 模型和提供商 |
| `prompt` | string | Agent 的系统提示词，定义其行为和角色 |
| `temperature` | number | 控制模型输出的随机性 (0-1) |
| `topP` | number | 核采样参数，控制输出的多样性 |
| `steps` | number | 限制 Agent 可以执行的最大步骤数 |

## 运行模式

### Primary 模式

**特点**:
- 直接响应用户输入
- 可以创建子 Agent
- 可以使用 Tab 键切换
- 通常拥有完整的工具访问权限

**适用场景**:
- 通用开发任务
- 需要协调其他 Agent 的复杂任务
- 用户直接交互的场景

```typescript
const primaryAgent: Agent.Info = {
  name: "primary",
  description: "默认 Agent，具有所有工具权限",
  mode: "primary",
  permission: {
    // 完整权限
  }
}
```

### Subagent 模式

**特点**:
- 不直接响应用户输入
- 被 Primary Agent 创建和调用
- 运行在独立的子会话中
- 通常具有受限的工具权限

**适用场景**:
- 专业化任务（代码探索、构建、测试）
- 需要隔离执行环境
- 并行处理的子任务

```typescript
const subagent: Agent.Info = {
  name: "explore",
  description: "快速探索代码库",
  mode: "subagent",
  permission: {
    // 只读权限
  }
}
```

## 内置 Agent

OpenCode 提供了多个内置 Agent，每个都有专门的用途：

### 1. Build Agent

```typescript
{
  name: "build",
  description: "默认 Agent，具有所有工具权限",
  mode: "primary",
  permission: buildPermission,  // 完整权限
  prompt: "You are an AI programming assistant..."
}
```

**用途**: 通用开发，需要完整文件访问和系统命令

### 2. Plan Agent

```typescript
{
  name: "plan",
  description: "受限 Agent，用于规划和分析",
  mode: "primary",
  permission: planPermission,  // 默认禁止文件编辑和 bash
  prompt: "You are a planning agent..."
}
```

**用途**: 代码审查、架构分析、任务规划

**权限限制**:
```typescript
const planPermission = {
  edit: { deny: ["**"] },      // 禁止编辑
  bash: { deny: ["**"] },      // 禁止命令执行
  write: { deny: ["**"] }      // 禁止写入
}
```

### 3. General Agent

```typescript
{
  name: "general-purpose",
  description: "通用目的 Agent，用于复杂任务",
  mode: "subagent",
  permission: generalPermission,  // 除 todo 工具外完整权限
}
```

**用途**: 复杂的多步骤任务

### 4. Explore Agent

```typescript
{
  name: "explore",
  description: "快速探索代码库，只读权限",
  mode: "subagent",
  permission: explorePermission,  // 只读权限
  model: {
    modelID: "claude-3-5-haiku-20241022",  // 使用快速模型
    providerID: "anthropic"
  }
}
```

**用途**: 文件查找、代码搜索、代码库问答

**只读权限**:
```typescript
const explorePermission = {
  edit: { deny: ["**"] },
  bash: { deny: ["**"] },
  write: { deny: ["**"] }
}
```

## Agent 创建

### 1. 静态定义

最常用的方式，在配置文件中定义：

```typescript
// config.ts
export const agents: Record<string, Agent.Info> = {
  "my-agent": {
    name: "my-agent",
    description: "我的自定义 Agent",
    mode: "subagent",
    permission: {
      read: { allow: ["**/*"] },
      edit: { allow: ["**/*.ts"] }
    },
    prompt: "你是一个专注于 TypeScript 的专家..."
  }
}
```

### 2. 动态生成

使用 AI 自动生成 Agent 配置：

```typescript
// 位于 packages/opencode/src/agent/agent.ts
export async function generate(input: {
  description: string;
  model?: { providerID: string; modelID: string }
}) {
  const params = {
    model: input.model || defaultModel,
    schema: Agent.Info,
    prompt: `
      根据以下描述生成一个 Agent 配置:
      ${input.description}

      请返回完整的 Agent.Info 对象。
    `,
    output: "object"
  }

  const result = await generateObject(params)
  return result.object
}
```

**使用示例**:
```typescript
const agent = await Agent.generate({
  description: "创建一个专门处理 Python 测试的 Agent"
})

// 自动生成类似:
// {
//   name: "python-tester",
//   mode: "subagent",
//   permission: { ... },
//   prompt: "你是一个 Python 测试专家..."
// }
```

## Agent 提示词系统

### 提示词目录结构

```
packages/opencode/src/agent/prompt/
├── generate.txt      # Agent 生成提示词
├── compaction.txt   # 会话压缩提示词
├── explore.txt      # Explore Agent 提示词
├── summary.txt      # 摘要生成提示词
└── title.txt        # 标题生成提示词
```

### 提示词加载机制

```typescript
export async function loadPrompt(name: string): Promise<string> {
  const path = join(__dirname, "prompt", `${name}.txt`)
  return await readFile(path, "utf-8")
}

// 使用
const explorePrompt = await loadPrompt("explore")
```

### 自定义 Agent 提示词

```typescript
const customAgent: Agent.Info = {
  name: "security-auditor",
  description: "安全审计 Agent",
  mode: "subagent",
  prompt: await loadPrompt("security-auditor"),  // 从文件加载
  // 或者直接内联
  prompt: `
    你是一个安全审计专家。

    你的任务是：
    1. 检查代码中的安全漏洞
    2. 验证依赖项的安全性
    3. 提供安全改进建议

    请专注于以下安全问题：
    - SQL 注入
    - XSS 攻击
    - CSRF 保护
    - 认证和授权
  `,
  permission: {
    read: { allow: ["**/*"] },
    // 安全审计不需要写入权限
  }
}
```

## Agent 调用机制

### 1. 手动调用

用户可以通过 `@` 符号手动调用 Subagent：

```
# 用户输入
@explore 找到所有包含 "User" 的组件

# 系统响应
[创建 explore 子会话]
[执行搜索]
[返回结果]
```

### 2. 自动调用

Primary Agent 可以自动创建和调用 Subagent：

```typescript
// 在 Primary Agent 的执行过程中
if (task.requiresExploration) {
  const subagent = await agent.create({
    type: "explore",
    task: task.description
  })

  const result = await subagent.execute()
  return result
}
```

### 3. 并行调用

```typescript
const results = await Promise.all([
  agent.create({ type: "explore", query: "components" }),
  agent.create({ type: "explore", query: "tests" }),
  agent.create({ type: "general", task: "update docs" })
])
```

## Agent 配置管理

### 配置文件结构

```typescript
export const ConfigInfo = z.object({
  agent: z.record(z.string(), z.object({
    name: z.string(),
    description: z.string(),
    model: z.string().optional(),
    variant: z.string().optional(),
    prompt: z.string().optional(),
    permission: PermissionNext.Ruleset.optional(),
    color: z.string().optional(),
    hidden: z.boolean().optional(),
    disable: z.boolean().optional(),
  }))
})
```

### 配置示例

```yaml
# config.yaml
agents:
  frontend-dev:
    name: "frontend-dev"
    description: "前端开发专家"
    model: "anthropic:claude-3-5-sonnet"
    permission:
      read:
        allow: ["src/**/*", "public/**/*"]
      edit:
        allow: ["**/*.{ts,tsx,css}"]
      bash:
        allow: ["npm *", "yarn *"]

  backend-dev:
    name: "backend-dev"
    description: "后端开发专家"
    permission:
      read:
        allow: ["server/**/*", "api/**/*"]
      edit:
        allow: ["**/*.{ts,js,go}"]
```

### 配置优先级

1. **Agent 级别配置**: 最高优先级
2. **全局配置**: 中等优先级
3. **默认配置**: 最低优先级

```typescript
// 最终配置是合并的结果
const finalConfig = merge(
  defaults,
  globalConfig,
  agentConfig
)
```

## Agent 生命周期

### 创建阶段

```typescript
// 1. 解析配置
const config = resolveAgentConfig(name)

// 2. 验证权限
validatePermissions(config.permission)

// 3. 初始化工具
const tools = await ToolRegistry.tools(config.model, config)

// 4. 创建实例
const agent = new Agent(config, tools)

// 5. 返回实例
return agent
```

### 执行阶段

```typescript
// 1. 创建会话
const session = await Session.create({
  agent: agent,
  parent: parentSession
})

// 2. 发送消息
const response = await session.sendMessage(message)

// 3. 处理工具调用
for await (const toolCall of response.toolCalls) {
  const result = await executeToolCall(toolCall)
  await session.sendToolResult(result)
}

// 4. 获取最终响应
const final = await response.finalMessage()
```

### 销毁阶段

```typescript
// 1. 清理资源
await session.cleanup()

// 2. 保存状态
await session.saveSnapshot()

// 3. 关闭连接
await session.close()

// 4. 触发事件
emitter.emit('agent:destroyed', { agent })
```

## Agent 工具分配

### 工具过滤机制

```typescript
// packages/opencode/src/tool/registry.ts
export async function tools(
  model: Model,
  agent?: Agent.Info
): Promise<Tool[]> {
  const allTools = await getAll()

  // 根据权限过滤
  const allowed = allTools.filter(tool => {
    return checkPermission(tool, agent?.permission)
  })

  // 根据模型能力过滤
  const compatible = allowed.filter(tool => {
    return isCompatible(tool, model)
  })

  return compatible
}
```

### 工具分配示例

| Agent | Read | Edit | Write | Bash | Grep | Glob | LSP | Task |
|-------|------|------|-------|------|------|------|-----|------|
| Build | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Plan | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| Explore | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| General | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |

## Agent 监控和调试

### 状态查询

```typescript
// 获取 Agent 状态
const status = await agent.getStatus()

console.log(status)
// {
//   state: "running",
//   session: "abc123",
//   tools: ["read", "edit", "bash"],
//   steps: 5,
//   maxSteps: 100
// }
```

### 日志记录

```typescript
// 启用详细日志
agent.on('log', (entry) => {
  console.log(`[${entry.level}] ${entry.message}`)
})

// 记录工具调用
agent.on('tool-call', (call) => {
  logger.info({
    tool: call.tool,
    args: call.args,
    result: call.result
  })
})
```

### 性能分析

```typescript
// 测量 Agent 执行时间
const metrics = await agent.getMetrics()

console.log(metrics)
// {
//   totalSteps: 15,
//   totalTime: 5234,  // ms
//   toolCalls: 23,
//   tokensUsed: 4521
// }
```

## 最佳实践

### 1. 选择合适的模式

- **Primary**: 用于需要用户交互和协调的场景
- **Subagent**: 用于可独立执行的专门任务

### 2. 合理设置权限

- 只授予必要的权限
- 使用 `deny` 规则保护敏感操作
- 为危险工具设置 `ask` 规则

### 3. 优化提示词

- 明确 Agent 的角色和职责
- 指定输出格式和约束
- 提供相关的上下文和示例

### 4. 选择合适的模型

- **简单任务**: 使用 Haiku（快速、便宜）
- **复杂任务**: 使用 Sonnet（平衡）
- **困难任务**: 使用 Opus（最强能力）

```typescript
const exploreAgent = {
  model: { modelID: "haiku", providerID: "anthropic" }  // 快速
}

const codingAgent = {
  model: { modelID: "sonnet", providerID: "anthropic" }  // 平衡
}
```

## 后续文档

- [会话管理机制](./03-session-management.md) - 了解 Agent 如何在会话中运行
- [权限管理系统](./07-permission-system.md) - 深入了解权限配置
