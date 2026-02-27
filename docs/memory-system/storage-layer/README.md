# 存储层 (Storage Layer)

> **版本：** 5.1.0（极简架构）
> **代码量：** 560行

---

## 📖 什么是存储层？

存储层负责数据的持久化存储和缓存，为上层（Service层、Adapter层）提供统一的数据访问接口。

```
┌─────────────────────────────────────┐
│        业务层 (Service)              │
│   UserPreferenceService (358行)     │
└──────────────────┬──────────────────┘
                   ↓ 访问
┌─────────────────────────────────────┐
│      存储层 (Storage) ◄── 我们在这里   │
│  ┌────────────┬──────────────┐       │
│  │ Database   │ Redis Cache  │       │
│  │ (MySQL)    │ (缓存)        │       │
│  └────────────┴──────────────┘       │
└─────────────────────────────────────┘
```

---

## 🎯 核心价值

| 价值 | 说明 | 示例 |
|------|------|------|
| **数据持久化** | 永久存储用户数据 | MySQL数据库 |
| **性能优化** | 通过缓存减少数据库访问 | Redis缓存 |
| **数据一致性** | 统一的事务管理 | Session.commit() |
| **连接管理** | 数据库连接池、连接复用 | QueuePool |

---

## 📊 v5.1 极简架构

```
存储层 (560行)
├── database.py (215行)     # MySQL数据库管理
├── redis_cache.py (185行)    # Redis缓存管理
└── models/ (160行)           # 数据模型（文件夹形式）
    ├── __init__.py (60行)   # 模块导出
    ├── base.py (36行)        # BaseModel基类
    └── user_profile.py (123行) # UserProfile模型

v5.1 简化：
- ✅ 保留 models/ 文件夹 - 正在使用
- ❌ 删除 models.py - 旧版本，重复定义
- ✅ 只保留 UserProfile - 唯一使用的模型
```

---

## 🧩 核心组件

### 1. DatabaseManager (database.py)

**职责：**
- 管理数据库连接（单例模式）
- 提供连接池（QueuePool）
- 会话管理（SessionLocal）
- 健康检查

**详细说明：** [DatabaseManager详解](./database.md)

### 2. RedisCache (redis_cache.py)

**职责：**
- Redis连接管理
- 缓存读写（get/set/delete）
- JSON序列化支持
- 业务特定缓存方法

**详细说明：** [RedisCache详解](./redis_cache.md)

### 3. 数据模型 (models/)

**职责：**
- 定义数据库表结构
- 提供数据验证
- 业务逻辑封装

**组织方式：**
```
models/
├── __init__.py         # 模块导出
├── base.py              # BaseModel基类
└── user_profile.py      # UserProfile模型
```

**模型列表：**
- `BaseModel` - 基类（时间戳、to_dict接口）
- `UserProfile` - 用户配置

**详细说明：** [数据模型详解](./models.md)

---

## 🚀 快速开始

### 使用数据库

```python
from backend.memory.storage.database import get_db

# 使用上下文管理器
db = get_db()
with db.get_session() as session:
    profile = session.query(UserProfile).filter_by(
        user_id="user123"
    ).first()
    print(profile.to_dict())
```

### 使用Redis缓存

```python
from backend.memory.storage.redis_cache import RedisCache

# 初始化缓存
cache = RedisCache()

# 检查可用性
if cache.is_available():
    # 设置缓存
    await cache.set("key", "value", ttl=3600)
    # 获取缓存
    value = await cache.get("key")
```

### 在Service中使用

```python
class UserPreferenceService:
    def __init__(
        self,
        db_session: Optional[Session] = None,
        cache_client: Optional[RedisCache] = None
    ):
        self.db_session = db_session  # 注入数据库会话
        self.cache_client = cache_client  # 注入缓存客户端

    async def get_user_preferences(self, user_id: str):
        # 1. 先查缓存
        if self.cache_client:
            cached = await self.cache_client.get_user_preferences(user_id)
            if cached:
                return cached

        # 2. 查数据库
        if self.db_session:
            profile = self.db_session.query(UserProfile).filter_by(
                user_id=user_id
            ).first()

            if profile:
                # 3. 写缓存
                if self.cache_client:
                    await self.cache_client.set_user_preferences(
                        user_id, profile.to_dict()
                    )
                return profile.to_dict()

        return {}
```

---

## 📚 文档导航

| 文档 | 说明 | 面向 |
|------|------|------|
| [开发者指南](./开发者指南.md) | 为什么需要存储层、设计原则、实现指南 | 存储层开发者 |
| [DatabaseManager详解](./database.md) | 数据库管理器完整说明 | 数据库开发者 |
| [RedisCache详解](./redis_cache.md) | Redis缓存完整说明 | 缓存开发者 |
| [数据模型详解](./models.md) | BaseModel和UserProfile说明 | 模型开发者 |

---

## 🔧 配置说明

### 数据库配置

```bash
# MySQL（推荐）
export DATABASE_URL="mysql+pymysql://root:password@localhost:3306/multiagent_ppt"

# PostgreSQL
export DATABASE_URL="postgresql://user:password@localhost:5432/multiagent_ppt"

# SQLite（开发用）
export DATABASE_URL="sqlite:///./memory.db"
```

### Redis配置

```bash
# Redis
export REDIS_URL="redis://localhost:6379/0"

# 带密码的Redis
export REDIS_URL="redis://:password@localhost:6379/0"
```

---

## 🛠️ 维护命令

### 数据库初始化

```bash
# 初始化数据库
python backend/memory/storage/database.py --init

# 删除并重建（⚠️ 警告：会删除所有数据）
python backend/memory/storage/database.py --init --drop

# 健康检查
python backend/memory/storage/database.py --health
```

---

## 🔗 相关文档

### 上层文档
- [业务层详解](../service-layer/) - Service如何使用存储层

### 下层文档
- [MySQL文档](https://dev.mysql.com/doc/) - MySQL官方文档
- [Redis文档](https://redis.io/docs/) - Redis官方文档
- [SQLAlchemy文档](https://docs.sqlalchemy.org/) - ORM框架文档

---

**文档版本：** 5.1.0
**最后更新：** 2026-02-10
