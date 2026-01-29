# 部署指南

本文档介绍如何部署MultiAgent PPT系统到生产环境。

## 部署方式

### 1. Docker部署（推荐）

#### 构建镜像

```bash
docker build -t multiagent-ppt:latest .
```

#### 运行容器

```bash
docker run -d \
  --name multiagent-ppt \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your_api_key \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  multiagent-ppt:latest
```

#### Docker Compose

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped
```

### 2. 传统部署

#### 系统要求

- Python 3.10+
- 2GB RAM
- 10GB 磁盘空间

#### 安装步骤

1. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
export ANTHROPIC_API_KEY="your_api_key"
```

4. 运行服务
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. 云平台部署

#### AWS ECS

1. 创建ECS任务定义
2. 配置负载均衡器
3. 设置自动伸缩

#### Google Cloud Run

```bash
gcloud run deploy multiagent-ppt \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
```

#### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name multiagent-ppt \
  --image multiagent-ppt:latest \
  --environment-variables ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  --ports 8000
```

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| ANTHROPIC_API_KEY | Anthropic API密钥 | 必填 |
| OPENAI_API_KEY | OpenAI API密钥 | 可选 |
| LOG_LEVEL | 日志级别 | INFO |
| WORKERS | 工作进程数 | 4 |
| HOST | 监听地址 | 0.0.0.0 |
| PORT | 监听端口 | 8000 |

## 监控和日志

### 日志配置

日志文件位置：`logs/app.log`

日志轮转：每天或文件大小超过10MB时轮转

### 健康检查

```bash
curl http://localhost:8000/health
```

### 性能监控

启用Prometheus指标（可选）：

```python
# config.yaml
monitoring:
  prometheus:
    enabled: true
    port: 9090
```

## 安全建议

1. **API密钥保护**
   - 使用环境变量存储密钥
   - 不要将密钥提交到代码仓库
   - 定期轮换密钥

2. **HTTPS配置**
   - 使用Let's Encrypt获取免费证书
   - 强制HTTPS重定向

3. **速率限制**
   - 实施API速率限制
   - 防止滥用

4. **输入验证**
   - 验证所有用户输入
   - 防止注入攻击

## 故障排查

### 常见问题

**问题**: API调用失败
**解决**: 检查API密钥是否正确，网络连接是否正常

**问题**: 内存不足
**解决**: 增加容器内存限制或减少工作进程数

**问题**: 生成超时
**解决**: 增加timeout配置或优化Agent逻辑

### 日志查看

```bash
# 实时查看日志
tail -f logs/app.log

# 查看错误日志
grep ERROR logs/app.log

# Docker容器日志
docker logs -f multiagent-ppt
```

## 备份和恢复

### 数据备份

```bash
# 备份数据目录
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# 定时备份（cron）
0 2 * * * /path/to/backup-script.sh
```

### 恢复数据

```bash
tar -xzf backup-20240101.tar.gz -C /
```
