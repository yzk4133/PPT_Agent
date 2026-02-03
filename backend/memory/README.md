# 持久化记忆系统 - 完整指南

## 📂 目录结构

```
persistent_memory/
├── core/                           # 三层内存架构核心
│   ├── memory_layer_base.py             抽象基类和接口定义
│   ├── l1_transient_layer.py            L1瞬时内存（纯内存，LRU）
│   ├── l2_short_term_layer.py           L2短期内存（Redis）
│   ├── l3_longterm_layer.py             L3长期内存（PostgreSQL+pgvector）
│   └── hierarchical_memory_manager.py   统一管理器
│
├── services/                       # 业务服务层
│   ├── postgres_session_service.py      会话管理服务
│   ├── user_preference_service.py       用户偏好服务
│   ├── vector_memory_service.py         向量检索服务
│   ├── agent_decision_service.py        Agent决策追踪
│   ├── tool_feedback_service.py         工具执行反馈
│   ├── shared_workspace_service.py      Multi-Agent协作
│   └── context_optimizer.py             上下文窗口优化
│
├── demos/                          # 演示和测试
│   ├── demo_hierarchical_memory.py      三层架构完整演示
│   ├── demo_p0_p1_integration.py        P0-P1功能演示
│   └── benchmark_hierarchical_memory.py 性能基准测试
│
├── migrations/                     # 数据库迁移
│   ├── migrate_hierarchical_memory.py   三层架构迁移
│   └── migrate_p0_p1.py                 P0-P1功能迁移
│
├── database.py                     # 数据库连接管理
├── models.py                       # SQLAlchemy数据模型
├── redis_cache.py                  # Redis缓存封装
├── requirements.txt                # Python依赖
└── README.md                       # 本文档
```

---

## 🎯 架构概览

### 三层内存架构

```
┌─────────────────────────────────────────────────────────┐
│              应用层 (Agent Services)                     │
├─────────────────────────────────────────────────────────┤
│        HierarchicalMemoryManager (统一接口)             │
├─────────────────────────────────────────────────────────┤
│  L1 瞬时内存    │  L2 短期内存    │  L3 长期内存       │
│  (Transient)    │  (Short-term)   │  (Long-term)        │
│                 │                 │                      │
│  • 纯内存存储    │  • Redis存储    │  • PostgreSQL       │
│  • LRU淘汰      │  • Session级    │  • pgvector语义检索 │
│  • Task级TTL    │  • 1小时TTL     │  • 永久持久化       │
│  • 5-10x写入速度│  • 批量操作     │  • 跨会话数据       │
└─────────────────────────────────────────────────────────┘

自动提升规则：
• L1→L2: 访问≥3次 或 重要性≥0.7
• L2→L3: 跨会话使用≥2次
• 手动：用户标记重要 → 直接L3
```

### 性能提升

- ⚡ **写入加速 5-10x**: L1纯内存写入
- 🚀 **读取加速 10-50x**: 缓存命中避免DB查询
- 📦 **批量操作 2-5x**: 减少网络往返
- 💾 **DB负载降低 60%+**: 过滤临时数据

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
cd backend/persistent_memory
pip install -r requirements.txt

# 配置环境变量
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/multiagent_ppt"
export REDIS_URL="redis://localhost:6379/0"
export OPENAI_API_KEY="sk-your-key"

# 启动数据库服务
docker-compose up -d postgres redis
```

### 2. 数据库迁移

```bash
# 初始化三层架构
python migrations/migrate_hierarchical_memory.py

# 初始化P0-P1功能（可选）
python migrations/migrate_p0_p1.py
```

### 3. 基础使用

```python
from persistent_memory import HierarchicalMemoryManager, MemoryScope

# 创建内存管理器
memory = HierarchicalMemoryManager(l1_capacity=1000)
await memory.start_background_tasks()

# 写入数据
await memory.set(
    key="user_pref",
    value={"theme": "dark", "lang": "zh-CN"},
    scope=MemoryScope.USER,
    scope_id="user_123",
    importance=0.7  # 0-1，影响存储层选择
)

# 读取数据（自动搜索L1→L2→L3）
result = await memory.get("user_pref", MemoryScope.USER, "user_123")
if result:
    value, metadata = result
    print(f"值: {value}, 层级: {metadata.layer.value}")

# 清理
await memory.stop_background_tasks()
```

### 4. 全局单例模式（推荐）

```python
from persistent_memory import (
    init_global_memory_manager,
    get_global_memory_manager,
    shutdown_global_memory_manager
)

