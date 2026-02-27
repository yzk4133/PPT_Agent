# 记忆系统故障排查指南

> **版本：** 5.1.0（极简架构）

---

## 📋 目录

- [常见问题](#常见问题)
- [数据库问题](#数据库问题)
- [Redis问题](#redis问题)
- [性能问题](#性能问题)
- [导入错误](#导入错误)

---

## 🔥 常见问题

### Q1: 导入错误 - `ImportError: cannot import name 'BaseService'`

**错误信息：**
```python
ImportError: cannot import name 'BaseService' from 'memory.services'
```

**原因：**
v5.0 删除了 `BaseService`，这是旧代码引用。

**解决方法：**
```python
# ❌ 旧代码
from memory.services import BaseService

# ✅ 新代码
from memory.services import UserPreferenceService
```

---

### Q2: 记忆功能不工作

**症状：**
```python
await self.remember("key", "value")  # 返回 False
cached = await self.recall("key")     # 返回 None
```

**可能原因：**

1. **记忆系统未初始化**
```python
# 应用启动时初始化
from backend.memory import initialize_memory_system
await initialize_memory_system()
```

2. **enable_memory=False**
```python
# 检查 Agent 配置
agent = MyAgent(enable_memory=True)  # 确保启用
```

3. **未调用 _get_memory()**
```python
async def run_node(self, state):
    self._get_memory(state)  # 必须先调用
    cached = await self.recall("key")
```

---

### Q3: 用户偏好不生效

**症状：**
```python
preferences = await self.get_user_preferences()  # 返回 {}
```

**可能原因：**

1. **数据库未连接**
```python
# 检查数据库
from backend.memory.storage import get_db
db = get_db()
print(db.health_check())  # 应该返回 True
```

2. **用户不存在**
```python
# 需要指定 create_if_not_exists=True
preferences = await self._user_pref_service.get_user_preferences(
    user_id="user123",
    create_if_not_exists=True  # 自动创建
)
```

---

## 💾 数据库问题

### Q4: 数据库连接失败

**错误信息：**
```
sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError) (2003, "Can't connect to MySQL server")
```

**解决方法：**

1. **检查数据库是否运行**
```bash
# MySQL
mysql -u root -p -e "SELECT 1"

# PostgreSQL
psql -U postgres -c "SELECT 1"
```

2. **检查环境变量**
```bash
echo $DATABASE_URL
# 应该类似：mysql+pymysql://root:password@localhost:3306/multiagent_ppt
```

3. **检查防火墙**
```bash
telnet localhost 3306  # MySQL
telnet localhost 5432  # PostgreSQL
```

4. **检查数据库权限**
```sql
-- MySQL
CREATE USER 'multiagent'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON multiagent_ppt.* TO 'multiagent'@'localhost';
FLUSH PRIVILEGES;
```

---

### Q5: 表不存在

**错误信息：**
```
sqlalchemy.exc.ProgrammingError: (pymysql.err.ProgrammingError) (1146, "Table 'multiagent_ppt.user_profiles' doesn't exist")
```

**解决方法：**

```bash
# 初始化数据库
cd backend
python -m memory.storage.database --init

# 或者手动创建表
python -c "
from backend.memory.storage import get_db
from backend.memory.storage.models import Base
db = get_db()
Base.metadata.create_all(db.engine)
print('Database initialized!')
"
```

---

### Q6: 连接池耗尽

**错误信息：**
```
sqlalchemy.exc.TimeoutError: QueuePool limit exceeded
```

**解决方法：**

```bash
# 增加连接池大小
MEMORY_CONNECTION_POOL_SIZE=20
MEMORY_MAX_OVERFLOW=40
```

或修改代码：
```python
# backend/memory/storage/database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,              # 增加连接池
    max_overflow=40,           # 增加溢出
    pool_timeout=30,           # 增加超时时间
)
```

---

## 🔴 Redis问题

### Q7: Redis连接失败

**错误信息：**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**解决方法：**

1. **检查Redis是否运行**
```bash
redis-cli ping
# 应该返回 PONG
```

2. **启动Redis**
```bash
# Linux/Mac
redis-server

# Windows
redis-server.exe
```

3. **检查环境变量**
```bash
echo $REDIS_URL
# 应该类似：redis://localhost:6379/0
```

---

### Q8: 缓存不生效

**症状：**
```python
# 设置缓存
await cache.set("key", "value", ttl=3600)  # 返回 False

# 获取缓存
value = await cache.get("key")  # 返回 None
```

**可能原因：**

1. **Redis未连接**
```python
from backend.memory.storage import RedisCache
cache = RedisCache()
print(cache.is_available())  # 应该返回 True
```

2. **检查Redis客户端**
```bash
redis-cli
> GET key
> SET key value
> GET key
```

3. **检查TTL**
```bash
redis-cli
> TTL key  # 查看剩余时间
```

---

## 🚀 性能问题

### Q9: 查询慢

**症状：**
```python
profile = db.query(UserProfile).filter_by(user_id="user123").first()
# 耗时 > 1秒
```

**解决方法：**

1. **添加索引**
```sql
CREATE INDEX idx_user_id ON user_profiles(user_id);
```

2. **使用缓存**
```python
# 先查缓存
cached = await cache.get_user_preferences(user_id)
if cached:
    return cached

# 再查数据库
profile = db.query(UserProfile).filter_by(user_id=user_id).first()
```

3. **启用连接池**
```bash
MEMORY_CONNECTION_POOL_SIZE=20
```

---

### Q10: 内存占用高

**症状：**
```
Redis占用内存过高
```

**解决方法：**

```bash
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru

# 检查内存使用
redis-cli INFO memory

# 清理过期key
redis-cli --scan --pattern "user_pref:*" | xargs redis-cli DEL
```

---

## 🔧 导入错误

### Q11: 循环导入

**错误信息：**
```
ImportError: cannot import name 'MemoryAwareAgent' from partially initialized module
```

**可能原因：**
v5.0 修复了循环导入问题，确保代码已更新。

**解决方法：**
```bash
# 更新代码
git pull origin main

# 检查导入路径
# ✅ 正确
from backend.memory import MemoryAwareAgent

# ❌ 错误（相对导入）
from ..memory import MemoryAwareAgent
```

---

### Q12: 模块未找到

**错误信息：**
```
ModuleNotFoundError: No module named 'memory'
```

**解决方法：**

```bash
# 确保在 backend 目录下
cd backend

# 添加到 PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 或者使用绝对导入
from backend.memory import MemoryAwareAgent
```

---

## 📊 调试技巧

### 启用详细日志

```python
import logging

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)

# 记忆系统日志
logger = logging.getLogger("backend.memory")
logger.setLevel(logging.DEBUG)
```

### 健康检查

```python
from backend.memory.core import get_global_memory_system

async def diagnose():
    system = get_global_memory_system()
    if not system:
        print("❌ Memory system not initialized")
        return

    status = await system.health_check()
    print(f"Database: {'✅' if status['database'] else '❌'}")
    print(f"Cache: {'✅' if status['cache'] else '❌'}")
    print(f"Services: {'✅' if status['user_preference_service'] else '❌'}")
```

### 性能分析

```python
import time

async def test_performance():
    start = time.time()

    # 测试缓存
    await cache.set("key", "value")
    value = await cache.get("key")

    elapsed = time.time() - start
    print(f"Elapsed: {elapsed:.3f}s")
```

---

## 🔗 相关文档

- [配置指南](./configuration.md) - 环境配置
- [存储层详解](../storage-layer/) - 数据库和缓存
- [架构设计](../03-architecture/) - 系统架构

---

**文档版本：** 5.1.0
**最后更新：** 2026-02-10
