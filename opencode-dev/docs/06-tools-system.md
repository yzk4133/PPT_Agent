# 工具系统

## 概述

工具系统是 OpenCode 架构中 Agent 与外部世界交互的唯一途径。所有文件操作、命令执行、代码搜索等功能都通过标准化的工具接口实现。

## 核心架构

```
┌─────────────────────────────────────────────────────────┐
│                      Agent                               │
│                  (工具调用者)                             │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  Tool Registry                           │
│            (工具注册表和管理器)                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │  Read   │ │  Edit   │ │  Bash   │ │  Grep   │       │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘       │
└───────┼───────────┼───────────┼───────────┼─────────────┘
        │           │           │           │
        ▼           ▼           ▼           ▼
┌─────────────────────────────────────────────────────────┐
│                  Tool Executor                           │
│              (工具执行引擎)                                │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│          文件系统 / 操作系统 / 网络 / LSP                 │
└─────────────────────────────────────────────────────────┘
```

## 工具定义

### 工具接口

```typescript
interface Tool {
  // 基本信息
  name: string;                    // 工具名称
  description: string;             // 工具描述
  category: ToolCategory;          // 工具分类

  // 输入输出定义
  inputSchema: z.ZodTypeAny;       // 输入参数 schema
  outputSchema: z.ZodTypeAny;      // 输出结果 schema

  // 执行逻辑
  execute: (input: any) => Promise<any>;

  // 元数据
  metadata: {
    dangerous: boolean;            // 是否危险操作
    timeout: number;               // 超时时间 (ms)
    retryable: boolean;            // 是否可重试
    experimental: boolean;         // 是否实验性功能
  };

  // 权限要求
  permission?: PermissionPattern;
}
```

### 工具分类

```typescript
enum ToolCategory {
  // 文件操作
  File = 'file',

  // 搜索
  Search = 'search',

  // 系统命令
  System = 'system',

  // 代码分析
  Code = 'code',

  // Web 操作
  Web = 'web',

  // 任务管理
  Task = 'task',

  // 版本控制
  VersionControl = 'version-control',

  // LSP (Language Server Protocol)
  LSP = 'lsp'
}
```

## 工具注册表

### 注册机制

```typescript
// packages/opencode/src/tool/registry.ts
export class ToolRegistry {
  private tools: Map<string, Tool> = new Map();
  private aliases: Map<string, string> = new Map();

  // 注册工具
  register(tool: Tool): void {
    // 验证工具定义
    this.validate(tool);

    // 注册主名称
    this.tools.set(tool.name, tool);

    // 注册别名
    for (const alias of tool.metadata.aliases || []) {
      this.aliases.set(alias, tool.name);
    }

    // 触发事件
    this.emit('tool:registered', { tool });
  }

  // 获取工具
  get(name: string): Tool | undefined {
    // 解析别名
    const resolvedName = this.aliases.get(name) || name;
    return this.tools.get(resolvedName);
  }

  // 列出所有工具
  list(): Tool[] {
    return Array.from(this.tools.values());
  }

  // 根据权限过滤工具
  filter(agent: Agent.Info): Tool[] {
    const all = this.list();

    return all.filter(tool => {
      // 检查权限
      const allowed = this.checkPermission(tool, agent.permission);

      // 检查模型兼容性
      const compatible = this.checkCompatibility(tool, agent.model);

      return allowed && compatible;
    });
  }

  private checkPermission(
    tool: Tool,
    permission: Ruleset
  ): boolean {
    if (!tool.permission) return true;

    const result = evaluate(
      tool.permission.pattern,
      permission
    );

    return result !== 'deny';
  }

  private checkCompatibility(
    tool: Tool,
    model: ModelConfig
  ): boolean {
    // 检查工具是否支持该模型
    if (tool.metadata.supportedModels) {
      return tool.metadata.supportedModels.includes(model.modelID);
    }

    return true;
  }
}
```

### 全局注册表实例

```typescript
export const toolRegistry = new ToolRegistry();

// 注册内置工具
toolRegistry.register(readTool);
toolRegistry.register(editTool);
toolRegistry.register(writeTool);
toolRegistry.register(globTool);
toolRegistry.register(grepTool);
toolRegistry.register(bashTool);
// ... 更多工具
```

## 内置工具

### 1. 文件操作工具

#### Read 工具

