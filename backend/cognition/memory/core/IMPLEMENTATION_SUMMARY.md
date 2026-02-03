# MultiAgentPPT 记忆系统架构实现总结

## 实施日期
2026-02-03

## 实施概览

本次实施完成了记忆系统的核心架构改进，包括自动提升机制、分布式锁、向量缓存和生命周期管理。

---

## 一、已实现功能

### 1.1 自动提升引擎 (Phase 1)

**文件**: `backend/cognition/memory/core/core/promotion_engine.py`

**核心组件**:
1. **ActiveScopeTracker** - 活跃作用域追踪器
   - 维护活跃作用域列表，避免全量扫描
   - TTL自动过期清理
   - 支持增量更新

2. **PromotionRuleEngine** - 提升规则引擎
   - L1→L2规则: 访问≥3次 或 重要性≥0.7
   - L2→L3规则: 跨会话使用≥2次
   - 支持多规则组合决策

3. **DataMigrator** - 数据迁移器
   - 批量写入L2（50条/批）
   - 逐个写入L3（事务保证）
   - 详细的成功/失败统计

4. **PromotionEventLogger** - 提升事件记录器
   - 记录所有提升事件
   - 支持多维度筛选查询
   - 自动清理旧事件（7天+）

5. **PromotionEngine** - 主提升引擎
   - 整合所有组件
   - 后台自动扫描（每5分钟）
   - 配置化阈值参数

**配置参数**:
```python
PROMOTE_L1_ACCESS_COUNT = 3      # L1→L2访问次数阈值
PROMOTE_L1_IMPORTANCE = 0.7      # L1→L2重要性阈值
PROMOTE_L2_SESSION_COUNT = 2     # L2→L3会话数阈值
PROMOTION_SCAN_INTERVAL = 300    # 扫描间隔（秒）
```

**集成到HierarchicalMemoryManager**:
- `hierarchical_memory_manager.py` 已更新
- 新增 `promotion_config` 参数
- 新增 `get_promotion_history()` 方法
- 自动标记活跃作用域

---

### 1.2 分布式锁服务 (Phase 2)

**文件**: `backend/cognition/memory/core/services/distributed_lock_service.py`

**核心功能**:
1. **分布式锁实现**
   - 基于Redis SET NX + Lua脚本
   - 防止误删其他客户端的锁
   - 自动重试机制（最多3次）

2. **锁续期机制**
   - 手动延长TTL
   - 自动续期循环（70%阈值触发）
   - 支持长时间任务

3. **上下文管理器**
   - 支持async with语法
   - 自动释放锁
   - 异常安全

4. **装饰器支持**
   ```python
   @distributed_lock("update_user:{user_id}", ttl=5000)
   async def update_user(user_id: str, data: dict):
       ...
   ```

**配置参数**:
```python
DEFAULT_TTL = 10000              # 默认TTL（10秒）
MAX_RETRIES = 3                  # 最大重试次数
RETRY_DELAY_MS = 200             # 重试延迟（毫秒）
AUTO_RENEWAL_THRESHOLD = 0.7     # 自动续期阈值
```

**使用示例**:
```python
lock_service = get_lock_service()

# 方式1: 上下文管理器
async with lock_service.acquire("user_profile:update:123", ttl=10):
    await update_user_profile(...)

# 方式2: 手动控制
lock = await lock_service.acquire("key", ttl=5000, auto_renewal=True)
try:
    await long_running_task()
finally:
    await lock.release()
```

---

### 1.3 向量缓存服务 (Phase 2)

**文件**: `backend/cognition/memory/core/services/vector_cache_service.py`

**核心功能**:
1. **LRU内存缓存**
   - 容量限制（10000条）
   - 自动淘汰最旧条目
   - TTL过期清理

2. **Redis二级缓存**
   - 分布式缓存共享
   - 减少重复计算
   - 缓存预热支持

3. **OpenAI集成**
   - text-embedding-3-small模型
   - 批量向量生成
   - API调用统计

4. **后台清理任务**
   - 每5分钟清理过期
   - 自动优化缓存

