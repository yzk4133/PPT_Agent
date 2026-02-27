# 权限管理系统

## 概述

权限管理系统是 OpenCode 架构中的安全核心，负责控制 Agent 和工具的访问权限，确保系统在安全的范围内运行。

## 设计理念

### 核心原则

1. **默认拒绝**: 未明确允许的操作一律拒绝
2. **最小权限**: Agent 只授予完成任务所需的最小权限
3. **细粒度控制**: 支持文件路径、命令、工具类型的细粒度控制
4. **用户确认**: 危险操作需要用户显式确认
5. **审计日志**: 记录所有权限决策

### 权限层次

```
全局配置 (Global)
    │
    ├──► Agent 级别 (Agent)
    │       │
    │       └──► 工具级别 (Tool)
    │               │
    │               └──► 操作级别 (Operation)
```

## 权限规则

### 规则结构

```typescript
interface PermissionRuleset {
  // 文件操作权限
  read?: PermissionRule;
  write?: PermissionRule;
  edit?: PermissionRule;

  // 工具权限
  bash?: PermissionRule;
  grep?: PermissionRule;
  glob?: PermissionRule;

  // 特殊权限
  web?: PermissionRule;
  lsp?: PermissionRule;

  // 通配符规则
  '*': PermissionRule;
}

type PermissionRule = {
  allow?: Pattern[];  // 允许的模式
  deny?: Pattern[];   // 拒绝的模式
  ask?: Pattern[];    // 需要用户确认的模式
};

type Pattern = string;  // glob 模式或正则表达式
```

### 规则示例

```typescript
// 完整权限（Build Agent）
const buildPermission: PermissionRuleset = {
  read: { allow: ["**/*"] },
  write: { allow: ["**/*"] },
  edit: { allow: ["**/*"] },
  bash: { allow: ["**"] },
  grep: { allow: ["**/*"] },
  glob: { allow: ["**/*"] }
};

// 只读权限（Explore Agent）
const explorePermission: PermissionRuleset = {
  read: { allow: ["**/*"] },
  write: { deny: ["**"] },
  edit: { deny: ["**"] },
  bash: { deny: ["**"] },
  grep: { allow: ["**/*"] },
  glob: { allow: ["**/*"] }
};

// 受限权限（Plan Agent）
const planPermission: PermissionRuleset = {
  read: { allow: ["**/*"] },
  write: { deny: ["**"] },
  edit: { deny: ["**"] },
  bash: { deny: ["**"] },
  grep: { allow: ["**/*"] },
  glob: { allow: ["**/*"] }
};

// 前端开发权限
const frontendPermission: PermissionRuleset = {
  read: { allow: ["src/**/*", "public/**/*"] },
  write: { allow: ["src/**/*.{ts,tsx,css}", "public/**/*"] },
  edit: { allow: ["src/**/*.{ts,tsx,css}"] },
  bash: {
    allow: ["npm *", "yarn *", "pnpm *"],
    ask: ["npm install", "yarn install"]
  }
};
```

## 权限评估

### 评估函数

```typescript
// packages/opencode/src/permission/evaluator.ts
export function evaluate(
  permission: string,
  ruleset: PermissionRuleset
): Action {
  // 解析权限字符串
  const { tool, scope } = parsePermission(permission);

  // 获取工具规则
  const rule = ruleset[tool] || ruleset['*'];

  if (!rule) {
    return 'deny';
  }

  // 检查 deny 规则（优先级最高）
  if (rule.deny) {
    for (const pattern of rule.deny) {
      if (matchPattern(scope, pattern)) {
        return 'deny';
      }
    }
  }

  // 检查 ask 规则
  if (rule.ask) {
    for (const pattern of rule.ask) {
      if (matchPattern(scope, pattern)) {
        return 'ask';
      }
    }
  }

  // 检查 allow 规则
  if (rule.allow) {
    for (const pattern of rule.allow) {
      if (matchPattern(scope, pattern)) {
        return 'allow';
      }
    }
  }

  // 默认拒绝
  return 'deny';
}

type Action = 'allow' | 'deny' | 'ask';
```

### 模式匹配

```typescript
function matchPattern(
  scope: string,
  pattern: string
): boolean {
  // Glob 模式匹配
  if (pattern.includes('*')) {
    return minimatch(scope, pattern);
  }

  // 精确匹配
  if (pattern === scope) {
    return true;
  }

  // 正则表达式
  if (pattern.startsWith('/') && pattern.endsWith('/')) {
    const regex = new RegExp(pattern.slice(1, -1));
    return regex.test(scope);
  }

  return false;
}
```