```typescript
const readTool: Tool = {
  name: 'read',
  description: '读取文件内容',
  category: ToolCategory.File,

  inputSchema: z.object({
    file_path: z.string(),  // 文件的绝对路径
    offset: z.number().optional(),  // 起始行号
    limit: z.number().optional()    // 读取行数
  }),

  outputSchema: z.string(),

  async execute(input) {
    const content = await fs.readFile(input.file_path, 'utf-8');
    const lines = content.split('\n');

    if (input.offset || input.limit) {
      const start = input.offset || 0;
      const end = input.limit ? start + input.limit : lines.length;
      return lines.slice(start, end).join('\n');
    }

    return content;
  },

  metadata: {
    dangerous: false,
    timeout: 5000,
    retryable: true,
    experimental: false
  },

  permission: {
    pattern: 'read:{{file_path}}',
    scope: 'file'
  }
};
```

#### Edit 工具

```typescript
const editTool: Tool = {
  name: 'edit',
  description: '精确替换文件中的文本',
  category: ToolCategory.File,

  inputSchema: z.object({
    file_path: z.string(),
    old_string: z.string(),  // 要替换的文本
    new_string: z.string(),  // 替换后的文本
    replace_all: z.boolean().optional()  // 是否替换所有匹配
  }),

  outputSchema: z.object({
    success: z.boolean(),
    changes: z.number()
  }),

  async execute(input) {
    const content = await fs.readFile(input.file_path, 'utf-8');

    let newContent;
    let changes;

    if (input.replace_all) {
      const regex = new RegExp(
        escapeRegExp(input.old_string),
        'g'
      );
      const matches = content.match(regex);
      changes = matches ? matches.length : 0;
      newContent = content.replace(regex, input.new_string);
    } else {
      if (!content.includes(input.old_string)) {
        throw new Error('old_string not found in file');
      }
      changes = 1;
      newContent = content.replace(input.old_string, input.new_string);
    }

    await fs.writeFile(input.file_path, newContent, 'utf-8');

    return { success: true, changes };
  },

  metadata: {
    dangerous: true,  // 修改文件
    timeout: 10000,
    retryable: false,
    experimental: false
  },

  permission: {
    pattern: 'edit:{{file_path}}',
    scope: 'file'
  }
};
```

#### Write 工具

```typescript
const writeTool: Tool = {
  name: 'write',
  description: '写入文件内容（覆盖现有文件）',
  category: ToolCategory.File,

  inputSchema: z.object({
    file_path: z.string(),
    content: z.string()
  }),

  outputSchema: z.object({
    success: z.boolean(),
    bytes_written: z.number()
  }),

  async execute(input) {
    await fs.writeFile(input.file_path, input.content, 'utf-8');

    return {
      success: true,
      bytes_written: Buffer.byteLength(input.content, 'utf-8')
    };
  },

  metadata: {
    dangerous: true,
    timeout: 10000,
    retryable: false,
    experimental: false
  },

  permission: {
    pattern: 'write:{{file_path}}',
    scope: 'file'
  }
};
```

### 2. 搜索工具

#### Glob 工具

```typescript
const globTool: Tool = {
  name: 'glob',
  description: '使用 glob 模式查找文件',
  category: ToolCategory.Search,

  inputSchema: z.object({
    pattern: z.string(),  // glob 模式，如 "**/*.ts"
    path: z.string().optional()  // 搜索路径（可选）
  }),

  outputSchema: z.array(z.string()),  // 匹配的文件路径列表

  async execute(input) {
    const { glob } = await import('fast-glob');

    const files = await glob(input.pattern, {
      cwd: input.path || process.cwd(),
      absolute: true
    });

    return files;
  },

  metadata: {
    dangerous: false,
    timeout: 30000,
    retryable: true,
    experimental: false
  },

  permission: {
    pattern: 'read:*',
    scope: 'file'
  }
};
```

#### Grep 工具

