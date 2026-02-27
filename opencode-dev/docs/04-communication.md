# Agent 通信协议 (ACP)

## 概述

Agent Communication Protocol (ACP) 是 OpenCode 中 Agent 之间通信的标准协议。它定义了消息格式、会话管理、工具调用协调等规范。

## 核心文件

```
packages/opencode/src/acp/
└── agent.ts           # ACP 核心实现
```

## 协议架构

### 分层结构

```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
│              (Agent 业务逻辑)                             │
├─────────────────────────────────────────────────────────┤
│                   ACP Protocol Layer                     │
│         (消息格式、会话管理、工具协调)                      │
├─────────────────────────────────────────────────────────┤
│                   Transport Layer                        │
│           (流式传输、事件、连接管理)                       │
└─────────────────────────────────────────────────────────┘
```

### 核心组件

1. **Agent Client**: 实现 ACP 的客户端
2. **Message Protocol**: 消息格式规范
3. **Session Manager**: 会话生命周期管理
4. **Tool Coordinator**: 工具调用协调

## Agent Client

### 客户端接口

```typescript
// packages/opencode/src/acp/agent.ts
export interface AgentClient {
  // 会话管理
  createSession(config: SessionConfig): Promise<Session>;
  loadSession(id: string): Promise<Session>;
  forkSession(id: string): Promise<Session>;
  resumeSession(id: string): Promise<Session>;

  // 消息传递
  sendMessage(sessionId: string, message: Message): Promise<Response>;
  sendEvent(sessionId: string, event: Event): Promise<void>;

  // 工具调用
  callTool(sessionId: string, toolCall: ToolCall): Promise<ToolResult>;

  // 流式处理
  streamMessages(sessionId: string): AsyncIterable<Message>;

  // 状态查询
  getStatus(sessionId: string): Promise<SessionStatus>;
}
```

### 客户端实现

```typescript
export class ACPClient implements AgentClient {
  private transport: Transport;
  private sessionManager: SessionManager;

  constructor(config: ClientConfig) {
    this.transport = new Transport(config.transport);
    this.sessionManager = new SessionManager(config.storage);
  }

  async createSession(config: SessionConfig): Promise<Session> {
    // 1. 验证配置
    this.validateConfig(config);

    // 2. 创建会话 ID
    const sessionId = generateId();

    // 3. 初始化会话
    const session = await this.sessionManager.create({
      id: sessionId,
      agent: config.agent,
      parent: config.parent,
      tools: config.tools
    });

    // 4. 建立连接
    await this.transport.connect(sessionId);

    // 5. 返回会话
    return session;
  }

  async sendMessage(
    sessionId: string,
    message: Message
  ): Promise<Response> {
    // 1. 获取会话
    const session = await this.sessionManager.get(sessionId);

    // 2. 序列化消息
    const payload = this.serializeMessage(message);

    // 3. 发送消息
    const result = await this.transport.send(sessionId, payload);

    // 4. 反序列化响应
    return this.deserializeResponse(result);
  }

  async streamMessages(
    sessionId: string
  ): AsyncIterable<Message> {
    const stream = await this.transport.stream(sessionId);

    return this.deserializeStream(stream);
  }
}
```

## 消息协议

### 消息类型

```typescript
export namespace ACPMessage {
  // 请求消息
  export const Request = z.discriminatedUnion("type", [
    // 会话创建
    z.object({
      type: z.literal("session-create"),
      requestId: z.string(),
      payload: z.object({
        agent: z.string(),
        parent: z.string().optional(),
        options: z.record(z.any()).optional()
      })
    }),

    // 消息发送
    z.object({
      type: z.literal("message-send"),
      requestId: z.string(),
      sessionId: z.string(),
      payload: z.object({
        content: z.string(),
        metadata: z.record(z.any()).optional()
      })
    }),

    // 工具调用
    z.object({
      type: z.literal("tool-call"),
      requestId: z.string(),
      sessionId: z.string(),
      payload: z.object({
        id: z.string(),
        name: z.string(),
        input: z.any()
      })
    }),

    // 会话查询
    z.object({
      type: z.literal("session-query"),
      requestId: z.string(),
      sessionId: z.string()
    })
  ])

  // 响应消息
  export const Response = z.discriminatedUnion("type", [
    // 成功响应
    z.object({
      type: z.literal("success"),
      requestId: z.string(),
      payload: z.any()
    }),

    // 错误响应
    z.object({
      type: z.literal("error"),
      requestId: z.string(),
      error: z.object({
        code: z.string(),
        message: z.string(),
        details: z.any().optional()
      })
    }),

    // 流式响应
    z.object({
      type: z.literal("stream-chunk"),
      requestId: z.string(),
      chunk: z.any(),
      done: z.boolean()
    })
  ])
}
```

