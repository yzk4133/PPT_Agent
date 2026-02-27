# 内置 Agent 详解

## 概述

OpenCode 提供了多个内置 Agent，每个都针对特定任务优化。本文档详细说明每个内置 Agent 的用途、能力、权限和使用场景。

## Agent 列表

| Agent 名称 | 模式 | 主要用途 | 模型 |
|-----------|------|---------|------|
| `build` | primary | 通用开发，完整工具访问 | Sonnet |
| `plan` | primary | 规划和分析，受限权限 | Sonnet |
| `general-purpose` | subagent | 复杂任务，多步骤执行 | Sonnet |
| `explore` | subagent | 代码探索，只读操作 | Haiku |

## Build Agent

### 基本信息

```typescript
{
  name: "build",
  description: "默认 Agent，具有所有工具权限",
  mode: "primary",
  model: {
    modelID: "claude-3-5-sonnet-20241022",
    providerID: "anthropic"
  }
}
```

### 权限配置

```typescript
const buildPermission = {
  read: { allow: ["**/*"] },
  write: { allow: ["**/*"] },
  edit: { allow: ["**/*"] },
  bash: { allow: ["**"] },
  grep: { allow: ["**/*"] },
  glob: { allow: ["**/*"] },
  web: { allow: ["**"] },
  lsp: { allow: ["**/*"] }
}
```

### 可用工具

- ✅ Read - 读取文件
- ✅ Edit - 编辑文件
- ✅ Write - 写入文件
- ✅ Glob - 文件查找
- ✅ Grep - 内容搜索
- ✅ Bash - 命令执行
- ✅ LSP - 代码分析
- ✅ Task - 任务管理
- ✅ WebFetch - 网络请求
- ✅ WebSearch - 网络搜索

### 使用场景

1. **日常开发**
   ```
   用户: "在 UserService 中添加一个获取用户的方法"
   ```

2. **构建和测试**
   ```
   用户: "运行测试并修复失败的测试"
   ```

3. **代码重构**
   ```
   用户: "重构这个组件，提取重复的逻辑"
   ```

4. **Git 操作**
   ```
   用户: "创建一个新分支并提交更改"
   ```

### 示例对话

```
用户: 我需要在 src/utils/date.ts 中添加一个格式化日期的函数

Build Agent:
[思考] 用户需要在日期工具文件中添加新函数

[行动] 1. 读取文件
>>> read src/utils/date.ts

[行动] 2. 编写函数
>>> edit src/utils/date.ts
old_string: |
  export const getCurrentDate = (): Date => {
    return new Date();
  };

new_string: |
  export const getCurrentDate = (): Date => {
    return new Date();
  };

  export const formatDate = (
    date: Date,
    format: string = 'YYYY-MM-DD'
  ): string => {
    // 格式化逻辑
    // ...
    return formatted;
  };

[完成] 已添加 formatDate 函数到 src/utils/date.ts
```

## Plan Agent

### 基本信息

```typescript
{
  name: "plan",
  description: "受限 Agent，用于规划和分析",
  mode: "primary",
  model: {
    modelID: "claude-3-5-sonnet-20241022",
    providerID: "anthropic"
  }
}
```

### 权限配置

```typescript
const planPermission = {
  read: { allow: ["**/*"] },
  write: { deny: ["**"] },
  edit: { deny: ["**"] },
  bash: { deny: ["**"] },
  grep: { allow: ["**/*"] },
  glob: { allow: ["**/*"] }
}
```

### 可用工具

- ✅ Read - 读取文件
- ✅ Glob - 文件查找
- ✅ Grep - 内容搜索
- ❌ Edit - 禁止编辑
- ❌ Write - 禁止写入
- ❌ Bash - 禁止命令执行

### 使用场景

1. **代码审查**
   ```
   用户: "审查这个 PR 的代码质量"
   ```

2. **架构分析**
   ```
   用户: "分析这个项目的架构设计"
   ```

3. **任务规划**
   ```
   用户: "规划如何实现这个新功能"
   ```

4. **依赖分析**
   ```
   用户: "分析模块之间的依赖关系"
   ```

