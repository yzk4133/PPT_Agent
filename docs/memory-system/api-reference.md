# API 接口文档

## 一、REST API 概述

记忆系统提供了一套完整的REST API，用于监控、管理和查询记忆系统。

**基础URL**: `http://localhost:8001/api/memory`

**认证方式**: Bearer Token（可选，根据部署配置）

**响应格式**: JSON

---

## 二、统计和监控接口

### 2.1 获取全局统计信息

**接口**: `GET /stats`

**描述**: 获取记忆系统的全局统计信息，包括各层数据量、命中率、提升统计等。

**请求参数**: 无

**响应示例**:
```json
{
  "l1_transient": {
    "layer": "transient",
    "data_count": 856,
    "capacity": 1000,
    "hit_rate": 0.75,
    "hits": 3250,
    "misses": 1083,
    "evictions": 145
  },
  "l2_short_term": {
    "layer": "short_term",
    "redis_available": true,
    "redis_memory_used_mb": 45.6,
    "hit_rate": 0.82,
    "hits": 5120,
    "misses": 1125
  },
  "l3_long_term": {
    "layer": "long_term",
    "total_records": 4520,
    "avg_importance": 0.62,
    "total_accesses": 15630,
    "unique_users": 245
  },
  "promotion": {
    "total_promotions": 1250,
    "unique_keys_promoted": 856,
    "by_reason": {
      "high_access_frequency": 680,
      "high_importance_score": 420,
      "cross_session_usage": 150
    },
    "by_layer_transition": {
      "L1_TRANSIENT_to_L2_SHORT_TERM": 856,
      "L2_SHORT_TERM_to_L3_LONG_TERM": 394
    }
  },
  "total_data_count": 5376,
  "promotion_engine": {
    "scope_tracker": {
      "total_active_scopes": 42
    },
    "migration": {
      "l1_to_l2": {"total": 856, "success": 856, "failed": 0},
      "l2_to_l3": {"total": 394, "success": 394, "failed": 0}
    },
    "events": {
      "total_events": 1250,
      "successful": 1250,
      "failed": 0
    }
  }
}
```

**使用场景**:
- 监控系统健康状态
- 查看资源使用情况
- 分析数据流转效率

---

### 2.2 获取提升历史

**接口**: `GET /promotions`

**描述**: 查询数据提升事件历史，支持多种筛选条件。

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| limit | integer | 否 | 最大返回数，默认100，最大1000 |
| from_layer | string | 否 | 筛选源层级 (L1_TRANSIENT, L2_SHORT_TERM) |
| to_layer | string | 否 | 筛选目标层级 (L2_SHORT_TERM, L3_LONG_TERM) |
| reason | string | 否 | 筛选原因 (HIGH_ACCESS_FREQUENCY, HIGH_IMPORTANCE_SCORE, CROSS_SESSION_USAGE) |
| key | string | 否 | 筛选特定键名 |

**响应示例**:
```json
[
  {
    "event_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-02-03T10:30:00Z",
    "key": "user_research_findings",
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
  },
  {
    "event_id": "550e8400-e29b-41d4-a716-446655440001",
    "timestamp": "2026-02-03T10:35:00Z",
    "key": "shared_workspace_data",
    "from_layer": "L2_SHORT_TERM",
    "to_layer": "L3_LONG_TERM",
    "reason": "CROSS_SESSION_USAGE",
    "scope": "session",
    "scope_id": "session_abc",
    "access_count": 8,
    "importance": 0.6,
    "session_count": 3,
    "explanation": "cross_session_count=3 >= 2",
    "success": true
  }
]
```

**使用场景**:
- 分析数据流转模式
- 调试自动提升逻辑
- 优化提升阈值参数

---

### 2.3 获取生命周期统计

**接口**: `GET /lifecycle`

**描述**: 获取数据生命周期统计，包括温度分布、归档数量等。

**请求参数**: 无

**响应示例**:
```json
{
  "data_temperature": {
    "hot": 1520,
    "warm": 890,
    "cold": 120,
    "total": 2530
  },
  "avg_importance": 0.52,
  "archived_count": 45,
  "stats": {
    "archived_count": 45,
    "decayed_count": 1250,
    "cleaned_count": 85,
    "summary_generated": 45
  }
}
```

**使用场景**:
- 监控数据老化情况
- 评估归档策略效果
- 预测存储增长

---

### 2.4 健康检查

**接口**: `GET /health`

