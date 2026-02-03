# 配置说明

## 一、配置文件

### 1.1 配置文件位置

记忆系统的配置可以通过多种方式设置：

| 位置 | 优先级 | 说明 |
|------|--------|------|
| 环境变量 | 最高 | 运行时动态配置 |
| 配置文件 | 中 | YAML/TOML格式的配置文件 |
| 代码默认值 | 最低 | 系统内置默认值 |

### 1.2 配置文件示例

**config/memory_config.yaml**:
```yaml
# 记忆系统配置

# L1瞬时内存配置
l1:
  capacity: 1000              # L1容量（条目数）
  default_ttl: 300            # 默认TTL（秒）
  cleanup_interval: 60         # 清理间隔（秒）

# L2短期内存配置
l2:
  redis_url: "redis://localhost:6379/0"
  default_ttl: 3600           # 默认TTL（秒）
  batch_size: 50              # 批量操作大小

# L3长期内存配置
l3:
  database_url: "postgresql://user:pass@localhost:5432/multiagent_ppt"
  pool_size: 10               # 连接池大小
  max_overflow: 20            # 最大溢出连接数

# 自动提升配置
promotion:
  enabled: true
  scan_interval: 300          # 扫描间隔（秒）

  # L1→L2阈值
  l1_to_l2:
    access_count: 3           # 访问次数阈值
    importance: 0.7           # 重要性阈值
    lifetime_minutes: 10      # 最小生存时间（分钟）

  # L2→L3阈值
  l2_to_l3:
    session_count: 2          # 跨会话次数阈值
    access_count: 5           # 访问次数阈值
    importance: 0.8           # 重要性阈值

# 分布式锁配置
distributed_lock:
  enabled: true
  default_ttl: 10000          # 默认TTL（毫秒）
  max_retries: 3              # 最大重试次数
  retry_delay: 200            # 重试延迟（毫秒）

# 向量缓存配置
vector_cache:
  enabled: true
  max_cache_size: 10000       # 最大缓存数
  default_ttl: 7200           # 默认TTL（秒）
  embedding_model: "text-embedding-3-small"
  embedding_dimension: 1536

# 生命周期管理配置
lifecycle:
  enabled: true
  cleanup_interval: 86400      # 清理间隔（秒，1天）

  # 时间衰减
  decay_rate: 0.95            # 衰减率
  decay_period_days: 30       # 衰减周期（天）

  # 数据温度
  hot_days: 30                # 热数据天数
  warm_days: 180              # 温数据天数
  cold_days: 180              # 冷数据天数

# API服务配置
api:
  host: "0.0.0.0"
  port: 8001
  workers: 4
  log_level: "INFO"
```

---

## 二、层级配置

### 2.1 L1瞬时内存配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `capacity` | int | 1000 | L1最大容量，超过时LRU淘汰 |
| `default_ttl` | int | 300 | 默认过期时间（秒） |
| `cleanup_interval` | int | 60 | 后台清理间隔（秒） |

**配置建议**:

```yaml
# 高并发场景
l1:
  capacity: 5000              # 增大容量
  default_ttl: 180            # 缩短TTL，加快流转

# 低并发场景
l1:
  capacity: 500
  default_ttl: 600            # 延长TTL，减少提升
```

### 2.2 L2短期内存配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `redis_url` | string | redis://localhost:6379/0 | Redis连接地址 |
| `default_ttl` | int | 3600 | 默认过期时间（秒） |
| `batch_size` | int | 50 | 批量操作大小 |

**配置建议**:

```yaml
# 生产环境
l2:
  redis_url: "redis://redis-cluster:6379/0"
  default_ttl: 3600
  batch_size: 100             # 增大批量大小

# 开发环境
l2:
  redis_url: "redis://localhost:6379/1"
  default_ttl: 1800           # 缩短TTL便于测试
```

### 2.3 L3长期内存配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `database_url` | string | - | PostgreSQL连接地址 |
| `pool_size` | int | 10 | 连接池大小 |
| `max_overflow` | int | 20 | 最大溢出连接数 |
| `pool_recycle` | int | 3600 | 连接回收时间（秒） |

**配置建议**:

```yaml
# 高负载场景
l3:
  database_url: "postgresql://user:pass@pg-cluster:5432/db"
  pool_size: 20
  max_overflow: 40
  pool_recycle: 1800

# 低负载场景
l3:
  pool_size: 5
  max_overflow: 10
```

---

## 三、自动提升配置

### 3.1 提升阈值配置

**L1→L2 提升阈值**:

```yaml
promotion:
  l1_to_l2:
    access_count: 3           # 访问次数达到3次提升
    importance: 0.7           # 重要性达到0.7提升
    lifetime_minutes: 10      # 存活10分钟且访问≥2次提升
```

**调整建议**:

| 场景 | access_count | importance | 说明 |
|------|--------------|------------|------|
| 保守 | 5 | 0.9 | 减少提升，保留在L1 |
| 激进 | 2 | 0.5 | 加快提升，更多持久化 |
| 平衡 | 3 | 0.7 | 默认配置 |