### 权限解析

```typescript
function parsePermission(permission: string): {
  tool: string;
  scope: string;
} {
  // 解析权限字符串，如 "read:/path/to/file" 或 "bash:npm install"
  const [tool, ...scopeParts] = permission.split(':');
  const scope = scopeParts.join(':');

  return { tool, scope };
}
```

## 权限检查器

### 检查器类

```typescript
export class PermissionChecker {
  private ruleset: PermissionRuleset;
  private userInteraction: UserInteraction;

  constructor(
    ruleset: PermissionRuleset,
    userInteraction: UserInteraction
  ) {
    this.ruleset = ruleset;
    this.userInteraction = userInteraction;
  }

  async check(
    permission: string,
    context?: any
  ): Promise<PermissionResult> {
    // 1. 评估权限
    const action = evaluate(permission, this.ruleset);

    // 2. 处理结果
    switch (action) {
      case 'allow':
        return {
          allowed: true,
          reason: 'Permission granted by ruleset'
        };

      case 'deny':
        return {
          allowed: false,
          reason: 'Permission denied by ruleset'
        };

      case 'ask':
        // 请求用户确认
        const confirmed = await this.requestConfirmation(
          permission,
          context
        );

        return {
          allowed: confirmed,
          reason: confirmed
            ? 'User granted permission'
            : 'User denied permission'
        };
    }
  }

  private async requestConfirmation(
    permission: string,
    context: any
  ): Promise<boolean> {
    // 解析权限
    const { tool, scope } = parsePermission(permission);

    // 构建确认消息
    const message = this.buildConfirmationMessage(tool, scope, context);

    // 请求用户确认
    return await this.userInteraction.confirm({
      message,
      details: context,
      permission
    });
  }

  private buildConfirmationMessage(
    tool: string,
    scope: string,
    context: any
  ): string {
    switch (tool) {
      case 'bash':
        return `执行命令: ${scope}`;

      case 'edit':
      case 'write':
        return `修改文件: ${scope}`;

      case 'read':
        return `读取文件: ${scope}`;

      default:
        return `${tool}: ${scope}`;
    }
  }
}
```

## 权限继承

### 继承规则

```typescript
class PermissionResolver {
  resolve(agent: Agent.Info): PermissionRuleset {
    // 1. 从全局配置开始
    let resolved = { ...globalConfig.permissions };

    // 2. 应用 Agent 级别配置
    if (agent.permission) {
      resolved = this.merge(resolved, agent.permission);
    }

    // 3. 应用模型特定限制
    const modelRestrictions = this.getModelRestrictions(agent.model);
    resolved = this.merge(resolved, modelRestrictions);

    // 4. 应用用户自定义限制
    const userRestrictions = this.getUserRestrictions(agent.name);
    if (userRestrictions) {
      resolved = this.merge(resolved, userRestrictions);
    }

    return resolved;
  }

  private merge(
    base: PermissionRuleset,
    override: PermissionRuleset
  ): PermissionRuleset {
    const result: PermissionRuleset = { ...base };

    for (const [tool, rule] of Object.entries(override)) {
      if (rule === null) {
        // 删除规则
        delete result[tool];
      } else {
        // 合并规则
        result[tool] = {
          ...base[tool],
          ...rule
        };
      }
    }

    return result;
  }

  private getModelRestrictions(model: ModelConfig): PermissionRuleset {
    // 根据模型能力限制权限
    if (model.modelID.includes('haiku')) {
      // Haiku 模型能力有限，限制某些操作
      return {
        bash: { deny: ['**'] },
        edit: { deny: ['**'] }
      };
    }

    return {};
  }

  private getUserRestrictions(agentName: string): PermissionRuleset | null {
    // 从用户配置读取限制
    return userConfig.agents[agentName]?.permission || null;
  }
}
```

## 危险操作保护

### 危险操作检测

