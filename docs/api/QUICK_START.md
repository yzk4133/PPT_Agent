# 快速启动指南

## 启动后端

### 方式一：使用 Python 模块（推荐）

```bash
cd backend
python -m api.main
```

### 方式二：使用 Uvicorn

```bash
cd backend
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 验证启动成功

```bash
curl http://localhost:8000/api/health
```

预期响应：
```json
{
  "status": "healthy",
  "service": "fastapi_gateway",
  "version": "2.0.0"
}
```

---

## 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问: http://localhost:3000

---

## 完整启动流程

### 开发环境

**终端 1 - 后端**:
```bash
cd backend
python -m api.main
```

**终端 2 - 前端**:
```bash
cd frontend
npm run dev
```

### 访问地址

| 服务 | URL | 说明 |
|------|-----|------|
| 前端 | http://localhost:3000 | Next.js 应用 |
| API 文档 (Swagger) | http://localhost:8000/docs | 交互式 API 文档 |
| API 文档 (ReDoc) | http://localhost:8000/redoc | 美观的 API 文档 |
| 健康检查 | http://localhost:8000/api/health | 服务健康状态 |

---

## 环境变量配置

### 后端（可选）

创建 `backend/.env`:

```bash
# FastAPI 配置
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# Agent 配置
OUTLINE_MODEL=deepseek-chat
OUTLINE_PROVIDER=deepseek
MAX_CONCURRENCY=3

# 环境标识
ENV=development
```

### 前端（必需）

`frontend/.env` 已配置:

```env
FASTAPI_URL=http://localhost:8000
DOWNLOAD_SLIDES_URL=http://localhost:10021
```

---

## 测试 API

### 1. 测试大纲生成

```bash
curl -X POST http://localhost:8000/api/ppt/outline/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "生成关于量子计算的PPT大纲",
    "numberOfCards": 10,
    "language": "zh-CN"
  }'
```

### 2. 测试幻灯片生成

```bash
curl -X POST http://localhost:8000/api/ppt/slides/generate \
  -H "Content-Type: application/json" \
  -d '{
    "title": "量子计算应用",
    "outline": ["引言", "量子比特", "量子门", "量子算法"],
    "language": "zh-CN",
    "tone": "professional",
    "numSlides": 10
  }'
```

### 3. 使用 Swagger UI 测试

访问 http://localhost:8000/docs：

1. 找到需要测试的端点
2. 点击 "Try it out"
3. 填写请求参数
4. 点击 "Execute"
5. 查看响应结果

---

## 常见问题

### 端口 8000 被占用

**macOS/Linux**:
```bash
lsof -i :8000
kill -9 <PID>
```

**Windows**:
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

或使用其他端口:
```bash
FASTAPI_PORT=8001 python -m api.main
```

### Agent 初始化失败

检查：
1. MCP 配置文件是否存在: `backend/archive/slide_outline/mcp_config.json`
2. 模型 API key 是否配置
3. 依赖是否完整安装: `pip install -r backend/requirements.txt`

### 前端无法连接后端

检查：
1. 后端是否启动: `curl http://localhost:8000/api/health`
2. 前端 `.env` 中的 `FASTAPI_URL` 是否正确
3. 浏览器控制台是否有 CORS 错误

---

## 停止服务

### 停止后端

在终端按 `Ctrl + C`

### 停止前端

在终端按 `Ctrl + C`

---

## 生产环境部署

### 使用 Gunicorn

```bash
pip install gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 使用 Docker

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "api.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### 使用 Systemd

创建 `/etc/systemd/system/ppt-api.service`:

```ini
[Unit]
Description=Multi-Agent PPT API
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/backend
ExecStart=/path/to/venv/bin/gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl start ppt-api
sudo systemctl enable ppt-api
```

---

## 日志

### 后端日志

后端日志输出到终端，包含：

```
➡️  POST /api/ppt/outline/generate
⬅️  POST /api/ppt/outline/generate - Status: 200 - Time: 5.234s
```

### 前端日志

查看浏览器控制台（F12）：

```
FastAPI Gateway URL: http://localhost:8000
Received event: {...}
```

---

## 下一步

- 阅读 [架构设计](./ARCHITECTURE.md) 了解更多
- 查看 [API 参考](./API_REFERENCE.md) 了解所有端点
- 访问 http://localhost:8000/docs 体验交互式文档

---

**版本**: 2.0.0
**最后更新**: 2025-02-03