**配置参数**:
```python
DEFAULT_TTL = 7200               # 缓存TTL（2小时）
MAX_CACHE_SIZE = 10000           # 最大缓存数
BATCH_SIZE = 100                 # 批量大小
EMBEDDING_MODEL = "text-embedding-3-small"
```

**使用示例**:
```python
cache_service = get_vector_cache()

# 获取向量（自动缓存）
embedding = await cache_service.get_embedding("查询文本")

# 批量获取
embeddings = await cache_service.get_embeddings(["文本1", "文本2"])

# 预热缓存
await cache_service.warm_cache(["常用问题1", "常用问题2"])

# 查看统计
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

### 1.4 生命周期管理服务 (Phase 3)

**文件**: `backend/cognition/memory/core/services/lifecycle_manager_service.py`

**核心功能**:
1. **时间衰减重要性**
   - 公式: `importance * 0.95^(days/30)`
   - 自动更新L3数据重要性
   - 最低值保护（0.1）

2. **数据温度分类**
   - 热数据: 0-30天（PG主库）
   - 温数据: 30-180天（只读副本）
   - 冷数据: 180天+（归档）

3. **内容摘要**
   - LLM自动摘要（GPT-3.5）
   - 压缩到500字以内
   - 保留向量嵌入

4. **定期清理**
   - 删除低价值过期数据
   - 每天24:00执行
   - 统计报告

**配置参数**:
```python
DECAY_RATE = 0.95               # 衰减率
DECAY_PERIOD_DAYS = 30          # 衰减周期
HOT_DAYS = 30                   # 热数据阈值
WARM_DAYS = 180                 # 温数据阈值
COLD_DAYS = 180                 # 冷数据阈值
```

**使用示例**:
```python
lifecycle = get_lifecycle_manager(db_manager)

# 计算衰减重要性
decayed = lifecycle.calculate_decay_importance(
    original_importance=0.8,
    days_since_creation=60
)
# 返回: 0.8 * 0.95^2 ≈ 0.72

# 手动归档
archived_count = await lifecycle.archive_cold_data()

# 恢复归档数据
data = await lifecycle.retrieve_archived_data(memory_id)

# 获取统计
stats = await lifecycle.get_lifecycle_stats()
# {
#     "data_temperature": {"hot": 1520, "warm": 890, "cold": 120},
#     "avg_importance": 0.52,
#     "archived_count": 45
# }
```

---

### 1.5 REST API (Phase 1-3)

**文件**: `backend/cognition/memory/core/api/memory_api.py`

**API端点**:

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/memory/stats` | 全局统计信息 |
| GET | `/api/memory/promotions` | 提升历史查询 |
| GET | `/api/memory/users/{id}/preferences` | 用户偏好查询 |
| GET | `/api/memory/agents/{name}/performance` | Agent性能统计 |
| POST | `/api/memory/promote` | 手动提升数据 |
| POST | `/api/memory/cleanup` | 执行清理任务 |
| GET | `/api/memory/lifecycle` | 生命周期统计 |
| GET | `/api/memory/health` | 健康检查 |

**使用示例**:
```bash
# 获取统计信息
curl http://localhost:8001/api/memory/stats

# 查询提升历史
curl "http://localhost:8001/api/memory/promotions?limit=50&reason=cross_session_usage"

# 手动提升数据
curl -X POST http://localhost:8001/api/memory/promote \
  -H "Content-Type: application/json" \
  -d '{"key": "research_findings", "scope": "user", "scope_id": "user123"}'

# 执行清理
curl -X POST http://localhost:8001/api/memory/cleanup
```

---

## 二、依赖项

### 新增依赖

```txt
# requirements.txt 新增项
fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0.0
openai>=1.0.0
redis>=4.5.0
```

### 环境变量

```bash
# Redis配置
REDIS_URL=redis://localhost:6379/0

# 数据库配置
DATABASE_URL=postgresql://user:pass@localhost:5432/multiagent_ppt

# OpenAI配置
OPENAI_API_KEY=sk-...
```

---

## 三、部署指南

### 3.1 初始化数据库

```bash
cd backend/cognition/memory/core
python database.py --init
```

