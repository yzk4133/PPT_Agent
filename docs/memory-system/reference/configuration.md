# 记忆系统配置指南

> **版本：** 5.1.0（极简架构）
> **数据库：** MySQL 5.7+ / PostgreSQL 12+

---

## 📋 目录

- [环境变量配置](#环境变量配置)
- [功能开关](#功能开关)
- [数据库配置](#数据库配置)
- [Redis配置](#redis配置)
- [性能调优](#性能调优)

---

## 🔧 环境变量配置

### 核心配置

在项目根目录的 `.env` 文件中配置：

```bash
# === 数据库配置 ===
# MySQL（推荐）
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/multiagent_ppt

# PostgreSQL（备选）
# DATABASE_URL=postgresql://user:password@localhost:5432/multiagent_ppt

# SQLite（开发环境）
# DATABASE_URL=sqlite:///./memory.db

# === Redis配置 ===
REDIS_URL=redis://localhost:6379/0

# 带密码的Redis
# REDIS_URL=redis://:password@localhost:6379/0
```

---

## ⚙️ 功能开关

### v5.1 简化版配置

```bash
# === 记忆系统功能开关 ===

# 用户偏好功能（默认开启）
MEMORY_ENABLE_USER_PREFERENCES=true

# 缓存功能（默认开启）
MEMORY_ENABLE_CACHE=true

# === 性能配置 ===

# L2缓存默认TTL（秒）
MEMORY_L2_TTL_SECONDS=3600

# 数据库连接池大小
MEMORY_CONNECTION_POOL_SIZE=10

# === 日志配置 ===

# 日志级别
MEMORY_LOG_LEVEL=INFO

# 是否记录记忆操作日志
MEMORY_LOG_MEMORY_OPERATIONS=true

# 是否记录SQL语句
MEMORY_LOG_SQL=false
```

**已废弃的功能（v5.0删除）：**
```bash
# ❌ 以下功能已删除，无需配置
# MEMORY_ENABLE_DECISION_TRACKING   # 决策追踪已删除
# MEMORY_ENABLE_WORKSPACE           # 工作空间已删除
# MEMORY_ENABLE_VECTOR_SEARCH       # 向量搜索已删除
```

---

## 💾 数据库配置

### MySQL（推荐生产环境）

```bash
# 基础配置
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/multiagent_ppt

# 连接池配置
MEMORY_CONNECTION_POOL_SIZE=10        # 连接池大小
MEMORY_MAX_OVERFLOW=20                # 最大溢出连接数

# 字符集
# 确保MySQL使用 utf8mb4
# 在 my.cnf 中配置：
# [client]
# default-character-set=utf8mb4
#
# [mysqld]
# character-set-server=utf8mb4
# collation-server=utf8mb4_unicode_ci
```

### PostgreSQL

```bash
# 基础配置
DATABASE_URL=postgresql://user:password@localhost:5432/multiagent_ppt

# 连接池配置
MEMORY_CONNECTION_POOL_SIZE=10
MEMORY_MAX_OVERFLOW=20
```

### SQLite（开发环境）

```bash
# 文件数据库
DATABASE_URL=sqlite:///./memory.db

# 内存数据库（测试用）
# DATABASE_URL=sqlite:///:memory:
```

---

## 🔴 Redis配置

### 基础配置

```bash
# 标准 Redis
REDIS_URL=redis://localhost:6379/0

# 带密码的 Redis
REDIS_URL=redis://:password@localhost:6379/0

# 指定数据库
REDIS_URL=redis://localhost:6379/1
```

### 高可用配置

```bash
# Redis Sentinel
REDIS_URL=redis://:password@sentinel1:26379,sentinel2:26379/mymaster/0

# Redis Cluster
REDIS_URL=redis-cluster://:password@host1:7000,host2:7001/0
```

### 连接池配置

```python
# 在 backend/memory/storage/redis_cache.py 中配置
self.client = Redis.from_url(
    redis_url,
    decode_responses=True,       # 自动解码为字符串
    socket_timeout=5,            # 5秒超时
    socket_connect_timeout=5,    # 5秒连接超时
    retry_on_timeout=True,       # 超时重试
    health_check_interval=30,    # 30秒健康检查
    max_connections=50,          # 最大连接数
)
```

---

## 🚀 性能调优

### 数据库优化

```sql
-- MySQL 优化建议

-- 1. 使用 InnoDB 引擎
ALTER TABLE user_profiles ENGINE=InnoDB;

-- 2. 添加索引
CREATE INDEX idx_user_id ON user_profiles(user_id);
CREATE INDEX idx_satisfaction ON user_profiles(avg_satisfaction_score);

-- 3. 调整缓冲池大小（my.cnf）
[mysqld]
innodb_buffer_pool_size = 2G      # 设置为物理内存的50-70%

-- 4. 调整连接数
max_connections = 200
```

### Redis优化

```bash
# redis.conf 配置

# 最大内存
maxmemory 2gb

# 内存淘汰策略
maxmemory-policy allkeys-lru      # 删除最少使用的key

# 持久化（可选）
save 900 1                        # 900秒内至少1个key变化则保存
save 300 10                       # 300秒内至少10个key变化则保存
save 60 10000                     # 60秒内至少10000个key变化则保存
```

### 连接池优化

```bash
# 根据并发量调整
MEMORY_CONNECTION_POOL_SIZE=20    # 高并发环境增大
MEMORY_MAX_OVERFLOW=40            # 最大溢出连接数
```

---

## 📊 监控配置

### 启用日志

```bash
# 详细日志（调试用）
MEMORY_LOG_LEVEL=DEBUG
MEMORY_LOG_MEMORY_OPERATIONS=true
MEMORY_LOG_SQL=true

# 生产环境
MEMORY_LOG_LEVEL=INFO
MEMORY_LOG_MEMORY_OPERATIONS=true
MEMORY_LOG_SQL=false
```

### 健康检查

```python
from backend.memory.core import get_global_memory_system

async def check_health():
    system = get_global_memory_system()
    if system:
        status = await system.health_check()
        print(f"Database: {status['database']}")
        print(f"Cache: {status['cache']}")
        print(f"Services: {status['user_preference_service']}")
```

---

## 🔍 故障排查

### 常见问题

**Q: 数据库连接失败？**
```bash
# 检查数据库是否运行
mysql -u root -p -e "SELECT 1"

# 检查连接字符串
echo $DATABASE_URL

# 检查防火墙
telnet localhost 3306
```

**Q: Redis连接失败？**
```bash
# 检查Redis是否运行
redis-cli ping

# 检查连接字符串
echo $REDIS_URL

# 检查防火墙
telnet localhost 6379
```

**Q: 性能慢？**
```bash
# 检查慢查询
# MySQL
SHOW VARIABLES LIKE 'slow_query_log';

# Redis
redis-cli slowlog get 10
```

---

## 🔗 相关文档

- [存储层详解](../storage-layer/) - 数据库和缓存管理
- [服务层详解](../service-layer/) - 业务逻辑层
- [故障排除](./troubleshooting.md) - 常见问题解决

---

**文档版本：** 5.1.0
**最后更新：** 2026-02-10
