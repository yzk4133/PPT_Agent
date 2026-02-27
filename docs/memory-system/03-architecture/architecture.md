# 架构设计

> **版本：** 2.0.0
> **更新日期：** 2025-02-09

---

## 目录

- [整体架构](#整体架构)
- [技术选型](#技术选型)
- [设计原则](#设计原则)
- [数据流](#数据流)
- [组件交互](#组件交互)

---

## 整体架构

记忆系统采用四层架构设计，从上到下依次为：

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                   应用层 (Application)                       │
│              LangGraph Agents - 业务层                       │
│  RequirementAgent | ResearchAgent | FrameworkAgent | ...    │
└────────────────────────────┬────────────────────────────────┘
                              │ 继承
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              记忆适配层 (Memory Adapter)                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  MemoryAwareAgent (基类)                              │   │
│  │  - remember(), recall(), forget() 等便捷接口         │   │
│  │  - 管理记忆管理器的生命周期                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                              │                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  StateBoundMemoryManager (桥接器)                     │   │
│  │  - 从 LangChain 状态提取上下文                        │   │
│  │  - 作用域推断和路由                                    │   │
│  │  - 调用底层服务                                        │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                              │ 调用
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   服务层 (Service)                           │
│                                                              │
│  ┌──────────────────┐ ┌─────────────────┐ ┌─────────────┐  │
│  │ UserPreference   │ │  Decision       │ │  Workspace  │  │
│  │ Service          │ │  Service        │ │  Service    │  │
│  │                  │ │                 │ │             │  │
│  │ - 用户偏好管理   │ │ - 决策追踪      │ │ - 数据共享  │  │
│  │ - 使用统计       │ │ - 行为分析      │ │ - TTL管理   │  │
│  └──────────────────┘ └─────────────────┘ └─────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                              │ 调用
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   存储层 (Storage)                           │
│                                                              │
│  ┌──────────────────┐     ┌──────────────────┐             │
│  │  MySQL           │     │     Redis        │             │
│  │                  │     │                  │             │
│  │  - 会话状态       │     │  - L2 缓存        │             │
│  │  - 用户偏好       │     │  - 会话缓存       │             │
│  │  - 决策追踪       │     │  - 热点数据       │             │
│  │  - 工作空间       │     │  - 分布式锁       │             │
│  └──────────────────┘     └──────────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

### 层次说明

| 层次 | 职责 | 主要组件 |
|------|------|----------|
| **应用层** | 业务逻辑 | LangGraph Agents |
| **适配层** | LangChain 集成 | MemoryAwareAgent, StateBoundMemoryManager |
| **服务层** | 业务逻辑 | UserPreferenceService, DecisionService, WorkspaceService |
| **存储层** | 数据持久化 | DatabaseManager, RedisCache, Models |

---

## 技术选型

### 核心技术

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| **ORM** | SQLAlchemy | 支持 MySQL，提供抽象层 |
| **缓存** | Redis | L2 缓存、分布式锁、会话存储 |
| **数据库** | MySQL 5.7+ | 主数据存储 |
| **AI 框架** | LangChain/LangGraph | Agent 框架集成 |
| **配置管理** | dataclasses + 环境变量 | 类型安全的配置管理 |

### 为什么选择 MySQL

| 特性 | 说明 |
|------|------|
| **JSON 支持** | MySQL 5.7+ 原生支持 JSON 类型，满足灵活数据存储需求 |
| **成熟稳定** | 广泛使用，社区支持完善 |
| **事务支持** | 完整的 ACID 支持，保证数据一致性 |
| **性能优异** | 读写性能良好，适合高并发场景 |
| **运维简单** | 部署和维护相对简单 |

### 为什么使用 Redis

| 用途 | 说明 |
|------|------|
| **L2 缓存** | 缓存热点数据，减少数据库查询 |
| **会话存储** | 存储会话状态，支持快速访问 |
| **分布式锁** | 保证并发安全 |
| **过期管理** | 自动过期清理，简化 TTL 管理 |

---

## 设计原则

### 1. LangChain 深度集成

- **状态感知**：从 LangChain 状态自动提取上下文（task_id、user_id、session_id）
- **节点混入**：通过 `LangGraphAgentMixin` 提供标准集成模式
- **零侵入性**：不修改 LangGraph 的状态传递机制

### 2. 优雅降级

- **可选依赖**：记忆系统不可用时，Agent 仍可正常执行任务
- **错误隔离**：记忆错误不影响主业务流程
- **零配置运行**：提供默认配置，开箱即用

### 3. 简化使用

- **统一入口**：`initialize_memory_system()` 一次性初始化所有组件
- **便捷接口**：Agent 只需调用 `remember()`、`recall()` 等简单方法
- **自动推断**：根据 key 自动推断记忆作用域

### 4. 数据持久化

- **MySQL 存储**：所有重要数据持久化到 MySQL
- **Redis 缓存**：热点数据缓存到 Redis，提升性能
- **事务保证**：支持数据库事务和回滚

### 5. 关注点分离

- **服务独立**：每个服务独立管理自己的业务逻辑
- **模块解耦**：各层之间通过接口交互，降低耦合
- **可测试性**：每个组件都可以独立测试

---

## 数据流

### 记忆存储流程

```
Agent 执行节点
    │
    ├─→ 调用 _get_memory(state)
    │       │
    │       ├─→ 提取 task_id, user_id, session_id
    │       └─→ 创建 StateBoundMemoryManager
    │
    ├─→ 调用 remember("key", "value")
    │       │
    │       ├─→ 推断作用域 (scope inference)
    │       ├─→ 添加标签 (agent_name, key)
    │       └─→ 存储到数据库 + Redis 缓存
    │               │
    │               ├─→ 写入 MySQL
    │               └─→ 写入 Redis (L2 缓存)
    │
    └─→ 返回成功/失败
```

### 记忆检索流程

```
Agent 调用 recall("key")
    │
    ├─→ 检查 Redis 缓存 (L2)
    │       │
    │       ├─→ 命中 → 返回缓存数据
    │       └─→ 未命中 → 继续下一步
    │
    ├─→ 查询 MySQL 数据库
    │       │
    │       ├─→ 找到数据 → 更新 Redis 缓存 → 返回数据
    │       └─→ 未找到 → 返回 None
    │
    └─→ 返回结果
```

### 工作空间共享流程

```
Agent A 调用 share_data(data_type, data_key, data_content)
    │
    ├─→ 创建共享记录
    │       │
    │       ├─→ 写入 MySQL shared_workspace_memory 表
    │       ├─→ 设置 TTL (过期时间)
    │       └─→ 记录 source_agent 和 target_agents
    │
    ├─→ 写入 Redis 缓存
    │
    └─→ 返回 data_id

Agent B 调用 get_shared_data(data_type, data_key)
    │
    ├─→ 检查 Redis 缓存
    │       │
    │       ├─→ 命中 → 检查访问权限 → 返回数据
    │       └─→ 未命中 → 继续下一步
    │
    ├─→ 查询 MySQL
    │       │
    │       ├─→ 找到数据 → 检查是否过期 → 检查访问权限
    │       ├─→ 更新 accessed_count 和 last_accessed_at
    │       └─→ 返回数据
    │
    └─→ 返回结果
```

---

## 组件交互

### 初始化流程

```python
# 1. 应用启动
from backend.agents.memory import initialize_memory_system

# 2. 初始化全局记忆系统
system = await initialize_memory_system()
    │
    ├─→ 加载配置 (MemoryConfig)
    ├─→ 创建 DatabaseManager
    ├─→ 创建 RedisCache
    ├─→ 初始化 UserPreferenceService
    ├─→ 初始化 DecisionService
    └─→ 初始化 WorkspaceService

# 3. 系统就绪
status = await system.health_check()
```

### Agent 执行流程

```python
# 1. Agent 节点被调用
class ResearchAgent(MemoryAwareAgent):
    async def run_node(self, state):
        # 2. 初始化记忆管理器
        self._get_memory(state)
            │
            ├─→ 提取上下文 (task_id, user_id, session_id)
            └─→ 创建 StateBoundMemoryManager

        # 3. 使用记忆
        cached = await self.recall("previous_research")
        if not cached:
            # 执行研究
            result = await self.do_research(state["query"])
            # 存储结果
            await self.remember("research_result", result)

        # 4. 共享数据
        await self.share_data(
            data_type="research_result",
            data_key="findings",
            data_content=result
        )

        # 5. 记录决策
        await self.record_decision(
            decision_type="search_method",
            selected_action="web_search",
            context={"query": state["query"]}
        )

        return state
```

---

## 扩展性设计

### 添加新服务

```python
# 1. 在 services/ 下创建新服务
class CustomService(BaseService):
    async def do_something(self):
        pass

# 2. 在 MemoryConfig 中添加配置
@dataclass
class MemoryConfig:
    enable_custom_service: bool = True

# 3. 在 MemorySystem 中初始化
async def initialize(self):
    if self.config.enable_custom_service:
        self._custom_service = CustomService(
            db_session=self._db.SessionLocal(),
            cache_client=self._cache
        )
```

### 添加新数据表

```python
# 1. 在 storage/models/ 下创建模型
class CustomModel(Base):
    __tablename__ = "custom_table"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # ... 其他字段

# 2. 创建数据库迁移脚本
# 3. 更新 database-schema.md 文档
```

---

**文档版本：** 2.0.0
**最后更新：** 2025-02-09