### 3.2 启动API服务

```bash
cd backend/cognition/memory/core/api
python memory_api.py
# 或使用uvicorn
uvicorn memory_api:app --host 0.0.0.0 --port 8001
```

### 3.3 集成到主应用

```python
from fastapi import FastAPI
from cognition.memory.core.api import router

app = FastAPI()
app.include_router(router)
```

---

## 四、监控指标

### 4.1 性能指标

- L1/L2/L3命中率
- 平均访问延迟
- 提升事件频率
- 数据流转速率

### 4.2 资源指标

- L1内存使用率
- Redis内存使用率
- PostgreSQL连接数
- 向量索引大小

### 4.3 业务指标

- 用户偏好学习准确度
- Agent决策成功率
- 共享工作空间利用率
- API调用节省比例

---

## 五、架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    REST API层 (FastAPI)                         │
├─────────────────────────────────────────────────────────────────┤
│          统一管理器 (HierarchicalMemoryManager)                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ 提升引擎     │  │ 分布式锁     │  │ 生命周期管理         │ │
│  │ Promotion    │  │ Distributed  │  │ LifecycleManager     │ │
│  │ Engine       │  │ Lock         │  │                      │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ 向量缓存     │  │ 用户偏好     │  │ Agent决策追踪        │ │
│  │ VectorCache  │  │ UserPref     │  │ AgentDecision        │ │
│  │ Service      │  │ Service      │  │ Service              │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
├─────────────┬────────────────┬──────────────────────────────────┤
│  L1 瞬时    │   L2 短期      │      L3 长期                   │
│  Python     │   Redis缓存    │      PostgreSQL + pgvector     │
│  LRU        │   会话级(1h)   │      永久存储                   │
└─────────────┴────────────────┴──────────────────────────────────┘
```

---

## 六、后续优化建议

### Phase 4: 企业级特性（可选）

1. **L4分布式存储层**
   - Cassandra/Qdrant集成
   - 跨实例数据同步
   - 百万级向量检索

2. **高可用部署**
   - 主从复制
   - 故障自动转移
   - 多区域部署

3. **高级分析**
   - 访问模式分析
   - 预测性缓存
   - 自动调优

---

## 七、文件清单

### 新增文件

```
backend/cognition/memory/core/
├── core/
│   └── promotion_engine.py          # 自动提升引擎
├── services/
│   ├── distributed_lock_service.py  # 分布式锁服务
│   ├── vector_cache_service.py      # 向量缓存服务
│   └── lifecycle_manager_service.py # 生命周期管理服务
└── api/
    ├── __init__.py
    └── memory_api.py                # REST API
```

### 修改文件

```
backend/cognition/memory/core/
├── core/
│   └── hierarchical_memory_manager.py  # 集成提升引擎
├── models.py                          # 添加Boolean/func导入
└── services/
    └── shared_workspace_service.py    # 添加func导入
```

---

## 八、测试建议

### 单元测试

```python
# tests/test_promotion_engine.py
async def test_active_scope_tracker():
    tracker = ActiveScopeTracker()
    await tracker.mark_active(MemoryScope.USER, "user123")
    assert await tracker.is_active(MemoryScope.USER, "user123")

# tests/test_distributed_lock.py
async def test_lock_acquire_release():
    service = DistributedLockService()
    lock = await service.acquire("test_key", ttl=1000)
    assert lock is not None
    await lock.release()
```

### 集成测试

```python
# tests/test_memory_integration.py
async def test_auto_promotion_flow():
    manager = HierarchicalMemoryManager(enable_auto_promotion=True)
    await manager.start_background_tasks()

    # 写入L1数据
    await manager.set("key1", "value1", MemoryScope.USER, "user123")

    # 多次访问触发提升
    for _ in range(3):
        await manager.get("key1", MemoryScope.USER, "user123")

    # 等待提升任务执行
    await asyncio.sleep(310)

    # 验证已提升到L2
    result = await manager.l2.get("key1", MemoryScope.USER, "user123")
    assert result is not None
```

---

**文档版本**: v1.0
**实施者**: Claude Sonnet
**状态**: 已完成
