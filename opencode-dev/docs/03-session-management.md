# 会话管理机制

## 概述

会话 (Session) 是 Agent 的执行环境，负责管理消息流、状态维护和工具调用。每个 Agent 运行在独立的会话中，确保上下文隔离。

## 核心概念

### 会话类型

1. **主会话 (Primary Session)**
   - Primary Agent 的会话
   - 直接响应用户输入
   - 可以创建子会话

2. **子会话 (Subagent Session)**
   - Subagent 的会话
   - 由主会话或其他子会话创建
   - 独立的上下文和状态

### 会话层级

```
Primary Session (root)
├── Subagent Session A
│   ├── Subagent Session A1
│   └── Subagent Session A2
└── Subagent Session B
```

## 会话结构

### 核心文件

```
packages/opencode/src/session/
├── index.ts           # 会话核心 API
├── processor.ts       # 会话处理器，处理消息流
├── message-v2.ts      # 消息系统定义
├── system.ts          # 系统提示词管理
└── snapshot.ts        # 会话快照
```

### 会话接口

```typescript
interface Session {
  id: string;              // 唯一标识
  agent: Agent.Info;       // 关联的 Agent
  parent?: string;         // 父会话 ID
  messages: Message[];     // 消息历史
  state: SessionState;     // 会话状态
  tools: Tool[];           // 可用工具
  created: Date;           // 创建时间
  updated: Date;           // 更新时间
}

enum SessionState {
  Idle = "idle",           // 空闲
  Running = "running",     // 运行中
  Paused = "paused",       // 暂停
  Completed = "completed", // 已完成
  Error = "error"          // 错误
}
```

## 会话创建

### 基本创建

```typescript
// packages/opencode/src/session/index.ts
export async function create(input: {
  agent: string | Agent.Info;  // Agent 名称或配置
  parent?: string;              // 父会话 ID
  options?: SessionOptions;     // 额外选项
}): Promise<Session> {
  // 1. 解析 Agent 配置
  const agentConfig = resolveAgent(input.agent);

  // 2. 初始化工具
  const tools = await ToolRegistry.tools(
    agentConfig.model,
    agentConfig
  );

  // 3. 创建会话实例
  const session: Session = {
    id: generateId(),
    agent: agentConfig,
    parent: input.parent,
    messages: [],
    tools: tools,
    state: SessionState.Idle,
    created: new Date(),
    updated: new Date()
  };

  // 4. 初始化系统提示词
  await initializeSystemPrompt(session);

  // 5. 保存会话
  await store.save(session);

  return session;
}
```

### 创建子会话

```typescript
// 创建子会话
const childSession = await session.create({
  agent: "explore",
  parent: session.id
});

// 子会话继承父会话的某些属性
console.log(childSession.parent); // session.id
```

### 批量创建子会话

```typescript
// 并行创建多个子会话
const sessions = await Promise.all([
  session.create({ agent: "explore" }),
  session.create({ agent: "general" }),
  session.create({ agent: "build" })
]);
```

## 会话生命周期

### 状态转换图

```
     create()
        │
        ▼
    [Idle] ──────► start() ──────► [Running]
        │                                │
        │                                │ complete()
        │                                ▼
        │                           [Completed]
        │                                │
        │                                │ destroy()
        ▼                                ▼
    ────────────────────────────────── [Destroyed]
```

### 生命周期方法

```typescript
class SessionManager {
  // 初始化
  async initialize(session: Session) {
    // 加载配置
    // 初始化工具
    // 建立连接
  }

  // 启动
  async start(session: Session) {
    session.state = SessionState.Running;
    await this.runProcessor(session);
  }

  // 暂停
  async pause(session: Session) {
    session.state = SessionState.Paused;
    await this.saveSnapshot(session);
  }

  // 恢复
  async resume(session: Session) {
    session.state = SessionState.Running;
    await this.runProcessor(session);
  }

  // 完成
  async complete(session: Session) {
    session.state = SessionState.Completed;
    await this.cleanup(session);
  }

  // 销毁
  async destroy(session: Session) {
    await this.cleanup(session);
    await store.delete(session.id);
  }
}
```

