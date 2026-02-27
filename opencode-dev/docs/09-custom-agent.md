# 自定义 Agent 开发指南

## 概述

本文档指导如何创建和配置自定义 Agent，扩展 OpenCode 的功能。

## 创建方式

### 方式 1: 配置文件定义

最简单的方式，在配置文件中定义 Agent。

#### 配置文件位置

```
~/.config/opencode/config.yaml
# 或项目根目录
.opencode/config.yaml
```

#### 配置示例

```yaml
agents:
  # 前端开发专家
  frontend-expert:
    name: "frontend-expert"
    description: "前端开发专家，专注于 React 和 TypeScript"
    mode: "subagent"
    model: "anthropic:claude-3-5-sonnet"
    prompt: |
      你是一个前端开发专家，专注于 React 和 TypeScript。

      你的专长包括：
      - React Hooks 和组件设计
      - TypeScript 类型系统
      - CSS-in-JS (styled-components, emotion)
      - 状态管理 (Redux, Zustand)
      - 性能优化

      请遵循最佳实践：
      - 使用函数组件和 Hooks
      - 编写类型安全的代码
      - 组件应该是可复用的
      - 关注点分离
    permission:
      read:
        allow:
          - "src/**/*.{ts,tsx,css}"
          - "package.json"
      write:
        allow:
          - "src/**/*.{ts,tsx,css}"
      edit:
        allow:
          - "src/**/*.{ts,tsx,css}"
      bash:
        allow:
          - "npm *"
          - "yarn *"
          - "pnpm *"

  # 文档生成器
  doc-writer:
    name: "doc-writer"
    description: "自动生成和更新项目文档"
    mode: "subagent"
    prompt: |
      你是一个技术文档专家。

      你的任务：
      1. 为代码生成清晰的文档
      2. 更新 README 和 API 文档
      3. 编写使用示例
      4. 创建架构图说明

      文档风格：
      - 简洁明了
      - 包含代码示例
      - 使用 Markdown 格式
      - 添加适当的图表和链接
    permission:
      read:
        allow: ["**/*"]
      write:
        allow: ["**/*.md", "docs/**/*"]
      edit:
        allow: ["**/*.md"]
```

### 方式 2: 动态生成

使用 AI 自动生成 Agent 配置。

```typescript
import { Agent } from '@opencode/agent';

// 生成 Agent
const agent = await Agent.generate({
  description: `
    创建一个专门处理 Python 数据分析的 Agent。
    它应该能够：
    1. 分析 pandas 数据帧
    2. 创建数据可视化
    3. 编写数据处理脚本
  `,
  model: {
    providerID: "anthropic",
    modelID: "claude-3-5-sonnet"
  }
});

// 生成的 Agent 可能类似于：
// {
//   name: "python-data-analyst",
//   description: "Python 数据分析专家",
//   mode: "subagent",
//   permission: {
//     read: { allow: ["**/*.py", "data/**/*"] },
//     write: { allow: ["**/*.py"] },
//     bash: { allow: ["python *", "jupyter *"] }
//   },
//   prompt: "你是一个 Python 数据分析专家..."
// }
```

### 方式 3: 编程方式定义

在代码中直接定义 Agent。

```typescript
import { Agent } from '@opencode/agent';

const customAgent: Agent.Info = {
  name: 'api-tester',
  description: 'API 测试专家',
  mode: 'subagent',
  model: {
    modelID: 'claude-3-5-sonnet-20241022',
    providerID: 'anthropic'
  },
  temperature: 0.2,  // 降低随机性，提高一致性
  topP: 0.9,
  permission: {
    read: { allow: ['**/*.{ts,js,json}'] },
    write: { allow: ['tests/**/*.spec.{ts,js}'] },
    bash: {
      allow: ['npm test*', 'yarn test*', 'jest*'],
      ask: ['npm test -- --watch*']  // 监视模式需要确认
    }
  },
  prompt: `
    你是一个 API 测试专家。

    你的职责：
    1. 编写单元测试和集成测试
    2. 使用 Jest 或 Mocha 测试框架
    3. 确保测试覆盖率达到 80% 以上
    4. 编写清晰的测试描述

    测试原则：
    - 测试应该快速运行
    - 测试之间应该独立
    - 使用 mock 隔离外部依赖
    - 测试正常流程和边界情况
  `,
  options: {
    maxSteps: 50,  // 限制最大步骤数
    timeout: 300000  // 5 分钟超时
  }
};

// 注册 Agent
await agentRegistry.register(customAgent);
```

