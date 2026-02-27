# DatabaseManager 详解

> **版本：** 5.0.0
> **位置：** `backend/memory/storage/database.py`
> **代码行数：** 216行

---

## 📋 目录

- [职责](#职责)
- [架构设计](#架构设计)
- [核心方法](#核心方法)
- [使用示例](#使用示例)
- [最佳实践](#最佳实践)

---

## 🎯 职责

DatabaseManager负责：

1. **数据库连接管理** - 单例模式，全局唯一实例
2. **连接池管理** - QueuePool，自动复用连接
3. **会话管理** - SessionLocal，创建数据库会话
4. **健康检查** - 检测数据库可用性
5. **表初始化** - 创建/删除数据库表

---

## 🏗️ 架构设计

### 单例模式

```python
class DatabaseManager:
    """数据库管理器 - 单例模式"""

    _instance: Optional["DatabaseManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return  # 避免重复初始化
        # 初始化逻辑...
        self._initialized = True
```

**为什么用单例？**
- ✅ 全局共享一个连接池
- ✅ 避免创建多个连接池浪费资源
- ✅ 统一管理数据库配置

### 连接池配置

```python
# MySQL配置
engine_kwargs = {
    "poolclass": QueuePool,    # 连接池
    "pool_size": 10,           # 池大小
    "max_overflow": 20,        # 最大溢出连接数
    "pool_recycle": 3600,      # 1小时回收连接
    "pool_pre_ping": True,     # 连接前ping检查
    "echo": False,             # 不打印SQL
}
```

**参数说明：**
- `pool_size=10` - 常驻10个连接
- `max_overflow=20` - 最多额外创建20个连接（总计30个）
- `pool_recycle=3600` - 1小时后回收连接（避免MySQL超时）
- `pool_pre_ping=True` - 使用前检查连接可用性

### 多数据库支持

```python
if database_url.startswith("mysql"):
    # MySQL配置
    engine_kwargs.update({
        "connect_args": {
            "charset": "utf8mb4",  # 支持emoji和中文
            "autocommit": False,
        }
    })
elif database_url.startswith("postgresql"):
    # PostgreSQL配置
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
    })
elif database_url.startswith("sqlite"):
    # SQLite配置（开发用）
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
        "poolclass": NullPool,
    })
```

---

## 🔧 核心方法

### 1. `__init__()` - 初始化

```python
def __init__(self):
    if self._initialized:
        return

    # 1. 获取数据库URL
    self.database_url = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/multiagent_ppt"
    )

    # 2. 创建引擎
    self.engine = create_engine(self.database_url, **engine_kwargs)

    # 3. 创建会话工厂
    self.SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=self.engine
    )

    self._initialized = True
```

### 2. `init_db()` - 初始化表

```python
def init_db(self, drop_existing: bool = False):
    """初始化数据库表"""
    try:
        if drop_existing:
            logger.warning("Dropping all existing tables...")
            Base.metadata.drop_all(bind=self.engine)

        # 创建所有表
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")

        # 创建扩展（仅PostgreSQL）
        if not self.database_url.startswith("mysql"):
            self._create_vector_extension()

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
```

**使用示例：**
```python
# 初始化数据库
db = get_db()
db.init_db()

# 删除并重建（⚠️ 警告：会删除所有数据）
db.init_db(drop_existing=True)
```

### 3. `get_session()` - 获取会话（上下文管理器）

```python
@contextmanager
def get_session(self):
    """获取数据库会话（上下文管理器）"""
    session = self.SessionLocal()
    try:
        yield session
        session.commit()  # 自动提交
    except Exception as e:
        session.rollback()  # 自动回滚
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()  # 自动关闭
```

**使用示例：**
```python
db = get_db()

# 方式1: 使用上下文管理器（推荐）
with db.get_session() as session:
    user = session.query(UserProfile).filter_by(user_id="user123").first()
    user.preferences = '{"language": "EN-US"}'
    # 自动提交

# 方式2: 手动管理
session = db.SessionLocal()
try:
    user = session.query(UserProfile).first()
    session.commit()
finally:
    session.close()
```

### 4. `health_check()` - 健康检查

```python
def health_check(self) -> bool:
    """健康检查"""
    try:
        with self.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
```

**使用示例：**
```python
db = get_db()

if db.health_check():
    print("✅ Database is healthy")
else:
    print("❌ Database is down")
```

---

## 💡 使用示例

### 基础查询

```python
from backend.memory.storage.database import get_db
from backend.memory.storage.models import UserProfile

db = get_db()

with db.get_session() as session:
    # 1. 查询单条记录
    profile = session.query(UserProfile).filter_by(
        user_id="user123"
    ).first()

    # 2. 查询多条记录
    profiles = session.query(UserProfile).filter(
        UserProfile.total_sessions >= 10
    ).all()

    # 3. 排序和限制
    profiles = session.query(UserProfile).order_by(
        UserProfile.created_at.desc()
    ).limit(10).all()

    # 4. 统计
    count = session.query(UserProfile).count()
```

### 创建数据

```python
with db.get_session() as session:
    # 创建新记录
    profile = UserProfile(
        user_id="user123",
        preferences='{"language": "ZH-CN"}',
        total_sessions=0
    )
    session.add(profile)
    # 自动提交
```

### 更新数据

```python
with db.get_session() as session:
    # 方式1: 先查询再更新
    profile = session.query(UserProfile).filter_by(user_id="user123").first()
    if profile:
        profile.preferences = '{"language": "EN-US"}'
        # 自动提交

    # 方式2: 批量更新
    session.query(UserProfile).filter(
        UserProfile.total_sessions == 0
    ).update({"total_sessions": 1}, synchronize_session=False)
    # 自动提交
```

### 删除数据

```python
with db.get_session() as session:
    # 方式1: 先查询再删除
    profile = session.query(UserProfile).filter_by(user_id="user123").first()
    if profile:
        session.delete(profile)
        # 自动提交

    # 方式2: 批量删除
    session.query(UserProfile).filter(
        UserProfile.created_at < datetime(2020, 1, 1)
    ).delete(synchronize_session=False)
    # 自动提交
```

### 事务管理

```python
with db.get_session() as session:
    try:
        # 多个操作在一个事务中
        profile1 = session.query(UserProfile).filter_by(user_id="user1").first()
        profile1.total_sessions += 1

        profile2 = session.query(UserProfile).filter_by(user_id="user2").first()
        profile2.total_sessions += 1

        # 一起提交
        # 自动提交（上下文管理器）
    except Exception as e:
        # 自动回滚（上下文管理器）
        print(f"Error: {e}")
```

---

## ✅ 最佳实践

### 1. 总是使用上下文管理器

```python
# ✅ 好的做法
with db.get_session() as session:
    user = session.query(UserProfile).first()
    # 自动关闭连接

# ❌ 不好的做法
session = db.SessionLocal()
user = session.query(UserProfile).first()
# 忘记关闭连接！
```

### 2. 异常处理

```python
# ✅ 好的做法
try:
    with db.get_session() as session:
        user = session.query(UserProfile).first()
except Exception as e:
    logger.error(f"Database error: {e}")
    # 上下文管理器自动回滚

# ❌ 不好的做法
with db.get_session() as session:
    user = session.query(UserProfile).first()
    # 没有异常处理
```

### 3. 索引优化

```python
# ✅ 好的设计 - 业务字段加索引
class UserProfile(BaseModel):
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), index=True)

# ❌ 不好的设计 - 没有索引
class UserProfile(BaseModel):
    user_id = Column(String(255))  # 查询慢
```

### 4. 连接池配置

```python
# ✅ 好的配置
engine = create_engine(
    DATABASE_URL,
    pool_size=10,        # 根据并发量调整
    max_overflow=20,     # pool_size的2倍
    pool_recycle=3600,   # 小于MySQL超时时间
    pool_pre_ping=True   # 避免使用失效连接
)

# ❌ 不好的配置
engine = create_engine(
    DATABASE_URL,
    pool_size=100,       # 太大，浪费资源
    pool_recycle=28800,  # 太长（8小时），MySQL默认8小时超时
    pool_pre_ping=False  # 容易使用失效连接
)
```

### 5. JSON字段处理

```python
# ✅ 好的做法 - 用Text存储JSON（兼容MySQL）
class UserProfile(BaseModel):
    preferences = Column(Text, default="{}")

    def get_preference(self, key: str):
        import json
        prefs = json.loads(self.preferences) if self.preferences else {}
        return prefs.get(key)

# ❌ 不好的做法 - 直接用JSON类型（MySQL兼容性差）
class UserProfile(BaseModel):
    preferences = Column(JSON)  # PostgreSQL专用
```

---

## 🔧 维护命令

### 命令行工具

```bash
# 初始化数据库
python backend/memory/storage/database.py --init

# 删除并重建（⚠️ 会删除所有数据）
python backend/memory/storage/database.py --init --drop

# 健康检查
python backend/memory/storage/database.py --health
```

### 环境变量配置

```bash
# MySQL（推荐）
export DATABASE_URL="mysql+pymysql://root:password@localhost:3306/multiagent_ppt"

# PostgreSQL
export DATABASE_URL="postgresql://user:password@localhost:5432/multiagent_ppt"

# SQLite（开发用）
export DATABASE_URL="sqlite:///./memory.db"

# 打印SQL（调试）
export SQL_ECHO="true"
```

---

## 🔗 相关文档

- [开发者指南](./开发者指南.md) - 如何编写数据库代码
- [RedisCache详解](./redis_cache.md) - 缓存管理器
- [数据模型详解](./models.md) - 数据模型说明
- [返回主页](./README.md)