## 消息处理

### 消息结构

```typescript
// packages/opencode/src/session/message-v2.ts
export namespace Message {
  export const Part = z.discriminatedUnion("type", [
    // 用户输入
    z.object({
      type: z.literal("user"),
      content: z.string()
    }),

    // AI 响应
    z.object({
      type: z.literal("assistant"),
      content: z.string()
    }),

    // 工具调用
    z.object({
      type: z.literal("tool-call"),
      id: z.string(),
      name: z.string(),
      input: z.any()
    }),

    // 工具结果
    z.object({
      type: z.literal("tool-result"),
      id: z.string(),
      output: z.any(),
      error: z.any().optional()
    }),

    // Agent 创建
    z.object({
      type: z.literal("agent"),
      name: z.string(),
      source: z.object({
        value: z.string(),
        start: z.number(),
        end: z.number()
      }).optional()
    })
  ])

  export type Part = z.infer<typeof Part>
}
```

### 消息流程

```typescript
// 发送消息到会话
export async function sendMessage(
  session: Session,
  content: string
): Promise<Response> {
  // 1. 添加用户消息到历史
  session.messages.push({
    type: "user",
    content: content
  });

  // 2. 创建处理器
  const processor = new Processor(session);

  // 3. 开始处理循环
  const response = await processor.run();

  // 4. 返回流式响应
  return response;
}
```

## 会话处理器

### Processor 核心逻辑

```typescript
// packages/opencode/src/session/processor.ts
export class Processor {
  private session: Session;
  private tools: Map<string, Tool>;
  private pendingCalls: Map<string, ToolCall>;

  constructor(session: Session) {
    this.session = session;
    this.tools = new Map(
      session.tools.map(t => [t.name, t])
    );
    this.pendingCalls = new Map();
  }

  async run(): Promise<Response> {
    while (true) {
      try {
        // 1. 准备输入
        const input = this.prepareInput();

        // 2. 调用 LLM
        const stream = await LLM.stream(input);

        // 3. 处理响应流
        for await (const value of stream.fullStream) {
          await this.handleStreamValue(value);
        }

        // 4. 检查是否完成
        if (this.isComplete()) {
          break;
        }

      } catch (error) {
        await this.handleError(error);
        break;
      }
    }

    return this.buildResponse();
  }

  async handleStreamValue(value: any) {
    switch (value.type) {
      case "text-delta":
        // 处理文本输出
        await this.emitText(value.value);
        break;

      case "tool-call":
        // 处理工具调用
        await this.handleToolCall(value);
        break;

      case "tool-input-start":
        // 工具输入开始
        await this.emitToolInputStart(value);
        break;

      case "tool-input-done":
        // 工具输入完成
        await this.emitToolInputDone(value);
        break;

      case "error":
        // 处理错误
        await this.handleError(value.error);
        break;
    }
  }

  async handleToolCall(call: ToolCall) {
    const tool = this.tools.get(call.name);

    if (!tool) {
      await this.emitError(`Unknown tool: ${call.name}`);
      return;
    }

    // 标记为 pending
    this.pendingCalls.set(call.id, {
      ...call,
      status: "running"
    });

    try {
      // 执行工具
      const result = await tool.execute(call.input);

      // 保存结果
      this.session.messages.push({
        type: "tool-result",
        id: call.id,
        output: result
      });

      // 更新状态
      this.pendingCalls.set(call.id, {
        ...call,
        status: "completed",
        result: result
      });

    } catch (error) {
      // 处理错误
      this.session.messages.push({
        type: "tool-result",
        id: call.id,
        error: error
      });

      this.pendingCalls.set(call.id, {
        ...call,
        status: "error",
        error: error
      });
    }
  }
}
```

## 会话快照

### 快照结构