## Agent 配置详解

### 基本配置

```typescript
interface AgentConfig {
  // 必需字段
  name: string;              // 唯一标识符
  description: string;       // 人类可读的描述
  mode: 'primary' | 'subagent';  // 运行模式

  // 模型配置
  model?: {
    providerID: string;      // 模型提供商
    modelID: string;         // 模型 ID
  };

  // 行为配置
  temperature?: number;      // 0-1，控制随机性
  topP?: number;            // 0-1，核采样
  prompt?: string;          // 系统提示词

  // 权限配置
  permission?: PermissionRuleset;

  // 额外选项
  options?: {
    maxSteps?: number;       // 最大执行步骤
    timeout?: number;        // 超时时间 (ms)
    retryCount?: number;     // 重试次数
  };

  // UI 配置
  color?: string;           // 显示颜色
  hidden?: boolean;         // 是否隐藏
}
```

### 权限配置

```typescript
interface PermissionRuleset {
  // 文件操作
  read?: PermissionRule;
  write?: PermissionRule;
  edit?: PermissionRule;

  // 工具操作
  bash?: PermissionRule;
  grep?: PermissionRule;
  glob?: PermissionRule;
  web?: PermissionRule;

  // 每个规则可以包含：
  allow?: string[];  // 允许的模式
  deny?: string[];   // 拒绝的模式
  ask?: string[];    // 需要确认的模式
}

// 示例
const permission: PermissionRuleset = {
  read: {
    allow: ['src/**/*', 'tests/**/*'],
    deny: ['node_modules/**', '**/*.log']
  },
  write: {
    allow: ['src/**/*.ts', 'tests/**/*.ts'],
    deny: ['**/dist/**']
  },
  bash: {
    allow: ['npm test*', 'jest*'],
    ask: ['npm install*', 'npm uninstall*']
  }
};
```

### 提示词最佳实践

#### 好的提示词结构

```typescript
const goodPrompt = `
# 角色定义
你是一个 [领域] 专家，专注于 [具体专长]。

# 能力描述
你擅长：
1. [能力 1]
2. [能力 2]
3. [能力 3]

# 工作原则
遵循以下原则：
- [原则 1]
- [原则 2]
- [原则 3]

# 输出格式
你的输出应该：
- 使用 [格式]
- 包含 [内容]
- 遵循 [风格指南]

# 限制
- 不要 [限制 1]
- 避免 [限制 2]
- 总是 [限制 3]
`;
```

#### 示例：代码审查 Agent

```typescript
const codeReviewerPrompt = `
# 代码审查专家

你是一个资深的代码审查专家，具有以下专长：
- 深入理解多种编程语言和框架
- 识别代码异味和反模式
- 提出建设性的改进建议
- 关注代码可维护性和性能

## 审查重点

1. **代码质量**
   - 代码是否清晰易懂？
   - 是否有重复代码？
   - 变量和函数命名是否恰当？

2. **最佳实践**
   - 是否遵循语言/框架的最佳实践？
   - 设计模式是否正确使用？
   - 错误处理是否完善？

3. **性能**
   - 是否有性能瓶颈？
   - 是否有不必要的计算？
   - 内存使用是否合理？

4. **安全性**
   - 是否存在安全漏洞？
   - 用户输入是否验证？
   - 敏感数据是否保护？

## 输出格式

对于每段代码，提供：

