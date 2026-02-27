# 记忆系统架构设计

> **版本：** 5.1.0（极简架构）

---

## 📋 目录

- [四层架构](#四层架构)
- [设计原则](#设计原则)
- [数据流](#数据流)
- [架构演进](#架构演进)

---

## 🏗️ 四层架构

记忆系统采用清晰的分层架构，每层职责明确：

```
┌─────────────────────────────────────────────────────────────┐
│  应用层                                   │
│  实际使用记忆的Agent：                                         │
│  - RequirementParserAgent (需求解析)                         │
│  - FrameworkDesignerAgent (框架设计)                         │
│  - ResearchAgent (研究)                                     │
│  - ContentAgent (内容生成)                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ 继承/使用
┌──────────────────────────▼──────────────────────────────────┐
│  适配层                                │
│  - MemoryAwareAgent (315行) - 为Agent提供记忆功能            │
│  - UserPreferenceMixin (200行) - 用户偏好管理                │
└──────────────────────────┬──────────────────────────────────┘
                           │ 调用
┌──────────────────────────▼──────────────────────────────────┐
│  服务层                                 │
│  - UserPreferenceService (358行) - 用户偏好业务逻辑          │
└──────────────────────────┬──────────────────────────────────┘
                           │ 存储
┌──────────────────────────▼──────────────────────────────────┐
│  存储层                                  │
│  - DatabaseManager (215行) - MySQL数据库管理                │
│  - RedisCache (185行) - Redis缓存管理                       │
│  - Models (160行) - 数据模型（UserProfile）                  │
└─────────────────────────────────────────────────────────────┘
```

### 各层职责

| 层级 | 代码量 | 职责 | 主要文件 |
|------|--------|------|----------|
| **应用层** | - | 实际Agent使用记忆 | RequirementParserAgent等 |
| **适配层** | 515行 | 提供记忆接口 | MemoryAwareAgent, UserPreferenceMixin |
| **服务层** | 358行 | 业务逻辑 | UserPreferenceService |
| **存储层** | 560行 | 数据持久化 | DatabaseManager, RedisCache, Models |

---

## 🎯 设计原则

### 1. 单一职责原则

每层只负责自己的核心功能：

```
应用层：业务逻辑
  ↓ 只关注
适配层：接口适配
  ↓ 只调用
服务层：业务处理
  ↓ 只访问
存储层：数据存储
```

### 2. 依赖倒置原则

高层不直接依赖低层实现，通过接口解耦：

```python
# 适配层不直接访问数据库
# ❌ 错误
class MemoryAwareAgent:
    def __init__(self):
        self.db = create_engine(...)  # 直接依赖数据库

# ✅ 正确
class MemoryAwareAgent:
    def __init__(self, user_pref_service):
        self._user_pref_service = user_pref_service  # 依赖服务抽象
```

### 3. 开放封闭原则

对扩展开放，对修改关闭：

```python
# 添加新的Service不需要修改MemoryAwareAgent
class NewService:
    def do_something(self):
        pass

# Agent可以动态绑定新功能
class MyAgent(MemoryAwareAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.new_service = NewService()
```

### 4. 优雅降级原则

记忆不可用时系统仍能正常运行：

```python
async def get_user_preferences(self):
    if not self.has_memory:
        return {}  # 返回默认值，不抛异常

    try:
        return await self._user_pref_service.get_user_preferences()
    except Exception as e:
        logger.error(f"Memory error: {e}")
        return {}  # 降级处理
```

---

## 🌊 数据流

### 用户偏好数据流

```
用户请求
    ↓
应用层 Agent
    ↓ 调用 get_user_preferences()
适配层 MemoryAwareAgent
    ↓ 调用 get_user_preferences()
服务层 UserPreferenceService
    ↓ 1. 先查 Redis 缓存 (1-5ms)
    │   缓存命中 → 返回
    ↓ 2. 缓存未命中 → 查 MySQL (10-50ms)
存储层 DatabaseManager
    ↓ 返回结果
服务层 写入 Redis 缓存
    ↓ 返回给适配层
适配层 返回给应用层
```

**性能优化：**
- 缓存命中：1-5ms
- 缓存未命中：10-50ms + 写缓存1-5ms
- 缓存命中率：通常 > 80%

### Agent协作数据流

```
Agent A (RequirementParser)
    ↓ 通过 LangGraph State 传递
state["requirements"]
    ↓
Agent B (FrameworkDesigner)
    ↓ 读取 state["requirements"]
    ↓ 输出
state["framework"]
    ↓
Agent C (ContentAgent)
    ↓ 读取 state["requirements"]
    ↓ 读取 state["framework"]
```

**优势：**
- 轻量级：只传递必要数据
- 结构化：TypedDict类型安全
- 可追溯：LangGraph自动记录

---

## 📈 架构演进

### v1.0 → v5.0 简化历程

| 版本 | 特点 | 代码量 | 问题 |
|------|------|--------|------|
| **v1.0** | 初始版本，功能复杂 | ~3000行 | 过度设计 |
| **v2.0** | 添加工作空间共享 | ~3500行 | 更复杂 |
| **v3.0** | 添加决策追踪 | ~4000行 | 维护困难 |
| **v4.0** | 开始简化 | ~2500行 | 仍有冗余 |
| **v5.0** | 极简架构 | ~1500行 | ✅ 清晰高效 |

### v5.0 删除的功能

| 功能 | 原代码量 | 删除原因 |
|------|----------|----------|
| **DecisionService** | 334行 | 调试功能，非必需 |
| **WorkspaceService** | 598行 | LangGraph State足够 |
| **6个未使用的Model** | 694行 | 未实际使用 |
| **context_extractor** | 120行 | 功能重复 |
| **复杂工具函数** | 200行 | 过度设计 |

**总计删除：** ~1946行代码

### v5.0 保留的核心

| 功能 | 价值 | 代码量 |
|------|------|--------|
| **UserPreferenceService** | 用户个性化 | 358行 |
| **UserProfile模型** | 偏好存储 | 123行 |
| **DatabaseManager** | 数据库管理 | 215行 |
| **RedisCache** | 缓存管理 | 185行 |

**总计保留：** ~881行核心代码

---

## 🔗 相关文档

### 各层详解

- **应用层** → [04-application/](../04-application/) - Agent如何使用记忆
- **适配层** → [adapter-layer/](../adapter-layer/) - MemoryAwareAgent详解
- **服务层** → [service-layer/](../service-layer/) - 业务逻辑实现
- **存储层** → [storage-layer/](../storage-layer/) - 数据库和缓存

### 详细设计

- [架构详解](./architecture.md) - 完整架构图
- [层级详解](./layer-details.md) - 每层实现细节
- [模块说明](./modules.md) - 文件组织结构
- [数据库设计](./database-schema.md) - 表结构和索引

---

**文档版本：** 5.1.0
**最后更新：** 2026-02-10
