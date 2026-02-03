# 新架构快速开始指南

> 5分钟了解如何使用新的架构设计

---

## 🚀 核心改进

### 之前（旧架构）

```python
# ❌ 类型不安全
ctx.session.state["data"] = {...}
data = ctx.session.state.get("data")  # Any类型

# ❌ 硬编码依赖
from agents.orchestrator.master_coordinator import master_coordinator_agent
result = await master_coordinator_agent.run(...)

# ❌ 全局变量
_service = None
```

### 现在（新架构）

```python
# ✅ 强类型
context = AgentContext(
    request_id="req_123",
    requirement=Requirement(topic="AI", num_slides=10)
)
context.framework = PPTFramework(...)  # IDE自动补全

# ✅ 依赖注入
def __init__(self, agent_gateway: AgentGateway):
    self.agent_gateway = agent_gateway

result = await self.agent_gateway.execute_master_coordinator(context)

# ✅ 容器管理
container.presentation_service()
```

---

## 📦 新增核心模块

### 1. 强类型上下文（domain/models/agent_context.py）

```python
from domain.models.agent_context import AgentContext, Requirement

# 创建上下文
context = AgentContext(
    request_id="req_123",
    requirement=Requirement(
        topic="人工智能发展趋势",
        num_slides=10,
        language="中文"
    )
)

# 类型安全的数据访问
context.framework = PPTFramework(...)
print(context.framework.title)  # IDE提供补全
```

### 2. 统一结果封装（domain/models/agent_result.py）

```python
from domain.models.agent_result import AgentResult, ResultStatus

# 返回成功结果
result = AgentResult.success(
    data=ppt_data,
    message="生成成功",
    execution_time=12.5
)

# 返回失败结果
result = AgentResult.failure(
    message="LLM调用失败",
    errors=["连接超时"]
)

# 使用降级策略
result = AgentResult.partial(
    data=default_data,
    fallback_reason="格式解析失败"
)

# 检查结果
if result.is_success:
    print(result.data)
```

### 3. Agent网关（agents/orchestrator/agent_gateway.py）

```python
from agents.orchestrator.agent_gateway import AgentGateway

# 创建网关
gateway = AgentGateway(llm_provider=llm)

# 执行Agent（自动重试、异常处理）
result = await gateway.execute_master_coordinator(context)

# 带降级策略
async def fallback(ctx):
    return {"default": "content"}

result = await gateway.execute_with_fallback(context, fallback)
```

### 4. 依赖注入容器（infrastructure/di/container.py）

```python
from infrastructure.di import create_container

# 创建容器
container = create_container()

# 获取服务
presentation_service = container.presentation_service()
outline_service = container.outline_service()
```

### 5. API依赖注入（api/dependencies.py）

```python
from fastapi import APIRouter
from api.dependencies import PresentationServiceDep

router = APIRouter()

@router.post("/presentations")
async def create(
    request: CreateRequest,
    service: PresentationServiceDep  # 自动注入
):
    return await service.generate_presentation(...)
```

### 6. 统一异常处理（api/middleware/error_handler.py）

```python
from api.middleware import APIException, ResourceNotFoundError

# 抛出异常
raise ResourceNotFoundError("Presentation", "ppt_123")

# 自动转换为标准JSON响应：
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Presentation未找到: ppt_123"
  },
  "timestamp": "2026-02-03T10:00:00"
}
```

---

## 🔧 如何使用

### 编写新的Service

```python
# services/my_service.py
from domain.models.agent_context import AgentContext, Requirement
from domain.models.agent_result import AgentResult
from agents.orchestrator.agent_gateway import AgentGateway

class MyService:
    def __init__(self, agent_gateway: AgentGateway, database):
        self.agent_gateway = agent_gateway
        self.db = database

    async def do_something(self, params):
        # 1. 创建强类型上下文
        context = AgentContext(
            request_id=f"req_{uuid.uuid4()}",
            requirement=Requirement(
                topic=params.topic,
                num_slides=params.num_slides
            )
        )

        # 2. 调用Agent网关
        result: AgentResult = await self.agent_gateway.execute_master_coordinator(context)

        # 3. 处理结果
        if result.is_success:
            return context.final_ppt_path
        else:
            raise Exception(result.message)
```

### 编写新的API

```python
# api/routes/my_routes.py
from fastapi import APIRouter
from api.dependencies import PresentationServiceDep
from api.middleware import APIException

router = APIRouter(prefix="/api/v1/my", tags=["My"])

@router.post("")
async def my_endpoint(
    request: MyRequest,
    service: PresentationServiceDep
):
    try:
        result = await service.do_something(request)
        return {"success": True, "data": result}
    except Exception as e:
        raise APIException(str(e))
```

