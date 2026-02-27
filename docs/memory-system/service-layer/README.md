# 业务层 (Service Layer)

> **版本：** 5.1.0（极简架构）
> **代码量：** 358行

---

## 📖 什么是业务层？

业务层是连接应用层和存储层的关键桥梁，提供核心业务逻辑。

```
┌─────────────────────────────────────┐
│        应用层 (Application)          │
│     Agent: RequirementParser        │
└──────────────────┬──────────────────┘
                   ↓ 调用
┌─────────────────────────────────────┐
│      业务层 (Service) ◄── 我们在这里   │
│   UserPreferenceService (358行)     │
└──────────────────┬──────────────────┘
                   ↓ 访问
┌─────────────────────────────────────┐
│       存储层 (Storage)               │
│  Database (MySQL) + Cache (Redis)   │
└─────────────────────────────────────┘
```

---

## 🎯 核心价值

| 价值 | 说明 |
|------|------|
| **封装复杂性** | 隐藏数据库操作、缓存逻辑 |
| **代码复用** | 避免在多个Agent中重复相同逻辑 |
| **数据一致性** | 统一处理事务、缓存同步 |
| **易于测试** | 业务逻辑独立，便于单元测试 |
| **易于维护** | 修改业务逻辑只需改Service |

---

## 📊 v5.1 极简架构

```
业务层 (358行)
└── UserPreferenceService (358行) - 用户偏好管理

已删除:
❌ BaseService (36行) - 只有一个子类，继承价值不大
❌ DecisionService (334行) - 过度设计，实际未使用
❌ WorkspaceService (598行) - 功能与LangGraph State重复

代码减少: 83% (从2080行 → 358行)
```

---

## 🧩 核心组件

### UserPreferenceService (358行)

**位置：** `backend/memory/services/user_preference_service.py`

**职责：**
- 管理用户偏好设置（语言、幻灯片数、语调等）
- 跟踪用户使用统计（会话数、生成次数）
- 记录用户满意度评分
- 提供缓存优化

**核心方法：**
- `get_user_preferences()` - 获取用户偏好
- `update_preferences()` - 更新用户偏好
- `update_satisfaction_score()` - 更新满意度评分

**详细说明：** [UserPreferenceService详解](./user-preference-service.md)

---

## 🚀 快速开始

### 使用UserPreferenceService

```python
from backend.memory.services import UserPreferenceService

# 初始化服务
service = UserPreferenceService(
    db_session=session,
    cache_client=redis_client,
    enable_cache=True
)

# 获取用户偏好
preferences = await service.get_user_preferences("user123")
# {
#     "language": "ZH-CN",
#     "default_slides": 15,
#     "tone": "professional",
#     ...
# }

# 更新用户偏好
await service.update_preferences("user123", {
    "language": "EN-US",
    "tone": "casual"
})

# 记录满意度评分
await service.update_satisfaction_score("user123", 0.8)
```

### 在Agent中使用

```python
class RequirementParserAgent(BaseAgent):
    async def run_node(self, state):
        if self.has_memory:
            self._get_memory(state)

            # 获取用户偏好
            prefs = await self.get_user_preferences()

            # 应用偏好到需求（个性化）
            requirement = await self.apply_user_preferences_to_requirement(
                state["user_input"]
            )

            # 解析需求
            parsed = await self._parse_requirements(requirement)

            return {**state, "parsed_requirements": parsed}
```

---

## 📚 文档导航

| 文档 | 说明 | 面向 |
|------|------|------|
| [开发者指南](./开发者指南.md) | 设计原则、编码规范、实现指南 | Service开发者 |
| [UserPreferenceService详解](./user-preference-service.md) | API文档、使用示例 | 所有开发者 |

---

## 📈 架构演进

```
v1.0 (2024-12-01): 2080行
├── BaseService
├── UserPreferenceService
├── DecisionService
├── WorkspaceService
└── ... 其他6个Service

v5.0 (2026-02-10): 377行 (-82%)
├── BaseService (36行)
└── UserPreferenceService (341行)

v5.1 (2026-02-10): 358行 (-83%)
└── UserPreferenceService (358行) - 独立存在
```

---

## 🔗 相关文档

### 上层文档
- [适配层详解](../adapter-layer/) - 如何使用Service
- [应用层详解](../04-application/) - Agent如何调用Service

### 下层文档
- [存储层详解](../03-architecture/) - 数据库和缓存设计

---

**文档版本：** 5.1.0
**最后更新：** 2026-02-10
