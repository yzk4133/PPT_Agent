# 功能详细说明

## 一、自动提升引擎 (Promotion Engine)

### 1.1 功能概述

自动提升引擎是记忆系统的核心组件，负责根据数据的使用模式和重要性，自动将数据在三层之间流转，实现智能分层存储。

### 1.2 核心组件

#### ActiveScopeTracker - 活跃作用域追踪器

**功能**: 维护活跃作用域列表，避免全量扫描所有数据

**工作原理**:
```
有数据写入 → 标记作用域为活跃
                    ↓
        记录当前时间戳
                    ↓
        后台扫描时仅检查活跃作用域
                    ↓
        超过1小时未活跃 → 自动移除
```

**伪代码**:
```python
class ActiveScopeTracker:
    def __init__(self):
        self.active_scopes = {}  # {scope_key: last_active_time}
        self.ttl = 3600  # 1小时

    async def mark_active(self, scope, scope_id):
        key = f"{scope}:{scope_id}"
        self.active_scopes[key] = now()

    async def get_active_scopes(self):
        # 返回未过期的活跃作用域
        current = now()
        return [
            (scope, scope_id)
            for key, (scope, scope_id, time) in self.active_scopes
            if current - time < self.ttl
        ]
```

**优势**:
- 避免全量扫描，提升性能
- 自动过期清理，无内存泄漏
- 支持增量更新

---

#### PromotionRuleEngine - 提升规则引擎

**功能**: 评估数据是否满足提升条件

**L1 → L2 提升规则**:

| 规则 | 条件 | 说明 |
|------|------|------|
| 高访问频率 | access_count ≥ 3 | 热数据自动上浮 |
| 高重要性 | importance ≥ 0.7 | 重要数据持久化 |
| 长期存在 | age ≥ 10min AND access ≥ 2 | 中等热度数据 |

**L2 → L3 提升规则**:

| 规则 | 条件 | 说明 |
|------|------|------|
| 跨会话使用 | session_count ≥ 2 | 多会话共享数据 |
| 高频高重要性 | access ≥ 5 AND importance ≥ 0.8 | 极热数据 |

**伪代码**:
```python
class PromotionRuleEngine:
    def should_promote_l1_to_l2(self, metadata, age_seconds):
        # 规则1: 访问频率
        if metadata.access_count >= 3:
            return True, "HIGH_ACCESS_FREQUENCY"

        # 规则2: 重要性
        if metadata.importance >= 0.7:
            return True, "HIGH_IMPORTANCE_SCORE"

        # 规则3: 长期存在
        if age_seconds >= 600 and metadata.access_count >= 2:
            return True, "LONG_LIFETIME"

        return False, None

    def should_promote_l2_to_l3(self, metadata, cross_session_count):
        # 规则1: 跨会话使用
        if cross_session_count >= 2:
            return True, "CROSS_SESSION_USAGE"

        # 规则2: 高频高重要性
        if (metadata.access_count >= 5 and
            metadata.importance >= 0.8):
            return True, "HIGH_ACCESS_FREQUENCY"

        return False, None
```

**规则优先级**: 重要性 > 访问频率 > 长期存在

---

#### DataMigrator - 数据迁移器

**功能**: 执行批量数据迁移，保证事务性

**L1 → L2 迁移**:
```
1. 扫描L1，收集候选数据
2. 分批处理（50条/批）
3. 使用Redis Pipeline批量写入
4. 记录迁移事件
5. 从L1删除已迁移数据
```

**L2 → L3 迁移**:
```
1. 扫描L2，收集候选数据
2. 逐个写入L3（保证事务）
3. 记录迁移事件
4. 从L2删除已迁移数据
```

**伪代码**:
```python
class DataMigrator:
    async def migrate_l1_to_l2(self, candidates, l2_layer):
        batch_size = 50
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i+batch_size]

            # 准备批量数据
            items = [(key, value, scope, scope_id, metadata)
                     for key, value, metadata, _ in batch]

            # 批量写入L2
            count = await l2_layer.batch_set(items)

            # 记录成功/失败
            log_migration_result(count, len(batch))

    async def migrate_l2_to_l3(self, candidates, l3_layer):
        for key, value, metadata, _ in candidates:
            # 更新元数据
            metadata.layer = L3_LONG_TERM
            metadata.importance = max(metadata.importance, 0.8)

            # 写入L3
            success = await l3_layer.set(key, value, scope, scope_id, metadata)

            if success:
                # 从L2删除
                await l2_layer.delete(key, scope, scope_id)
```