### 消息流转

```
Primary Agent              ACP Layer               Subagent
     │                       │                        │
     │─── Request ────────────┼───────────────────────>│
     │                       │                        │
     │                       │                        ├─── Process
     │                       │                        │
     │<── Stream Chunk ───────┼───────────────────────┤
     │                       │                        │
     │<── Stream Chunk ───────┼───────────────────────┤
     │                       │                        │
     │<── Success ────────────┼───────────────────────┤
```

## 会话管理协议

### 会话创建

```typescript
// 请求
{
  "type": "session-create",
  "requestId": "req-123",
  "payload": {
    "agent": "explore",
    "parent": "parent-session-id",
    "options": {
      "model": "claude-3-5-haiku",
      "maxSteps": 50
    }
  }
}

// 响应
{
  "type": "success",
  "requestId": "req-123",
  "payload": {
    "sessionId": "new-session-id",
    "status": "idle",
    "tools": ["read", "grep", "glob"]
  }
}
```

### 会话加载

```typescript
{
  "type": "session-load",
  "requestId": "req-124",
  "payload": {
    "sessionId": "existing-session-id"
  }
}
```

### 会话分叉

```typescript
{
  "type": "session-fork",
  "requestId": "req-125",
  "payload": {
    "sessionId": "original-session-id",
    "options": {
      "preserveMessages": true
    }
  }
}
```

## 工具调用协议

### 工具调用流程

```typescript
// 1. 发起工具调用
{
  "type": "tool-call",
  "requestId": "req-126",
  "sessionId": "session-123",
  "payload": {
    "id": "call-456",
    "name": "read",
    "input": {
      "file_path": "/path/to/file.ts"
    }
  }
}

// 2. 工具开始执行
{
  "type": "tool-start",
  "requestId": "req-126",
  "payload": {
    "callId": "call-456",
    "status": "running"
  }
}

// 3. 工具执行结果
{
  "type": "tool-result",
  "requestId": "req-126",
  "payload": {
    "callId": "call-456",
    "status": "completed",
    "output": "file content here..."
  }
}
```

### 工具调用协调

```typescript
class ToolCoordinator {
  private pendingCalls: Map<string, ToolCall> = new Map();
  private results: Map<string, ToolResult> = new Map();

  async executeCall(call: ToolCall): Promise<ToolResult> {
    // 1. 注册调用
    this.pendingCalls.set(call.id, call);

    // 2. 通知开始
    this.emit('tool:start', { callId: call.id });

    try {
      // 3. 执行工具
      const tool = await this.resolveTool(call.name);
      const result = await tool.execute(call.input);

      // 4. 保存结果
      this.results.set(call.id, result);

      // 5. 通知完成
      this.emit('tool:complete', {
        callId: call.id,
        result: result
      });

      return result;

    } catch (error) {
      // 处理错误
      this.emit('tool:error', {
        callId: call.id,
        error: error
      });

      throw error;
    } finally {
      // 清理
      this.pendingCalls.delete(call.id);
    }
  }

  async executeParallel(calls: ToolCall[]): Promise<ToolResult[]> {
    // 并行执行多个工具调用
    const promises = calls.map(call => this.executeCall(call));
    return Promise.all(promises);
  }

  getStatus(callId: string): ToolCallStatus {
    const call = this.pendingCalls.get(callId);
    if (call) return 'running';

    const result = this.results.get(callId);
    if (result) return 'completed';

    return 'unknown';
  }
}
```

## 流式传输

### 流式消息

```typescript
interface StreamMessage {
  type: 'stream-chunk';
  requestId: string;
  chunk: {
    type: 'text' | 'tool-call' | 'error';
    content: any;
  };
  done: boolean;
}
```