# 应用启动
await init_global_memory_manager(l1_capacity=2000)

# 任何地方使用
memory = get_global_memory_manager()
await memory.set("key", "value", MemoryScope.TASK, "task_123")

# 应用关闭
await shutdown_global_memory_manager()
```

---

## 📚 核心功能

### 1. 三层内存架构

#### L1 瞬时内存

- **存储**: 纯Python字典 + LRU
- **容量**: 1000条（可配置）
- **生命周期**: 任务级，5分钟默认TTL
- **适用**: 临时计算结果、中间状态

```python
# 自动存入L1（低重要性）
await memory.set(
    "temp_result",
    {"data": "..."},
    MemoryScope.TASK,
    "task_123",
    importance=0.3
)
```

#### L2 短期内存

- **存储**: Redis
- **生命周期**: 会话级，1小时TTL
- **适用**: 会话状态、用户偏好

```python
# 自动存入L2（中等重要性）
await memory.set(
    "session_state",
    {"step": 1},
    MemoryScope.SESSION,
    "sess_456",
    importance=0.6
)
```

#### L3 长期内存

- **存储**: PostgreSQL + pgvector
- **生命周期**: 永久
- **适用**: 用户数据、知识库

```python
# 强制存入L3（高重要性）
await memory.set(
    "user_profile",
    {"name": "张三"},
    MemoryScope.USER,
    "user_123",
    importance=0.9,
    target_layer=MemoryLayer.L3_LONG_TERM
)
```

### 2. 作用域系统

```python
from persistent_memory import MemoryScope

MemoryScope.TASK       # 单个任务（秒级）
MemoryScope.SESSION    # 单个会话（小时级）
MemoryScope.AGENT      # 单个Agent（跨会话）
MemoryScope.WORKSPACE  # 多Agent协作（项目级）
MemoryScope.USER       # 用户全局（永久）
```

### 3. 自动提升机制

```python
# 系统自动监测访问模式
for i in range(5):
    await memory.get("hot_data", MemoryScope.TASK, "task_123")
    # 第3次访问后自动提升到L2

# 手动提升到L3
await memory.promote_to_l3(
    "important_data",
    MemoryScope.USER,
    "user_123",
    reason=PromotionReason.MANUAL_PROMOTION
)
```

### 4. 批量操作

```python
# 任务执行中写入多条数据到L1
for i in range(10):
    await memory.set(f"result_{i}", data, MemoryScope.TASK, "task_123")

# 任务结束批量刷新到L2
flushed = await memory.batch_flush_l1_to_l2(MemoryScope.TASK, "task_123")
print(f"刷新了 {flushed} 条数据")

# 清理L1临时数据
await memory.clear_scope(
    MemoryScope.TASK,
    "task_123",
    layers=[MemoryLayer.L1_TRANSIENT]
)
```

### 5. 语义检索（L3）

```python
# 生成查询向量
import openai
response = openai.embeddings.create(
    model="text-embedding-3-small",
    input="查询文本"
)
query_embedding = response.data[0].embedding

# 语义搜索
results = await memory.semantic_search(
    query_embedding=query_embedding,
    scope=MemoryScope.USER,
    scope_id="user_123",
    limit=10,
    min_importance=0.5
)

for key, content, similarity in results:
    print(f"{key}: {similarity:.2f}")
```

---

## 🎓 使用场景

### 场景1: Agent任务执行

```python
async def execute_agent_task(task_id: str):
    memory = get_global_memory_manager()

    # 1. 存储任务上下文（L1）
    await memory.set(
        "context",
        {"step": 1, "status": "running"},
        MemoryScope.TASK,
        task_id,
        importance=0.3
    )

    # 2. 执行任务，保存中间结果
    for i in range(10):
        result = process_step(i)
        await memory.set(
            f"step_{i}",
            result,
            MemoryScope.TASK,
            task_id,
            importance=0.5
        )

    # 3. 任务完成，批量刷新重要数据到L2
    await memory.batch_flush_l1_to_l2(MemoryScope.TASK, task_id)

    # 4. 清理L1临时数据
    await memory.clear_scope(
        MemoryScope.TASK,
        task_id,
        layers=[MemoryLayer.L1_TRANSIENT]
    )
