# 任务执行流程

## 概述

本文档详细说明 OpenCode 中任务的执行流程，包括任务分发、Agent 协作、工具调用和结果处理。

## 任务执行架构

```
用户请求
    │
    ▼
┌─────────────┐
│ Task Router │  ← 任务路由，决定使用哪个 Agent
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Agent     │  ← Primary Agent 接收任务
│  Manager    │
└──────┬──────┘
       │
       ├──► 分析任务需求
       │
       ├──► 创建执行计划
       │
       ▼
┌─────────────────────┐
│  Task Decomposer    │  ← 任务分解器
└────────┬────────────┘
         │
         ├──► 子任务 A ──► Subagent A
         │
         ├──► 子任务 B ──► Subagent B
         │
         └──► 子任务 C ──► Subagent C
         │
         ▼
┌─────────────────────┐
│  Result Aggregator  │  ← 结果聚合器
└────────┬────────────┘
         │
         ▼
    最终响应
```

## 核心组件

### 1. Task Router (任务路由器)

负责将用户请求路由到合适的 Agent。

```typescript
class TaskRouter {
  private routes: Map<string, RouteConfig> = new Map();

  async route(request: TaskRequest): Promise<Agent.Info> {
    // 1. 分析任务类型
    const taskType = await this.analyzeTask(request);

    // 2. 查找匹配的路由
    const route = this.findRoute(taskType);

    // 3. 选择 Agent
    const agent = await this.selectAgent(route);

    return agent;
  }

  private async analyzeTask(request: TaskRequest): Promise<TaskType> {
    // 使用 LLM 分析任务
    const analysis = await llm.complete({
      prompt: `
        分析以下任务的类型:
        ${request.content}

        任务类型:
        - code-edit: 代码编辑
        - code-explore: 代码探索
        - build: 构建和测试
        - plan: 规划和分析
        - general: 通用任务
      `,
      schema: TaskType
    });

    return analysis;
  }

  private findRoute(taskType: TaskType): RouteConfig {
    // 查找匹配的路由规则
    return this.routes.get(taskType) || this.routes.get('default');
  }
}
```

### 2. Task Decomposer (任务分解器)

将复杂任务分解为多个子任务。

```typescript
class TaskDecomposer {
  async decompose(
    task: Task,
    agent: Agent.Info
  ): Promise<SubTask[]> {
    // 1. 分析任务复杂度
    const complexity = await this.analyzeComplexity(task);

    // 2. 如果任务简单，直接返回
    if (complexity === 'simple') {
      return [{ ...task, id: generateId() }];
    }

    // 3. 分解任务
    const subtasks = await this.breakdown(task);

    // 4. 设置依赖关系
    await this.setDependencies(subtasks);

    return subtasks;
  }

  private async breakdown(task: Task): Promise<SubTask[]> {
    // 使用 LLM 分解任务
    const result = await llm.complete({
      prompt: `
        将以下任务分解为多个子任务:
        ${task.description}

        要求:
        1. 每个子任务应该独立可执行
        2. 明确子任务之间的依赖关系
        3. 指定每个子任务适合的 Agent 类型
      `,
      schema: z.array(SubTask)
    });

    return result;
  }

  private async setDependencies(subtasks: SubTask[]): Promise<void> {
    // 构建依赖图
    for (const task of subtasks) {
      task.dependencies = task.dependencies || [];
      for (const depId of task.dependencies) {
        const depTask = subtasks.find(t => t.id === depId);
        if (depTask) {
          depTask.blocks = depTask.blocks || [];
          depTask.blocks.push(task.id);
        }
      }
    }
  }
}
```

### 3. Agent Executor (Agent 执行器)

协调 Agent 执行任务。

