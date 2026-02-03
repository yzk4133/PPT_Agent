# Multi-Agent PPT API 文档

## 概述

Multi-Agent PPT Generation API 采用 **FastAPI 统一网关架构**，前端只需调用一个入口点，后端自动调度 Agent 服务处理业务逻辑。

### 架构特点

- ✅ **单一入口**: 所有请求通过 `backend/api/main.py` (端口 8000)
- ✅ **内部调度**: Agent 服务通过函数调用（非 HTTP）执行
- ✅ **流式响应**: 支持 SSE 和 NDJSON 流式数据传输
- ✅ **统一异常处理**: 标准化的错误响应格式
- ✅ **自动文档**: Swagger UI 自动生成 API 文档

---

## 快速开始

### 1. 启动后端

```bash
cd backend
python -m api.main
```

后端将在 http://localhost:8000 启动。

### 2. 访问 API 文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 文件结构

```
backend/api/
├── main.py                    # FastAPI 应用入口
├── routes/                    # API 路由
│   ├── presentation.py        # 演示文稿管理
│   └── ppt_generation.py      # PPT 生成
└── schemas/                   # 数据模型
    ├── requests.py            # 请求模型
    └── responses.py           # 响应模型
```

---

## API 端点

### 大纲与幻灯片

| 方法 | 路径 | 功能 | 响应类型 |
|------|------|------|----------|
| POST | `/api/ppt/outline/generate` | 生成大纲 | text/event-stream (SSE) |
| POST | `/api/ppt/slides/generate` | 生成幻灯片 | application/json (NDJSON) |
| GET | `/api/ppt/health` | 健康检查 | application/json |

### 演示文稿管理

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/presentation/create` | 创建演示文稿 |
| GET | `/api/presentation/progress/{id}` | 查询进度 |
| GET | `/api/presentation/detail/{id}` | 获取详情 |

---

## 详细文档

| 文档 | 说明 |
|------|------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 架构设计与数据流 |
| [API_REFERENCE.md](./API_REFERENCE.md) | API 接口详细说明 |
| [QUICK_START.md](./QUICK_START.md) | 快速启动指南 |

---

## 环境变量

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

---

## 故障排查

### 问题：端口 8000 已被占用

```bash
# 查找占用进程
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# 或更换端口
FASTAPI_PORT=8001 python -m api.main
```

### 问题：Agent 初始化失败

检查：
1. MCP 配置文件是否存在
2. 模型 API key 是否配置
3. 依赖是否完整安装

---

## 开发指南

### 添加新端点

1. 在 `routes/` 中创建或更新路由文件
2. 在 `main.py` 中注册路由
3. 在 `schemas/` 中定义请求/响应模型

### 修改现有端点

1. 更新对应的路由文件
2. 更新数据模型（如需要）
3. 重启后端服务

---

**版本**: 2.0.0
**最后更新**: 2025-02-03