**描述**: 检查记忆系统各层服务的健康状态。

**请求参数**: 无

**响应示例**:
```json
{
  "status": "healthy",
  "l1_transient": "ok",
  "l2_short_term": "ok",
  "l3_long_term": "ok"
}
```

**降级响应示例**:
```json
{
  "status": "degraded",
  "l1_transient": "ok",
  "l2_short_term": "error",
  "l3_long_term": "ok"
}
```

**使用场景**:
- 服务健康监控
- 负载均衡健康检查
- 告警系统触发

---

## 三、用户偏好接口

### 3.1 获取用户偏好

**接口**: `GET /users/{user_id}/preferences`

**描述**: 获取指定用户的偏好配置和统计信息。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户ID |

**响应示例**:
```json
{
  "user_id": "user123",
  "preferences": {
    "language": "zh-CN",
    "default_slides": 10,
    "style": "professional",
    "color_scheme": "blue",
    "font_size": "medium",
    "template": "modern_business"
  },
  "total_sessions": 25,
  "successful_generations": 22,
  "avg_satisfaction_score": 0.82
}
```

**使用场景**:
- 生成时应用用户偏好
- 分析用户行为模式
- 个性化推荐

---

## 四、Agent性能接口

### 4.1 获取Agent性能统计

**接口**: `GET /agents/{agent_name}/performance`

**描述**: 获取指定Agent的性能统计数据。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| agent_name | string | Agent名称 |

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| session_id | string | 否 | 筛选特定会话 |
| limit | integer | 否 | 返回数量，默认50，最大500 |

**响应示例**:
```json
{
  "agent_name": "ResearchAgent",
  "total_decisions": 156,
  "success_rate": 0.92,
  "avg_execution_time_ms": 245.5,
  "common_actions": [
    {"action": "search", "count": 85},
    {"action": "database_query", "count": 45},
    {"action": "api_call", "count": 26}
  ],
  "recent_decisions": [
    {
      "decision_type": "tool_selection",
      "selected_action": "search",
      "outcome": "success",
      "execution_time_ms": 180,
      "timestamp": "2026-02-03T10:30:00Z"
    }
  ]
}
```

**使用场景**:
- 监控Agent运行状态
- 分析工具使用模式
- 优化决策逻辑

---

## 五、管理操作接口

### 5.1 手动提升数据

**接口**: `POST /promote`

**描述**: 手动将指定数据提升到L3长期存储层。

**请求体**:
```json
{
  "key": "research_findings",
  "scope": "user",
  "scope_id": "user123",
  "reason": "manual_promotion"
}
```

**参数说明**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| key | string | 是 | 数据键名 |
| scope | string | 是 | 作用域 (task, session, agent, workspace, user) |
| scope_id | string | 是 | 作用域ID |
| reason | string | 否 | 提升原因，默认manual_promotion |

**响应示例**:
```json
{
  "success": true,
  "message": "Successfully promoted research_findings to L3"
}
```

**失败响应**:
```json
{
  "success": false,
  "message": "Failed to promote research_findings (not found)"
}
```

**使用场景**:
- 用户标记重要数据
- 紧急数据持久化
- 调试和测试

---

### 5.2 执行清理任务

**接口**: `POST /cleanup`

**描述**: 手动触发数据生命周期管理任务，包括更新衰减、归档和清理。

**请求参数**: 无

**响应示例**:
```json
{
  "decayed_count": 125,
  "archived_count": 15,
  "cleaned_count": 8,
  "message": "Cleanup completed successfully"
}
```

**使用场景**:
- 立即清理过期数据
- 手动触发归档
- 维护操作

---

## 六、Python SDK 接口

除了REST API，记忆系统还提供了Python SDK供内部使用。

### 6.1 HierarchicalMemoryManager

**初始化**:
```python
# 伪代码
manager = HierarchicalMemoryManager(
    l1_capacity=1000,                    # L1容量
    l2_redis_url="redis://localhost",    # Redis地址
    l3_db_manager=db_manager,            # 数据库管理器
    enable_auto_promotion=True,          # 启用自动提升
    promotion_config=custom_config       # 提升配置（可选）
)
```

**写入数据**:
```python
# 伪代码
await manager.set(
    key="research_findings",             # 数据键
    value={"findings": [...]},          # 数据值
    scope=MemoryScope.USER,             # 作用域
    scope_id="user123",                 # 作用域ID
    importance=0.8,                     # 重要性(0-1)
    target_layer=None,                  # 目标层（None=自动选择）
    tags=["research", "important"]      # 标签
)
```