```typescript
const grepTool: Tool = {
  name: 'grep',
  description: '在文件中搜索内容',
  category: ToolCategory.Search,

  inputSchema: z.object({
    pattern: z.string(),  // 正则表达式
    path: z.string().optional(),  // 搜索路径
    glob: z.string().optional(),  // 文件过滤
    output_mode: z.enum(['content', 'files_with_matches', 'count']).optional(),
    '-C': z.number().optional(),  // 上下文行数
    '-n': z.boolean().optional(),  // 显示行号
    '-i': z.boolean().optional()  // 忽略大小写
  }),

  outputSchema: z.union([
    z.array(z.object({
      file: z.string(),
      line: z.number(),
      content: z.string()
    })),
    z.array(z.string()),  // files_with_matches
    z.array(z.object({
      file: z.string(),
      count: z.number()
    }))  // count
  ]),

  async execute(input) {
    const { parse } = await import('grep-rx');

    const options = {
      cwd: input.path || process.cwd(),
      glob: input.glob,
      context: input['-C'],
      lineNumbers: input['-n'],
      caseInsensitive: input['-i']
    };

    const results = await parse(input.pattern, options);

    // 根据输出模式转换结果
    switch (input.output_mode) {
      case 'files_with_matches':
        return [...new Set(results.map(r => r.file))];

      case 'count':
        const counts = new Map();
        for (const r of results) {
          counts.set(r.file, (counts.get(r.file) || 0) + 1);
        }
        return Array.from(counts.entries()).map(([file, count]) => ({ file, count }));

      default:
        return results;
    }
  },

  metadata: {
    dangerous: false,
    timeout: 30000,
    retryable: true,
    experimental: false
  }
};
```

### 3. 系统工具

#### Bash 工具

```typescript
const bashTool: Tool = {
  name: 'bash',
  description: '执行 shell 命令',
  category: ToolCategory.System,

  inputSchema: z.object({
    command: z.string(),
    timeout: z.number().optional(),  // 自定义超时
    run_in_background: z.boolean().optional()
  }),

  outputSchema: z.object({
    stdout: z.string(),
    stderr: z.string(),
    exit_code: z.number()
  }),

  async execute(input) {
    const { spawn } = await import('child_process');

    return new Promise((resolve, reject) => {
      const [cmd, ...args] = parseCommand(input.command);

      const process = spawn(cmd, args, {
        shell: true,
        cwd: process.cwd()
      });

      let stdout = '';
      let stderr = '';

      process.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      process.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      const timeout = input.timeout || 120000;
      const timer = setTimeout(() => {
        process.kill();
        reject(new Error('Command timeout'));
      }, timeout);

      process.on('close', (code) => {
        clearTimeout(timer);
        resolve({
          stdout,
          stderr,
          exit_code: code
        });
      });
    });
  },

  metadata: {
    dangerous: true,  // 执行任意命令
    timeout: 120000,
    retryable: false,
    experimental: false
  },

  permission: {
    pattern: 'bash:{{command}}',
    scope: 'command'
  }
};
```

### 4. 代码分析工具

#### LSP 工具

```typescript
const lspTool: Tool = {
  name: 'lsp',
  description: '使用 Language Server Protocol 进行代码分析',
  category: ToolCategory.LSP,

  inputSchema: z.object({
    operation: z.enum([
      'goToDefinition',
      'findReferences',
      'hover',
      'documentSymbol',
      'workspaceSymbol',
      'goToImplementation',
      'prepareCallHierarchy',
      'incomingCalls',
      'outgoingCalls'
    ]),
    filePath: z.string(),
    line: z.number(),
    character: z.number()
  }),

  outputSchema: z.any(),  // 输出取决于操作类型

  async execute(input) {
    const lsp = await getLSPServer(input.filePath);

    switch (input.operation) {
      case 'goToDefinition':
        return lsp.goToDefinition({
          textDocument: { uri: input.filePath },
          position: { line: input.line, character: input.character }
        });

      case 'findReferences':
        return lsp.findReferences({
          textDocument: { uri: input.filePath },
          position: { line: input.line, character: input.character }
        });

      case 'hover':
        return lsp.hover({
          textDocument: { uri: input.filePath },
          position: { line: input.line, character: input.character }
        });

      // ... 其他操作
    }
  },

  metadata: {
    dangerous: false,
    timeout: 10000,
    retryable: true,
    experimental: false
  }
};
```

## 工具执行

### 执行流程