### 示例对话

```
用户: 帮我规划如何实现用户认证功能

Plan Agent:
[分析] 让我先探索现有的代码结构

[行动] 1. 查找认证相关文件
>>> glob **/*auth*

找到: src/auth/login.ts, src/auth/register.ts

[行动] 2. 查找用户模型
>>> grep -r "interface User" src/

找到: src/models/user.ts

[行动] 3. 读取现有认证实现
>>> read src/auth/login.ts

[规划] 基于代码分析，这是实现用户认证的建议计划：

## 认证功能实现计划

### 1. 后端实现
- [ ] 在 src/auth/ 下创建 JWT token 验证中间件
- [ ] 实现密码哈希和验证函数
- [ ] 创建 /api/auth/login 和 /api/auth/register 端点
- [ ] 添加 token 刷新机制

### 2. 前端实现
- [ ] 创建登录页面组件
- [ ] 创建注册页面组件
- [ ] 实现认证上下文 (AuthContext)
- [ ] 添加路由守卫保护私有页面

### 3. 安全考虑
- [ ] 实现 HTTPS only cookies
- [ ] 添加 CSRF 保护
- [ ] 实现速率限制
- [ ] 密码强度验证

### 4. 测试
- [ ] 单元测试：认证逻辑
- [ ] 集成测试：登录/注册流程
- [ ] 安全测试：SQL 注入、XSS 等

注意：Plan Agent 只能提供规划，实际实现需要切换到 Build Agent。
```

## General Purpose Agent

### 基本信息

```typescript
{
  name: "general-purpose",
  description: "通用目的 Agent，用于复杂任务和多步执行",
  mode: "subagent",
  model: {
    modelID: "claude-3-5-sonnet-20241022",
    providerID: "anthropic"
  }
}
```

### 权限配置

```typescript
const generalPermission = {
  read: { allow: ["**/*"] },
  write: { allow: ["**/*"] },
  edit: { allow: ["**/*"] },
  bash: { allow: ["**"] },
  grep: { allow: ["**/*"] },
  glob: { allow: ["**/*"] }
}
```

### 特殊限制

- ❌ 不能使用 Todo 工具（避免与主 Agent 的任务管理冲突）

### 使用场景

1. **并行任务**
   ```
   用户: "同时更新文档和测试"
   ```

2. **独立任务**
   ```
   用户: "创建一个独立的脚本来处理数据迁移"
   ```

3. **长时间运行的任务**
   ```
   用户: "批量处理这些文件"
   ```

### 示例对话

```
用户: 更新所有组件的 README 文件

Build Agent:
[分析] 这是一个可以并行的任务，我将调用 General Agent

[行动] 创建 General Agent 子会话
>>> @general-purpose 批量更新组件 README

General Agent (子会话):
[思考] 需要找到所有组件并更新它们的 README

[步骤 1] 查找所有组件
>>> glob **/components/**/README.md

找到 15 个组件 README

[步骤 2] 批量更新
for component in components:
  - 读取现有 README
  - 添加新的 API 文档部分
  - 更新使用示例
  - 写入更新后的内容

[完成] 已更新 15 个组件的 README 文件：
- src/components/Button/README.md ✓
- src/components/Input/README.md ✓
- src/components/Modal/README.md ✓
...
```

## Explore Agent

### 基本信息

```typescript
{
  name: "explore",
  description: "快速探索代码库，只读权限",
  mode: "subagent",
  model: {
    modelID: "claude-3-5-haiku-20241022",  // 使用快速模型
    providerID: "anthropic"
  }
}
```

### 权限配置

```typescript
const explorePermission = {
  read: { allow: ["**/*"] },
  write: { deny: ["**"] },
  edit: { deny: ["**"] },
  bash: { deny: ["**"] },
  grep: { allow: ["**/*"] },
  glob: { allow: ["**/*"] }
}
```

### 特点

- **快速**: 使用 Haiku 模型，响应速度快
- **只读**: 完全禁止修改操作
- **专注**: 专门优化代码探索任务

### 使用场景