---

#### PromotionEventLogger - 提升事件记录器

**功能**: 记录所有提升事件，支持查询和分析

**事件结构**:
```json
{
  "event_id": "uuid",
  "timestamp": "2026-02-03T10:30:00Z",
  "key": "research_findings",
  "from_layer": "L1_TRANSIENT",
  "to_layer": "L2_SHORT_TERM",
  "reason": "HIGH_ACCESS_FREQUENCY",
  "scope": "user",
  "scope_id": "user123",
  "access_count": 5,
  "importance": 0.7,
  "session_count": 1,
  "explanation": "access_count=5 >= 3",
  "success": true
}
```

**查询功能**:
```python
# 查询最近的提升事件
events = await logger.get_events(limit=100)

# 按层级过滤
events = await logger.get_events(
    from_layer="L1_TRANSIENT",
    to_layer="L2_SHORT_TERM"
)

# 按原因过滤
events = await logger.get_events(
    reason="CROSS_SESSION_USAGE"
)

# 按键过滤
events = await logger.get_events(key="specific_key")
```

---

### 1.3 后台任务流程

```
┌─────────────────────────────────────────┐
│  自动提升循环 (每5分钟)                  │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  获取活跃作用域列表                      │
│  ActiveScopeTracker.get_active_scopes() │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  L1 → L2 提升扫描                       │
│  for each active scope:                 │
│    - list L1 keys                       │
│    - evaluate promotion rules           │
│    - collect candidates                 │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  批量迁移 L1 → L2                       │
│  DataMigrator.migrate_l1_to_l2()        │
│  - batch write to L2 (50条/批)          │
│  - delete from L1                       │
│  - log events                           │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  L2 → L3 提升扫描                       │
│  for each active scope:                 │
│    - list L2 keys                       │
│    - get cross-session count            │
│    - evaluate promotion rules           │
│    - collect candidates                 │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  逐个迁移 L2 → L3                       │
│  DataMigrator.migrate_l2_to_l3()        │
│  - write to L3 (one by one)             │
│  - delete from L2                       │
│  - log events                           │
└─────────────────────────────────────────┘
```

---

## 二、分布式锁服务 (Distributed Lock Service)

### 2.1 功能概述

基于Redis Redlock算法实现的分布式锁，用于保护关键操作的并发安全。

### 2.2 核心特性

#### 原子性获取锁

使用Redis的SET NX + PX命令组合，保证原子性：

```
SET lock:key token NX PX 10000
    ↓
NX: 仅当键不存在时设置
PX: 设置毫秒级TTL
    ↓
返回: OK (成功) 或 nil (失败)
```

#### 安全释放锁

使用Lua脚本确保只释放自己持有的锁：

```lua
-- Lua脚本
local token = ARGV[1]
local current = redis.call('GET', KEYS[1])

if current == token then
    return redis.call('DEL', KEYS[1])
else
    return 0
end
```

**为什么需要Lua脚本？**
- 防止误删其他客户端持有的锁
- 避免GET和DEL之间的竞态条件
- 保证操作的原子性

#### 自动重试机制

```python
# 伪代码
async def acquire(key, ttl, max_retries=3):
    for attempt in range(max_retries):
        acquired = redis.set(key, token, nx=True, px=ttl)

        if acquired:
            return Lock(key, token)

        # 等待后重试
        await sleep(200)  # 200ms

    raise LockAcquisitionError("Max retries exceeded")
```

#### 自动续期

```python
# 伪代码
async def auto_renewal_loop(lock):
    while True:
        await sleep(lock.ttl * 0.7)  # 70%时续期

        # 续期
        success = redis.eval(extend_script, lock.key, lock.token)

        if not success:
            break  # 锁已过期
```

---

### 2.3 使用场景

#### 场景1: UserProfile并发更新

**问题**: 多个Agent同时更新用户配置，可能导致冲突

**解决方案**:
```python
# 伪代码
async def update_user_preferences(user_id, new_preferences):
    lock_key = f"user_profile:update:{user_id}"

    async with lock_service.acquire(lock_key, ttl=5000):
        # 获取当前配置
        current = await db.get_user_profile(user_id)

        # 检查版本号（乐观锁）
        if current.version != expected_version:
            raise ConflictError("Concurrent modification detected")

        # 更新配置
        current.preferences.update(new_preferences)
        current.version += 1

        # 保存
        await db.save(current)
```

#### 场景2: 批量向量写入

**问题**: 批量写入向量时，其他进程可能读取到不完整数据