**读取数据**:
```python
# 伪代码
result = await manager.get(
    key="research_findings",
    scope=MemoryScope.USER,
    scope_id="user123",
    search_all_layers=True              # 是否搜索所有层
)

if result:
    value, metadata = result
    print(f"数据: {value}")
    print(f"访问次数: {metadata.access_count}")
    print(f"重要性: {metadata.importance}")
```

**删除数据**:
```python
# 伪代码
deleted = await manager.delete(
    key="research_findings",
    scope=MemoryScope.USER,
    scope_id="user123",
    delete_all_layers=True              # 是否删除所有层
)
```

**清空作用域**:
```python
# 伪代码
counts = await manager.clear_scope(
    scope=MemoryScope.SESSION,
    scope_id="session_abc",
    layers=[MemoryLayer.L1_TRANSIENT]   # 指定清理的层
)
```

**手动提升到L3**:
```python
# 伪代码
success = await manager.promote_to_l3(
    key="important_data",
    scope=MemoryScope.USER,
    scope_id="user123",
    reason=PromotionReason.MANUAL_PROMOTION
)
```

**语义检索**:
```python
# 伪代码
results = await manager.semantic_search(
    query_embedding=[0.1, 0.2, ...],     # 查询向量
    scope=MemoryScope.USER,
    scope_id="user123",
    limit=10,                           # 返回数量
    min_importance=0.3                   # 最低重要性
)

for key, content, similarity in results:
    print(f"{key}: {similarity:.2f}")
```

---

### 6.2 DistributedLockService

**获取锁（上下文管理器）**:
```python
# 伪代码
lock_service = get_lock_service()

async with lock_service.acquire(
    key="user_profile:update:123",
    ttl=10000,                          # TTL（毫秒）
    auto_renewal=True                   # 自动续期
) as lock:
    # 执行临界区代码
    await update_user_profile(123, new_data)
    # 锁会在退出时自动释放
```

**获取锁（手动控制）**:
```python
# 伪代码
lock = await lock_service.acquire(
    key="vector_memory:batch_write",
    ttl=30000,
    wait_timeout=5000                   # 等待超时（毫秒）
)

try:
    await batch_write_vectors(vectors)
finally:
    await lock.release()
```

**装饰器使用**:
```python
# 伪代码
@distributed_lock("update_user:{user_id}", ttl=5000)
async def update_user(user_id: str, data: dict):
    await db.update_user(user_id, data)
```

---

### 6.3 VectorCacheService

**获取向量嵌入**:
```python
# 伪代码
cache_service = get_vector_cache()

embedding = await cache_service.get_embedding(
    text="用户查询文本",
    model="text-embedding-3-small",      # 可选
    use_cache=True                       # 是否使用缓存
)
```

**批量获取**:
```python
# 伪代码
embeddings = await cache_service.get_embeddings(
    texts=["文本1", "文本2", "文本3"],
    use_cache=True
)
```

**预热缓存**:
```python
# 伪代码
await cache_service.warm_cache([
    "常用问题1",
    "常用问题2",
    "系统关键文本"
])
```

**获取统计**:
```python
# 伪代码
stats = await cache_service.get_stats()
# {
#     "hits": 1250,
#     "misses": 150,
#     "api_calls": 150,
#     "hit_rate": 0.89,
#     "api_calls_saved": 1250
# }
```

---

### 6.4 LifecycleManagerService

**计算衰减重要性**:
```python
# 伪代码
lifecycle = get_lifecycle_manager(db_manager)

decayed = lifecycle.calculate_decay_importance(
    original_importance=0.8,
    days_since_creation=60
)
# 返回: 0.72 (0.8 * 0.95^2)
```

**手动归档**:
```python
# 伪代码
archived_count = await lifecycle.archive_cold_data(
    min_access_count=1                  # 最低访问次数
)
```

**恢复归档数据**:
```python
# 伪代码
data = await lifecycle.retrieve_archived_data(
    memory_id="550e8400-..."
)
```

**执行生命周期任务**:
```python
# 伪代码
await lifecycle.perform_lifecycle_tasks()
# 自动执行：
# 1. 更新衰减重要性
# 2. 归档冷数据
# 3. 清理过期数据
```

---

## 七、错误处理

### 7.1 错误响应格式

所有错误响应遵循统一格式：