```typescript
class DangerDetector {
  private dangerousPatterns = [
    // 文件删除
    { tool: 'bash', pattern: 'rm -rf', risk: 'critical' },
    { tool: 'bash', pattern: 'del /', risk: 'critical' },

    // 系统修改
    { tool: 'bash', pattern: 'sudo', risk: 'high' },
    { tool: 'bash', pattern: 'chmod 777', risk: 'high' },

    // 网络操作
    { tool: 'bash', pattern: 'curl', risk: 'medium' },
    { tool: 'bash', pattern: 'wget', risk: 'medium' },

    // 包管理
    { tool: 'bash', pattern: 'npm install', risk: 'medium' },
    { tool: 'bash', pattern: 'pip install', risk: 'medium' },

    // Git 操作
    { tool: 'bash', pattern: 'git push --force', risk: 'high' },
    { tool: 'bash', pattern: 'git reset --hard', risk: 'high' }
  ];

  detect(tool: string, scope: string): DangerLevel {
    for (const pattern of this.dangerousPatterns) {
      if (pattern.tool === tool && scope.includes(pattern.pattern)) {
        return pattern.risk;
      }
    }

    return 'none';
  }
}

type DangerLevel = 'none' | 'low' | 'medium' | 'high' | 'critical';
```

### 强制确认

```typescript
class SafePermissionChecker extends PermissionChecker {
  private dangerDetector: DangerDetector;

  async check(
    permission: string,
    context?: any
  ): Promise<PermissionResult> {
    // 1. 检测危险级别
    const { tool, scope } = parsePermission(permission);
    const danger = this.dangerDetector.detect(tool, scope);

    // 2. 根据危险级别决定处理方式
    if (danger === 'critical') {
      // 关键操作，强制确认
      const confirmed = await this.forceConfirmation(permission, context);
      return {
        allowed: confirmed,
        reason: confirmed
          ? 'User confirmed critical operation'
          : 'User denied critical operation'
      };
    }

    if (danger === 'high') {
      // 高危操作，显示警告
      this.showWarning(permission, danger);
    }

    // 3. 正常权限检查
    return super.check(permission, context);
  }

  private async forceConfirmation(
    permission: string,
    context: any
  ): Promise<boolean> {
    const { tool, scope } = parsePermission(permission);

    return await this.userInteraction.forceConfirm({
      title: '⚠️ 危险操作确认',
      message: `您即将执行一个危险操作:\n\n${scope}\n\n此操作可能导致数据丢失或系统损坏。`,
      details: {
        tool,
        scope,
        context
      },
      requireExplicit: true  // 需要明确输入 "yes" 确认
    });
  }

  private showWarning(permission: string, danger: DangerLevel): void {
    const { tool, scope } = parsePermission(permission);

    this.userInteraction.notify({
      level: 'warning',
      title: '⚠️ 高危操作',
      message: `${scope}`,
      details: `此操作被标记为 ${danger} 风险级别`
    });
  }
}
```

## 审计日志

### 日志记录

```typescript
class AuditLogger {
  private logPath: string;

  async log(entry: AuditEntry): Promise<void> {
    const logEntry = {
      timestamp: new Date().toISOString(),
      ...entry
    };

    // 写入日志文件
    await fs.appendFile(
      this.logPath,
      JSON.stringify(logEntry) + '\n'
    );

    // 如果是敏感操作，也输出到控制台
    if (entry.sensitive) {
      console.warn(`[AUDIT] ${JSON.stringify(logEntry)}`);
    }
  }

  async query(filter: AuditFilter): Promise<AuditEntry[]> {
    // 读取并过滤日志
    const logs = await this.readLogs();
    return logs.filter(log => this.matchesFilter(log, filter));
  }

  private matchesFilter(log: AuditEntry, filter: AuditFilter): boolean {
    if (filter.agent && log.agent !== filter.agent) return false;
    if (filter.tool && log.tool !== filter.tool) return false;
    if (filter.startTime && log.timestamp < filter.startTime) return false;
    if (filter.endTime && log.timestamp > filter.endTime) return false;
    if (filter.action && log.action !== filter.action) return false;
    return true;
  }
}

interface AuditEntry {
  timestamp: string;
  agent: string;
  tool: string;
  scope: string;
  action: 'allow' | 'deny' | 'ask';
  allowed: boolean;
  sensitive?: boolean;
  context?: any;
}
```

### 权限审查