**解决方案**:
```python
# 伪代码
async def batch_write_vectors(vectors):
    lock_key = "vector_memory:batch_write"

    lock = await lock_service.acquire(lock_key, ttl=30000, auto_renewal=True)

    try:
        for vector in vectors:
            await l3_layer.set(vector.key, vector.value, ...)
    finally:
        await lock.release()
```

#### 场景3: 提升任务互斥

**问题**: 多个实例同时执行提升任务，可能重复处理

**解决方案**:
```python
# 伪代码
async def perform_promotion():
    lock_key = "promotion:execute:L1_L2"

    try:
        lock = await lock_service.acquire(lock_key, ttl=300, wait_timeout=0)
    except LockAcquisitionError:
        return  # 其他实例正在执行

    try:
        await promote_l1_to_l2()
    finally:
        await lock.release()
```

---

### 2.4 装饰器支持

```python
# 伪代码
@distributed_lock("update_user:{user_id}", ttl=5000)
async def update_user(user_id: str, data: dict):
    # 函数执行期间自动持有锁
    await db.update_user(user_id, data)
```

**实现原理**:
```python
# 伪代码
def distributed_lock(key_pattern, ttl):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 构建锁键
            lock_key = key_pattern.format(**kwargs)

            async with lock_service.acquire(lock_key, ttl):
                return await func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## 三、向量缓存服务 (Vector Cache Service)

### 3.1 功能概述

缓存向量嵌入，减少OpenAI API调用，降低成本和延迟。

### 3.2 二级缓存架构

```
┌──────────────────────────────────────────┐
│           应用层请求                      │
│     get_embedding("用户查询文本")         │
└──────────────────────────────────────────┘
                  ↓
        ┌─────────────────┐
        │  L1: 内存LRU     │ ← 容量: 10000
        │  命中率: ~60%    │   TTL: 2小时
        │  延迟: <1ms      │
        └─────────────────┘
                  ↓ 未命中
        ┌─────────────────┐
        │  L2: Redis       │ ← 命中率: ~30%
        │  延迟: 1-5ms     │   分布式共享
        └─────────────────┘
                  ↓ 未命中
        ┌─────────────────┐
        │  OpenAI API      │ ← 调用率: ~10%
        │  延迟: 200-500ms │   成本: $0.0001/1K tokens
        └─────────────────┘
```

### 3.3 缓存键设计

**问题**: 文本长度不固定，直接作为键不合适

**解决方案**: 使用SHA256哈希

```python
# 伪代码
def build_cache_key(text, model):
    content = f"{model}:{text}"
    return sha256(content.encode()).hexdigest()

# 示例
text = "这是一段很长的用户查询文本，包含了各种复杂的信息..."
key = build_cache_key(text, "text-embedding-3-small")
# 输出: "a3f2b1c4e5d6..."
```

**Redis键格式**:
```
vector_cache:text-embedding-3-small:a3f2b1c4e5d6...
```

### 3.4 批量操作优化

```python
# 伪代码
async def get_embeddings(texts):
    # 先查缓存
    results = {}
    missing = []

    for text in texts:
        cache_key = build_cache_key(text)
        cached = await cache.get(cache_key)

        if cached:
            results[text] = cached
        else:
            missing.append(text)

    # 批量调用API
    if missing:
        api_results = await openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=missing  # 支持批量输入
        )

        # 写入缓存
        for text, embedding in zip(missing, api_results):
            cache_key = build_cache_key(text)
            await cache.set(cache_key, embedding)
            results[text] = embedding

    return results
```

### 3.5 缓存预热

**功能**: 预加载高频文本的向量

```python
# 伪代码
async def warm_cache(priority_texts):
    # 1. 从数据库获取高频文本
    #    - 访问次数最多的
    #    - 最近查询的
    #    - 系统关键文本

    # 2. 异步预加载
    tasks = []
    for text in priority_texts:
        task = asyncio.create_task(
            get_embedding(text, use_cache=True)
        )
        tasks.append(task)

    # 3. 等待完成
    await asyncio.gather(*tasks)

    return len(tasks)