```typescript
class AgentExecutor {
  async execute(
    task: Task,
    agent: Agent.Info
  ): Promise<TaskResult> {
    // 1. 创建会话
    const session = await this.createSession(agent, task);

    // 2. 发送任务
    await session.sendMessage(task.description);

    // 3. 处理响应流
    const result = await this.processResponse(session);

    // 4. 返回结果
    return result;
  }

  private async processResponse(
    session: Session
  ): Promise<TaskResult> {
    const messages: Message[] = [];
    const toolCalls: ToolCall[] = [];

    for await (const message of session.streamMessages()) {
      messages.push(message);

      if (message.type === 'tool-call') {
        // 处理工具调用
        const result = await this.executeToolCall(message);
        toolCalls.push(result);

        // 发送工具结果回会话
        await session.sendToolResult(result);
      }
    }

    return {
      messages,
      toolCalls,
      status: 'completed'
    };
  }
}
```

### 4. Result Aggregator (结果聚合器)

聚合多个 Agent 的执行结果。

```typescript
class ResultAggregator {
  async aggregate(results: TaskResult[]): Promise<FinalResult> {
    // 1. 合并所有消息
    const messages = results.flatMap(r => r.messages);

    // 2. 统计工具调用
    const toolCalls = results.flatMap(r => r.toolCalls);

    // 3. 生成摘要
    const summary = await this.generateSummary(results);

    // 4. 检查错误
    const errors = results.filter(r => r.status === 'error');

    return {
      messages,
      toolCalls,
      summary,
      errors,
      status: errors.length > 0 ? 'partial' : 'success'
    };
  }

  private async generateSummary(
    results: TaskResult[]
  ): Promise<string> {
    // 使用 LLM 生成摘要
    const summary = await llm.complete({
      prompt: `
        为以下任务结果生成摘要:
        ${JSON.stringify(results, null, 2)}

        摘要应该包含:
        1. 完成的主要工作
        2. 使用的关键工具
        3. 任何需要注意的问题
      `
    });

    return summary;
  }
}
```

## 执行流程

### 简单任务流程

```typescript
async function executeSimpleTask(request: TaskRequest): Promise<TaskResult> {
  // 1. 路由到合适的 Agent
  const agent = await taskRouter.route(request);

  // 2. 直接执行
  const result = await agentExecutor.execute({
    description: request.content,
    agent: agent
  });

  return result;
}
```

**示例**:
```
用户: "读取 package.json 文件"

流程:
1. Task Router → Build Agent (有读取权限)
2. Agent Executor → 执行 read 工具
3. 返回文件内容
```

### 复杂任务流程

```typescript
async function executeComplexTask(request: TaskRequest): Promise<TaskResult> {
  // 1. 路由到 Primary Agent
  const primaryAgent = await taskRouter.route(request);

  // 2. Primary Agent 分解任务
  const subtasks = await taskDecomposer.decompose(
    { description: request.content },
    primaryAgent
  );

  // 3. 创建执行图
  const executionGraph = buildExecutionGraph(subtasks);

  // 4. 按拓扑序执行
  const results: TaskResult[] = [];
  for (const task of executionGraph.topologicalOrder()) {
    // 等待依赖完成
    await waitForDependencies(task);

    // 选择 Agent
    const agent = await selectAgentForTask(task);

    // 执行任务
    const result = await agentExecutor.execute(task, agent);
    results.push(result);

    // 更新依赖状态
    markTaskCompleted(task);
  }

  // 5. 聚合结果
  const final = await resultAggregator.aggregate(results);

  return final;
}
```

**示例**:
```
用户: "重构用户认证模块"

流程:
1. Task Router → Primary Agent
2. Task Decomposer:
   - 子任务 A: Explore Agent - 查找认证相关文件
   - 子任务 B: General Agent - 重构认证逻辑
   - 子任务 C: General Agent - 更新测试
3. 执行:
   - Explore Agent 扫描代码库
   - General Agent 执行重构
   - General Agent 更新测试
4. Result Aggregator 合并结果
```

## 并行执行

