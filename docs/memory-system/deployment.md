# 部署指南

## 一、系统要求

### 1.1 硬件要求

**最低配置**（开发/测试）:
- CPU: 2核心
- 内存: 4GB
- 磁盘: 20GB SSD

**推荐配置**（生产环境）:
- CPU: 4-8核心
- 内存: 16GB
- 磁盘: 100GB SSD

**高负载配置**:
- CPU: 16+核心
- 内存: 32GB+
- 磁盘: 500GB SSD + 备份

### 1.2 软件要求

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.9+ | 推荐使用3.10或3.11 |
| PostgreSQL | 14+ | 需要pgvector扩展 |
| Redis | 6.0+ | 推荐使用7.0 |
| pgvector | 0.4.0+ | 向量相似度搜索 |

### 1.3 依赖安装

```bash
# 安装Python依赖
pip install -r requirements.txt

# requirements.txt 内容：
fastapi>=0.100.0
uvicorn>=0.23.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
redis>=4.5.0
openai>=1.0.0
pydantic>=2.0.0
aiofiles>=23.0.0
```

---

## 二、数据库设置

### 2.1 PostgreSQL安装

**Ubuntu/Debian**:
```bash
# 安装PostgreSQL
sudo apt-get update
sudo apt-get install postgresql-14 postgresql-contrib-14

# 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS**:
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Windows**:
下载安装包：https://www.postgresql.org/download/windows/

### 2.2 pgvector扩展安装

```bash
# 安装pgvector
cd /tmp
git clone --branch v0.4.0 https://github.com/pgvector/pgvector.git
cd pgvector

# 编译安装
make
sudo make install

# 在PostgreSQL中启用扩展
psql -d multiagent_ppt -c "CREATE EXTENSION vector;"
```

### 2.3 数据库初始化

```bash
cd backend/cognition/memory/core

# 初始化数据库（创建表）
python database.py --init

# 删除并重建（仅开发环境）
python database.py --init --drop

# 健康检查
python database.py --health
```

**预期输出**:
```
✅ Database initialized successfully!
```

### 2.4 创建用户和权限

```sql
-- 连接到PostgreSQL
psql -U postgres

-- 创建用户
CREATE USER multiagent_user WITH PASSWORD 'your_secure_password';

-- 创建数据库
CREATE DATABASE multiagent_ppt OWNER multiagent_user;

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE multiagent_ppt TO multiagent_user;

-- 连接到数据库
\c multiagent_ppt

-- 授予schema权限
GRANT ALL ON SCHEMA public TO multiagent_user;
```

---

## 三、Redis设置

### 3.1 Redis安装

**Ubuntu/Debian**:
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**macOS**:
```bash
brew install redis
brew services start redis
```

**Docker方式**:
```bash
docker run -d \
  --name redis \
  -p 6379:6379 \
  -v redis_data:/data \
  redis:7-alpine \
  redis-server --appendonly yes
```

### 3.2 Redis配置

**配置文件** (`/etc/redis/redis.conf`):
```conf
# 内存限制
maxmemory 2gb

# 内存策略：allkeys-lru（所有键LRU淘汰）
maxmemory-policy allkeys-lru

# 持久化：仅AOF
appendonly yes
appendfsync everysec

# 日志级别
loglevel notice
```

### 3.3 Redis连接测试

```bash
# 测试连接
redis-cli ping
# 应该返回: PONG

# 查看信息
redis-cli info stats
```

---

## 四、应用部署

### 4.1 配置环境变量

**创建 `.env` 文件**:
```bash
# .env
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://multiagent_user:password@localhost:5432/multiagent_ppt
OPENAI_API_KEY=sk-your-api-key

# 可选
API_HOST=0.0.0.0
API_PORT=8001
LOG_LEVEL=INFO
```

**加载环境变量**:
```bash
# 使用python-dotenv
pip install python-dotenv

# 在代码中加载
from dotenv import load_dotenv
load_dotenv()
```

### 4.2 启动API服务

**开发模式**:
```bash
cd backend/cognition/memory/core/api

# 直接运行
python memory_api.py

# 或使用uvicorn（支持热重载）
uvicorn memory_api:app --reload --host 0.0.0.0 --port 8001
```

**生产模式**:
```bash
# 使用gunicorn
pip install gunicorn

gunicorn memory_api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8001 \
  --access-logfile - \
  --error-logfile -
```

### 4.3 后台任务部署

**使用systemd（Linux）**:

创建服务文件 `/etc/systemd/system/memory-api.service`:
```ini
[Unit]
Description=MultiAgentPPT Memory API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/MultiAgentPPT/backend/cognition/memory/core
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn memory_api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8001
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl daemon-reload
sudo systemctl start memory-api
sudo systemctl enable memory-api
```

---

## 五、Docker部署

### 5.1 Dockerfile

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY backend/ ./backend/

# 暴露端口
EXPOSE 8001

# 启动命令
CMD ["uvicorn", "backend.cognition.memory.core.api.memory_api:app", \
     "--host", "0.0.0.0", "--port", "8001"]
```