### 流式处理

```typescript
class StreamProcessor {
  async *processStream(
    sessionId: string,
    requestId: string
  ): AsyncIterable<StreamChunk> {
    const stream = await this.transport.openStream(sessionId);

    try {
      while (true) {
        const message = await stream.read();

        if (message.done) {
          break;
        }

        // 处理不同类型的块
        switch (message.chunk.type) {
          case 'text':
            yield this.processTextChunk(message.chunk);
            break;

          case 'tool-call':
            yield await this.processToolCall(message.chunk);
            break;

          case 'error':
            yield this.processError(message.chunk);
            break;
        }
      }
    } finally {
      await stream.close();
    }
  }

  private async processToolCall(chunk: any): Promise<ToolCallChunk> {
    // 执行工具调用
    const result = await this.executeTool(chunk.content);

    return {
      type: 'tool-result',
      toolId: chunk.content.id,
      result: result
    };
  }
}
```

## 错误处理

### 错误类型

```typescript
enum ACPErrorType {
  // 会话错误
  SessionNotFound = 'session-not-found',
  SessionAlreadyExists = 'session-already-exists',
  SessionInvalid = 'session-invalid',

  // 消息错误
  MessageInvalid = 'message-invalid',
  MessageTooLarge = 'message-too-large',

  // 工具错误
  ToolNotFound = 'tool-not-found',
  ToolExecutionFailed = 'tool-execution-failed',
  ToolPermissionDenied = 'tool-permission-denied',

  // 协议错误
  ProtocolViolation = 'protocol-violation',
  VersionMismatch = 'version-mismatch'
}
```

### 错误响应

```typescript
interface ACPErrorResponse {
  type: 'error';
  requestId: string;
  error: {
    code: ACPErrorType;
    message: string;
    details?: any;
    stack?: string;
  };
}
```

### 错误处理策略

```typescript
class ErrorHandler {
  async handleError(error: ACPError): Promise<ACPErrorResponse> {
    // 1. 记录错误
    this.logger.error('ACP Error:', error);

    // 2. 构建响应
    const response: ACPErrorResponse = {
      type: 'error',
      requestId: error.requestId,
      error: {
        code: error.code,
        message: this.getUserMessage(error),
        details: error.details,
        stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
      }
    };

    // 3. 特定错误处理
    switch (error.code) {
      case ACPErrorType.SessionNotFound:
        await this.handleSessionNotFound(error);
        break;

      case ACPErrorType.ToolExecutionFailed:
        await this.handleToolFailed(error);
        break;
    }

    return response;
  }

  private getUserMessage(error: ACPError): string {
    // 将技术错误转换为用户友好的消息
    const messages = {
      [ACPErrorType.SessionNotFound]: '会话不存在或已过期',
      [ACPErrorType.ToolNotFound]: `找不到工具: ${error.details?.toolName}`,
      [ACPErrorType.ToolPermissionDenied]: '没有权限执行此操作'
    };

    return messages[error.code] || '发生未知错误';
  }
}
```

## 权限验证

### 权限检查

```typescript
class PermissionChecker {
  async checkToolCall(
    sessionId: string,
    toolCall: ToolCall
  ): Promise<boolean> {
    // 1. 获取会话
    const session = await this.sessionManager.get(sessionId);

    // 2. 获取工具权限
    const permission = session.agent.permission;

    // 3. 检查权限
    const result = evaluate(
      `tool:${toolCall.name}`,
      toolCall.input,
      permission
    );

    // 4. 处理结果
    if (result === 'deny') {
      throw new ACPError({
        code: ACPErrorType.ToolPermissionDenied,
        message: '权限被拒绝',
        details: { toolCall }
      });
    }

    if (result === 'ask') {
      // 需要用户确认
      return await this.requestPermission(toolCall);
    }

    return true;
  }

  private async requestPermission(toolCall: ToolCall): Promise<boolean> {
    // 发送权限请求事件
    const response = await this.emitter.emitAsync('permission:request', {
      tool: toolCall.name,
      input: toolCall.input
    });

    return response.allowed;
  }
}
```

## 事件系统

### 事件类型