**L2→L3 提升阈值**:

```yaml
promotion:
  l2_to_l3:
    session_count: 2          # 2个不同会话使用后提升
    access_count: 5           # 访问5次且重要性≥0.8提升
    importance: 0.8           # 重要性阈值
```

### 3.2 扫描配置

```yaml
promotion:
  enabled: true               # 是否启用自动提升
  scan_interval: 300          # 扫描间隔（秒），5分钟
  max_candidates: 50          # 每次扫描最大候选数
  max_promotions: 100         # 每次运行最大提升数
```

**调整建议**:

| 场景 | scan_interval | 说明 |
|------|---------------|------|
| 实时性要求高 | 60 | 每分钟扫描，数据快速流转 |
| 默认 | 300 | 每5分钟扫描，平衡性能和实时性 |
| 性能优先 | 600 | 每10分钟扫描，减少开销 |

---

## 四、分布式锁配置

### 4.1 锁参数配置

```yaml
distributed_lock:
  enabled: true               # 是否启用分布式锁
  default_ttl: 10000          # 默认锁TTL（毫秒）
  max_retries: 3              # 获取锁失败最大重试次数
  retry_delay: 200            # 重试延迟（毫秒）
  auto_renewal_threshold: 0.7 # 自动续期阈值（TTL百分比）
```

### 4.2 特定场景锁配置

```yaml
# 用户配置更新锁
locks:
  user_profile_update:
    key: "user_profile:update:{user_id}"
    ttl: 5000                 # 5秒
    auto_renewal: false

# 批量向量写入锁
locks:
  vector_batch_write:
    key: "vector_memory:batch_write"
    ttl: 30000                # 30秒
    auto_renewal: true        # 启用自动续期

# 提升任务锁
locks:
  promotion_execute:
    key: "promotion:execute:L1_L2"
    ttl: 300000               # 5分钟
    wait_timeout: 0           # 不等待，直接失败
```

---

## 五、向量缓存配置

### 5.1 缓存参数配置

```yaml
vector_cache:
  enabled: true
  max_cache_size: 10000       # 最大缓存数
  default_ttl: 7200           # 默认TTL（秒），2小时
  cleanup_interval: 300       # 清理间隔（秒）

  # OpenAI配置
  embedding_model: "text-embedding-3-small"
  embedding_dimension: 1536
  api_key: "${OPENAI_API_KEY}" # 环境变量引用

  # 性能配置
  batch_size: 100             # 批量获取大小
  warmup_enabled: true        # 是否启用预热
  warmup_priority_threshold: 3 # 访问次数≥3标记为高优先级
```

### 5.2 不同模型配置

```yaml
# 高精度场景
vector_cache:
  embedding_model: "text-embedding-3-large"
  embedding_dimension: 3072

# 低成本场景
vector_cache:
  embedding_model: "text-embedding-3-small"
  embedding_dimension: 1536

# 本地模型（需要自行实现）
vector_cache:
  embedding_model: "local:sentence-transformers"
  embedding_dimension: 768
```

---

## 六、生命周期管理配置

### 6.1 时间衰减配置

```yaml
lifecycle:
  # 时间衰减参数
  decay_rate: 0.95            # 衰减率
  decay_period_days: 30       # 衰减周期（天）
  min_importance: 0.1         # 最低重要性保护

  # 衰减效果示例：
  # 30天后: importance * 0.95^1
  # 60天后: importance * 0.95^2
  # 90天后: importance * 0.95^3
```

**调整建议**:

| 场景 | decay_rate | 说明 |
|------|-----------|------|
| 快速衰减 | 0.90 | 数据价值快速下降 |
| 默认 | 0.95 | 温和衰减 |
| 慢速衰减 | 0.98 | 长期保留价值 |

### 6.2 数据温度配置

```yaml
lifecycle:
  # 数据温度阈值（天）
  hot_days: 30                # 热数据：< 30天
  warm_days: 180              # 温数据：30-180天
  cold_days: 180              # 冷数据：> 180天

  # 归档配置
  archive:
    enabled: true
    min_access_count: 1       # 最低访问次数
    min_importance: 0.5       # 最低重要性

  # 清理配置
  cleanup:
    min_importance: 0.2       # 最低重要性
    min_access_count: 2       # 最低访问次数
    max_age_days: 365         # 最大保留天数
```

### 6.3 摘要配置

```yaml
lifecycle:
  # LLM摘要配置
  summarization:
    enabled: true
    max_length: 500           # 摘要最大长度（字）
    min_compression: 0.3      # 最小压缩比
    model: "gpt-3.5-turbo"
    max_tokens: 300
```

---

## 七、环境变量

### 7.1 必需环境变量

```bash
# Redis
export REDIS_URL="redis://localhost:6379/0"

# PostgreSQL
export DATABASE_URL="postgresql://user:pass@localhost:5432/multiagent_ppt"

# OpenAI
export OPENAI_API_KEY="sk-..."
```