\`\`\`
### 🔍 审查结果

**文件**: [文件路径]
**行号**: [行号范围]

**问题**: [问题描述]
**级别**: [严重/中等/轻微]
**建议**: [改进建议]

**修改前**:
\`\`\`language
[原代码]
\`\`\`

**修改后**:
\`\`\`language
[改进后的代码]
\`\`\`
\`\`\`

## 注意事项
- 只关注真正的问题
- 提供可操作的建议
- 保持语调建设性
- 承认好的代码实践
`;
```

## 常见用例

### 用例 1: 前端开发 Agent

```yaml
agents:
  react-expert:
    name: "react-expert"
    description: "React 开发专家"
    mode: "subagent"
    model: "anthropic:claude-3-5-sonnet"
    prompt: |
      你是一个 React 开发专家。

      技术栈：
      - React 18+
      - TypeScript
      - Tailwind CSS
      - React Query
      - Zustand

      代码风格：
      - 使用函数组件和 Hooks
      - TypeScript 严格模式
      - 组件拆分和复用
      - 性能优化（memo, useMemo, useCallback）

      组件设计原则：
      1. 单一职责
      2. Props 接口明确
      3. 可访问性 (a11y)
      4. 响应式设计
    permission:
      read:
        allow: ["src/**/*.{ts,tsx}", "package.json"]
      write:
        allow: ["src/**/*.{ts,tsx}"]
      bash:
        allow: ["npm run dev", "npm run build", "npm test*"]
```

### 用例 2: 后端开发 Agent

```yaml
agents:
  backend-dev:
    name: "backend-dev"
    description: "后端开发专家"
    mode: "subagent"
    model: "anthropic:claude-3-5-sonnet"
    prompt: |
      你是一个后端开发专家，专注于 Node.js 和 TypeScript。

      技术栈：
      - Node.js 20+
      - Express / Fastify
      - TypeScript
      - PostgreSQL / MongoDB
      - Redis

      开发原则：
      1. RESTful API 设计
      2. 输入验证和错误处理
      3. 安全性（认证、授权、数据验证）
      4. 性能优化（缓存、索引、查询优化）
      5. 测试（单元测试、集成测试）

      API 设计规范：
      - 使用语义化的 HTTP 方法
      - 统一的响应格式
      - 适当的 HTTP 状态码
      - API 版本控制
    permission:
      read:
        allow: ["server/**/*", "api/**/*", "**/*.{ts,js}"]
      write:
        allow: ["server/**/*", "api/**/*"]
      bash:
        allow: ["npm run *", "node *", "ts-node *"]
```

### 用例 3: 文档生成 Agent

```yaml
agents:
  doc-generator:
    name: "doc-generator"
    description: "自动生成项目文档"
    mode: "subagent"
    model: "anthropic:claude-3-5-haiku"  # 使用快速模型
    prompt: |
      你是一个技术文档专家。

      任务：
      1. 为代码生成 API 文档
      2. 创建使用示例
      3. 编写架构说明
      4. 更新 README

      文档格式：
      - Markdown
      - 包含代码示例
      - 添加适当的图表
      - 提供清晰的说明

      注意事项：
      - 文档应该简洁明了
      - 使用一致的格式
      - 包含必要的链接
      - 保持更新
    permission:
      read:
        allow: ["**/*"]
      write:
        allow: ["**/*.md", "docs/**/*"]
      edit:
        allow: ["**/*.md"]
```

### 用例 4: 测试 Agent

```yaml
agents:
  test-writer:
    name: "test-writer"
    description: "测试代码编写专家"
    mode: "subagent"
    model: "anthropic:claude-3-5-sonnet"
    prompt: |
      你是一个测试专家，专注于编写高质量的测试。

      测试框架：
      - Jest / Vitest
      - Testing Library
      - Supertest (API 测试)

      测试原则：
      1. 测试应该快速且可靠
      2. 遵循 AAA 模式（Arrange, Act, Assert）
      3. 测试行为而非实现
      4. 使用描述性的测试名称
      5. 保持测试简单

      测试覆盖：
      - 正常流程
      - 边界情况
      - 错误处理
      - 边缘条件

      示例格式：
      \`\`\`typescript
      describe('ComponentName', () => {
        describe('when [条件]', () => {
          it('should [期望行为]', () => {
            // Arrange
            const input = ...;

            // Act
            const result = ...;

            // Assert
            expect(result).toBe(...);
          });
        });
      });
      \`\`\`
    permission:
      read:
        allow: ["**/*.{ts,tsx,js,jsx}"]
      write:
        allow: ["**/*.spec.{ts,tsx,js,jsx}", "**/*.test.{ts,tsx,js,jsx}"]
      bash:
        allow: ["npm test*", "jest*", "vitest*"]
```