### 初始化FastAPI应用

```python
# main.py
from fastapi import FastAPI
from infrastructure.di import create_container
from api.middleware import register_exception_handlers

app = FastAPI(title="MultiAgentPPT API")

# 初始化容器
container = create_container()
app.state.container = container

# 注册异常处理
register_exception_handlers(app)

# 注册路由
from api.routes import presentations
app.include_router(presentations.router)
```

---

## 🎯 迁移现有代码

### Step 1: 更新Service

```python
# 旧代码
class PresentationService:
    def __init__(self):
        from agents.orchestrator.master_coordinator import master_coordinator_agent
        self._coordinator = master_coordinator_agent

# 新代码
class PresentationService:
    def __init__(self, agent_gateway: AgentGateway, database):
        self.agent_gateway = agent_gateway
        self.db = database
```

### Step 2: 使用强类型上下文

```python
# 旧代码
ctx.session.state["ppt_framework"] = {...}
framework = ctx.session.state.get("ppt_framework")

# 新代码
context = AgentContext(...)
context.framework = PPTFramework(...)
framework = context.framework  # 类型安全
```

### Step 3: 统一结果处理

```python
# 旧代码
try:
    result = await agent.run()
    if result["success"]:
        return result["data"]
except Exception as e:
    return {"error": str(e)}

# 新代码
result: AgentResult = await gateway.execute_master_coordinator(context)
if result.is_success:
    return result.data
else:
    raise APIException(result.message)
```

---

## 📝 完整示例

```python
# ========== Domain Models ==========
from domain.models.agent_context import AgentContext, Requirement
from domain.models.agent_result import AgentResult

# ========== Agent Gateway ==========
from agents.orchestrator.agent_gateway import AgentGateway

class PresentationService:
    def __init__(self, agent_gateway: AgentGateway, database):
        self.agent_gateway = agent_gateway
        self.db = database

    async def generate_presentation(self, presentation_id: str):
        # 获取任务信息
        task = await self.db.get(presentation_id)

        # 创建强类型上下文
        context = AgentContext(
            request_id=presentation_id,
            requirement=Requirement(
                topic=task["topic"],
                num_slides=task["num_slides"],
                language=task["language"]
            )
        )

        # 调用Agent网关（自动重试、异常处理）
        result: AgentResult = await self.agent_gateway.execute_master_coordinator(context)

        # 处理结果
        if result.is_success:
            await self.db.update(presentation_id, {
                "status": "completed",
                "ppt_path": context.final_ppt_path
            })
            return result
        else:
            await self.db.update(presentation_id, {
                "status": "failed",
                "error": result.message
            })
            raise Exception(result.message)

# ========== API Layer ==========
from fastapi import APIRouter
from api.dependencies import PresentationServiceDep
from api.middleware import APIException

router = APIRouter(prefix="/api/v1/presentations")

@router.post("")
async def create_presentation(
    request: CreatePresentationRequest,
    service: PresentationServiceDep  # 自动注入
):
    try:
        presentation_id = await service.create_task(request)
        return {"success": True, "data": {"presentation_id": presentation_id}}
    except Exception as e:
        raise APIException(str(e), status_code=500)

# ========== Application Initialization ==========
from fastapi import FastAPI
from infrastructure.di import create_container
from api.middleware import register_exception_handlers

app = FastAPI()

# 初始化容器
container = create_container()
app.state.container = container

# 注册异常处理
register_exception_handlers(app)

# 注册路由
app.include_router(router)
```

---

## 🔍 常见问题

### Q: 如何测试使用依赖注入的Service？

```python
# 使用mock
from unittest.mock import Mock

gateway_mock = Mock(spec=AgentGateway)
gateway_mock.execute_master_coordinator.return_value = AgentResult.success(...)

service = PresentationService(agent_gateway=gateway_mock, database=db_mock)
```

### Q: 如何添加新的Agent？

1. 在 `agents/core/` 创建Agent
2. 在 `AgentGateway._get_agent_by_name()` 添加映射
3. 直接使用 `gateway.execute_single_agent("my_agent", context)`

### Q: 如何添加降级策略？

```python
async def my_fallback(context: AgentContext):
    # 返回降级数据
    return {"default": "content"}

result = await gateway.execute_with_fallback(context, my_fallback)
```

---

## 📚 更多文档

- [API_SERVICE_DESIGN.md](./API_SERVICE_DESIGN.md) - 完整架构设计（93页）
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - 实施总结
- [ARCHITECTURE.md](./ARCHITECTURE.md) - 整体架构

---

**开始使用**: 阅读 [API_SERVICE_DESIGN.md](./API_SERVICE_DESIGN.md) 了解详细设计  
**问题反馈**: 查看实施计划或提交Issue
