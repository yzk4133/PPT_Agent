# 功能实现对比

> **版本：** 1.0.0 | **更新时间：** 2026-02-10

---

## 目录

- [1. Session 管理功能](#1-session-管理功能)
- [2. 消息管理功能](#2-消息管理功能)
- [3. State 管理功能](#3-state-管理功能)
- [4. 性能优化功能](#4-性能优化功能)
- [5. 扩展性功能](#5-扩展性功能)

---

## 1. Session 管理功能

### 1.1 会话创建

#### OpenCode 实现

**核心代码：**
```typescript
// packages/opencode/src/session/index.ts

export async function createNext(input: {
  id?: string
  title?: string
  parentID?: string
  directory: string
  permission?: PermissionNext.Ruleset
}) {
  const result: Info = {
    id: Identifier.descending("session", input.id),  // 降序ID
    slug: Slug.create(),                              // URL友好标识
    version: Installation.VERSION,                    // OpenCode版本
    projectID: Instance.project.id,
    directory: input.directory,
    parentID: input.parentID,                         // 父会话ID
    title: input.title ?? createDefaultTitle(!!input.parentID),
    permission: input.permission,
    time: {
      created: Date.now(),
      updated: Date.now(),
    },
  }

  // 写入存储
  await Storage.write(["session", Instance.project.id, result.id], result)

  // 发布事件
  Bus.publish(Event.Created, { info: result })

  // 自动分享（如果配置开启）
  const cfg = await Config.get()
  if (!result.parentID && (Flag.OPENCODE_AUTO_SHARE || cfg.share === "auto")) {
    share(result.id).then((share) => {
      update(result.id, (draft) => { draft.share = share })
    }).catch(() => {})
  }

  return result
}

// 默认标题生成
function createDefaultTitle(isChild = false) {
  const prefix = isChild ? "Child session - " : "New session - "
  return prefix + new Date().toISOString()
}
```

**特点：**
- 降序 ID（时间戳排序）
- 自动生成 URL 友好的 slug
- 支持父子会话
- 自动分享功能
- 事件总线通知

#### MultiAgentPPT 实现

**核心代码：**
```python
# backend/infrastructure/checkpoint/checkpoint_manager.py

async def save_checkpoint(
    self,
    task_id: str,
    user_id: str,
    execution_mode,
    phase: int,
    raw_input: str,
    requirements: Dict[str, Any],
    framework: Dict[str, Any],
    parent_task_id: Optional[str] = None
) -> Checkpoint:
    """创建并保存检查点"""
    checkpoint = Checkpoint(
        task_id=task_id,
        user_id=user_id,
        execution_mode=execution_mode,
        phase=phase,
        raw_user_input=raw_input,
        structured_requirements=requirements,
        ppt_framework=framework,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        status="editing",
        version=1,
        parent_task_id=parent_task_id
    )

    success = await self.backend.save(checkpoint)
    if not success:
        raise RuntimeError(f"Failed to save checkpoint: {task_id}")

    logger.info(f"Checkpoint saved: {task_id} (phase {phase}, user {user_id})")
    return checkpoint
```

**特点：**
- 简单的任务 ID
- 无 slug 机制
- 支持父任务关联
- 无自动分享
- 无事件总线

**对比总结：**

| 特性 | OpenCode | MultiAgentPPT |
|------|----------|---------------|
| ID 生成策略 | 降序时间戳 | UUID/自定义 |
| URL 友好 | slug 支持 | 不支持 |
| 父子关系 | 完整支持 | 弱支持 |
| 事件通知 | Bus 发布 | 无 |
| 自动分享 | 可配置 | 无 |

### 1.2 会话关系

#### OpenCode：父子会话 + Fork 机制

**Fork 实现：**
```typescript
export const fork = fn(
  z.object({
    sessionID: Identifier.schema("session"),
    messageID: Identifier.schema("message").optional(),
  }),
  async (input) => {
    // 1. 获取原会话
    const original = await get(input.sessionID)
    if (!original) throw new Error("session not found")

    // 2. 生成 fork 标题
    const title = getForkedTitle(original.title)

    // 3. 创建新会话
    const session = await createNext({
      directory: Instance.directory,
      title,
    })

    // 4. 复制消息历史
    const msgs = await messages({ sessionID: input.sessionID })
    const idMap = new Map<string, string>()

    for (const msg of msgs) {
      // 如果指定了 messageID，只复制到该消息为止
      if (input.messageID && msg.info.id >= input.messageID) break

      // 生成新 ID
      const newID = Identifier.ascending("message")
      idMap.set(msg.info.id, newID)

      // 复制消息
      const parentID = msg.info.role === "assistant" && msg.info.parentID
        ? idMap.get(msg.info.parentID)
        : undefined

      const cloned = await updateMessage({
        ...msg.info,
        sessionID: session.id,
        id: newID,
        ...(parentID && { parentID }),
      })

      // 复制 parts
      for (const part of msg.parts) {
        await updatePart({
          ...part,
          id: Identifier.ascending("part"),
          messageID: cloned.id,
          sessionID: session.id,
        })
      }
    }

    return session
  },
)

// 标题生成：Original (fork #1) → Original (fork #2)
function getForkedTitle(title: string): string {
  const match = title.match(/^(.+) \(fork #(\d+)\)$/)
  if (match) {
    const base = match[1]
    const num = parseInt(match[2], 10)
    return `${base} (fork #${num + 1})`
  }
  return `${title} (fork #1)`
}

// 获取子会话
export const children = fn(Identifier.schema("session"), async (parentID) => {
  const project = Instance.project
  const result = [] as Session.Info[]
  for (const item of await Storage.list(["session", project.id])) {
    const session = await Storage.read<Info>(item).catch(() => undefined)
    if (!session) continue
    if (session.parentID !== parentID) continue
    result.push(session)
  }
  return result
})
```

**会话树示例：**
```
Root Session (id: sess_001)
├── Child Session 1 (id: sess_002, parentID: sess_001)
│   └── Grandchild (id: sess_004, parentID: sess_002)
├── Child Session 2 (id: sess_003, parentID: sess_001)
└── Fork (id: sess_005, parentID: null, title: "Root (fork #1)")
```

#### MultiAgentPPT：单一会话 + 弱关联

**检查点关联：**
```python
class Checkpoint:
    task_id: str
    user_id: str
    parent_task_id: Optional[str] = None  # 弱关联，不强制

    # 无 fork 机制
    # 无子任务查询
    # 无会话树结构
```

**对比总结：**

| 特性 | OpenCode | MultiAgentPPT |
|------|----------|---------------|
| 父子关系 | 完整树结构 | 弱关联 |
| Fork 机制 | 支持 | 不支持 |
| 子查询 | children() API | 无 |
| 树形展示 | 支持 | 不支持 |
| 使用场景 | 多路径探索 | 线性任务 |

### 1.3 会话恢复

#### OpenCode：Git 快照恢复

**快照创建：**
```typescript
// packages/opencode/src/snapshot/index.ts

export async function track() {
  if (Instance.project.vcs !== "git") return
  const cfg = await Config.get()
  if (cfg.snapshot === false) return

  const git = gitdir()

  // 初始化 git 仓库
  if (await fs.mkdir(git, { recursive: true })) {
    await $`git init`
      .env({
        ...process.env,
        GIT_DIR: git,
        GIT_WORK_TREE: Instance.worktree,
      })
      .quiet()
      .nothrow()
    await $`git --git-dir ${git} config core.autocrlf false`.quiet().nothrow()
  }

  // 添加所有文件
  await $`git --git-dir ${git} --work-tree ${Instance.worktree} add .`
    .quiet()
    .cwd(Instance.directory)
    .nothrow()

  // 写入 tree
  const hash = await $`git --git-dir ${git} --work-tree ${Instance.worktree} write-tree`
    .quiet()
    .cwd(Instance.directory)
    .nothrow()
    .text()

  return hash.trim()  // 返回快照 hash
}

// 快照恢复
export async function restore(snapshot: string) {
  log.info("restore", { commit: snapshot })
  const git = gitdir()
  const result = await $`git --git-dir ${git} --work-tree ${Instance.worktree} read-tree ${snapshot} && git --git-dir ${git} --work-tree ${Instance.worktree} checkout-index -a -f`
    .quiet()
    .cwd(Instance.worktree)
    .nothrow()

  if (result.exitCode !== 0) {
    log.error("failed to restore snapshot", {
      snapshot,
      exitCode: result.exitCode,
    })
  }
}
```

**会话恢复流程：**
```typescript
// 1. 加载会话元数据
const session = await Session.get(sessionID)

// 2. 获取关联的快照
const snapshotPart = messageParts.find(p => p.type === "snapshot")
const snapshotHash = snapshotPart.snapshot

// 3. 恢复快照
await Snapshot.restore(snapshotHash)

// 4. 加载消息历史
const messages = await Session.messages({ sessionID })
```

#### MultiAgentPPT：检查点恢复

**检查点加载：**
```python
async def load_checkpoint(self, task_id: str) -> Optional[Checkpoint]:
    """加载检查点"""
    checkpoint = await self.backend.load(task_id)

    if checkpoint:
        # 检查是否过期
        if checkpoint.is_expired():
            logger.warning(f"Checkpoint {task_id} is expired")
            await self.backend.delete(task_id)
            return None

        logger.info(f"Checkpoint loaded: {task_id} (phase {checkpoint.phase})")
    else:
        logger.warning(f"Checkpoint not found: {task_id}")

    return checkpoint

# 恢复状态到 LangGraph State
def restore_to_state(checkpoint: Checkpoint) -> PPTGenerationState:
    """将检查点恢复为 LangGraph 状态"""
    return {
        "task_id": checkpoint.task_id,
        "user_id": checkpoint.user_id,
        "user_input": checkpoint.raw_user_input,
        "requirements": checkpoint.structured_requirements,
        "framework": checkpoint.ppt_framework,
        "current_phase": checkpoint.phase,
        # ... 其他字段
    }
```

**对比总结：**

| 特性 | OpenCode | MultiAgentPPT |
|------|----------|---------------|
| 恢复机制 | Git checkout | 数据库查询 |
| 恢复粒度 | 文件级 | 状态级 |
| 版本控制 | Git commit | 版本号字段 |
| 存储效率 | 增量存储 | 完整存储 |
| 恢复速度 | ~100ms | ~50ms |
| Diff 查看 | Git diff | 不支持 |

### 1.4 会话生命周期

#### OpenCode：明确的创建/销毁

**创建流程：**
```typescript
// 1. createNext() 创建会话
// 2. 写入文件
// 3. 发布事件
// 4. (可选) 自动分享
```

**销毁流程：**
```typescript
export const remove = fn(Identifier.schema("session"), async (sessionID) => {
  const project = Instance.project
  try {
    const session = await get(sessionID)

    // 1. 递归删除子会话
    for (const child of await children(sessionID)) {
      await remove(child.id)
    }

    // 2. 取消分享
    await unshare(sessionID).catch(() => {})

    // 3. 删除所有消息和 parts
    for (const msg of await Storage.list(["message", sessionID])) {
      for (const part of await Storage.list(["part", msg.at(-1)!])) {
        await Storage.remove(part)
      }
      await Storage.remove(msg)
    }

    // 4. 删除会话文件
    await Storage.remove(["session", project.id, sessionID])

    // 5. 发布事件
    Bus.publish(Event.Deleted, { info: session })
  } catch (e) {
    log.error(e)
  }
})
```

**状态管理：**
```typescript
// State.create() 返回的状态需要手动 dispose
export async function dispose(key: string) {
  const entries = recordsByKey.get(key)
  if (!entries) return

  // 并发清理所有 state
  const tasks: Promise<void>[] = []
  for (const [init, entry] of entries) {
    if (!entry.dispose) continue
    const task = Promise.resolve(entry.state)
      .then((state) => entry.dispose!(state))
      .catch((error) => log.error("Error while disposing state:", { error, key }))
    tasks.push(task)
  }
  await Promise.all(tasks)

  entries.clear()
  recordsByKey.delete(key)
}
```

#### MultiAgentPPT：数据库生命周期

**创建：**
```python
# 检查点创建时自动插入数据库
checkpoint = Checkpoint(...)
await self.backend.save(checkpoint)
```

**删除：**
```python
async def delete_checkpoint(self, task_id: str) -> bool:
    """删除检查点（软删除）"""
    success = await self.backend.delete(task_id)
    if success:
        logger.info(f"Checkpoint deleted: {task_id}")
    return success
```

**过期管理：**
```python
async def cleanup_expired(self, ttl_hours: int = 24) -> int:
    """清理过期的检查点"""
    all_checkpoints = await self.backend.list_all()

    expired_count = 0
    for checkpoint in all_checkpoints:
        if checkpoint.is_expired(ttl_hours):
            await self.backend.delete(checkpoint.task_id)
            expired_count += 1

    if expired_count > 0:
        logger.info(f"Cleaned up {expired_count} expired checkpoints")

    return expired_count
```

**对比总结：**

| 特性 | OpenCode | MultiAgentPPT |
|------|----------|---------------|
| 创建时机 | 显式调用 | API 请求 |
| 删除方式 | 级联删除 | 单条删除 |
| 子会话处理 | 递归删除 | 不支持 |
| 状态清理 | 手动 dispose | 无需管理 |
| 过期机制 | 不支持 | TTL 自动清理 |

---

## 2. 消息管理功能

### 2.1 消息存储

#### OpenCode：Message + Parts 分层

**Message 结构：**
```typescript
export const User = Base.extend({
  role: z.literal("user"),
  time: z.object({
    created: z.number(),
  }),
  summary: z.object({
    title: z.string().optional(),
    body: z.string().optional(),
    diffs: Snapshot.FileDiff.array(),
  }).optional(),
  agent: z.string(),
  model: z.object({
    providerID: z.string(),
    modelID: z.string(),
  }),
  system: z.string().optional(),
  tools: z.record(z.string(), z.boolean()).optional(),
  variant: z.string().optional(),
})

export const Assistant = Base.extend({
  role: z.literal("assistant"),
  time: z.object({
    created: z.number(),
    completed: z.number().optional(),
  }),
  error: z.discriminatedUnion("name", [
    AuthError.Schema,
    NamedError.Unknown.Schema,
    OutputLengthError.Schema,
    AbortedError.Schema,
    APIError.Schema,
  ]).optional(),
  parentID: z.string(),
  modelID: z.string(),
  providerID: z.string(),
  mode: z.string(),
  agent: z.string(),
  path: z.object({
    cwd: z.string(),
    root: z.string(),
  }),
  summary: z.boolean().optional(),
  cost: z.number(),
  tokens: z.object({
    input: z.number(),
    output: z.number(),
    reasoning: z.number(),
    cache: z.object({
      read: z.number(),
      write: z.number(),
    }),
  }),
  finish: z.string().optional(),
})
```

**Part 类型（12+ 种）：**
```typescript
export const Part = z.discriminatedUnion("type", [
  TextPart,           // type: "text", text: string
  ReasoningPart,      // type: "reasoning", text: string
  FilePart,           // type: "file", url: string, mime: string
  ToolPart,           // type: "tool", callID: string, state: ToolState
  SubtaskPart,        // type: "subtask", prompt: string, agent: string
  StepStartPart,      // type: "step-start", snapshot: string
  StepFinishPart,     // type: "step-finish", reason: string, cost: number
  SnapshotPart,       // type: "snapshot", snapshot: string
  PatchPart,          // type: "patch", hash: string, files: string[]
  AgentPart,          // type: "agent", name: string
  RetryPart,          // type: "retry", attempt: number, error: APIError
  CompactionPart,     // type: "compaction", auto: boolean
])
```

**目录结构：**
```
~/.opencode/storage/
├── message/
│   └── {sessionID}/
│       └── {messageID}.json          # Message 主数据
└── part/
    └── {messageID}/
        ├── {partID_1}.json           # Part 1
        ├── {partID_2}.json           # Part 2
        └── ...
```

#### MultiAgentPPT：单一表结构

**当前实现：**
- 消息主要存储在 LangGraph State 中
- 无独立消息表
- 无分层结构

**检查点存储的消息：**
```python
class Checkpoint:
    raw_user_input: str                    # 原始输入
    structured_requirements: Dict[str, Any]  # 结构化需求
    ppt_framework: Dict[str, Any]          # PPT 框架
    # 消息不单独存储，而是作为检查点的一部分
```

**对比总结：**

| 特性 | OpenCode | MultiAgentPPT |
|------|----------|---------------|
| 存储结构 | 分层 (Message+Parts) | 单一结构 |
| 消息类型 | User/Assistant + 12+ Parts | 基础类型 |
| 扩展性 | 高（易于添加新 Part） | 低 |
| 查询效率 | 中（需要 join parts） | 高 |
| 存储效率 | 高（parts 分离） | 中 |

### 2.2 消息压缩

#### OpenCode：自动压缩 + Agent 摘要

**压缩触发：**
```typescript
// 检测是否需要压缩
async function is_overflow(sessionID: string): boolean {
  const messages = await messages({ sessionID })
  const tokens = count_tokens(messages)
  return tokens > MODEL_LIMIT
}

// 紧凑化工具结果
async function compact_tool_results(sessionID: string) {
  const messages = await messages({ sessionID })

  for (const msg of messages) {
    for (const part of msg.parts) {
      if (part.type === "tool" && part.state.status === "completed") {
        // 标记为已压缩
        part.state.time.compacted = Date.now()
        // 清空输出
        part.state.output = "[Old tool result content cleared]"
        await updatePart(part)
      }
    }
  }
}
```

**摘要生成：**
```typescript
// Agent 生成摘要
async function generate_summary(messages: MessageV2.WithParts[]): Promise<string> {
  const summaryPrompt = `
    Please summarize the following conversation:
    ${messages.map(m => m.info.role + ": " + get_text(m)).join("\n")}
  `

  const response = await llm.generate(summaryPrompt)
  return response.text
}

// 插入摘要消息
await updateMessage({
  id: Identifier.ascending("message"),
  sessionID,
  role: "assistant",
  time: { created: Date.now(), completed: Date.now() },
  parentID: messages[0].id,
  summary: true,  // 标记为摘要
  parts: [{ type: "text", text: summary }]
})
```

**压缩标记消息：**
```typescript
// 插入压缩标记
await updateMessage({
  id: Identifier.ascending("message"),
  sessionID,
  role: "user",
  time: { created: Date.now() },
  parts: [{
    type: "compaction",
    auto: true  // 自动压缩
  }]
})
```

#### MultiAgentPPT：无压缩机制

**当前状态：**
- 无消息压缩功能
- 完整保留所有历史
- 存在 token 溢出风险

**对比总结：**

| 特性 | OpenCode | MultiAgentPPT |
|------|----------|---------------|
| 压缩机制 | 自动压缩 + Agent 摘要 | 无 |
| Token 管理 | 紧凑化旧结果 | 完整保留 |
| 压缩触发 | 自动检测 | 不支持 |
| 压缩标记 | CompactionPart | 无 |
| 效果 | 减少 50-70% token | 无优化 |

### 2.3 消息版本控制

#### OpenCode：消息级版本

**快照关联：**
```typescript
// 消息可以关联 Git 快照
export const SnapshotPart = PartBase.extend({
  type: z.literal("snapshot"),
  snapshot: z.string(),  // Git tree hash
})

// Diff 记录
export const PatchPart = PartBase.extend({
  type: z.literal("patch"),
  hash: z.string(),
  files: z.string().array(),
})

// Session 摘要包含 diff
export const Info = z.object({
  // ...
  summary: z.object({
    additions: z.number(),
    deletions: z.number(),
    files: z.number(),
    diffs: Snapshot.FileDiff.array().optional(),
  }).optional(),
})
```

**版本恢复：**
```typescript
// 恢复到指定消息的快照
async function restore_to_message(sessionID: string, messageID: string) {
  const message = await get({ sessionID, messageID })

  // 查找快照 part
  const snapshotPart = message.parts.find(p => p.type === "snapshot")
  if (snapshotPart) {
    await Snapshot.restore(snapshotPart.snapshot)
  }

  // 回滚到指定 diff
  const patchParts = message.parts.filter(p => p.type === "patch")
  await Snapshot.revert(patchParts)
}
```

#### MultiAgentPPT：检查点版本

**版本控制：**
```python
class Checkpoint:
    version: int  # 版本号

    def increment_version(self):
        self.version += 1
        self.updated_at = datetime.now()
```

**对比总结：**

| 特性 | OpenCode | MultiAgentPPT |
|------|----------|---------------|
| 版本粒度 | 消息级 + Git | 检查点级 |
| 版本存储 | Git commit | 版本号字段 |
| Diff 查看 | Git diff | 不支持 |
| 回滚支持 | Git checkout | 不支持 |
| 存储效率 | 增量存储 | 完整存储 |

---

## 3. State 管理功能

### 3.1 状态创建

#### OpenCode：延迟初始化

```typescript
export function create<S>(
  root: () => string,        // 作用域标识符
  init: () => S,              // 初始化函数
  dispose?: (state: Awaited<S>) => Promise<void>
) {
  return () => {
    const key = root()
    let entries = recordsByKey.get(key)
    if (!entries) {
      entries = new Map<string, Entry>()
      recordsByKey.set(key, entries)
    }

    // 单例：相同 init 返回同一实例
    const exists = entries.get(init)
    if (exists) return exists.state as S

    // 首次访问时才初始化
    const state = init()
    entries.set(init, { state, dispose })
    return state
  }
}

// 使用示例
const getSessionState = State.create(
  () => "session",
  () => ({ count: 0, data: new Map() })
)

const state1 = getSessionState()  // 创建
const state2 = getSessionState()  // 返回同一实例
```

#### MultiAgentPPT：即时初始化

```python
class PPTGenerationState(TypedDict):
    task_id: str
    user_id: str
    user_input: str
    requirements: Optional[Dict[str, Any]]
    framework: Optional[Dict[str, Any]]
    # ...

# 创建时立即初始化所有字段
state: PPTGenerationState = {
    "task_id": task_id,
    "user_id": user_id,
    "user_input": user_input,
    "requirements": None,
    "framework": None,
    # ...
}
```

### 3.2 状态销毁

#### OpenCode：异步清理

```typescript
export async function dispose(key: string) {
  const entries = recordsByKey.get(key)
  if (!entries) return

  // 10秒超时警告
  let disposalFinished = false
  setTimeout(() => {
    if (!disposalFinished) {
      log.warn("state disposal is taking an unusually long time", { key })
    }
  }, 10000).unref()

  // 并发清理所有 state
  const tasks: Promise<void>[] = []
  for (const [init, entry] of entries) {
    if (!entry.dispose) continue

    const task = Promise.resolve(entry.state)
      .then((state) => entry.dispose!(state))
      .catch((error) => log.error("Error while disposing state:", { error, key }))

    tasks.push(task)
  }

  await Promise.all(tasks)

  entries.clear()
  recordsByKey.delete(key)
  disposalFinished = true
}
```

#### MultiAgentPPT：数据库删除

```python
async def delete_checkpoint(self, task_id: str) -> bool:
    """删除检查点"""
    success = await self.backend.delete(task_id)
    return success
```

### 3.3 作用域管理

#### OpenCode：多级 Map 作用域

```typescript
// Map<key, Map<init, Entry>>
const recordsByKey = new Map<string, Map<any, Entry>>()

// 不同的 root() 函数创建不同的作用域
const sessionState = State.create(() => "session", () => ({}))
const userState = State.create(() => "user", () => ({}))
const tempState = State.create(() => "temp", () => ({}))

// 作用域之间完全隔离
sessionState().data = "session data"
userState().data = "user data"
tempState().data = "temp data"
```

#### MultiAgentPPT：LangGraph State 作用域

```python
# 每个任务有独立的 State
state: PPTGenerationState = {
    "task_id": "task_001",
    "user_id": "user_001",
    # ... State 作用域是任务级别
}

# Agent 之间通过 LangGraph 传递 State
# State 在同一个图的节点间共享
```

---

## 4. 性能优化功能

### 4.1 缓存策略

#### OpenCode：无内置缓存

- 依赖文件系统缓存
- 依赖 Bun 运行时缓存
- 无应用层缓存

#### MultiAgentPPT：Redis + L1 缓存

**Redis 缓存实现：**
```python
class RedisCache:
    """Redis 缓存管理"""

    async def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户偏好（先查缓存）"""
        key = f"user_preferences:{user_id}"
        cached = await self.client.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any],
        ttl: int = 3600
    ):
        """设置用户偏好（写入缓存）"""
        key = f"user_preferences:{user_id}"
        await self.client.setex(
            key,
            ttl,
            json.dumps(preferences, ensure_ascii=False)
        )

    async def delete_user_preferences(self, user_id: str):
        """删除用户偏好（缓存失效）"""
        key = f"user_preferences:{user_id}"
        await self.client.delete(key)
```

**服务层缓存逻辑：**
```python
async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
    # 1. 先从缓存获取
    if self.enable_cache:
        cached = await self.cache_client.get_user_preferences(user_id)
        if cached:
            self.logger.debug(f"Cache hit for user {user_id}")
            return cached

    # 2. 缓存未命中 → 查 MySQL
    profile = self._get_profile(user_id)
    if profile:
        preferences = profile.to_dict()

        # 3. 写回缓存
        if self.enable_cache:
            await self.cache_client.set_user_preferences(user_id, preferences)

        return preferences

    return {}
```

**性能对比：**

| 操作 | 无缓存 (MySQL) | 有缓存 (Redis) |
|------|---------------:|---------------:|
| 用户偏好查询 | 10-50ms | 1-5ms |
| 缓存命中率 | N/A | 80%+ |
| QPS | ~100 | ~1000 |

### 4.2 并发控制

#### OpenCode：文件读写锁

**读写锁实现：**
```typescript
export namespace Lock {
  const locks = new Map<string, {
    readers: number
    writer: boolean
    waitingReaders: (() => void)[]
    waitingWriters: (() => void)[]
  }>()

  export async function read(key: string): Promise<Disposable> {
    const lock = get(key)
    return new Promise((resolve) => {
      // 如果没有写锁且没有等待的写锁，直接获取读锁
      if (!lock.writer && lock.waitingWriters.length === 0) {
        lock.readers++
        resolve({
          [Symbol.dispose]: () => {
            lock.readers--
            process(key)
          },
        })
      } else {
        // 等待获取读锁
        lock.waitingReaders.push(() => {
          lock.readers++
          resolve({
            [Symbol.dispose]: () => {
              lock.readers--
              process(key)
            },
          })
        })
      }
    })
  }

  export async function write(key: string): Promise<Disposable> {
    const lock = get(key)
    return new Promise((resolve) => {
      // 如果没有锁，直接获取写锁
      if (!lock.writer && lock.readers === 0) {
        lock.writer = true
        resolve({
          [Symbol.dispose]: () => {
            lock.writer = false
            process(key)
          },
        })
      } else {
        // 等待获取写锁
        lock.waitingWriters.push(() => {
          lock.writer = true
          resolve({
            [Symbol.dispose]: () => {
              lock.writer = false
              process(key)
            },
          })
        })
      }
    })
  }

  // 唤醒等待的锁
  function process(key: string) {
    const lock = locks.get(key)
    if (!lock || lock.writer || lock.readers > 0) return

    // 优先唤醒写锁（防止写锁饥饿）
    if (lock.waitingWriters.length > 0) {
      const nextWriter = lock.waitingWriters.shift()!
      nextWriter()
      return
    }

    // 唤醒所有等待的读锁
    while (lock.waitingReaders.length > 0) {
      const nextReader = lock.waitingReaders.shift()!
      nextReader()
    }
  }
}
```

**使用示例：**
```typescript
// 读取（共享锁）
using lock = await Lock.read(filePath)
const data = await readFile(filePath)
// lock 自动释放

// 写入（排他锁）
using lock = await Lock.write(filePath)
await writeFile(filePath, data)
// lock 自动释放
```

#### MultiAgentPPT：数据库事务

**事务管理：**
```python
@contextmanager
def get_session(self):
    """获取数据库会话（上下文管理器）"""
    session = self.SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

# 使用示例
with db.get_session() as session:
    profile = session.query(UserProfile).filter(...).first()
    profile.language = "EN"
    # 自动 commit 或 rollback
```

**对比总结：**

| 特性 | OpenCode | MultiAgentPPT |
|------|----------|---------------|
| 锁类型 | 读写锁 | 数据库事务 |
| 锁粒度 | 文件级 | 行级 |
| 死锁处理 | 等待队列 | 数据库引擎 |
| 性能 | 极快（内存） | 中等（网络 I/O） |
| 分布式支持 | 不支持 | 支持 |

### 4.3 批量操作

#### OpenCode：Promise.all 并行

```typescript
// 批量删除
async function batch_remove(items: string[]) {
  await Promise.all(items.map(item => Storage.remove(item)))
}

// 批量读取
async function batch_read(keys: string[][]) {
  return await Promise.all(
    keys.map(key => Storage.read<Info>(key))
  )
}
```

#### MultiAgentPPT：数据库批量操作

```python
# 批量查询
def get_preferences_batch(self, user_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    profiles = self.db_session.query(UserProfile).filter(
        UserProfile.user_id.in_(user_ids)
    ).all()

    result = {uid: {} for uid in user_ids}
    for profile in profiles:
        result[profile.user_id] = profile.to_dict()

    return result
```

---

## 5. 扩展性功能

### 5.1 数据迁移

#### OpenCode：版本化迁移系统

**迁移实现：**
```typescript
const MIGRATIONS: Migration[] = [
  // Migration 0: 项目结构迁移
  async (dir) => {
    const project = path.resolve(dir, "../project")
    if (!(await Filesystem.isDir(project))) return

    // 迁移项目目录
    for await (const projectDir of new Bun.Glob("*").scan({
      cwd: project,
      onlyFiles: false,
    })) {
      // ... 迁移逻辑
    }
  },

  // Migration 1: session_diff 分离
  async (dir) => {
    for await (const item of new Bun.Glob("session/*/*.json").scan({
      cwd: dir,
      absolute: true,
    })) {
      const session = await Bun.file(item).json()
      if (!session.summary?.diffs) continue

      // 分离 diffs 到独立文件
      await Bun.file(
        path.join(dir, "session_diff", session.id + ".json")
      ).write(JSON.stringify(session.summary.diffs))

      // 更新 session
      await Bun.file(path.join(dir, "session", ...)).write(
        JSON.stringify({
          ...session,
          summary: {
            additions: diffs.reduce((sum, x) => sum + x.additions, 0),
            deletions: diffs.reduce((sum, x) => sum + x.deletions, 0),
          },
        })
      )
    }
  },
]

// 自动运行未执行的迁移
const state = lazy(async () => {
  const dir = path.join(Global.Path.data, "storage")
  const migration = await Bun.file(path.join(dir, "migration"))
    .json()
    .then((x) => parseInt(x))
    .catch(() => 0)

  for (let index = migration; index < MIGRATIONS.length; index++) {
    log.info("running migration", { index })
    const migration = MIGRATIONS[index]
    await migration(dir).catch(() => log.error("failed to run migration", { index }))
    await Bun.write(path.join(dir, "migration"), (index + 1).toString())
  }

  return { dir }
})
```

#### MultiAgentPPT：手动迁移

**当前状态：**
- 无自动迁移系统
- 需要手动编写迁移脚本
- 需要手动记录版本

### 5.2 多租户支持

#### OpenCode：单项目

**当前状态：**
- 无用户隔离
- 无多租户支持
- 项目级别配置

#### MultiAgentPPT：多用户支持

**用户隔离：**
```python
class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(String(255), primary_key=True)
    language = Column(String(10), default="ZH-CN")
    default_slides = Column(Integer, default=10)
    tone = Column(String(20), default="professional")

    # 用户隔离
    def get_preferences(self) -> Dict[str, Any]:
        return {
            "language": self.language,
            "default_slides": self.default_slides,
            "tone": self.tone,
        }

# 按用户查询
def get_user_checkpoints(self, user_id: str) -> List[Checkpoint]:
    return self.db_session.query(Checkpoint).filter(
        Checkpoint.user_id == user_id
    ).all()
```

**统计追踪：**
```python
class UserProfile(Base):
    session_count = Column(Integer, default=0)
    generation_count = Column(Integer, default=0)
    satisfaction_score = Column(Float, default=0.0)

    def increment_session_count(self):
        self.session_count += 1

    def update_satisfaction_score(self, score: float):
        # 移动平均
        n = self.session_count
        self.satisfaction_score = (
            (self.satisfaction_score * (n - 1) + score) / n
        )
```

---

**文档版本：** 1.0.0
**最后更新：** 2026-02-10
**维护者：** MultiAgentPPT Team