```

### 场景2: Multi-Agent协作

```python
# Agent1: 生成大纲
async def outline_agent(workspace_id: str):
    memory = get_global_memory_manager()
    await memory.set(
        "ppt_outline",
        {"slides": [...]},
        MemoryScope.WORKSPACE,
        workspace_id,
        importance=0.8,
        tags=["outline", "shared"]
    )

# Agent2: 读取大纲并设计
async def design_agent(workspace_id: str):
    memory = get_global_memory_manager()
    result = await memory.get("ppt_outline", MemoryScope.WORKSPACE, workspace_id)
    if result:
        outline, _ = result
        # 基于大纲进行设计...
```

### 场景3: 会话状态管理

```python
# 保存会话状态
async def save_session(session_id: str, state: dict):
    memory = get_global_memory_manager()
    await memory.set(
        "session_state",
        state,
        MemoryScope.SESSION,
        session_id,
        importance=0.6
    )

# 恢复会话
async def restore_session(session_id: str):
    memory = get_global_memory_manager()
    result = await memory.get("session_state", MemoryScope.SESSION, session_id)
    return result[0] if result else None
```

---

## 🔧 高级功能

### P0-P1功能（业务服务层）

#### Agent决策追踪

```python
from persistent_memory import AgentDecisionService

service = AgentDecisionService()

# 记录决策
await service.record_decision(
    agent_id="agent_outline",
    session_id="sess_123",
    decision_type="select_template",
    context={"user_input": "商务PPT"},
    alternatives=["模板A", "模板B"],
    chosen_option="模板A",
    reasoning="更适合商务场景"
)

# 分析性能
stats = await service.analyze_agent_performance("agent_outline", days=7)
print(f"成功率: {stats['success_rate']:.2%}")
```

#### 工具执行反馈

```python
from persistent_memory import ToolFeedbackService

service = ToolFeedbackService()

# 记录工具调用
feedback_id = await service.record_tool_execution(
    tool_name="bing_search",
    input_params={"query": "AI趋势"},
    output_summary="找到10条结果",
    latency_ms=245,
    success=True
)

# 更新使用反馈
await service.update_usage_feedback(
    feedback_id,
    used_in_final_output=True,
    relevance_score=0.9
)

# 获取工具排名
rankings = await service.get_tool_rankings(metric="success_rate")
```

#### 上下文优化

```python
from persistent_memory import ContextWindowOptimizer

optimizer = ContextWindowOptimizer(max_tokens=8000)

# 构建优化上下文
context = await optimizer.build_optimized_context(
    session_id="sess_123",
    required_skills=["outline", "design"],
    user_id="user_123"
)

print(f"Token使用: {context['token_count']}/{context['max_tokens']}")
```

---

## 🧪 测试和演示

### 运行完整演示

```bash
python demos/demo_hierarchical_memory.py
```

演示内容：

1. 基础操作（get/set/delete/exists）
2. 自动提升（L1→L2→L3）
3. 批量操作
4. Multi-Agent协作
5. 系统统计
6. 全局单例

### 运行性能测试

```bash
python demos/benchmark_hierarchical_memory.py
```

预期结果：

- ✅ 写入性能提升 5-10x
- ✅ 读取性能提升 10-50x
- ✅ DB负载减少 60%+

### 运行P0-P1演示

```bash
python demos/demo_p0_p1_integration.py
```

---

## 📊 API参考

### HierarchicalMemoryManager

#### 初始化

```python
memory = HierarchicalMemoryManager(
    l1_capacity=1000,              # L1最大容量
    l2_redis_url=None,             # Redis连接（None使用环境变量）
    l3_db_manager=None,            # DB管理器（None使用默认）
    enable_auto_promotion=True     # 启用自动提升
)
```

#### 核心方法

```python
# 写入
await memory.set(key, value, scope, scope_id, importance=0.5,
                 target_layer=None, tags=None)

# 读取（自动搜索L1→L2→L3）
result = await memory.get(key, scope, scope_id, search_all_layers=True)

# 删除
await memory.delete(key, scope, scope_id, delete_all_layers=True)

# 存在性检查
exists = await memory.exists(key, scope, scope_id)

# 批量刷新L1→L2
count = await memory.batch_flush_l1_to_l2(scope, scope_id)

# 清空作用域
cleared = await memory.clear_scope(scope, scope_id, layers=None)

# 手动提升到L3
promoted = await memory.promote_to_l3(key, scope, scope_id, reason)

# 语义搜索
results = await memory.semantic_search(query_embedding, scope, scope_id,
                                       limit=10, min_importance=0.3)

