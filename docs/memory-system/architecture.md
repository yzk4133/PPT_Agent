# 记忆系统架构设计

## 一、总体架构

### 1.1 分层设计原则

记忆系统采用经典的三层缓存架构，每一层针对不同的访问模式和生命周期进行优化：

```
┌─────────────────────────────────────────────────────────────┐
│                        应用层                                │
│  • Agent Services                                            │
│  • User Preferences                                          │
│  • Decision Tracking                                         │
├─────────────────────────────────────────────────────────────┤
│                    统一管理层                                │
│  • HierarchicalMemoryManager                                │
│  • 自动路由决策                                              │
│  • 透明提升机制                                              │
├───────────┬─────────────────┬───────────────────────────────┤
│   L1      │      L2         │           L3                  │
│ 瞬时内存  │   短期内存      │       长期内存                 │
│           │                 │                               │
│ 容量:1000 │ 容量:动态       │ 容量:无限制                   │
│ TTL:5min  │ TTL:1hour       │ TTL:永久                      │
│ 延迟:<1ms │ 延迟:1-5ms      │ 延迟:10-50ms                  │
└───────────┴─────────────────┴───────────────────────────────┘
```

### 1.2 架构设计目标

| 目标 | 实现方式 | 收益 |
|------|---------|------|
| **高性能** | 三层缓存，热数据在L1 | 读取加速10-50x |
| **低成本** | 过滤临时数据，减少持久化 | DB负载降低60% |
| **智能流转** | 自动提升引擎 | 无需手动管理 |
| **高可用** | Redis分布式锁 | 并发安全 |
| **可扩展** | 模块化设计 | 易于添加新层 |

---

## 二、层级详细设计

### 2.1 L1 瞬时内存层

**设计定位**: 任务级临时数据，极速访问

**核心特性**:
- 纯Python OrderedDict实现，零网络IO
- LRU淘汰策略，容量限制1000条
- 默认TTL为5分钟
- 访问时自动更新LRU位置

**数据结构**:
```python
# 伪代码示例
class L1TransientLayer:
    cache: OrderedDict<full_key, value>
    metadata_cache: OrderedDict<full_key, Metadata>

    async def get(key, scope, scope_id):
        full_key = build_key(key, scope, scope_id)
        value = cache.get(full_key)
        metadata = metadata_cache.get(full_key)

        # 更新访问计数和LRU位置
        metadata.access_count += 1
        cache.move_to_end(full_key)

        return value, metadata

    async def set(key, value, scope, scope_id, metadata):
        full_key = build_key(key, scope, scope_id)
        metadata.expires_at = now() + 5min

        # 容量检查，LRU淘汰
        if len(cache) >= capacity:
            oldest_key = cache.first_key()
            cache.delete(oldest_key)

        cache.set(full_key, value)
        metadata_cache.set(full_key, metadata)
```

**键名格式**: `transient:{scope}:{scope_id}:{key}`

**适用场景**:
- 任务中间结果
- 临时计算状态
- 单次查询缓存
- Agent间数据传递

---

### 2.2 L2 短期内存层

**设计定位**: 会话级数据，快速持久化

**核心特性**:
- Redis存储，支持持久化
- 默认TTL为1小时
- 批量写入优化（Pipeline）
- 跨会话使用追踪

**数据结构**:
```python
# Redis键结构
data_key = "short_term:{scope}:{scope_id}:{key}:data"
meta_key = "short_term:{scope}:{scope_id}:{key}:meta"
tracker_key = "l2:cross_session_tracker:{key}"

# 数据存储格式
value: JSON序列化的数据
metadata: {
    "key": "...",
    "layer": "short_term",
    "scope": "...",
    "importance": 0.7,
    "access_count": 5,
    "session_ids": ["session1", "session2"],
    ...
}
```