```json
{
  "error": {
    "code": "MEMORY_NOT_FOUND",
    "message": "Requested memory key not found in any layer",
    "details": {
      "key": "non_existent_key",
      "scope": "user",
      "scope_id": "user123"
    }
  }
}
```

### 7.2 常见错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| MEMORY_NOT_FOUND | 404 | 指定的键不存在 |
| INVALID_SCOPE | 400 | 无效的作用域 |
| INVALID_LAYER | 400 | 无效的层级 |
| LOCK_ACQUISITION_FAILED | 429 | 获取锁失败 |
| REDIS_UNAVAILABLE | 503 | Redis服务不可用 |
| DATABASE_ERROR | 500 | 数据库错误 |

### 7.3 错误处理示例

```python
# 伪代码
try:
    result = await manager.get(key, scope, scope_id)
except MemoryNotFoundError:
    # 处理键不存在
    return None
except InvalidScopeError:
    # 处理无效作用域
    raise ValueError(f"Invalid scope: {scope}")
except RedisUnavailableError:
    # Redis降级，直接查询L3
    return await manager.l3.get(key, scope, scope_id)
```

---

## 八、速率限制

### 8.1 速率限制策略

| 端点类型 | 限制 | 窗口 |
|---------|------|------|
| 查询接口 (GET) | 100请求/分钟 | 滑动窗口 |
| 写入接口 (POST) | 20请求/分钟 | 滑动窗口 |
| 管理接口 (POST) | 10请求/分钟 | 滑动窗口 |

### 8.2 速率限制响应

超出限制时返回：

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1675776000

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please try again later.",
    "retry_after": 60
  }
}
```

---

## 九、API版本管理

### 9.1 版本策略

- 当前版本: `v1`
- 版本前缀: `/api/v1/memory`（可选，默认使用`/api/memory`）
- 向后兼容性: 保证v1 API向后兼容

### 9.2 版本迁移

**请求指定版本**:
```http
GET /api/v1/memory/stats
GET /api/v2/memory/stats  # 未来版本
```

**响应头标识版本**:
```http
X-API-Version: v1
```

---

## 十、API使用示例

### 10.1 监控脚本示例

```python
# 伪代码
import aiohttp
import asyncio

async def monitor_memory_system():
    async with aiohttp.ClientSession() as session:
        # 获取统计信息
        async with session.get("http://localhost:8001/api/memory/stats") as resp:
            stats = await resp.json()

        # 检查健康状态
        async with session.get("http://localhost:8001/api/memory/health") as resp:
            health = await resp.json()

        # 分析和告警
        if stats["l1_transient"]["hit_rate"] < 0.5:
            print("WARNING: L1 hit rate below 50%")

        if health["status"] != "healthy":
            print(f"ALERT: System status is {health['status']}")

        # 打印报告
        print(f"Total data: {stats['total_data_count']}")
        print(f"Promotions today: {stats['promotion']['total_promotions']}")

asyncio.run(monitor_memory_system())
```

### 10.2 数据管理示例

```python
# 伪代码
async def cleanup_old_session(session_id: str):
    """清理旧会话数据"""
    manager = get_global_memory_manager()

    # 检查会话是否存在
    stats = await manager.get_stats()
    print(f"Current L1 count: {stats['l1_transient']['data_count']}")

    # 清空会话数据
    counts = await manager.clear_scope(
        scope=MemoryScope.SESSION,
        scope_id=session_id
    )

    print(f"Cleaned: L1={counts['l1']}, L2={counts['l2']}, L3={counts['l3']}")

    # 触发清理任务
    async with aiohttp.ClientSession() as session:
        async with session.post("http://localhost:8001/api/memory/cleanup") as resp:
            result = await resp.json()
            print(f"Cleanup result: {result}")
```

---

## 十一、Webhook通知

### 11.1 配置Webhook

系统支持向指定URL发送事件通知：

```json
{
  "webhook_url": "https://your-server.com/memory-events",
  "events": [
    "promotion.completed",
    "lifecycle.cleanup",
    "system.alert"
  ]
}
```

### 11.2 Webhook Payload

```json
{
  "event": "promotion.completed",
  "timestamp": "2026-02-03T10:30:00Z",
  "data": {
    "key": "research_findings",
    "from_layer": "L1_TRANSIENT",
    "to_layer": "L2_SHORT_TERM",
    "reason": "HIGH_ACCESS_FREQUENCY"
  }
}
```