# 统计信息
stats = await memory.get_stats()
```

---

## ⚙️ 配置优化

### 1. 合理设置重要性

```python
importance=0.1-0.4  # 临时数据 → L1
importance=0.5-0.7  # 会话数据 → L2
importance=0.8-1.0  # 用户数据 → L3
```

### 2. 选择合适作用域

```python
MemoryScope.TASK       # 短生命周期
MemoryScope.SESSION    # 会话级
MemoryScope.USER       # 持久化
```

### 3. 调整L1容量

```python
# 高并发场景
memory = HierarchicalMemoryManager(l1_capacity=5000)

# 资源受限
memory = HierarchicalMemoryManager(l1_capacity=500)
```

### 4. 监控性能

```python
stats = await memory.get_stats()
print(f"L1命中率: {stats['l1_transient']['hit_rate']:.2%}")
print(f"L1数据量: {stats['l1_transient']['data_count']}")
print(f"总提升次数: {stats['promotion']['total_promotions']}")
```

---

## 🔍 故障排查

### Redis连接失败

```bash
# 检查服务
docker ps | grep redis
redis-cli ping  # 应返回PONG

# 检查环境变量
echo $REDIS_URL
```

### PostgreSQL连接失败

```bash
# 检查服务
docker ps | grep postgres
psql $DATABASE_URL -c "SELECT 1"

# 查看日志
docker logs multiagent_ppt_postgres
```

### pgvector不可用

```sql
-- 进入PostgreSQL
\c multiagent_ppt

-- 启用扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 验证
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### 性能不达预期

```python
# 检查命中率
stats = await memory.get_stats()
if stats['l1_transient']['hit_rate'] < 0.5:
    # 增加L1容量
    memory = HierarchicalMemoryManager(l1_capacity=5000)
    # 或提高数据重要性
    await memory.set(..., importance=0.7)
```

---

## 🤝 集成指南

### 步骤1: 应用启动/关闭

```python
# main.py
from persistent_memory import init_global_memory_manager, shutdown_global_memory_manager

async def startup():
    await init_global_memory_manager(
        l1_capacity=2000,
        enable_auto_promotion=True
    )
    print("内存系统已启动")

async def shutdown():
    await shutdown_global_memory_manager()
    print("内存系统已关闭")
```

### 步骤2: 更新Agent基类

```python
from persistent_memory import get_global_memory_manager, MemoryScope

class BaseAgent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.memory = get_global_memory_manager()

    async def save_state(self, key: str, value: Any):
        await self.memory.set(
            key=key,
            value=value,
            scope=MemoryScope.AGENT,
            scope_id=self.agent_id,
            importance=0.6
        )

    async def load_state(self, key: str):
        result = await self.memory.get(
            key=key,
            scope=MemoryScope.AGENT,
            scope_id=self.agent_id
        )
        return result[0] if result else None
```

### 步骤3: 替换直接DB访问

```python
# ❌ 旧方式
with db.get_session() as session:
    session.execute("INSERT INTO ...")
    session.commit()

# ✅ 新方式
await memory.set(
    "data_key",
    data,
    MemoryScope.SESSION,
    session_id,
    importance=0.5
)
```

---

## 📝 版本历史

### v2.0 - 三层内存架构重构

- ✅ 模块化目录结构（core/services/demos/migrations）
- ✅ L1瞬时内存层（LRU缓存）
- ✅ L2短期内存层（Redis）
- ✅ L3长期内存层（PostgreSQL+pgvector）
- ✅ 自动提升机制
- ✅ 批量操作优化
- ✅ 全局单例模式
- ✅ 统一文档系统

### v1.0 - P0-P1功能

- ✅ PostgreSQL会话存储
- ✅ Redis缓存
- ✅ pgvector语义检索
- ✅ Agent决策追踪
- ✅ 工具执行反馈
- ✅ Multi-Agent协作
- ✅ 上下文优化

---

## 📄 许可证

MIT License

---

**完整示例和详细文档请参考 `demos/` 目录**

### 向量记忆（VectorMemoryService）

**语义搜索和知识缓存：**

```python
from persistent_memory import VectorMemoryService

vector_service = VectorMemoryService(enable_cache=True)

# 存储知识
record_id = await vector_service.store(
    content="Tesla's Q4 2023 revenue was $25.17 billion...",
    namespace=VectorMemoryService.NS_RESEARCH,
    metadata={"topic": "Tesla financials", "date": "2024-01-01"}
)

# 语义搜索
results = await vector_service.search(
    query="Tesla revenue 2023",
    namespace=VectorMemoryService.NS_RESEARCH,
    k=5,  # 返回Top-5
    similarity_threshold=0.85  # 相似度阈值
)

for result in results:
    print(f"Content: {result['content']}")
    print(f"Similarity: {result['similarity']:.3f}")
```