**批量写入优化**:
```python
# 伪代码
async def batch_set(items):
    pipe = redis.pipeline()
    for (key, value, scope, scope_id, metadata) in items:
        data_key = build_data_key(key, scope, scope_id)
        meta_key = build_meta_key(key, scope, scope_id)

        pipe.setex(data_key, TTL, serialize(value))
        pipe.setex(meta_key, TTL, serialize(metadata))

    pipe.execute()  # 一次网络往返完成所有写入
```

**跨会话追踪**:
```python
# 使用Redis Set追踪哪些session访问过
sadd("l2:cross_session_tracker:key123", "session_abc")
sadd("l2:cross_session_tracker:key123", "session_xyz")
scard("l2:cross_session_tracker:key123")  # 返回2，用于提升判断
```

**适用场景**:
- 会话状态保存
- 用户偏好缓存
- Agent工作空间数据
- 跨任务共享数据

---

### 2.3 L3 长期内存层

**设计定位**: 用户级永久存储，智能检索

**核心特性**:
- PostgreSQL + pgvector
- 向量语义检索
- 跨会话持久化
- 支持复杂查询

**数据库表结构**:
```sql
CREATE TABLE longterm_memory (
    id UUID PRIMARY KEY,
    memory_key VARCHAR(500) NOT NULL,
    scope VARCHAR(50) NOT NULL,
    scope_id VARCHAR(255) NOT NULL,
    content JSONB NOT NULL,
    content_text TEXT,
    embedding VECTOR(1536),  -- pgvector
    importance FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    session_count INTEGER DEFAULT 0,
    tags JSONB DEFAULT '[]',
    promoted_from_layer VARCHAR(20),
    promotion_reason VARCHAR(50),
    created_at TIMESTAMP,
    last_accessed TIMESTAMP,
    updated_at TIMESTAMP,

    UNIQUE(memory_key, scope, scope_id)
);

-- 向量相似度索引
CREATE INDEX idx_vector_embedding
ON longterm_memory
USING hnsw (embedding vector_cosine_ops);
```

**语义检索原理**:
```python
# 伪代码
async def semantic_search(query_vector, scope, scope_id, limit):
    sql = """
        SELECT memory_key, content,
               1 - (embedding <=> :query_vector) as similarity
        FROM longterm_memory
        WHERE scope = :scope
        AND scope_id = :scope_id
        AND importance >= :min_importance
        ORDER BY embedding <=> :query_vector
        LIMIT :limit
    """
    # <=> 是pgvector的余弦距离操作符
    # 返回最相似的N条记录
```

**适用场景**:
- 用户长期偏好
- 向量记忆（研究结论、模板）
- Agent决策历史
- 共享工作空间归档

---

## 三、数据流转机制

### 3.1 写入路由决策

```
用户调用: memory_manager.set(key, value, scope, scope_id, importance)
                    ↓
        ┌───────────────────────────┐
        │  活跃作用域标记           │
        │  scope_tracker.mark_active │
        └───────────────────────────┘
                    ↓
        ┌───────────────────────────┐
        │  初始层级决策             │
        │  - importance >= 0.8 → L2  │
        │  - USER作用域 → L2         │
        │  - 默认 → L1               │
        └───────────────────────────┘
                    ↓
        ┌───────────────────────────┐
        │  写入目标层               │
        │  - 创建元数据              │
        │  - 序列化数据              │
        │  - 设置TTL                │
        └───────────────────────────┘
```

### 3.2 读取自动回填

```
用户调用: memory_manager.get(key, scope, scope_id)
                    ↓
        ┌───────────────────────────┐
        │  查询L1                   │
        │  命中? → 返回 + 更新统计  │
        └───────────────────────────┘
                    ↓ 未命中
        ┌───────────────────────────┐
        │  查询L2                   │
        │  命中?                    │
        │   → 回写L1                │
        │   → 返回 + 更新统计       │
        └───────────────────────────┘
                    ↓ 未命中
        ┌───────────────────────────┐
        │  查询L3                   │
        │  命中?                    │
        │   → 回写L2 + L1           │
        │   → 返回 + 更新统计       │
        └───────────────────────────┘
                    ↓ 未命中
        返回 None
```