### 7.2 可选环境变量

```bash
# API服务
export API_HOST="0.0.0.0"
export API_PORT="8001"
export API_WORKERS="4"
export LOG_LEVEL="INFO"

# 调试
export SQL_ECHO="false"        # 是否打印SQL
export DEBUG_MODE="false"

# 性能
export L1_CAPACITY="1000"
export PROMOTION_INTERVAL="300"
```

---

## 八、配置最佳实践

### 8.1 分环境配置

**开发环境** (`config/dev.yaml`):
```yaml
l1:
  capacity: 500                # 减少内存使用
  default_ttl: 120            # 快速过期便于测试

promotion:
  enabled: false              # 关闭自动提升便于调试

api:
  log_level: "DEBUG"           # 详细日志
```

**生产环境** (`config/prod.yaml`):
```yaml
l1:
  capacity: 2000               # 增大容量
  default_ttl: 300

promotion:
  enabled: true
  scan_interval: 180          # 更频繁的扫描

api:
  log_level: "INFO"
  workers: 8                  # 多worker
```

### 8.2 配置验证

```python
# 伪代码
def validate_config(config: dict) -> bool:
    """验证配置有效性"""

    # 检查必需项
    required_fields = [
        "l1.capacity",
        "l2.redis_url",
        "l3.database_url"
    ]

    for field in required_fields:
        if not get_nested_value(config, field):
            raise ConfigError(f"Missing required field: {field}")

    # 检查数值范围
    if config["l1"]["capacity"] < 100:
        raise ConfigError("L1 capacity too small")

    if config["l1"]["capacity"] > 10000:
        raise ConfigError("L1 capacity too large")

    # 检查阈值合理性
    l1_access = config["promotion"]["l1_to_l2"]["access_count"]
    l2_access = config["promotion"]["l2_to_l3"]["access_count"]

    if l1_access >= l2_access:
        print("WARNING: L1 access threshold >= L2, may cause premature promotion")

    return True
```

### 8.3 配置热更新

```python
# 伪代码
class ConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self.load_config()
        self.watchers = []

    def load_config(self) -> dict:
        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def watch_changes(self):
        """监听配置文件变化"""
        last_mtime = os.path.getmtime(self.config_path)

        while True:
            current_mtime = os.path.getmtime(self.config_path)

            if current_mtime != last_mtime:
                print("Config file changed, reloading...")
                new_config = self.load_config()

                if self.validate_config(new_config):
                    self.config = new_config
                    self.notify_watchers()

                last_mtime = current_mtime

            await asyncio.sleep(5)

    def notify_watchers(self):
        """通知配置观察者"""
        for watcher in self.watchers:
            watcher.on_config_changed(self.config)
```

---

## 九、配置迁移

### 9.1 版本迁移

从v1.x迁移到v2.0：

```yaml
# v1.x 配置
l1_capacity: 1000
redis_url: "redis://localhost"

# v2.0 配置（结构化）
l1:
  capacity: 1000

l2:
  redis_url: "redis://localhost"
```

**迁移脚本**:
```python
# 伪代码
def migrate_config_v1_to_v2(old_config: dict) -> dict:
    new_config = {
        "l1": {
            "capacity": old_config.get("l1_capacity", 1000),
            "default_ttl": 300,
        },
        "l2": {
            "redis_url": old_config.get("redis_url", "redis://localhost"),
            "default_ttl": 3600,
        },
        # ... 其他默认值
    }
    return new_config
```

---

## 十、配置监控

### 10.1 配置健康检查

```python
# 伪代码
async def check_config_health(config: dict) -> dict:
    """检查配置健康状态"""

    health = {
        "status": "healthy",
        "warnings": [],
        "errors": []
    }

    # 检查L1容量使用率
    l1_usage = await get_l1_usage()
    capacity = config["l1"]["capacity"]

    if l1_usage / capacity > 0.9:
        health["warnings"].append(
            f"L1 usage > 90%: {l1_usage}/{capacity}"
        )
        health["status"] = "warning"

    # 检查Redis连接
    if not await ping_redis(config["l2"]["redis_url"]):
        health["errors"].append("Redis unreachable")
        health["status"] = "unhealthy"

    # 检查数据库连接
    if not await ping_db(config["l3"]["database_url"]):
        health["errors"].append("Database unreachable")
        health["status"] = "unhealthy"

    return health
```

### 10.2 配置审计

```python
# 伪代码
def audit_config(config: dict) -> dict:
    """审计配置变更"""

    audit_log = {
        "timestamp": now().isoformat(),
        "config_hash": hash_dict(config),
        "changes": [],
        "security_issues": []
    }

    # 检查敏感信息
    if "api_key" in config.get("vector_cache", {}):
        audit_log["security_issues"].append(
            "API key should be in environment variable, not config file"
        )

    # 检查不安全配置
    if config.get("api", {}).get("log_level") == "DEBUG":
        audit_log["security_issues"].append(
            "DEBUG log level in production"
        )

    return audit_log
```