**命名空间**：

- `NS_RESEARCH` = "research_findings" - 研究结果
- `NS_OUTLINES` = "outlines" - 大纲模板
- `NS_TEMPLATES` = "slide_templates" - 幻灯片模板

**特性**：

- ✅ pgvector HNSW索引（高性能）
- ✅ OpenAI text-embedding-3-small（1536维）
- ✅ 余弦相似度搜索
- ✅ Redis缓存查询结果
- ✅ 访问统计（自动记录访问次数）

---

### 用户偏好（UserPreferenceService）

**智能学习用户习惯：**

```python
from persistent_memory import UserPreferenceService

pref_service = UserPreferenceService(enable_cache=True)

# 获取用户偏好（不存在则创建默认）
prefs = await pref_service.get_user_preferences("user_123")
# {'language': 'EN-US', 'default_slides': 10, 'style': 'professional'}

# 更新偏好
await pref_service.update_preferences(
    user_id="user_123",
    preferences={"language": "ZH-CN", "default_slides": 15},
    merge=True  # 合并到现有偏好
)

# 从会话中学习
await pref_service.learn_from_session(
    user_id="user_123",
    session_metadata={"language": "EN-US", "numSlides": 12},
    successful=True,
    modification_count=1  # 用户修改了1次
)

# 获取统计信息
stats = await pref_service.get_user_stats("user_123")
# {
#   'total_sessions': 42,
#   'successful_generations': 38,
#   'success_rate': 0.905,
#   'avg_satisfaction_score': 0.87
# }
```

**满意度计算**：

- 0次修改 = 1.0分
- 1次修改 = 0.9分
- 2次修改 = 0.8分
- ...最低0.5分

**特性**：

- ✅ 自动学习（基于历史行为）
- ✅ 满意度追踪（修改次数反推）
- ✅ 偏好合并（新旧偏好智能融合）
- ✅ Redis缓存

---

### Redis缓存（RedisCache）

**统一缓存接口：**

```python
from persistent_memory import RedisCache

cache = RedisCache()

# 基础操作
await cache.set("key", "value", ttl=3600)
value = await cache.get("key")
await cache.delete("key")

# JSON操作
await cache.set_json("user:123", {"name": "Alice"}, ttl=7200)
data = await cache.get_json("user:123")

# 业务特定方法
await cache.set_session("sess_456", session_data)
session = await cache.get_session("sess_456")

# 批量失效
deleted_count = await cache.invalidate_pattern("session:*")
```

**TTL配置**：

- 会话缓存: 1小时
- 用户偏好: 24小时
- 向量结果: 2小时

---

## 🔧 Agent集成示例

### 修改 main_api.py

```python
from persistent_memory import PostgresSessionService, get_db
import os

# Feature flag控制
use_persistent_memory = (
    os.getenv('USE_PERSISTENT_MEMORY', 'false').lower() == 'true'
)

if use_persistent_memory:
    db = get_db()
    if not db.health_check():
        use_persistent_memory = False

session_service = (
    PostgresSessionService(enable_cache=True)
    if use_persistent_memory
    else InMemorySessionService()
)

runner = Runner(
    app_name=agent_card.name,
    agent=root_agent,
    session_service=session_service,
    # ...
)
```

### 修改 agent.py 加载用户偏好

```python
from persistent_memory import UserPreferenceService
import asyncio

user_pref_service = UserPreferenceService()

def before_agent_callback(callback_context: CallbackContext):
    metadata = callback_context.state.get("metadata", {})
    user_id = metadata.get("user_id", "anonymous")

    # 加载用户偏好
    loop = asyncio.get_event_loop()
    user_prefs = loop.run_until_complete(
        user_pref_service.get_user_preferences(user_id)
    )

    # 合并偏好
    merged = {**user_prefs, **metadata}
    callback_context.state["slides_plan_num"] = merged.get("numSlides", 10)
    callback_context.state["language"] = merged.get("language", "EN-US")
```

### 修改 tools.py 集成向量检索

