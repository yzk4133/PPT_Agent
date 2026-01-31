# 持久化记忆系统 - 使用指南

## 📚 概述

本模块为MultiAgentPPT项目提供**三层持久化记忆架构**：

1. **PostgreSQL**: 会话存储、用户配置、向量数据
2. **Redis**: 热数据缓存（1小时TTL）
3. **pgvector**: 语义检索（OpenAI embeddings）

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend/persistent_memory
pip install -r requirements.txt
```

### 2. 配置环境变量

复制环境变量模板：

```bash
cp ../env_template_memory ../slide_agent/.env
```

编辑 `.env` 文件，填入真实配置：

```ini
USE_PERSISTENT_MEMORY=true
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/multiagent_ppt
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-your-key-here
```

### 3. 启动数据库服务

使用Docker Compose启动PostgreSQL和Redis：

```bash
cd backend
docker-compose up -d postgres redis
```

### 4. 初始化数据库

```bash
cd backend/persistent_memory
python database.py --init
```

删除旧数据并重新初始化：

```bash
python database.py --init --drop
```

### 5. 健康检查

```bash
python database.py --health
```

## 📖 核心功能

### 会话管理（PostgresSessionService）

**支持乐观锁的会话持久化：**

```python
from persistent_memory import PostgresSessionService

session_service = PostgresSessionService(enable_cache=True)

# 创建会话
session = await session_service.create_session(
    app_name="my_app",
    user_id="user_123",
    session_id="sess_456",
    state={"key": "value"}
)

# 更新会话（自动处理版本冲突）
updated_session = await session_service.update_session(
    app_name="my_app",
    user_id="user_123",
    session_id="sess_456",
    state={"key": "new_value", "count": 1}
)
```

**特性**：

- ✅ 乐观锁并发控制（version字段）
- ✅ Redis缓存加速（先查缓存再查数据库）
- ✅ 自动重试（最多3次）
- ✅ 会话恢复（服务重启后可恢复）

---

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
