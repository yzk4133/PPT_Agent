# UserPreferenceService 详解

> **版本：** 5.0.0
> **位置：** `backend/memory/services/user_preference_service.py`
> **代码行数：** 341行

---

## 📋 目录

- [职责](#职责)
- [数据模型](#数据模型)
- [核心方法](#核心方法)
- [方法列表](#方法列表)
- [使用示例](#使用示例)

---

## 🎯 职责

UserPreferenceService负责：

1. **用户偏好管理** - 语言、幻灯片数、语调、模板类型等
2. **使用统计** - 会话数、生成次数
3. **满意度追踪** - 记录和计算用户满意度评分
4. **缓存优化** - Redis缓存提升性能

---

## 📊 数据模型

### UserProfile Model

```python
class UserProfile(Base):
    """
    用户偏好数据模型

    数据库表: user_profiles
    """
    __tablename__ = "user_profiles"

    # 主键
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), unique=True, nullable=False, index=True)

    # 偏好设置 (JSON格式)
    preferences = Column(JSON, default={})

    # 使用统计
    session_count = Column(Integer, default=0)  # 会话数
    generation_count = Column(Integer, default=0)  # 生成次数

    # 满意度追踪
    satisfaction_scores = Column(JSON, default=[])  # 历史评分
    avg_satisfaction = Column(Float, default=0.0)  # 平均满意度

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 支持的偏好字段

```python
{
    "language": "ZH-CN",           # 主要语言
    "default_slides": 15,          # 默认幻灯片数 (5-30)
    "tone": "professional",        # 内容语调 (professional/casual/creative)
    "template_type": "business",   # 模板类型 (business/academic/creative)
    "auto_save": true,             # 是否自动保存
}
```

---

## 🔧 核心方法

### 1. get_user_preferences()

获取用户偏好，支持缓存和自动创建

```python
async def get_user_preferences(
    self,
    user_id: str,
    create_if_not_exists: bool = False
) -> Dict[str, Any]:
    """
    获取用户偏好

    Args:
        user_id: 用户ID
        create_if_not_exists: 如果不存在是否创建

    Returns:
        用户偏好字典
    """
```

**数据流程：**
```
Agent调用
  ↓
检查缓存
  ├─ 缓存命中 → 直接返回（1-5ms）
  └─ 缓存未命中 ↓
查询数据库
  ├─ 用户存在 → 返回数据 + 更新缓存（10-50ms）
  └─ 用户不存在 ↓
    ├─ create_if_not_exists=True → 创建用户 + 返回（50-100ms）
    └─ create_if_not_exists=False → 返回空字典（10ms）
```

### 2. update_preferences()

更新用户偏好，自动处理缓存一致性

```python
async def update_preferences(
    self,
    user_id: str,
    preferences: Dict[str, Any]
) -> bool:
    """
    更新用户偏好

    Args:
        user_id: 用户ID
        preferences: 偏好更新

    Returns:
        是否成功
    """
```

**数据一致性保证：**
```python
# 更新后立即使缓存失效
await service.update_preferences("user123", {"language": "EN-US"})
# → 缓存已删除 → 下次读取会从数据库获取最新数据
```

### 3. update_satisfaction_score()

记录用户满意度评分，自动计算移动平均

```python
async def update_satisfaction_score(
    self,
    user_id: str,
    score: float
) -> bool:
    """
    更新满意度评分

    Args:
        user_id: 用户ID
        score: 满意度评分 (0.0-1.0)

    Returns:
        是否成功
    """
```

**评分算法：**
```python
# 使用移动平均计算满意度
avg_satisfaction = sum(s["score"] for s in history) / len(history)
```

---

## 📋 方法列表

### 偏好管理

| 方法 | 功能 | 使用场景 | 返回值 |
|------|------|----------|--------|
| `get_user_preferences()` | 获取用户偏好 | Agent需要个性化时 | `Dict[str, Any]` |
| `update_preferences()` | 更新用户偏好 | 用户修改设置时 | `bool` |
| `reset_preferences()` | 重置用户偏好 | 用户恢复默认设置 | `bool` |
| `get_preference()` | 获取单个偏好 | 快速查询某个字段 | `Any` |
| `set_preference()` | 设置单个偏好 | 快速设置某个字段 | `bool` |
| `get_all_preferences()` | 获取所有偏好 | 同`get_user_preferences()` | `Dict[str, Any]` |
| `get_preferences_batch()` | 批量获取偏好 | 批量操作 | `Dict[str, Dict]` |

### 统计管理

| 方法 | 功能 | 使用场景 | 返回值 |
|------|------|----------|--------|
| `increment_session_count()` | 增加会话计数 | 会话开始 | `bool` |
| `increment_generation_count()` | 增加生成计数 | PPT生成完成 | `bool` |
| `update_satisfaction_score()` | 更新满意度评分 | 用户评分 | `bool` |

---

## 💡 使用示例

### 基础用法

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
print(preferences)
# {
#     "language": "ZH-CN",
#     "default_slides": 15,
#     "tone": "professional",
#     "template_type": "business"
# }
```

### 更新偏好

```python
# 更新单个偏好
await service.set_preference("user123", "language", "EN-US")

# 更新多个偏好
await service.update_preferences("user123", {
    "language": "EN-US",
    "tone": "casual",
    "default_slides": 20
})
```

### 记录统计

```python
# 会话开始
await service.increment_session_count("user123")

# PPT生成完成
await service.increment_generation_count("user123")

# 用户评分
await service.update_satisfaction_score("user123", 0.8)
```

### 在Agent中使用

```python
class RequirementParserAgent(BaseAgent):
    async def run_node(self, state):
        if self.has_memory:
            self._get_memory(state)

            # 获取用户偏好
            prefs = await self._user_pref_service.get_user_preferences(
                state["user_id"]
            )

            # 应用偏好到需求（个性化）
            requirement = await self.apply_user_preferences_to_requirement(
                state["user_input"]
            )

            # 解析需求
            parsed = await self._parse_requirements(requirement)

            return {**state, "parsed_requirements": parsed}
```

### 批量操作

```python
# 批量获取多个用户的偏好
user_ids = ["user1", "user2", "user3"]
preferences_map = await service.get_preferences_batch(user_ids)

print(preferences_map)
# {
#     "user1": {"language": "ZH-CN", ...},
#     "user2": {"language": "EN-US", ...},
#     "user3": {"language": "ZH-CN", ...}
# }
```

---

## 🎯 最佳实践

### 1. 总是检查返回值

```python
# ✅ 好的做法
success = await service.update_preferences(user_id, prefs)
if not success:
    logger.error("Failed to update preferences")
    # 处理失败情况

# ❌ 不好的做法
await service.update_preferences(user_id, prefs)
# 没有检查是否成功
```

### 2. 使用缓存提升性能

```python
# ✅ 好的做法
service = UserPreferenceService(
    db_session=session,
    cache_client=redis_client,
    enable_cache=True  # 启用缓存
)

# ❌ 不好的做法
service = UserPreferenceService(
    db_session=session,
    cache_client=redis_client,
    enable_cache=False  # 禁用缓存，性能差
)
```

### 3. 优雅处理不存在的用户

```python
# ✅ 好的做法
prefs = await service.get_user_preferences(
    user_id,
    create_if_not_exists=True  # 自动创建
)

# ❌ 不好的做法
prefs = await service.get_user_preferences(
    user_id,
    create_if_not_exists=False  # 返回空字典，Agent需要额外处理
)
```

---

## 🔗 相关文档

- [BaseService详解](./base-service.md) - UserPreferenceService的父类
- [返回主页](../README.md)