```typescript
interface SessionSnapshot {
  id: string;
  sessionId: string;
  timestamp: Date;
  messages: Message[];
  state: SessionState;
  metadata: {
    agent: string;
    parent?: string;
    steps: number;
    tokens: number;
  };
}
```

### 创建快照

```typescript
export async function createSnapshot(
  session: Session
): Promise<SessionSnapshot> {
  return {
    id: generateId(),
    sessionId: session.id,
    timestamp: new Date(),
    messages: [...session.messages],
    state: session.state,
    metadata: {
      agent: session.agent.name,
      parent: session.parent,
      steps: session.messages.length,
      tokens: countTokens(session.messages)
    }
  };
}
```

### 恢复快照

```typescript
export async function restoreSnapshot(
  snapshotId: string
): Promise<Session> {
  // 1. 加载快照
  const snapshot = await store.load(snapshotId);

  // 2. 重建会话
  const session: Session = {
    id: snapshot.sessionId,
    agent: await resolveAgent(snapshot.metadata.agent),
    parent: snapshot.metadata.parent,
    messages: snapshot.messages,
    state: snapshot.state,
    tools: await loadTools(snapshot.metadata.agent),
    created: new Date(),  // 新的创建时间
    updated: new Date()
  };

  // 3. 恢复处理器
  await resumeProcessor(session);

  return session;
}
```

## 会话分叉

### 分叉概念

会话分叉允许从现有会话创建一个新分支，两个分支共享相同的历史但独立发展。

```typescript
export async function fork(
  session: Session,
  options?: ForkOptions
): Promise<Session> {
  // 1. 创建新会话
  const forked: Session = {
    ...session,
    id: generateId(),
    parent: session.id,
    messages: [...session.messages],  // 复制消息历史
    created: new Date(),
    updated: new Date()
  };

  // 2. 保存分叉信息
  await store.save({
    type: "fork",
    from: session.id,
    to: forked.id,
    timestamp: new Date()
  });

  return forked;
}
```

### 分叉图

```
Original Session
    │
    ├───► Fork A
    │        │
    │        └──► Fork A1
    │
    └───► Fork B
             └───► Fork B1
```

## 会话导航

### 会话树

```typescript
interface SessionTree {
  session: Session;
  children: SessionTree[];
}

async function buildSessionTree(
  rootId: string
): Promise<SessionTree> {
  const root = await store.load(rootId);
  const children = await store.findChildren(rootId);

  return {
    session: root,
    children: await Promise.all(
      children.map(c => buildSessionTree(c.id))
    )
  };
}
```

### 导航操作

```typescript
// 上一个会话
async function navigateUp(session: Session): Promise<Session | null> {
  if (!session.parent) return null;
  return store.load(session.parent);
}

// 下一个会话
async function navigateDown(
  session: Session,
  index: number
): Promise<Session | null> {
  const children = await store.findChildren(session.id);
  if (index >= children.length) return null;
  return store.load(children[index].id);
}

// 同级会话
async function navigateNext(
  session: Session
): Promise<Session | null> {
  const siblings = await store.findSiblings(session.id);
  const currentIndex = siblings.findIndex(s => s.id === session.id);
  if (currentIndex === -1 || currentIndex === siblings.length - 1) {
    return null;
  }
  return store.load(siblings[currentIndex + 1].id);
}
```

## 会话事件

### 事件类型

```typescript
enum SessionEvent {
  Created = "created",
  Started = "started",
  MessageAdded = "message-added",
  ToolCalled = "tool-called",
  Completed = "completed",
  Error = "error",
  Destroyed = "destroyed"
}
```

### 事件监听

```typescript
// 监听会话事件
session.on(SessionEvent.MessageAdded, (message) => {
  console.log('New message:', message.content);
});

session.on(SessionEvent.ToolCalled, (call) => {
  console.log('Tool called:', call.name);
});

session.on(SessionEvent.Error, (error) => {
  console.error('Session error:', error);
});
```