```typescript
enum ACPEvent {
  // 会话事件
  SessionCreated = 'session:created',
  SessionDestroyed = 'session:destroyed',
  SessionUpdated = 'session:updated',

  // 消息事件
  MessageSent = 'message:sent',
  MessageReceived = 'message:received',

  // 工具事件
  ToolCalled = 'tool:called',
  ToolCompleted = 'tool:completed',
  ToolFailed = 'tool:failed',

  // 错误事件
  Error = 'error'
}
```

### 事件发布/订阅

```typescript
class EventEmitter {
  private listeners: Map<string, Listener[]> = new Map();

  on(event: ACPEvent, listener: Listener): void {
    const existing = this.listeners.get(event) || [];
    existing.push(listener);
    this.listeners.set(event, existing);
  }

  async emit(event: ACPEvent, data: any): Promise<void> {
    const listeners = this.listeners.get(event) || [];

    for (const listener of listeners) {
      try {
        await listener(data);
      } catch (error) {
        console.error(`Listener error for ${event}:`, error);
      }
    }
  }

  off(event: ACPEvent, listener: Listener): void {
    const listeners = this.listeners.get(event) || [];
    const filtered = listeners.filter(l => l !== listener);
    this.listeners.set(event, filtered);
  }
}
```

## 协议版本

### 版本协商

```typescript
interface ProtocolVersion {
  major: number;
  minor: number;
  patch: number;
}

class VersionManager {
  async negotiateVersion(
    clientVersion: ProtocolVersion,
    serverVersion: ProtocolVersion
  ): Promise<ProtocolVersion> {
    // 选择兼容的版本
    if (clientVersion.major === serverVersion.major) {
      // 相同主版本，选择较低的次版本
      return clientVersion.minor <= serverVersion.minor
        ? clientVersion
        : serverVersion;
    }

    // 不兼容，抛出错误
    throw new ACPError({
      code: ACPErrorType.VersionMismatch,
      message: '协议版本不兼容',
      details: {
        client: clientVersion,
        server: serverVersion
      }
    });
  }
}
```

## 安全性

### 加密通信

```typescript
class SecureTransport implements Transport {
  private encryption: Encryption;

  async send(sessionId: string, data: any): Promise<any> {
    // 1. 序列化数据
    const serialized = JSON.stringify(data);

    // 2. 加密
    const encrypted = await this.encryption.encrypt(serialized);

    // 3. 发送
    return this.transport.send(sessionId, encrypted);
  }

  async receive(sessionId: string): Promise<any> {
    // 1. 接收
    const encrypted = await this.transport.receive(sessionId);

    // 2. 解密
    const decrypted = await this.encryption.decrypt(encrypted);

    // 3. 反序列化
    return JSON.parse(decrypted);
  }
}
```

### 认证

```typescript
class Authenticator {
  async authenticate(sessionId: string, token: string): Promise<boolean> {
    // 1. 验证 token
    const payload = await this.verifyToken(token);

    // 2. 检查权限
    const hasAccess = await this.checkAccess(payload);

    return hasAccess;
  }

  private async verifyToken(token: string): Promise<any> {
    // JWT 验证逻辑
    return jwt.verify(token, this.secret);
  }
}
```

## 最佳实践

### 1. 连接复用

```typescript
// 复用连接以提高性能
class ConnectionPool {
  private connections: Map<string, Connection> = new Map();

  async getSession(sessionId: string): Promise<Connection> {
    let conn = this.connections.get(sessionId);

    if (!conn) {
      conn = await this.createConnection(sessionId);
      this.connections.set(sessionId, conn);
    }

    return conn;
  }
}
```

### 2. 超时处理

```typescript
// 设置合理的超时
async function withTimeout<T>(
  promise: Promise<T>,
  timeout: number
): Promise<T> {
  const timer = setTimeout(() => {
    throw new Error('Timeout');
  }, timeout);

  try {
    return await promise;
  } finally {
    clearTimeout(timer);
  }
}
```

### 3. 重试机制

```typescript
// 指数退避重试
async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3
): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;

      const delay = Math.pow(2, i) * 1000;
      await sleep(delay);
    }
  }
}
```

## 后续文档

- [任务执行流程](./05-task-execution.md) - 了解 ACP 如何协调任务执行
- [权限管理系统](./07-permission-system.md) - 深入了解权限验证