### 5.2 Docker Compose

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg14
    environment:
      POSTGRES_USER: multiagent_user
      POSTGRES_PASSWORD: your_password
      POSTGRES_DB: multiagent_ppt
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U multiagent_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  memory-api:
    build: .
    environment:
      REDIS_URL: redis://redis:6379/0
      DATABASE_URL: postgresql://multiagent_user:your_password@postgres:5432/multiagent_ppt
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    ports:
      - "8001:8001"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

**启动服务**:
```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f memory-api

# 停止服务
docker-compose down
```

---

## 六、Kubernetes部署

### 6.1 ConfigMap

**configmap.yaml**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: memory-config
data:
  REDIS_URL: "redis://redis-service:6379/0"
  DATABASE_URL: "postgresql://user:pass@postgres-service:5432/multiagent_ppt"
  LOG_LEVEL: "INFO"
```

### 6.2 Secret

**secret.yaml**:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: memory-secret
type: Opaque
stringData:
  OPENAI_API_KEY: "sk-your-api-key"
  DB_PASSWORD: "your-secure-password"
```

### 6.3 Deployment

**deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memory-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: memory-api
  template:
    metadata:
      labels:
        app: memory-api
    spec:
      containers:
      - name: memory-api
        image: your-registry/memory-api:latest
        ports:
        - containerPort: 8001
        envFrom:
        - configMapRef:
            name: memory-config
        - secretRef:
            name: memory-secret
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /api/memory/health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/memory/health
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 5
```

### 6.4 Service

**service.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: memory-api-service
spec:
  selector:
    app: memory-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8001
  type: LoadBalancer
```

**部署**:
```bash
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

---

## 七、健康检查

### 7.1 API健康检查

```bash
# 检查API状态
curl http://localhost:8001/api/memory/health

# 预期响应
{
  "status": "healthy",
  "l1_transient": "ok",
  "l2_short_term": "ok",
  "l3_long_term": "ok"
}
```

### 7.2 数据库健康检查

```bash
# 运行健康检查脚本
cd backend/cognition/memory/core
python database.py --health

# 预期输出
✅ Database is healthy!
```

### 7.3 Redis健康检查

```bash
# 检查Redis
redis-cli ping

# 查看内存使用
redis-cli info memory
```

---

## 八、监控和日志

### 8.1 日志配置

**配置日志** (`logging.yaml`):
```yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
  json:
    format: '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout

  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: json
    filename: /var/log/memory-api/app.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

loggers:
  cognition.memory:
    level: INFO
    handlers: [console, file]
    propagate: false

root:
  level: WARNING
  handlers: [console]
```

### 8.2 Prometheus监控

**添加metrics endpoint**:
```python
# 伪代码
from prometheus_client import Counter, Histogram, generate_latest

# 定义指标
request_count = Counter('memory_requests_total', 'Total requests', ['layer', 'operation'])
request_duration = Histogram('memory_request_duration_seconds', 'Request duration')

# 在API中添加endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### 8.3 Grafana仪表板

**建议的监控面板**:

1. **系统概览**
   - API请求率
   - 错误率
   - 响应时间

2. **缓存性能**
   - L1/L2/L3命中率
   - 数据流转速率
   - 提升事件频率

3. **资源使用**
   - CPU使用率
   - 内存使用率
   - Redis内存
   - PostgreSQL连接数

---

## 九、备份和恢复

### 9.1 数据库备份

**备份脚本** (`backup.sh`):
```bash
#!/bin/bash

BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/multiagent_ppt_$DATE.sql.gz"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
pg_dump -U multiagent_user -h localhost multiagent_ppt | gzip > $BACKUP_FILE

# 保留最近7天的备份
find $BACKUP_DIR -name "multiagent_ppt_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
```

**定时备份** (crontab):
```bash
# 每天凌晨2点备份
0 2 * * * /path/to/backup.sh
```

### 9.2 Redis备份

**RDB快照** (已配置在redis.conf):
```conf
# 启用RDB
save 900 1
save 300 10
save 60 10000

# 快照文件
dbfilename dump.rdb
dir /var/lib/redis
```

**AOF持久化**:
```conf
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
```

### 9.3 恢复流程

**PostgreSQL恢复**:
```bash
# 停止应用
sudo systemctl stop memory-api

# 恢复数据库
gunzip -c /backups/postgres/multiagent_ppt_20260203_020000.sql.gz | \
  psql -U multiagent_user -h localhost multiagent_ppt

# 重启应用
sudo systemctl start memory-api
```