### 3.3 自动提升流程

```
后台任务 (每5分钟执行)
        ↓
┌───────────────────────────────────────────┐
│  获取活跃作用域列表                        │
│  避免全量扫描，仅检查有数据写入的scope    │
└───────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────┐
│  L1 → L2 扫描                             │
│  for each active scope:                   │
│    for each key in L1:                    │
│      metadata = get_metadata(key)         │
│      if (access_count >= 3 OR             │
│          importance >= 0.7):              │
│        candidates.add(key)                 │
└───────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────┐
│  批量迁移L1→L2                            │
│  for batch in candidates (50条/批):      │
│    l2.batch_set(batch)                    │
│    l1.delete(batch)                       │
│    record_promotion_event()               │
└───────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────┐
│  L2 → L3 扫描                             │
│  for each active scope:                   │
│    for each key in L2:                    │
│      metadata = get_metadata(key)         │
│      session_count = get_cross_session(k) │
│      if (session_count >= 2):             │
│        candidates.add(key)                 │
└───────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────┐
│  逐个迁移L2→L3                            │
│  for each candidate:                      │
│    l3.set(key, value, metadata)           │
│    l2.delete(key)                         │
│    record_promotion_event()               │
└───────────────────────────────────────────┘
```

---

## 四、提升引擎架构

### 4.1 组件关系

```
┌──────────────────────────────────────────────────────────┐
│                    PromotionEngine                        │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ ActiveScope  │→ │ Promotion    │→ │   Data       │  │
│  │ Tracker      │  │ RuleEngine   │  │ Migrator     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         ↓                 ↓                  ↓           │
│  维护活跃作用域      评估提升规则        执行数据迁移     │
│  避免全量扫描      (访问频率/重要性)    (批量写入)       │
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │         PromotionEventLogger                       │ │
│  │  记录所有提升事件 → 支持查询和分析                │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### 4.2 提升规则引擎

**规则决策树**:
```
L1 → L2 判断
    ├── 访问次数 >= 3?
    │   ├── 是 → 提升 (原因: HIGH_ACCESS_FREQUENCY)
    │   └── 否 ↓
    ├── 重要性 >= 0.7?
    │   ├── 是 → 提升 (原因: HIGH_IMPORTANCE_SCORE)
    │   └── 否 ↓
    ├── 存活时间 >= 10min AND 访问次数 >= 2?
    │   ├── 是 → 提升 (原因: LONG_LIFETIME)
    │   └── 否 → 不提升

L2 → L3 判断
    ├── 跨会话使用 >= 2?
    │   ├── 是 → 提升 (原因: CROSS_SESSION_USAGE)
    │   └── 否 ↓
    ├── 访问次数 >= 5 AND 重要性 >= 0.8?
    │   ├── 是 → 提升 (原因: HIGH_ACCESS_FREQUENCY)
    │   └── 否 → 不提升
```

**规则优先级**: 重要性 > 访问频率 > 长期存在

### 4.3 数据迁移策略

**L1 → L2 批量迁移**:
```python
# 伪代码
async def migrate_l1_to_l2(candidates):
    batch_size = 50
    for i in range(0, len(candidates), batch_size):
        batch = candidates[i:i+batch_size]

        # 准备批量数据
        items = []
        for (key, value, metadata) in batch:
            metadata.layer = L2_SHORT_TERM
            items.append((key, value, scope, scope_id, metadata))

        # 批量写入L2
        l2.batch_set(items)

        # 记录事件
        for (key, ...) in batch:
            event_logger.log_event(
                key=key,
                from_layer=L1,
                to_layer=L2,
                reason=...
            )