```python
from persistent_memory import VectorMemoryService

vector_service = VectorMemoryService()

async def DocumentSearch(keyword: str, number: int, tool_context: ToolContext):
    # 先查向量数据库
    results = await vector_service.search(
        query=keyword,
        namespace=VectorMemoryService.NS_RESEARCH,
        k=number,
        similarity_threshold=0.75
    )

    if not results:
        # 未命中，执行外部搜索
        results = external_search(keyword)

        # 存入向量库
        for result in results:
            await vector_service.store(
                content=result,
                namespace=VectorMemoryService.NS_RESEARCH,
                metadata={"keyword": keyword}
            )

    return results
```

---

## 📊 数据库Schema

### sessions 表

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    app_name VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    state JSONB NOT NULL DEFAULT '{}',
    version INTEGER NOT NULL DEFAULT 1,  -- 乐观锁
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    UNIQUE(user_id, app_name, session_id)
);

CREATE INDEX idx_sessions_state_gin ON sessions USING gin (state);
```

### user_profiles 表

```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    preferences JSONB NOT NULL DEFAULT '{}',
    total_sessions INTEGER DEFAULT 0,
    successful_generations INTEGER DEFAULT 0,
    avg_satisfaction_score FLOAT DEFAULT 0.0,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### vector_memories 表

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE vector_memories (
    id UUID PRIMARY KEY,
    namespace VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding vector(1536),  -- OpenAI embedding维度
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    user_id VARCHAR(255)
);

-- HNSW索引加速向量搜索
CREATE INDEX idx_vector_memories_embedding
ON vector_memories USING hnsw (embedding vector_cosine_ops);
```

---

## 🐛 故障排查

### 1. 数据库连接失败

```bash
# 检查PostgreSQL是否运行
docker ps | grep postgres

# 查看数据库日志
docker logs multiagent_postgres

# 手动连接测试
docker exec -it multiagent_postgres psql -U postgres -d multiagent_ppt
```

### 2. Redis连接失败

```bash
# 检查Redis是否运行
docker ps | grep redis

# 测试连接
docker exec -it multiagent_redis redis-cli ping
# 应返回: PONG
```

### 3. pgvector扩展未安装

```sql
-- 手动创建扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 验证版本
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### 4. 乐观锁冲突

```python
from persistent_memory.postgres_session_service import OptimisticLockError

try:
    await session_service.update_session(...)
except OptimisticLockError as e:
    print(f"并发冲突: {e}")
    # 自动重试3次后仍失败，需要人工介入
```

### 5. 向量检索不可用

```python
if not vector_service.is_available():
    print("向量服务不可用，检查：")
    print("1. OPENAI_API_KEY是否配置")
    print("2. openai包是否安装")
    print("3. pgvector扩展是否启用")
```

---

## 📈 性能优化建议

### 1. 连接池配置

```python
# database.py
engine = create_engine(
    database_url,
    pool_size=10,       # 常驻连接数
    max_overflow=20,    # 最大溢出连接数
    pool_pre_ping=True  # 连接前检查健康
)
```

### 2. Redis缓存命中率

监控缓存命中率：

```bash
docker exec -it multiagent_redis redis-cli info stats | grep keyspace
```

### 3. 向量索引调优

```sql
-- 调整HNSW索引参数
CREATE INDEX idx_vector_memories_embedding
ON vector_memories USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### 4. 定期清理过期数据

```python
# 清理30天前的旧会话
DELETE FROM sessions WHERE updated_at < NOW() - INTERVAL '30 days';

# 清理低访问量的向量记忆
DELETE FROM vector_memories WHERE access_count = 0 AND created_at < NOW() - INTERVAL '7 days';
```

---

## 🔐 安全注意事项

1. **生产环境必须修改默认密码**：

   ```ini
   DATABASE_URL=postgresql://prod_user:strong_password@host:5432/db
   ```

2. **限制数据库网络访问**：

   ```yaml
   # docker-compose.yml
   postgres:
     networks:
       - backend_network # 不暴露到公网
   ```

3. **加密敏感字段**（待实现）：

   ```python
   from cryptography.fernet import Fernet

   # 加密用户敏感数据
   encrypted_state = fernet.encrypt(json.dumps(state).encode())
   ```

---

## 📝 TODO

- [ ] 实现数据加密（GDPR合规）
- [ ] 添加Prometheus监控指标
- [ ] 支持数据库读写分离
- [ ] 实现向量索引定期优化任务
- [ ] 添加数据备份脚本
- [ ] 支持多租户隔离

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 License

MIT License