### 依赖图构建

```typescript
class ExecutionGraph {
  private nodes: Map<string, TaskNode> = new Map();
  private edges: Map<string, string[]> = new Map();

  constructor(tasks: SubTask[]) {
    // 构建节点
    for (const task of tasks) {
      this.nodes.set(task.id, {
        task,
        status: 'pending'
      });
    }

    // 构建边（依赖关系）
    for (const task of tasks) {
      this.edges.set(task.id, task.dependencies || []);
    }
  }

  topologicalOrder(): SubTask[] {
    // Kahn 算法实现拓扑排序
    const order: SubTask[] = [];
    const inDegree = new Map<string, number>();

    // 计算入度
    for (const [id, deps] of this.edges) {
      inDegree.set(id, deps.length);
    }

    // 找到入度为 0 的节点
    const queue: string[] = [];
    for (const [id, degree] of inDegree) {
      if (degree === 0) {
        queue.push(id);
      }
    }

    // 处理队列
    while (queue.length > 0) {
      const id = queue.shift();
      const node = this.nodes.get(id);
      order.push(node.task);

      // 减少依赖节点的入度
      for (const [otherId, deps] of this.edges) {
        if (deps.includes(id)) {
          const newDegree = inDegree.get(otherId) - 1;
          inDegree.set(otherId, newDegree);

          if (newDegree === 0) {
            queue.push(otherId);
          }
        }
      }
    }

    return order;
  }

  findReadyTasks(): SubTask[] {
    return Array.from(this.nodes.values())
      .filter(node => node.status === 'pending')
      .filter(node => {
        const deps = this.edges.get(node.task.id) || [];
        return deps.every(depId => {
          const depNode = this.nodes.get(depId);
          return depNode?.status === 'completed';
        });
      })
      .map(node => node.task);
  }
}
```

### 并行调度器

```typescript
class ParallelScheduler {
  private maxParallel: number = 3;

  async schedule(
    graph: ExecutionGraph
  ): Promise<TaskResult[]> {
    const results: Map<string, TaskResult> = new Map();
    const running: Set<Promise<void>> = new Set();

    while (true) {
      // 检查是否所有任务完成
      const ready = graph.findReadyTasks();
      const hasRunning = running.size > 0;

      if (ready.length === 0 && !hasRunning) {
        break;
      }

      // 启动新的任务（受 maxParallel 限制）
      const slots = this.maxParallel - running.size;
      const toStart = ready.slice(0, slots);

      for (const task of toStart) {
        const promise = this.executeTask(task, graph, results);
        running.add(promise);

        promise.then(() => {
          running.delete(promise);
        });
      }

      // 等待至少一个任务完成
      if (running.size > 0) {
        await Promise.race(running);
      }
    }

    return Array.from(results.values());
  }

  private async executeTask(
    task: SubTask,
    graph: ExecutionGraph,
    results: Map<string, TaskResult>
  ): Promise<void> {
    // 标记为运行中
    graph.markRunning(task.id);

    try {
      // 选择 Agent
      const agent = await this.selectAgent(task);

      // 执行任务
      const result = await agentExecutor.execute(task, agent);
      results.set(task.id, result);

      // 标记为完成
      graph.markCompleted(task.id);

    } catch (error) {
      // 标记为失败
      graph.markFailed(task.id, error);
    }
  }
}
```

## 错误处理

### 错误恢复策略