```

**L2 → L3 逐个迁移**:
```python
# L3不支持批量，逐个写入保证事务性
async def migrate_l2_to_l3(candidates):
    for (key, value, metadata) in candidates:
        try:
            metadata.layer = L3_LONG_TERM
            metadata.importance = max(metadata.importance, 0.8)

            success = l3.set(key, value, scope, scope_id, metadata)

            if success:
                l2.delete(key, scope, scope_id)
                event_logger.log_event(success=True, ...)
            else:
                event_logger.log_event(success=False, error="...")
        except Exception as e:
            event_logger.log_event(success=False, error=str(e))
```

---

## 五、并发控制机制

### 5.1 分布式锁设计

基于Redis的Redlock算法实现：

```python
# 伪代码
class DistributedLock:
    async def acquire(key, ttl):
        token = generate_uuid()
        lock_key = f"lock:{key}"

        # SET NX + PX (原子操作)
        acquired = redis.set(
            lock_key,
            token,
            nx=True,      # 仅当键不存在时设置
            px=ttl        # 毫秒级TTL
        )

        if acquired:
            return Lock(lock_key, token)
        return None

    async def release(lock):
        # Lua脚本确保只删除自己持有的锁
        script = """
            local token = ARGV[1]
            local current = redis.call('GET', KEYS[1])

            if current == token then
                return redis.call('DEL', KEYS[1])
            else
                return 0
            end
        """
        redis.eval(script, keys=[lock.key], args=[lock.token])
```

### 5.2 使用场景

| 场景 | 锁键 | TTL | 说明 |
|------|------|-----|------|
| UserProfile更新 | `user_profile:update:{user_id}` | 5s | 防止并发修改冲突 |
| 向量记忆写入 | `vector_memory:write:{namespace}` | 10s | 批量写入保护 |
| 提升任务执行 | `promotion:execute:L1_L2` | 300s | 避免重复提升 |

### 5.3 自动续期机制

```python
# 伪代码
async def auto_renewal_loop(lock):
    while True:
        await sleep(lock.ttl * 0.7)  # 70% TTL时续期

        # Lua脚本续期
        success = redis.eval(
            "if redis.call('GET', KEYS[1]) == ARGV[1] then "
            "return redis.call('PEXPIRE', KEYS[1], ARGV[2]) "
            "else return 0 end",
            keys=[lock.key],
            args=[lock.token, lock.ttl]
        )

        if not success:
            break  # 锁已过期或被其他客户端持有
```

---

## 六、向量缓存架构

### 6.1 二级缓存设计

```
┌─────────────────────────────────────────┐
│         应用层请求向量                   │
│         get_embedding(text)             │
└─────────────────────────────────────────┘
                  ↓
        ┌─────────────────┐
        │  L1: 内存LRU     │
        │  命中? → 返回    │
        └─────────────────┘
                  ↓ 未命中
        ┌─────────────────┐
        │  L2: Redis       │
        │  命中? → 返回    │
        │        ↓ 回写L1  │
        └─────────────────┘
                  ↓ 未命中
        ┌─────────────────┐
        │  OpenAI API      │
        │  调用embedding   │
        │        ↓         │
        │  写入L1 + L2     │
        └─────────────────┘
```

### 6.2 缓存键设计

```python
# 使用SHA256避免键过长
cache_key = sha256(f"{model}:{text}").hexdigest()

# Redis键格式
redis_key = f"vector_cache:{model}:{cache_key}"
```

### 6.3 缓存预热

```python
# 伪代码
async def warm_cache(priority_texts):
    for text in priority_texts:
        # 异步预加载，不阻塞主流程
        asyncio.create_task(
            get_embedding(text, use_cache=True)
        )
```

---

## 七、生命周期管理

### 7.1 数据温度分类

```
创建/访问时间
    │
    │ < 30天
    ├────────────→ 热数据 (HOT)
    │              • PG主库
    │              • 快速访问
    │
    │ 30-180天
    ├────────────→ 温数据 (WARM)
    │              • 只读副本
    │              • 降级服务
    │
    │ > 180天
    └────────────→ 冷数据 (COLD)
                   • 归档存储
                   • 仅保留摘要
