# API 架构设计

## 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         浏览器 (前端)                             │
│                    http://localhost:3000                         │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI 统一网关                             │
│                       (端口 8000)                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  main.py - FastAPI 应用                                    │  │
│  │  - CORS 中间件                                             │  │
│  │  - 请求日志                                                 │  │
│  │  - 异常处理                                                 │  │
│  │  - 路由注册                                                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│                             ↓                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  routes/ - API 路由层                                      │  │
│  │  ├── presentation.py      (演示文稿管理)                   │  │
│  │  └── ppt_generation.py    (PPT 生成)                       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                             ↓                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Agent Service Wrapper                                     │  │
│  │  - OutlineAgentService                                    │  │
│  │  - PPTAgentService                                        │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ 函数调用（非 HTTP）
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                       Agent 业务逻辑                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  FlatOutlineAgent (大纲生成)                               │  │
│  │  Stage 1: 需求分析 → Stage 2: 并行调研 → Stage 3: 大纲    │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  FlatPPTGenerationAgent (幻灯片生成)                       │  │
│  │  Stage 1: 主题拆分 → Stage 2: 并行研究 → Stage 3: 生成    │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 数据流向

### 请求流程

```
1. 用户输入 (React 组件)
   ↓
2. Next.js API Route (前端中间层)
   ↓ fetch()
3. FastAPI 网关 (main.py)
   ↓ 路由分发
4. Route Handler (routes/ppt_generation.py)
   ↓ 调用服务
5. Agent Service (延迟初始化)
   ↓ run_async()
6. Agent 业务逻辑
   ↓ LLM 调用
7. 生成结果
```

### 响应流程

```
7. Agent 生成内容
   ↓ yield
6. Agent Service 流式输出
   ↓ yield SSE/NDJSON
5. Route Handler 转换格式
   ↓ StreamingResponse
4. FastAPI 返回流
   ↓ HTTP Response
3. Next.js 解析流
   ↓ 传递给前端
2. 前端组件消费
   ↓ useChat()
1. UI 实时更新
```

---

## 组件职责

### main.py - FastAPI 应用入口

| 职责 | 说明 |
|------|------|
| 应用配置 | FastAPI 实例创建、元数据 |
| 中间件 | CORS、请求日志、响应时间 |
| 异常处理 | APIException、HTTPException、通用异常 |
| 路由注册 | 注册所有路由模块 |
| 健康检查 | `/api/health` 端点 |
| 生命周期 | startup/shutdown 事件 |

### routes/ppt_generation.py - PPT 生成路由

| 职责 | 说明 |
|------|------|
| 大纲生成 | `POST /api/ppt/outline/generate` |
| 幻灯片生成 | `POST /api/ppt/slides/generate` |
| 大纲管理 | CRUD 操作 |
| Agent 调用 | 封装 Agent 服务调用 |
| 流式响应 | SSE/NDJSON 格式转换 |

### routes/presentation.py - 演示文稿管理

| 职责 | 说明 |
|------|------|
| 创建演示文稿 | `POST /api/presentation/create` |
| 查询进度 | `GET /api/presentation/progress/{id}` |
| 获取详情 | `GET /api/presentation/detail/{id}` |
| 后台任务 | 异步生成管理 |

### schemas/ - 数据模型

| 文件 | 内容 |
|------|------|
| requests.py | 所有请求的 Pydantic 模型 |
| responses.py | 所有响应的 Pydantic 模型 |

---

## 关键设计决策

### 1. 单进程架构

**选择**: 所有组件在一个进程中运行

**优势**:
- 简化部署（单一命令启动）
- 减少网络开销（函数调用 vs HTTP）
- 统一日志和监控
- 便于调试

**权衡**:
- 扩展性需通过多实例实现
- Agent 故障可能影响整体

### 2. 延迟初始化

**选择**: Agent 服务在首次请求时初始化

**优势**:
- 快速启动（不阻塞）
- 按需加载（节省资源）
- 支持热重载

**实现**:
```python
async def _initialize(self):
    if self._agent is not None:
        return
    # 初始化 Agent
    self._agent = create_agent()
```

### 3. 流式响应

**选择**: 使用 SSE 和 NDJSON 流式传输

**优势**:
- 实时反馈（用户体验好）
- 减少延迟（边生成边传输）
- 适合 LLM 场景

**格式**:
- 大纲生成: SSE (`data: {...}\n\n`)
- 幻灯片生成: NDJSON (`{"type": "..."}\n`)

### 4. 统一异常处理

**选择**: 全局异常处理器 + 标准错误格式

**优势**:
- 一致的错误响应
- 自动日志记录
- 便于前端处理

**格式**:
```json
{
  "status": "error",
  "error_code": "OUTLINE_GENERATION_FAILED",
  "message": "大纲生成失败",
  "timestamp": "2025-02-03T12:00:00"
}
```

---

## 扩展点

### 添加新路由

```python
# 1. 在 routes/ 中创建文件
# routes/new_feature.py

router = APIRouter(prefix="/api/new-feature", tags=["New Feature"])

@router.post("/action")
async def new_action(request: RequestModel):
    # 业务逻辑
    return ResponseModel()

# 2. 在 main.py 中注册
from api.routes import new_feature
app.include_router(new_feature.router, prefix="/api")
```

### 添加中间件

```python
# 在 main.py 中添加
@app.middleware("http")
async def custom_middleware(request: Request, call_next):
    # 前置处理
    response = await call_next(request)
    # 后置处理
    return response
```

### 添加依赖注入

```python
# 创建依赖
async def get_service():
    return Service()

# 在路由中使用
@router.post("/action")
async def action(service=Depends(get_service)):
    return service.do_something()
```

---

## 性能优化建议

### 1. 使用异步操作

```python
# ✅ 好
async def generate_outline():
    async for chunk in service.generate():
        yield chunk

# ❌ 差
def generate_outline():
    for chunk in service.generate():
        yield chunk
```

### 2. 缓存频繁访问的数据

```python
from functools import lru_cache

@lru_cache(maxsize=10)
def get_config():
    return load_config()
```

### 3. 使用后台任务

```python
from fastapi import BackgroundTasks

@router.post("/generate")
async def generate(background_tasks: BackgroundTasks):
    background_tasks.add_task(long_running_task)
    return {"status": "started"}
```

---

## 安全建议

### 1. CORS 配置

```python
# 生产环境应限制允许的域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 而非 "*"
    allow_credentials=True,
)
```

### 2. 输入验证

```python
# 始终使用 Pydantic 验证输入
class RequestModel(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000)
```

### 3. 错误信息

```python
# 生产环境不暴露详细错误
if os.getenv("ENV") == "production":
    detail = "服务器内部错误"
else:
    detail = str(exc)
```

---

**版本**: 2.0.0
**最后更新**: 2025-02-03