### 事件传播

```typescript
// 子会话事件传播到父会话
async function propagateEvent(
  session: Session,
  event: SessionEvent,
  data: any
) {
  // 触发本地事件
  session.emit(event, data);

  // 如果有父会话，传播事件
  if (session.parent) {
    const parent = await store.load(session.parent);
    parent.emit(`child:${event}`, {
      child: session.id,
      data: data
    });
  }
}
```

## 会话存储

### 存储接口

```typescript
interface SessionStore {
  // 保存会话
  save(session: Session): Promise<void>;

  // 加载会话
  load(id: string): Promise<Session>;

  // 删除会话
  delete(id: string): Promise<void>;

  // 查找会话
  find(query: SessionQuery): Promise<Session[]>;

  // 查找子会话
  findChildren(parentId: string): Promise<Session[]>;

  // 查找兄弟会话
  findSiblings(id: string): Promise<Session[]>;
}
```

### 内存实现

```typescript
class MemorySessionStore implements SessionStore {
  private sessions: Map<string, Session> = new Map();
  private children: Map<string, string[]> = new Map();

  async save(session: Session): Promise<void> {
    this.sessions.set(session.id, session);

    if (session.parent) {
      const siblings = this.children.get(session.parent) || [];
      siblings.push(session.id);
      this.children.set(session.parent, siblings);
    }
  }

  async load(id: string): Promise<Session> {
    const session = this.sessions.get(id);
    if (!session) {
      throw new Error(`Session not found: ${id}`);
    }
    return session;
  }

  async findChildren(parentId: string): Promise<Session[]> {
    const childIds = this.children.get(parentId) || [];
    return Promise.all(
      childIds.map(id => this.load(id))
    );
  }
}
```

## 会话清理

### 自动清理策略

```typescript
class SessionCleaner {
  private config: {
    maxAge: number;          // 最大年龄 (ms)
    maxSessions: number;     // 最大会话数
    cleanupInterval: number; // 清理间隔 (ms)
  };

  async cleanup() {
    const sessions = await store.find({});

    // 按创建时间排序
    const sorted = sessions.sort((a, b) =>
      a.created.getTime() - b.created.getTime()
    );

    // 删除超过最大数量的会话
    if (sorted.length > this.config.maxSessions) {
      const toDelete = sorted.slice(0, sorted.length - this.config.maxSessions);
      for (const session of toDelete) {
        await store.delete(session.id);
      }
    }

    // 删除过期的会话
    const now = Date.now();
    for (const session of sorted) {
      const age = now - session.created.getTime();
      if (age > this.config.maxAge) {
        await store.delete(session.id);
      }
    }
  }

  start() {
    setInterval(() => {
      this.cleanup();
    }, this.config.cleanupInterval);
  }
}
```

## 最佳实践

### 1. 会话隔离

确保不同任务的会话相互隔离：

```typescript
// 为每个任务创建独立的会话
const taskSession = await session.create({
  agent: "general",
  metadata: { taskId: task.id }
});
```

### 2. 及时清理

完成任务的会话应该及时清理：

```typescript
// 使用完后立即销毁
try {
  await agent.execute(session);
} finally {
  await session.destroy();
}
```

### 3. 快照备份

重要状态应该创建快照：

```typescript
// 在关键步骤创建快照
if (isCriticalStep(session)) {
  await createSnapshot(session);
}
```

### 4. 错误处理

会话错误应该妥善处理：

```typescript
session.on(SessionEvent.Error, async (error) => {
  // 记录错误
  logger.error('Session error:', error);

  // 创建错误快照用于调试
  await createSnapshot(session);

  // 如果是致命错误，终止会话
  if (isFatal(error)) {
    await session.destroy();
  }
});
```

## 后续文档

- [Agent 通信协议](./04-communication.md) - 了解会话间如何通信
- [任务执行流程](./05-task-execution.md) - 深入了解任务在会话中的执行