```typescript
class PermissionAuditor {
  private auditLogger: AuditLogger;

  async reviewPeriod(
    startDate: Date,
    endDate: Date
  ): Promise<AuditReport> {
    // 查询日志
    const logs = await this.auditLogger.query({
      startTime: startDate.toISOString(),
      endTime: endDate.toISOString()
    });

    // 生成报告
    return {
      period: { startDate, endDate },
      totalActions: logs.length,
      allowedActions: logs.filter(l => l.allowed).length,
      deniedActions: logs.filter(l => !l.allowed).length,
      sensitiveActions: logs.filter(l => l.sensitive).length,
      topAgents: this.groupByAgent(logs),
      topTools: this.groupByTool(logs),
      deniedList: logs.filter(l => !l.allowed)
    };
  }

  private groupByAgent(logs: AuditEntry[]): Array<{ agent: string; count: number }> {
    const groups = new Map<string, number>();

    for (const log of logs) {
      groups.set(log.agent, (groups.get(log.agent) || 0) + 1);
    }

    return Array.from(groups.entries())
      .map(([agent, count]) => ({ agent, count }))
      .sort((a, b) => b.count - a.count);
  }

  private groupByTool(logs: AuditEntry[]): Array<{ tool: string; count: number }> {
    const groups = new Map<string, number>();

    for (const log of logs) {
      groups.set(log.tool, (groups.get(log.tool) || 0) + 1);
    }

    return Array.from(groups.entries())
      .map(([tool, count]) => ({ tool, count }))
      .sort((a, b) => b.count - a.count);
  }
}
```

## 权限配置示例

### 配置文件

```yaml
# config/permissions.yaml
agents:
  # Build Agent - 完整权限
  build:
    permissions:
      read: { allow: ["**/*"] }
      write: { allow: ["**/*"] }
      edit: { allow: ["**/*"] }
      bash:
        allow: ["**"]
        ask: ["rm -rf*", "sudo*", "git push --force"]

  # Explore Agent - 只读权限
  explore:
    permissions:
      read: { allow: ["**/*"] }
      write: { deny: ["**"] }
      edit: { deny: ["**"] }
      bash: { deny: ["**"] }

  # Frontend Agent - 前端专用权限
  frontend:
    permissions:
      read:
        allow:
          - "src/**/*"
          - "public/**/*"
          - "package.json"
      write:
        allow:
          - "src/**/*.{ts,tsx,css,scss}"
          - "public/**/*"
      edit:
        allow:
          - "src/**/*.{ts,tsx,css,scss}"
      bash:
        allow:
          - "npm *"
          - "yarn *"
          - "pnpm *"
        ask:
          - "npm install*"
          - "npm audit fix"

  # Security Agent - 安全审计专用
  security:
    permissions:
      read: { allow: ["**/*"] }
      write: { deny: ["**"] }
      edit: { deny: ["**"] }
      bash: { deny: ["**"] }
      web: { allow: ["**"] }

# 全局限制
global:
  # 禁止访问敏感目录
  deny:
    - "~/.ssh/**"
    - "/etc/**"
    - "C:\\Windows\\System32/**"

  # 危险命令总是需要确认
  alwaysAsk:
    - "rm -rf*"
    - "del /"
    - "sudo*"
    - "git push --force"
```

## 最佳实践

### 1. 最小权限原则

只授予 Agent 完成任务所需的最小权限：

```typescript
// ❌ 不好的做法 - 权限过大
const badAgent = {
  permission: {
    '*': { allow: ['**'] }  // 所有工具，所有操作
  }
};

// ✅ 好的做法 - 只授予必要权限
const goodAgent = {
  permission: {
    read: { allow: ['src/**/*.ts'] },
    grep: { allow: ['src/**/*.ts'] }
  }
};
```

### 2. 明确的拒绝规则

使用 `deny` 明确禁止危险操作：

```typescript
const safeAgent = {
  permission: {
    read: { allow: ['**/*'] },
    bash: {
      allow: ['cat *', 'ls *', 'echo *'],
      deny: ['rm *', 'sudo *', 'chmod *']  // 明确拒绝
    }
  }
};
```

### 3. 分层权限控制

在多个层次上设置权限：

```typescript
// 全局层
const globalPermissions = {
  deny: ['~/.ssh/**', '/etc/**']
};

// Agent 层
const agentPermissions = {
  read: { allow: ['src/**/*'] },
  write: { allow: ['src/**/*.ts'] }
};

// 工具层（在工具内部）
const toolRestrictions = {
  maxSize: 1024 * 1024,  // 1MB
  allowedExtensions: ['.ts', '.js', '.json']
};
```

### 4. 审计和监控

定期审查权限使用情况：

```typescript
// 每周生成权限报告
const report = await auditor.reviewPeriod(
  new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
  new Date()
);

console.log(`本周拒绝的操作: ${report.deniedActions}`);
console.log(`敏感操作: ${report.sensitiveActions}`);

// 检查异常
if (report.deniedActions > threshold) {
  alert('权限拒绝次数异常，请检查配置');
}
```

## 后续文档

- [内置 Agent 详解](./08-built-in-agents.md) - 查看各内置 Agent 的权限配置
- [自定义 Agent 开发](./09-custom-agent.md) - 学习如何为自定义 Agent 配置权限
