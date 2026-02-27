# 数据模型详解

> **版本：** 5.1.0（极简架构）
> **位置：** `backend/memory/storage/models/`
> **代码量：** 161行

---

## 📋 目录

- [模型概述](#模型概述)
- [BaseModel基类](#basemodel基类)
- [UserProfile模型](#userprofile模型)
- [使用示例](#使用示例)

---

## 🎯 模型概述

存储层只包含2个数据模型：

| 模型 | 表名 | 职责 | 使用频率 |
|------|------|------|----------|
| **BaseModel** | - | 模型基类（时间戳） | - |
| **UserProfile** | user_profiles | 用户偏好配置 | ⭐⭐⭐ 高 |

**v5.1 简化：**
- ✅ 保留 BaseModel - 模型基类
- ✅ 保留 UserProfile - 被UserPreferenceService使用
- ❌ 删除 Session - 未使用
- ❌ 删除 ConversationHistory - 未使用
- ❌ 删除 AgentDecision - 未使用
- ❌ 删除 ToolFeedback - 未使用
- ❌ 删除 VectorMemory - 未使用
- ❌ 删除 SharedWorkspaceMemory - 未使用

**代码统计：**
```
models/ (161行)
├── base.py (37行) - BaseModel基类
└── user_profile.py (124行) - 用户配置
```

---

## 🏗️ BaseModel基类

**位置：** `backend/memory/storage/models/base.py` (37行)

### 代码结构

```python
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BaseModel(Base):
    """
    模型基类

    提供通用的时间戳字段和转换方法
    """
    __abstract__ = True

    # 通用时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        子类必须实现此方法
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.to_dict() must be implemented"
        )
```

### BaseModel提供什么？

1. **统一的时间戳** - created_at, updated_at
2. **to_dict()接口** - 子类必须实现
3. **继承Base** - SQLAlchemy声明式基类

---

## 🧩 UserProfile模型

**位置：** `backend/memory/storage/models/user_profile.py` (124行)

### 职责

- 用户偏好设置（语言、幻灯片数、语调等）
- 使用统计（会话数、生成次数）
- 满意度评分

### 表结构

```python
class UserProfile(BaseModel):
    """
    用户配置表

    存储用户的使用偏好、使用统计和满意度评分
    """
    __tablename__ = "user_profiles"

    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), unique=True, nullable=False, index=True)

    # 用户偏好（使用Text存储JSON，兼容MySQL和PostgreSQL）
    preferences = Column(Text, nullable=False, default="{}")

    # 使用统计
    total_sessions = Column(Integer, default=0)
    successful_generations = Column(Integer, default=0)

    # 满意度评分（基于修改次数反推）
    avg_satisfaction_score = Column(Float, default=0.0)

    # 乐观锁版本号
    version = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        Index("idx_user_satisfaction", "avg_satisfaction_score"),
    )
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

### 核心方法

#### to_dict() - 转换为字典

```python
def to_dict(self) -> Dict[str, Any]:
    """转换为字典"""
    import json
    preferences = json.loads(self.preferences) if self.preferences else {}

    return {
        "id": str(self.id),
        "user_id": self.user_id,
        "preferences": preferences,
        "total_sessions": self.total_sessions,
        "successful_generations": self.successful_generations,
        "avg_satisfaction_score": self.avg_satisfaction_score,
        "created_at": self.created_at.isoformat(),
        "updated_at": self.updated_at.isoformat(),
        "version": self.version,
    }
```

#### get_preference() - 获取单个偏好

```python
def get_preference(self, key: str, default: Any = None) -> Any:
    """
    获取单个偏好设置

    Args:
        key: 偏好键
        default: 默认值

    Returns:
        偏好值或默认值
    """
    import json
    prefs = json.loads(self.preferences) if self.preferences else {}
    return prefs.get(key, default)
```

#### set_preference() - 设置单个偏好

```python
def set_preference(self, key: str, value: Any) -> None:
    """
    设置单个偏好

    Args:
        key: 偏好键
        value: 偏好值
    """
    import json
    prefs = json.loads(self.preferences) if self.preferences else {}
    prefs[key] = value
    self.preferences = json.dumps(prefs, ensure_ascii=False)
```

#### increment_session_count() - 增加会话计数

```python
def increment_session_count(self) -> int:
    """增加会话计数"""
    self.total_sessions += 1
    return self.total_sessions
```

#### increment_generation_count() - 增加生成计数

```python
def increment_generation_count(self) -> int:
    """增加生成计数"""
    self.successful_generations += 1
    return self.successful_generations
```

#### update_satisfaction_score() - 更新满意度评分

```python
def update_satisfaction_score(self, score: float) -> None:
    """
    更新满意度评分（使用移动平均）

    Args:
        score: 新的满意度评分 (0.0-1.0)
    """
    if self.avg_satisfaction_score == 0.0:
        self.avg_satisfaction_score = score
    else:
        # 简单的移动平均
        alpha = 0.3  # 平滑因子
        self.avg_satisfaction_score = (
            alpha * score + (1 - alpha) * self.avg_satisfaction_score
        )
```

---

## 💡 使用示例

### 创建记录

```python
from backend.memory.storage.models import UserProfile
from backend.memory.storage.database import get_db

db = get_db()

with db.get_session() as session:
    # 创建新用户配置
    profile = UserProfile(user_id="user123")
    profile.set_preference("language", "ZH-CN")
    profile.set_preference("default_slides", 15)

    session.add(profile)
    # 自动提交
```

### 查询记录

```python
with db.get_session() as session:
    # 查询单条记录
    profile = session.query(UserProfile).filter_by(
        user_id="user123"
    ).first()

    if profile:
        print(profile.to_dict())
        print(profile.get_preference("language"))

    # 查询多条记录
    profiles = session.query(UserProfile).filter(
        UserProfile.total_sessions >= 10
    ).all()

    # 排序
    profiles = session.query(UserProfile).order_by(
        UserProfile.created_at.desc()
    ).limit(10).all()
```

### 更新记录

```python
with db.get_session() as session:
    profile = session.query(UserProfile).filter_by(
        user_id="user123"
    ).first()

    if profile:
        # 方式1: 更新单个偏好
        profile.set_preference("language", "EN-US")

        # 方式2: 增加统计
        profile.increment_session_count()
        profile.increment_generation_count()

        # 方式3: 更新满意度
        profile.update_satisfaction_score(0.8)

        # 自动提交
```

### 在Service中使用

```python
class UserPreferenceService:
    def __init__(self, db_session, cache_client):
        self.db_session = db_session
        self.cache_client = cache_client

    async def get_user_preferences(self, user_id: str):
        # 查数据库
        profile = self._get_profile(user_id)

        if not profile:
            # 创建新用户
            profile = UserProfile(user_id=user_id)
            self.db_session.add(profile)
            self.db_session.commit()
            self.db_session.refresh(profile)

        if profile:
            data = profile.to_dict()

            # 写缓存
            if self.enable_cache:
                await self.cache_client.set_user_preferences(
                    user_id, data
                )

            return data

        return {}
```

---

## 📐 模型设计规范

### 1. 主键设计

```python
# ✅ 好的设计 - 使用UUID
id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

# ❌ 不好的设计 - 使用自增ID（不利于分布式）
id = Column(Integer, primary_key=True, autoincrement=True)
```

### 2. 业务字段索引

```python
# ✅ 好的设计 - 业务字段加索引
user_id = Column(String(255), unique=True, nullable=False, index=True)

# ❌ 不好的设计 - 没有索引
user_id = Column(String(255))  # 查询慢
```

### 3. JSON字段处理

```python
# ✅ 好的设计 - 用Text存储JSON（兼容MySQL）
preferences = Column(Text, default="{}")

def get_preference(self, key: str):
    import json
    prefs = json.loads(self.preferences) if self.preferences else {}
    return prefs.get(key)

# ❌ 不好的设计 - 直接用JSON类型（MySQL兼容性差）
preferences = Column(JSON)  # PostgreSQL专用
```

### 4. 时间戳字段

```python
# ✅ 好的设计 - 继承BaseModel
class UserProfile(BaseModel):
    # 自动有 created_at, updated_at
    pass

# ❌ 不好的设计 - 每个模型都写一遍
class UserProfile(BaseModel):
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 5. 乐观锁

```python
# ✅ 好的设计 - 使用版本号实现乐观锁
version = Column(Integer, nullable=False, default=1)

def increment_version(self):
    self.version += 1

# 更新时检查版本
profile = session.query(UserProfile).filter_by(
    user_id="user123",
    version=1  # 只更新版本为1的记录
).first()
```

---

## 🔗 相关文档

- [开发者指南](./开发者指南.md) - 如何编写数据模型
- [DatabaseManager详解](./database.md) - 数据库管理器
- [返回主页](./README.md)