1. **代码导航**
   ```
   用户: "找到所有使用 useState 的组件"
   ```

2. **依赖查找**
   ```
   用户: "这个函数在哪些地方被调用？"
   ```

3. **代码理解**
   ```
   用户: "解释这个模块是如何工作的"
   ```

4. **文件搜索**
   ```
   用户: "找到所有测试文件"
   ```

### 示例对话

```
用户: 这个项目中有哪些认证相关的代码？

Build Agent:
[行动] 调用 Explore Agent 进行代码探索
>>> @explore 查找认证相关代码

Explore Agent (子会话):
[搜索] 1. 查找包含 "auth" 的文件
>>> glob **/*auth*

找到:
- src/auth/login.ts
- src/auth/register.ts
- src/auth/middleware.ts
- src/auth/types.ts

[搜索] 2. 搜索认证相关函数
>>> grep "function.*auth" src/
找到:
- src/auth/login.ts: authenticateUser
- src/auth/middleware.ts: requireAuth
- src/utils/token.ts: verifyToken

[读取] 3. 读取关键文件
>>> read src/auth/login.ts

[分析] 项目中的认证相关代码包括：

## 认证系统结构

### 核心文件
1. **src/auth/login.ts** - 用户登录逻辑
   - authenticateUser(): 验证用户凭据
   - generateToken(): 生成 JWT token

2. **src/auth/register.ts** - 用户注册
   - createUser(): 创建新用户
   - validateEmail(): 邮箱验证

3. **src/auth/middleware.ts** - 认证中间件
   - requireAuth(): 路由保护

4. **src/utils/token.ts** - Token 工具
   - verifyToken(): 验证 JWT

### 架构
项目使用 JWT 认证，token 存储在 localStorage 中。
所有需要认证的路由都通过 requireAuth 中间件保护。
```

## Agent 选择指南

### 决策树

```
需要执行操作？
    │
    ├─ 是 → 需要修改文件或执行命令？
    │       │
    │       ├─ 是 → 使用 Build Agent
    │       │
    │       └─ 否 → 使用 Explore Agent（只读）
    │
    └─ 否 → 只需要分析和规划？
            │
            └─ 是 → 使用 Plan Agent
```

### 场景映射

| 场景 | 推荐Agent | 原因 |
|-----|----------|------|
| 编写新功能 | Build | 需要完整工具访问 |
| 修复 Bug | Build | 需要编辑和测试 |
| 代码审查 | Plan | 只读分析 |
| 架构设计 | Plan | 规划为主 |
| 查找代码 | Explore | 快速只读搜索 |
| 批量操作 | General | 独立会话执行 |
| 文档生成 | General | 长时间任务 |

## Agent 协作示例

### 复杂任务的多 Agent 协作

```
用户: 重构用户认证模块，提高安全性

Build Agent:
[分析] 这是一个复杂任务，需要多个阶段

阶段 1: 规划和分析
>>> @plan 分析现有认证模块的安全问题

Plan Agent:
[读取] 读取认证相关代码
[分析] 发现以下安全问题：
1. 密码未哈希
2. Token 无过期时间
3. 缺少 CSRF 保护

阶段 2: 代码探索
>>> @explore 查找所有使用认证的地方

Explore Agent:
[搜索] 找到 15 个使用认证的地方
- API 路由: 8 个
- 组件: 5 个
- 工具函数: 2 个

阶段 3: 实施重构
>>> @general-purpose 实施安全重构

General Agent:
[任务 1] 添加密码哈希
[任务 2] 实现 token 过期
[任务 3] 添加 CSRF 保护

[完成] 重构完成，更新了 15 个文件
```

## 性能对比

| Agent | 模型 | 平均响应时间 | 成本 (1M tokens) |
|-------|------|-------------|-----------------|
| Build | Sonnet | 2-3s | $3 |
| Plan | Sonnet | 2-3s | $3 |
| General | Sonnet | 2-3s | $3 |
| Explore | Haiku | 0.5-1s | $0.25 |

## 后续文档

- [自定义 Agent 开发](./09-custom-agent.md) - 学习如何创建自己的 Agent