```typescript
class ToolExecutor {
  private registry: ToolRegistry;
  private permissionChecker: PermissionChecker;

  async execute(
    agent: Agent.Info,
    call: ToolCall
  ): Promise<ToolResult> {
    // 1. 获取工具定义
    const tool = this.registry.get(call.name);
    if (!tool) {
      throw new Error(`Unknown tool: ${call.name}`);
    }

    // 2. 验证输入
    const input = this.validateInput(tool, call.input);

    // 3. 检查权限
    await this.checkPermission(agent, tool, input);

    // 4. 执行工具
    const result = await this.runTool(tool, input);

    // 5. 验证输出
    return this.validateOutput(tool, result);
  }

  private validateInput(tool: Tool, input: any): any {
    try {
      return tool.inputSchema.parse(input);
    } catch (error) {
      throw new ToolValidationError({
        tool: tool.name,
        input,
        errors: error.errors
      });
    }
  }

  private async checkPermission(
    agent: Agent.Info,
    tool: Tool,
    input: any
  ): Promise<void> {
    const permission = agent.permission;

    // 构建权限模式
    const pattern = this.buildPermissionPattern(tool, input);

    // 评估权限
    const result = evaluate(pattern, permission);

    if (result === 'deny') {
      throw new ToolPermissionDenied({
        tool: tool.name,
        input,
        reason: 'Permission denied'
      });
    }

    if (result === 'ask') {
      // 请求用户确认
      const allowed = await this.requestConfirmation(tool, input);
      if (!allowed) {
        throw new ToolPermissionDenied({
          tool: tool.name,
          input,
          reason: 'User denied'
        });
      }
    }
  }

  private async runTool(tool: Tool, input: any): Promise<any> {
    // 设置超时
    const timeout = tool.metadata.timeout || 30000;

    return Promise.race([
      tool.execute(input),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Tool timeout')), timeout)
      )
    ]);
  }

  private validateOutput(tool: Tool, output: any): any {
    try {
      return tool.outputSchema.parse(output);
    } catch (error) {
      throw new ToolValidationError({
        tool: tool.name,
        output,
        errors: error.errors
      });
    }
  }
}
```

## 工具组合

### Macro 工具

```typescript
// 定义工具组合（宏）
const macroTool: Tool = {
  name: 'batch-edit',
  description: '批量编辑多个文件',
  category: ToolCategory.File,

  inputSchema: z.object({
    operations: z.array(z.object({
      file_path: z.string(),
      old_string: z.string(),
      new_string: z.string()
    }))
  }),

  outputSchema: z.array(z.object({
    file_path: z.string(),
    success: z.boolean(),
    changes: z.number()
  })),

  async execute(input) {
    const results = [];

    for (const op of input.operations) {
      try {
        const result = await editTool.execute(op);
        results.push({
          file_path: op.file_path,
          success: true,
          changes: result.changes
        });
      } catch (error) {
        results.push({
          file_path: op.file_path,
          success: false,
          changes: 0,
          error: error.message
        });
      }
    }

    return results;
  },

  metadata: {
    dangerous: true,
    timeout: 60000,
    retryable: false,
    experimental: false
  }
};
```

## 工具监控

### 使用统计

```typescript
class ToolMonitor {
  private stats: Map<string, ToolStats> = new Map();

  record(call: ToolCall, result: ToolResult): void {
    let stats = this.stats.get(call.name);

    if (!stats) {
      stats = {
        tool: call.name,
        calls: 0,
        successes: 0,
        failures: 0,
        totalTime: 0,
        averageTime: 0
      };
      this.stats.set(call.name, stats);
    }

    stats.calls++;
    stats.totalTime += result.duration;

    if (result.success) {
      stats.successes++;
    } else {
      stats.failures++;
    }

    stats.averageTime = stats.totalTime / stats.calls;
  }

  getStats(toolName: string): ToolStats | undefined {
    return this.stats.get(toolName);
  }

  getAllStats(): ToolStats[] {
    return Array.from(this.stats.values());
  }
}
```

## 最佳实践

### 1. 工具设计原则

- **单一职责**: 每个工具只做一件事
- **明确接口**: 清晰的输入输出定义
- **错误处理**: 提供有意义的错误信息
- **幂等性**: 相同输入产生相同输出

### 2. 权限控制

- 危险操作需要用户确认
- 细粒度的权限控制
- 审计日志记录所有操作

### 3. 性能优化

- 缓存文件读取结果
- 批量操作减少开销
- 合理设置超时时间

### 4. 扩展性

- 通过注册表添加新工具
- 支持工具别名
- 工具组合和宏定义

## 后续文档

- [权限管理系统](./07-permission-system.md) - 了解工具权限控制
- [自定义 Agent 开发](./09-custom-agent.md) - 学习如何为 Agent 添加自定义工具
