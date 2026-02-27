# RedisCache 详解

> **版本：** 5.0.0
> **位置：** `backend/memory/storage/redis_cache.py`
> **代码行数：** 186行

---

## 📋 目录

- [职责](#职责)
- [架构设计](#架构设计)
- [核心方法](#核心方法)
- [使用示例](#使用示例)
- [最佳实践](#最佳实践)

---

## 🎯 职责

RedisCache负责：

1. **Redis连接管理** - 单例，全局唯一
2. **缓存读写** - get/set/delete基础操作
3. **JSON序列化** - 自动序列化/反序列化
4. **业务特定缓存** - 用户偏好、会话等
5. **优雅降级** - Redis不可用时不影响主流程

---

## 🏗️ 架构设计

### 缓存策略

```
Read-Through + Write-Back 策略：

读取流程：
1. 先查Redis缓存（1-5ms）
2. 缓存命中 → 直接返回
3. 缓存未命中 → 查数据库（10-50ms）
4. 数据库查询结果 → 写入Redis
5. 返回数据

写入流程：
1. 更新数据库
2. 使Redis缓存失效（delete）
3. 下次读取时重新加载缓存
```

**为什么使缓存失效而不是更新？**

```python
# ✅ 好的做法 - 使缓存失效
async def update_data(key, value):
    # 1. 更新数据库
    db.update(key, value)
    # 2. 使缓存失效
    await cache.delete(key)

# ❌ 不好的做法 - 更新缓存
async def update_data(key, value):
    # 1. 更新数据库
    db.update(key, value)
    # 2. 更新缓存（可能和数据不一致）
    await cache.set(key, value)
```

**理由：**
- 避免缓存和数据库不一致
- 下次读取时会重新加载最新数据
- 简单可靠

### TTL策略

```python
class RedisCache:
    # 默认TTL（秒）
    DEFAULT_TTL = 3600       # 1小时
    SESSION_TTL = 3600       # 会话缓存1小时
    USER_PREF_TTL = 86400    # 用户偏好缓存24小时
    VECTOR_TTL = 7200        # 向量检索结果缓存2小时
```

**TTL设计原则：**
- **用户偏好** - 24小时（变化不频繁）
- **会话数据** - 1小时（会话活跃期）
- **向量检索** - 2小时（查询结果）
- **默认数据** - 1小时（通用）

---

## 🔧 核心方法

### 1. `__init__()` - 初始化

```python
def __init__(self):
    """初始化Redis连接"""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    try:
        self.client = Redis.from_url(
            redis_url,
            decode_responses=True,  # 自动解码为字符串
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )

        # 测试连接
        self.client.ping()
        self.available = True
        logger.info(f"Redis connected: {redis_url}")

    except RedisError as e:
        logger.warning(f"Redis connection failed, cache disabled: {e}")
        self.client = None
        self.available = False
```

**关键配置：**
- `decode_responses=True` - 自动解码为字符串（不需要手动bytes.decode()）
- `socket_timeout=5` - 5秒超时
- `retry_on_timeout=True` - 超时自动重试
- `health_check_interval=30` - 30秒健康检查

### 2. 基础缓存操作

#### `get()` - 获取缓存

```python
async def get(self, key: str) -> Optional[str]:
    """获取缓存值"""
    if not self.client:
        return None

    try:
        value = self.client.get(key)
        if value:
            logger.debug(f"Cache hit: {key}")
        return value
    except RedisError as e:
        logger.warning(f"Redis get error: {e}")
        return None
```

#### `set()` - 设置缓存

```python
async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
    """设置缓存值"""
    if not self.client:
        return False

    try:
        ttl = ttl or self.DEFAULT_TTL
        self.client.setex(key, ttl, value)  # setex = set + expire
        logger.debug(f"Cache set: {key} (TTL={ttl}s)")
        return True
    except RedisError as e:
        logger.warning(f"Redis set error: {e}")
        return False
```

#### `delete()` - 删除缓存

```python
async def delete(self, key: str) -> bool:
    """删除缓存"""
    if not self.client:
        return False

    try:
        result = self.client.delete(key)
        logger.debug(f"Cache delete: {key} (deleted={result})")
        return result > 0
    except RedisError as e:
        logger.warning(f"Redis delete error: {e}")
        return False
```

### 3. JSON缓存操作

#### `get_json()` - 获取JSON缓存

```python
async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
    """获取JSON格式缓存"""
    value = await self.get(key)
    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error for key {key}: {e}")
            return None
    return None
```

#### `set_json()` - 设置JSON缓存

```python
async def set_json(
    self, key: str, value: Dict[str, Any], ttl: Optional[int] = None
) -> bool:
    """设置JSON格式缓存"""
    try:
        json_str = json.dumps(value, ensure_ascii=False)
        return await self.set(key, json_str, ttl)
    except (TypeError, ValueError) as e:
        logger.warning(f"JSON encode error: {e}")
        return False
```

### 4. 业务特定方法

#### 用户偏好缓存

```python
async def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
    """获取用户偏好缓存"""
    key = f"user_pref:{user_id}"
    return await self.get_json(key)

async def set_user_preferences(
    self, user_id: str, preferences: Dict[str, Any]
) -> bool:
    """设置用户偏好缓存"""
    key = f"user_pref:{user_id}"
    return await self.set_json(key, preferences, self.USER_PREF_TTL)
```

**使用示例：**
```python
# 设置缓存
await cache.set_user_preferences("user123", {
    "language": "ZH-CN",
    "default_slides": 15
})

# 获取缓存
prefs = await cache.get_user_preferences("user123")
```

#### 会话缓存

```python
async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
    """获取会话缓存"""
    key = f"session:{session_id}"
    return await self.get_json(key)

async def set_session(self, session_id: str, data: Dict[str, Any]) -> bool:
    """设置会话缓存"""
    key = f"session:{session_id}"
    return await self.set_json(key, data, self.SESSION_TTL)

async def delete_session(self, session_id: str) -> bool:
    """删除会话缓存"""
    key = f"session:{session_id}"
    return await self.delete(key)
```

### 5. 批量操作

#### `invalidate_pattern()` - 批量失效

```python
async def invalidate_pattern(self, pattern: str) -> int:
    """批量删除匹配模式的缓存"""
    if not self.client:
        return 0

    try:
        keys = self.client.keys(pattern)
        if keys:
            deleted = self.client.delete(*keys)
            logger.info(f"Invalidated {deleted} keys matching: {pattern}")
            return deleted
        return 0
    except RedisError as e:
        logger.warning(f"Redis pattern delete error: {e}")
        return 0
```

**使用示例：**
```python
# 删除所有用户偏好缓存
await cache.invalidate_pattern("user_pref:*")

# 删除所有会话缓存
await cache.invalidate_pattern("session:*")
```

---

## 💡 使用示例

### 基础使用

```python
from backend.memory.storage.redis_cache import RedisCache

# 初始化
cache = RedisCache()

# 检查可用性
if cache.is_available():
    print("✅ Redis is available")
else:
    print("❌ Redis is not available")
```

### 字符串缓存

```python
# 设置缓存
await cache.set("key1", "value1", ttl=3600)

# 获取缓存
value = await cache.get("key1")
print(value)  # "value1"

# 删除缓存
await cache.delete("key1")
```

### JSON缓存

```python
# 设置JSON
data = {
    "name": "Alice",
    "age": 30,
    "preferences": {
        "language": "ZH-CN",
        "theme": "dark"
    }
}
await cache.set_json("user:123", data, ttl=7200)

# 获取JSON
user = await cache.get_json("user:123")
print(user["name"])  # "Alice"
```

### 业务特定缓存

```python
# 用户偏好缓存
await cache.set_user_preferences("user123", {
    "language": "EN-US",
    "tone": "professional"
})
prefs = await cache.get_user_preferences("user123")

# 会话缓存
await cache.set_session("session_abc", {
    "user_id": "user123",
    "start_time": "2026-02-10T10:00:00"
})
session = await cache.get_session("session_abc")

# 删除会话
await cache.delete_session("session_abc")
```

### 在Service中使用

```python
class UserPreferenceService:
    def __init__(self, db_session, cache_client):
        self.db_session = db_session
        self.cache_client = cache_client

    async def get_user_preferences(self, user_id: str):
        # 1. 先查缓存
        if self.cache_client:
            cached = await self.cache_client.get_user_preferences(user_id)
            if cached:
                logger.debug(f"Cache hit for user {user_id}")
                return cached

        # 2. 查数据库
        profile = self.db_session.query(UserProfile).filter_by(
            user_id=user_id
        ).first()

        if profile:
            data = profile.to_dict()

            # 3. 写缓存
            if self.cache_client:
                await self.cache_client.set_user_preferences(user_id, data)

            return data

        return {}

    async def update_preferences(self, user_id: str, prefs: Dict):
        # 1. 更新数据库
        profile = self.db_session.query(UserProfile).filter_by(
            user_id=user_id
        ).first()

        for key, value in prefs.items():
            profile.set_preference(key, value)

        self.db_session.commit()

        # 2. 使缓存失效
        if self.cache_client:
            await self.cache_client.delete_user_preferences(user_id)

        return True
```

---

## ✅ 最佳实践

### 1. 总是检查可用性

```python
# ✅ 好的做法
if cache.is_available():
    await cache.set("key", "value")

# ❌ 不好的做法
await cache.set("key", "value")  # Redis不可用时会报错
```

### 2. 异常处理

```python
# ✅ 好的做法 - 缓存失败不影响主流程
async def get_data(key):
    # 尝试缓存
    try:
        cached = await cache.get(key)
        if cached:
            return cached
    except Exception as e:
        logger.warning(f"Cache error: {e}")

    # 降级到数据库
    return db.query(Model).filter_by(key=key).first()

# ❌ 不好的做法 - 缓存失败导致整个流程崩溃
async def get_data(key):
    return await cache.get(key) or db.query(Model).filter_by(key=key).first()
```

### 3. 合理设置TTL

```python
# ✅ 好的做法 - 根据数据变化频率设置TTL
await cache.set("user_pref:user123", prefs, ttl=86400)    # 24小时
await cache.set("session:abc", session, ttl=3600)         # 1小时
await cache.set("vector_result:xyz", result, ttl=7200)   # 2小时

# ❌ 不好的做法 - 所有数据都用相同TTL
await cache.set("user_pref:user123", prefs, ttl=3600)     # 太短
await cache.set("session:abc", session, ttl=86400)        # 太长
```

### 4. 缓存键命名规范

```python
# ✅ 好的命名 - 清晰表达用途
cache_key = f"user_pref:{user_id}"      # 用户偏好
cache_key = f"session:{session_id}"      # 会话数据
cache_key = f"vector:{query_hash}"       # 向量检索结果

# ❌ 不好的命名 - 不清晰
cache_key = f"{user_id}"                 # 可能冲突
cache_key = f"data_{user_id}"            # 下划线风格不一致
```

### 5. 更新后失效缓存

```python
# ✅ 好的做法 - 更新后失效
async def update_user_preferences(user_id, prefs):
    # 1. 更新数据库
    db.update(user_id, prefs)
    db.commit()

    # 2. 使缓存失效
    await cache.delete_user_preferences(user_id)

# ❌ 不好的做法 - 忘记失效缓存
async def update_user_preferences(user_id, prefs):
    db.update(user_id, prefs)
    db.commit()
    # 忘记删除缓存！下次读取会得到旧数据
```

### 6. 批量失效

```python
# ✅ 好的做法 - 批量失效相关缓存
async def update_user_role(user_id, new_role):
    # 1. 更新数据库
    db.update_role(user_id, new_role)

    # 2. 批量失效相关缓存
    await cache.delete(f"user_pref:{user_id}")
    await cache.delete(f"user_info:{user_id}")
    await cache.invalidate_pattern(f"session:{user_id}:*")

# ❌ 不好的做法 - 只失效部分缓存
async def update_user_role(user_id, new_role):
    db.update_role(user_id, new_role)
    await cache.delete(f"user_pref:{user_id}")  # 忘记失效其他相关缓存
```

---

## 🔧 配置说明

### 环境变量

```bash
# Redis（默认）
export REDIS_URL="redis://localhost:6379/0"

# 带密码的Redis
export REDIS_URL="redis://:password@localhost:6379/0"

# Redis Sentinel（高可用）
export REDIS_URL="sentinel://:password@sentinel1:26379,sentinel2:26379/mymaster/0"

# Redis Cluster（集群）
export REDIS_URL="redis-cluster://:password@host1:7000,host2:7001/0"
```

### 连接池配置

```python
self.client = Redis.from_url(
    redis_url,
    decode_responses=True,
    socket_timeout=5,            # 5秒超时
    socket_connect_timeout=5,    # 5秒连接超时
    retry_on_timeout=True,       # 超时重试
    health_check_interval=30,    # 30秒健康检查
    max_connections=50,          # 最大连接数
)
```

---

## 🔗 相关文档

- [开发者指南](./开发者指南.md) - 如何编写缓存代码
- [DatabaseManager详解](./database.md) - 数据库管理器
- [返回主页](./README.md)