**Redis恢复**:
```bash
# 停止Redis
sudo systemctl stop redis

# 备份当前数据
cp /var/lib/redis/dump.rdb /var/lib/redis/dump.rdb.backup

# 恢复数据
cp /backups/redis/dump.rdb /var/lib/redis/dump.rdb

# 启动Redis
sudo systemctl start redis
```

---

## 十、性能调优

### 10.1 数据库调优

**postgresql.conf配置**:
```conf
# 连接设置
max_connections = 100
shared_buffers = 4GB
effective_cache_size = 12GB

# 查询优化
random_page_cost = 1.1  # SSD使用此值
effective_io_concurrency = 200

# WAL设置
wal_buffers = 16MB
checkpoint_completion_target = 0.9

# 日志
log_min_duration_statement = 1000  # 记录慢查询
```

### 10.2 Redis调优

**redis.conf配置**:
```conf
# 内存优化
maxmemory 2gb
maxmemory-policy allkeys-lru

# 持久化优化
save ""  # 禁用RDB，仅使用AOF
appendonly yes
appendfsync everysec

# 网络优化
tcp-keepalive 300
tcp-backlog 511
```

### 10.3 应用调优

**worker数量**:
```python
# 根据CPU核心数设置
import os
workers = (os.cpu_count() * 2) + 1
```

**连接池**:
```python
# 增大连接池
engine = create_engine(
    database_url,
    pool_size=20,          # 增大池大小
    max_overflow=40,       # 增大溢出
    pool_pre_ping=True
)
```

---

## 十一、故障排查

### 11.1 常见问题

**问题1: Redis连接失败**
```bash
# 检查Redis状态
sudo systemctl status redis-server

# 检查端口
netstat -tlnp | grep 6379

# 查看日志
sudo journalctl -u redis-server -f
```

**问题2: PostgreSQL连接拒绝**
```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 检查连接数
psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# 增加最大连接数
# 编辑 postgresql.conf
max_connections = 200
```

**问题3: 内存不足**
```bash
# 检查内存使用
free -h

# 检查进程内存
ps aux --sort=-%mem | head

# 清理缓存
sync && echo 3 > /proc/sys/vm/drop_caches
```

### 11.2 日志分析

**查看错误日志**:
```bash
# API日志
tail -f /var/log/memory-api/app.log | grep ERROR

# 数据库日志
tail -f /var/log/postgresql/postgresql-14-main.log

# Redis日志
tail -f /var/log/redis/redis-server.log
```

---

## 十二、安全加固

### 12.1 网络安全

**配置防火墙**:
```bash
# 只允许本地访问Redis
sudo ufw allow from 127.0.0.1 to any port 6379

# 只允许本地访问PostgreSQL
sudo ufw allow from 127.0.0.1 to any port 5432

# 允许API访问
sudo ufw allow 8001/tcp
```

### 12.2 数据加密

**启用SSL/TLS**:
```python
# PostgreSQL SSL
DATABASE_URL="postgresql://user:pass@localhost:5432/db?sslmode=require"

# Redis TLS (使用stunnel)
REDIS_URL="rediss://localhost:6379/0"
```

### 12.3 访问控制

**数据库用户权限**:
```sql
-- 创建只读用户
CREATE USER memory_readonly WITH PASSWORD 'readonly_pass';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO memory_readonly;

-- 创建读写用户
CREATE USER memory_readwrite WITH PASSWORD 'readwrite_pass';
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO memory_readwrite;
```

---

## 十三、升级策略

### 13.1 滚动升级

```bash
# 1. 备份数据
./backup.sh

# 2. 更新代码
git pull origin main
pip install -r requirements.txt

# 3. 数据库迁移（如有）
python database.py --migrate

# 4. 重启服务（逐个实例）
sudo systemctl restart memory-api@instance1
# 等待健康检查通过
# 继续下一个实例...
```

### 13.2 版本兼容性

| 版本 | 兼容性 | 说明 |
|------|--------|------|
| 1.x → 2.0 | 需要迁移 | 配置文件格式变更 |
| 2.0 → 2.1 | 兼容 | 直接升级 |

---

## 十四、生产环境检查清单

部署前检查：

- [ ] PostgreSQL已安装并配置pgvector扩展
- [ ] Redis已安装并配置持久化
- [ ] 数据库已初始化
- [ ] 环境变量已配置
- [ ] 防火墙规则已设置
- [ ] 日志目录已创建并配置权限
- [ ] 备份计划已配置
- [ ] 监控已配置
- [ ] 健康检查端点可访问
- [ ] API服务可正常启动
- [ ] 基础功能测试通过

部署后验证：

- [ ] API健康检查正常
- [ ] 数据库连接正常
- [ ] Redis连接正常
- [ ] 写入L1数据成功
- [ ] 自动提升任务运行
- [ ] 日志正常输出
- [ ] 监控指标正常