```

### 7.2 时间衰减公式

```python
# 重要性随时间衰减
decayed_importance = original_importance * (0.95 ^ (days / 30))

# 示例：
# 原始重要性: 0.8
# 30天后: 0.8 * 0.95^1 = 0.76
# 60天后: 0.8 * 0.95^2 = 0.72
# 90天后: 0.8 * 0.95^3 = 0.69
```

### 7.3 内容摘要流程

```
原始内容 (> 10KB)
    ↓
┌─────────────────────────┐
│  LLM摘要生成             │
│  prompt: "将以下内容压缩  │
│  成500字以内的摘要"      │
└─────────────────────────┘
    ↓
摘要 + 向量嵌入
    ↓
归档存储 (内存/S3)
```

---

## 八、扩展性设计

### 8.1 添加新的存储层

```python
# 伪代码 - 扩展L4分布式存储层
class L4DistributedLayer(BaseMemoryLayer):
    def __init__(self, config):
        # 支持 Cassandra / Qdrant / Elasticsearch
        self.backend = create_backend(config.backend_type)

    async def set(self, key, value, scope, scope_id):
        await self.backend.write(key, value)

    async def get(self, key, scope, scope_id):
        return await self.backend.read(key)

# 集成到管理器
class HierarchicalMemoryManager:
    def __init__(self, ...):
        self.l4 = L4DistributedLayer(config)

    async def get(self, key, scope, scope_id):
        # L1 → L2 → L3 → L4
        result = await self.l4.get(key, scope, scope_id)
        if result:
            # 回写到上层
            await self.l1.set(...)
        return result
```

### 8.2 插件化规则引擎

```python
# 伪代码 - 自定义提升规则
class CustomPromotionRule:
    def evaluate(self, metadata, context):
        # 自定义逻辑
        if metadata.tags.contains("critical"):
            return True, "CRITICAL_DATA"
        return False, None

# 注册规则
rule_engine.register_rule(CustomPromotionRule())
```

---

## 九、监控可观测性

### 9.1 指标采集

```
┌─────────────────────────────────────────┐
│            应用层指标                    │
│  • API请求量                            │
│  • 响应时间                             │
│  • 错误率                               │
├─────────────────────────────────────────┤
│            缓存层指标                    │
│  • L1/L2/L3命中率                       │
│  • 提升事件频率                         │
│  • 数据流转速率                         │
├─────────────────────────────────────────┤
│            资源层指标                    │
│  • L1内存使用率                         │
│  • Redis内存使用率                      │
│  • PostgreSQL连接数                     │
│  • 向量索引大小                         │
└─────────────────────────────────────────┘
```

### 9.2 日志结构

```json
{
  "timestamp": "2026-02-03T10:30:00Z",
  "level": "INFO",
  "event": "promotion_completed",
  "data": {
    "from_layer": "L1_TRANSIENT",
    "to_layer": "L2_SHORT_TERM",
    "key": "user_research",
    "reason": "HIGH_ACCESS_FREQUENCY",
    "access_count": 5,
    "importance": 0.7
  }
}
```

---

## 十、故障恢复

### 10.1 Redis故障降级

```
Redis不可用
    ↓
L2层操作失败
    ↓
┌─────────────────────────────────┐
│  自动降级处理                    │
│  • 写入: 记录日志，继续执行      │
│  • 读取: 直接查询L3              │
│  • 统计: 标记Redis状态为DOWN     │
└─────────────────────────────────┘
```

### 10.2 数据一致性保证

```
写入流程
    ↓
L1写入 (内存，瞬时)
    ↓
L2写入 (Redis，异步)
    ↓
如果L2失败
    ↓
┌─────────────────────────────────┐
│  重试机制                        │
│  • 最多重试3次                   │
│  • 指数退避延迟                  │
│  • 失败后记录告警日志            │
└─────────────────────────────────┘
```