```typescript
class ErrorHandler {
  async handle(error: TaskError, context: ExecutionContext): Promise<ErrorHandling> {
    switch (error.type) {
      case 'tool-execution-failed':
        return await this.handleToolError(error, context);

      case 'agent-timeout':
        return await this.handleTimeout(error, context);

      case 'permission-denied':
        return await this.handlePermissionError(error, context);

      default:
        return { action: 'fail', error };
    }
  }

  private async handleToolError(
    error: TaskError,
    context: ExecutionContext
  ): Promise<ErrorHandling> {
    // 尝试重试
    if (error.retryable && context.retryCount < 3) {
      return {
        action: 'retry',
        delay: Math.pow(2, context.retryCount) * 1000
      };
    }

    // 尝试使用备用工具
    const alternative = await this.findAlternativeTool(error.tool);
    if (alternative) {
      return {
        action: 'retry-with-alternative',
        alternativeTool: alternative
      };
    }

    // 放弃
    return { action: 'fail', error };
  }

  private async handleTimeout(
    error: TaskError,
    context: ExecutionContext
  ): Promise<ErrorHandling> {
    // 增加超时时间重试
    if (context.retryCount < 2) {
      return {
        action: 'retry',
        timeout: context.timeout * 2
      };
    }

    // 将任务分解为更小的子任务
    if (context.task.canBeSplit) {
      return {
        action: 'split',
        subtasks: await this.splitTask(context.task)
      };
    }

    return { action: 'fail', error };
  }
}
```

## 执行监控

### 进度跟踪

```typescript
class ExecutionMonitor {
  private progress: Map<string, TaskProgress> = new Map();

  async track(taskId: string): Promise<TaskProgress> {
    return this.progress.get(taskId);
  }

  update(taskId: string, update: ProgressUpdate): void {
    const current = this.progress.get(taskId) || {
      status: 'pending',
      steps: [],
      currentStep: 0
    };

    if (update.step) {
      current.steps.push(update.step);
      current.currentStep++;
    }

    if (update.status) {
      current.status = update.status;
    }

    if (update.message) {
      current.message = update.message;
    }

    this.progress.set(taskId, current);

    // 触发事件
    this.emit('progress', { taskId, progress: current });
  }

  getOverallProgress(): number {
    const all = Array.from(this.progress.values());
    if (all.length === 0) return 0;

    const completed = all.filter(p => p.status === 'completed').length;
    return (completed / all.length) * 100;
  }
}
```

### 性能指标

```typescript
class MetricsCollector {
  private metrics: Map<string, TaskMetrics> = new Map();

  record(taskId: string, event: MetricEvent): void {
    let metrics = this.metrics.get(taskId);

    if (!metrics) {
      metrics = {
        taskId,
        startTime: Date.now(),
        endTime: 0,
        toolCalls: 0,
        tokensUsed: 0,
        errors: 0
      };
      this.metrics.set(taskId, metrics);
    }

    switch (event.type) {
      case 'tool-call':
        metrics.toolCalls++;
        break;

      case 'token-consumption':
        metrics.tokensUsed += event.amount;
        break;

      case 'error':
        metrics.errors++;
        break;

      case 'complete':
        metrics.endTime = Date.now();
        break;
    }
  }

  getReport(taskId: string): MetricsReport {
    const metrics = this.metrics.get(taskId);

    return {
      taskId,
      duration: metrics.endTime - metrics.startTime,
      toolCalls: metrics.toolCalls,
      tokensUsed: metrics.tokensUsed,
      errors: metrics.errors,
      success: metrics.errors === 0
    };
  }
}
```

## 最佳实践

### 1. 合理分解任务

- 任务粒度适中（每个子任务 5-10 分钟完成）
- 明确定义依赖关系
- 避免过度分解导致通信开销

### 2. 并行执行优化

- 识别可并行的独立任务
- 控制并发数量（避免资源耗尽）
- 使用拓扑排序确保依赖顺序

### 3. 错误恢复

- 为关键操作设置重试机制
- 提供备用方案
- 记录详细的错误信息

### 4. 进度反馈

- 实时更新任务进度
- 提供有意义的进度消息
- 允许用户中断长时间运行的任务

## 后续文档

- [工具系统](./06-tools-system.md) - 了解任务执行中的工具调用
- [内置 Agent 详解](./08-built-in-agents.md) - 查看具体 Agent 的执行模式