## 测试自定义 Agent

### 本地测试

```typescript
import { AgentRegistry, Session } from '@opencode/core';

// 1. 注册自定义 Agent
const customAgent = {
  name: 'my-agent',
  description: '我的自定义 Agent',
  mode: 'subagent',
  // ... 配置
};

await agentRegistry.register(customAgent);

// 2. 创建测试会话
const session = await Session.create({
  agent: 'my-agent'
});

// 3. 发送测试消息
const response = await session.sendMessage('测试任务');

console.log(response);
```

### 单元测试

```typescript
import { describe, it, expect } from 'vitest';
import { Agent } from '@opencode/agent';

describe('Custom Agent', () => {
  it('should have correct permissions', () => {
    const agent = loadAgent('my-agent');

    expect(agent.permission.read.allow).toContain('src/**/*');
    expect(agent.permission.bash.deny).toContain('rm *');
  });

  it('should follow prompt guidelines', async () => {
    const session = await createSession('my-agent');
    const response = await session.sendMessage('创建一个组件');

    expect(response.messages).not.toBeEmpty();
    expect(response.toolCalls).toContainEqual(
      expect.objectContaining({ name: 'write' })
    );
  });
});
```

## 调试技巧

### 1. 启用详细日志

```typescript
const session = await Session.create({
  agent: 'my-agent',
  debug: true,  // 启用调试模式
  verbose: true
});
```

### 2. 监控工具调用

```typescript
session.on('tool-call', (call) => {
  console.log(`工具调用: ${call.name}`, call.input);
});

session.on('tool-result', (result) => {
  console.log(`工具结果:`, result.output);
});
```

### 3. 检查权限决策

```typescript
import { PermissionChecker } from '@opencode/permission';

const checker = new PermissionChecker(myAgent.permission);

const result = await checker.check('read:src/file.ts');
console.log('权限结果:', result);
// { allowed: true, reason: '...' }
```

## 部署和分享

### 导出 Agent 配置

```bash
opencode agent export my-agent > my-agent.yaml
```

### 导入 Agent 配置

```bash
opencode agent import my-agent.yaml
```

### 分享 Agent

```bash
# 发布到 npm
npm publish my-opencode-agent

# 其他用户可以安装
npm install my-opencode-agent
```

## 常见问题

### Q: 如何限制 Agent 的资源使用？

```yaml
agents:
  my-agent:
    options:
      maxSteps: 100        # 限制最大步骤数
      timeout: 300000      # 5 分钟超时
      maxTokens: 100000    # 限制 token 使用
      maxRetries: 3        # 限制重试次数
```

### Q: 如何让 Agent 使用自定义工具？

```typescript
import { ToolRegistry } from '@opencode/tool';

// 1. 定义自定义工具
const myTool = {
  name: 'my-custom-tool',
  description: '我的自定义工具',
  execute: async (input) => {
    // 实现逻辑
  }
};

// 2. 注册工具
await ToolRegistry.register(myTool);

// 3. Agent 配置中添加权限
const myAgent = {
  name: 'my-agent',
  permission: {
    'my-custom-tool': { allow: ['**'] }
  }
};
```

### Q: 如何更新现有 Agent？

```yaml
agents:
  existing-agent:
    # 新配置会覆盖旧配置
    prompt: "新的提示词"
    permission:
      read:
        allow: ["**/*.ts"]  # 更新权限
```

## 最佳实践总结

1. **明确用途**: Agent 应该有明确的功能定位
2. **最小权限**: 只授予必要的权限
3. **清晰提示**: 提供详细的角色和任务说明
4. **合理模型**: 根据任务复杂度选择合适的模型
5. **测试验证**: 充分测试 Agent 的行为
6. **版本控制**: 将 Agent 配置纳入版本控制
7. **文档完善**: 为自定义 Agent 编写使用文档

## 相关资源

- [权限管理系统](./07-permission-system.md)
- [工具系统](./06-tools-system.md)
- [内置 Agent 详解](./08-built-in-agents.md)