```

**预热时机**:
- 系统启动时
- 定时任务（每天凌晨）
- 手动触发

### 3.6 性能指标

| 指标 | 无缓存 | 有缓存 | 提升 |
|------|--------|--------|------|
| 平均延迟 | 250ms | 5ms | 50x |
| API调用/天 | 100,000 | 10,000 | 10x |
| 成本/天 | $10 | $1 | 10x |
| 命中率 | - | 90% | - |

---

## 四、生命周期管理服务 (Lifecycle Manager Service)

### 4.1 功能概述

管理数据的完整生命周期，包括时间衰减、温度分类、归档和清理。

### 4.2 时间衰减机制

**目的**: 随时间推移降低旧数据的重要性

**衰减公式**:
```
decayed_importance = original_importance × (0.95 ^ (days / 30))
```

**衰减示例**:

| 原始重要性 | 30天后 | 60天后 | 90天后 | 180天后 |
|-----------|--------|--------|--------|---------|
| 1.0 | 0.95 | 0.90 | 0.86 | 0.74 |
| 0.8 | 0.76 | 0.72 | 0.69 | 0.59 |
| 0.5 | 0.48 | 0.45 | 0.43 | 0.37 |
| 0.3 | 0.29 | 0.27 | 0.26 | 0.22 |

**为什么选择0.95?**
- 30天衰减5%，温和下降
- 保留重要数据的长期价值
- 避免过快衰减导致数据丢失

### 4.3 数据温度分类

```
创建/访问时间
    │
    │ < 30天
    ├────────────────→ 热数据 (HOT)
    │                  • 存储位置: PG主库
    │                  • 访问模式: 随时读取
    │                  • 索引: 完整索引
    │
    │ 30-180天
    ├────────────────→ 温数据 (WARM)
    │                  • 存储位置: 只读副本
    │                  • 访问模式: 延迟可接受
    │                  • 索引: 部分索引
    │
    │ > 180天
    └────────────────→ 冷数据 (COLD)
                       • 存储位置: 归档(S3/文件)
                       • 访问模式: 需要恢复
                       • 内容: 仅摘要+向量
```

**分类伪代码**:
```python
def classify_temperature(days_since_access):
    if days_since_access < 30:
        return "HOT"
    elif days_since_access < 180:
        return "WARM"
    else:
        return "COLD"
```

### 4.4 内容摘要

**目的**: 压缩大内容，节省存储空间

**摘要流程**:
```
原始内容 (10KB)
    ↓
┌─────────────────────────────┐
│  判断是否需要摘要            │
│  if content_size > 10KB:    │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  LLM生成摘要                 │
│  prompt:                    │
│  "将以下内容压缩成           │
│   500字以内的摘要"           │
└─────────────────────────────┘
    ↓
摘要 (500字) + 向量嵌入
    ↓
归档存储
```

**摘要质量保证**:
- 保留关键信息
- 保留向量（用于语义检索）
- 可通过原key恢复

### 4.5 定期清理任务

**任务频率**: 每天24:00执行

**清理内容**:
```
1. 更新衰减重要性
   → 扫描L3数据
   → 计算衰减后重要性
   → 更新数据库

2. 归档冷数据
   → 查找180天+未访问
   → 生成摘要
   → 移至归档存储
   → 删除原记录

3. 清理过期数据
   → 重要性 < 0.2
   → 超过365天未访问
   → 访问次数 < 2
   → 永久删除
```

**伪代码**:
```python
async def perform_lifecycle_tasks():
    # 1. 更新衰减重要性
    decayed = await update_decay_importance()

    # 2. 归档冷数据
    archived = await archive_cold_data()

    # 3. 清理过期数据
    cleaned = await cleanup_expired_data()

    # 4. 记录统计
    log_lifecycle_stats({
        "decayed": decayed,
        "archived": archived,
        "cleaned": cleaned
    })
```

---

## 五、用户偏好学习服务 (User Preference Service)

### 5.1 功能概述

从用户行为中自动学习偏好，无需显式配置。

### 5.2 学习机制

**数据来源**:
- 用户修改PPT的次数
- 最终选择的模板样式
- 生成内容的调整方向
- 使用频率

**推断逻辑**:
```python
# 伪代码
def infer_satisfaction(modification_count):
    if modification_count == 0:
        return 1.0  # 完全满意
    elif modification_count <= 2:
        return 0.8  # 基本满意
    elif modification_count <= 5:
        return 0.5  # 一般
    else:
        return 0.2  # 不满意
```

**偏好更新**:
```python
# 伪代码
async def update_preferences(user_id, session_data):
    # 获取当前偏好
    current = await get_user_preferences(user_id)

    # 从会话中学习
    if session_data.template_used:
        current.preferred_template = session_data.template_used

    if session_data.color_scheme:
        current.color_scheme = session_data.color_scheme

    # 更新满意度
    satisfaction = infer_satisfaction(session_data.modifications)
    current.avg_satisfaction = (
        current.avg_satisfaction * 0.8 + satisfaction * 0.2
    )

    # 保存
    await save_preferences(user_id, current)
