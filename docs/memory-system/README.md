# MultiAgentPPT 记忆系统文档

> **版本：** 5.1.0（极简架构） | **数据库：** MySQL 5.7+ | **更新：** 2026-02-10

---

## 📖 文档导航

### 🚀 快速开始

| 文档 | 说明 | 时间 |
|------|------|------|
| [快速开始](./quick-start.md) | 5分钟上手指南 | 5分钟 |

### 📚 分层文档

| 层级 | 说明 | 文档 |
|------|------|------|
| **[架构层](./03-architecture/)** | 整体架构设计 | 四层架构、设计原则 |
| **[应用层](./04-application/)** | Agent如何使用记忆 | 5个Agent、使用示例 |
| **[适配层](./adapter-layer/)** | MemoryAwareAgent详解 | 接口、API参考 |
| **[服务层](./service-layer/)** | 业务逻辑层 | UserPreferenceService |
| **[存储层](./storage-layer/)** | 数据持久化 | Database、Redis、Models |

### 🔧 参考资料

| 文档 | 说明 |
|------|------|
| [配置指南](./reference/configuration.md) | 环境变量、功能开关 |
| [故障排除](./reference/troubleshooting.md) | 常见问题解决 |

---

## 🎯 系统概述

记忆系统为 MultiAgentPPT 提供**用户偏好管理**和**数据缓存**功能。

### 核心功能

| 功能 | 价值 |
|------|------|
| **用户个性化** | 记住用户偏好（语言、幻灯片数、语调等），改善体验 |
| **数据缓存** | 缓存LLM结果，节省50-80%成本，提升100倍速度 |
| **优雅降级** | 记忆不可用时系统仍可正常运行 |

### 技术栈

```
┌─────────────────────────────────────┐
│  应用层 Agent                        │
│  (RequirementParser, FrameworkDesigner, etc.) │
└──────────────────┬──────────────────┘
                   ↓ 继承
┌─────────────────────────────────────┐
│  MemoryAwareAgent (适配层)           │
│  - 用户偏好个性化                     │
│  - 数据缓存（可选）                   │
└──────────────────┬──────────────────┘
                   ↓ 调用
┌─────────────────────────────────────┐
│  UserPreferenceService (服务层)      │
│  - 偏好管理、统计追踪                 │
└──────────────────┬──────────────────┘
                   ↓ 存储
┌──────────────────┬─────────────────┐
│  MySQL (560行)   │  Redis (185行)  │
│  - 用户偏好       │  - L2 缓存      │
└──────────────────┴─────────────────┘
```

### v5.1 简化架构

**保留：**
- ✅ 用户偏好管理（UserPreferenceService）
- ✅ 数据缓存功能（可选）
- ✅ 优雅降级机制

**删除：**
- ❌ 决策追踪（DecisionService）- 过度设计
- ❌ 工作空间共享（WorkspaceService）- LangGraph State 足够
- ❌ 向量搜索 - 未使用

**代码精简：**
- Service层：从 2080行 → 358行（-83%）
- Storage层：从 1606行 → 560行（-65%）

---

## 🚀 快速开始

### 1. 环境配置

```bash
# .env 文件
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/multiagent_ppt
REDIS_URL=redis://localhost:6379/0

MEMORY_ENABLE_USER_PREFERENCES=true
MEMORY_ENABLE_CACHE=true
```

### 2. 初始化数据库

```bash
cd backend
python -m memory.storage.database --init
```

### 3. 启动记忆系统

```python
from backend.memory import initialize_memory_system

async def startup():
    system = await initialize_memory_system()
    print("✅ Memory system initialized")
```

### 4. 创建Agent

```python
from backend.memory import MemoryAwareAgent

class MyAgent(MemoryAwareAgent):
    async def run_node(self, state):
        self._get_memory(state)

        # 获取用户偏好
        prefs = await self.get_user_preferences()

        # 应用偏好
        personalized = await self.apply_user_preferences_to_requirement(
            state["user_input"]
        )

        return {**state, "requirements": personalized}
```

**详细指南：** [快速开始](./quick-start.md)

---

## 💡 主要功能

### 用户偏好个性化

```python
# 获取偏好
preferences = await self.get_user_preferences()
# {"language": "ZH-CN", "default_slides": 15, "tone": "professional"}

# 应用偏好到需求
personalized = await self.apply_user_preferences_to_requirement({
    "topic": "AI",
    "page_num": 10
})
# {"topic": "AI", "page_num": 15, "language": "ZH-CN"}
```

**详细文档：** [应用层 → 功能3](./04-application/)

### 数据缓存（可选）

```python
# 缓存结果
await self.remember("research_results", results, importance=0.8)

# 读取缓存
cached = await self.recall("research_results")
if cached:
    return cached  # 避免重复LLM调用
```

**详细文档：** [应用层 → 功能1](./04-application/)

---

## 📖 学习路径

### 新手入门

1. **快速开始** → [快速开始](./quick-start.md) - 5分钟上手
2. **应用层** → [04-application/](./04-application/) - 实际使用示例
3. **适配层** → [adapter-layer/](./adapter-layer/) - MemoryAwareAgent详解

### 深入理解

1. **架构层** → [03-architecture/](./03-architecture/) - 整体架构设计
2. **服务层** → [service-layer/](./service-layer/) - 业务逻辑实现
3. **存储层** → [storage-layer/](./storage-layer/) - 数据库和缓存

### 运维配置

1. [配置指南](./reference/configuration.md) - 环境配置详解
2. [故障排除](./reference/troubleshooting.md) - 常见问题解决

---

## 🔗 相关资源

- [项目主文档](../../../README.md)
- [后端架构](../../../docs/backend/)
- [记忆系统代码](../../../backend/memory/)

---

## 📊 文档统计

| 层级 | 文档数 | 说明 |
|------|--------|------|
| 架构层 | 4 | 整体架构、设计原则 |
| 应用层 | 2 | Agent使用示例 |
| 适配层 | 2 | MemoryAwareAgent详解 |
| 服务层 | 3 | 业务逻辑层 |
| 存储层 | 5 | 数据库、缓存、模型 |
| 参考资料 | 2 | 配置、故障排除 |
| **总计** | **18** | 完整文档系统 |

---

**文档版本：** 5.1.0
**最后更新：** 2026-02-10
**维护者：** MultiAgentPPT Team