```

### 5.3 偏好应用

**生成时自动应用**:
```python
# 伪代码
async def generate_ppt(user_id, requirements):
    # 获取用户偏好
    preferences = await get_user_preferences(user_id)

    # 应用偏好
    config = {
        "template": preferences.get("template", "default"),
        "color_scheme": preferences.get("color_scheme", "blue"),
        "font_size": preferences.get("font_size", "medium"),
    }

    # 生成
    return await ppt_generator.generate(requirements, config)
```

---

## 六、Agent决策追踪服务 (Agent Decision Service)

### 6.1 功能概述

记录Agent的决策过程，用于分析和优化。

### 6.2 决策记录结构

```json
{
  "agent_name": "ResearchAgent",
  "decision_type": "tool_selection",
  "context": {
    "user_query": "查找关于AI的最新研究",
    "available_tools": ["search", "database", "api"],
    "current_state": {...}
  },
  "selected_action": "search",
  "alternatives": ["database", "api"],
  "reasoning": "用户需要最新信息，搜索引擎更合适",
  "confidence_score": 0.9,
  "outcome": "success",
  "execution_time_ms": 150,
  "token_usage": {"prompt": 100, "completion": 50}
}
```

### 6.3 性能分析

**统计指标**:
```python
# 伪代码
async def analyze_agent_performance(agent_name):
    decisions = await get_agent_decisions(agent_name)

    return {
        "total_decisions": len(decisions),
        "success_rate": count_success(decisions) / len(decisions),
        "avg_execution_time": avg_time(decisions),
        "common_actions": top_actions(decisions, 10),
        "tool_success_rate": {
            "search": 0.95,
            "database": 0.80,
            "api": 0.75
        }
    }
```

**优化建议**:
```python
# 伪代码
def generate_optimization_suggestions(stats):
    suggestions = []

    if stats["tool_success_rate"]["api"] < 0.7:
        suggestions.append(
            "API调用成功率较低，建议添加重试机制"
        )

    if stats["avg_execution_time"] > 1000:
        suggestions.append(
            "平均执行时间较长，建议使用缓存"
        )

    return suggestions
```

---

## 七、共享工作空间服务 (Shared Workspace Service)

### 7.1 功能概述

多Agent协作时共享研究结果，避免重复工作。

### 7.2 数据共享流程

```
Agent A 完成研究
    ↓
share_data(
    data_key="research_findings",
    data_type="research_result",
    data_content={...}
)
    ↓
┌─────────────────────────────────┐
│  写入 shared_workspace_memory    │
│  - 记录源Agent                   │
│  - 设置TTL (60分钟)              │
│  - 缓存到Redis                   │
└─────────────────────────────────┘
    ↓
Agent B 检查是否存在
    ↓
check_data_exists("research_findings")
    ↓
存在 → 直接使用，跳过重复研究
不存在 → Agent B 执行研究
```

### 7.3 访问控制

```python
# 伪代码
async def get_shared_data(session_id, data_key, accessing_agent):
    data = await db.get_shared_data(session_id, data_key)

    # 检查访问权限
    if data.target_agents:
        if accessing_agent not in data.target_agents:
            raise AccessDeniedError()

    # 更新访问统计
    data.access_count += 1
    data.last_accessed_by = accessing_agent

    return data.data_content
```

---

## 八、监控和告警

### 8.1 监控指标

**性能指标**:
- L1/L2/L3命中率
- 平均访问延迟
- 提升事件频率
- API调用节省率

**资源指标**:
- L1内存使用率
- Redis内存使用率
- PostgreSQL连接数
- 向量索引大小

**业务指标**:
- 用户偏好学习准确度
- Agent决策成功率
- 共享工作空间利用率

### 8.2 告警规则

```python
# 伪代码
alert_rules = {
    "L1_MEMORY_HIGH": {
        "condition": lambda stats: stats["l1_usage"] > 0.9,
        "severity": "WARNING",
        "message": "L1内存使用率超过90%"
    },
    "REDIS_DOWN": {
        "condition": lambda stats: not stats["redis_available"],
        "severity": "CRITICAL",
        "message": "Redis服务不可用"
    },
    "LOW_HIT_RATE": {
        "condition": lambda stats: stats["hit_rate"] < 0.5,
        "severity": "INFO",
        "message": "整体命中率低于50%"
    }
}
```
