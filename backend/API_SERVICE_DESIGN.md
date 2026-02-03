# API与Service层架构设计方案

> **版本**: v2.0  
> **日期**: 2026-02-03  
> **架构**: 标准前后端分离 + 强类型Agent通信

---

## 📋 目录

- [1. 架构概览](#1-架构概览)
- [2. 强类型Agent通信](#2-强类型agent通信)
- [3. 依赖注入容器](#3-依赖注入容器)
- [4. API层设计](#4-api层设计)
- [5. Service层设计](#5-service层设计)
- [6. Agent网关层](#6-agent网关层)
- [7. 前后端协同](#7-前后端协同)
- [8. 实施计划](#8-实施计划)

---

## 1. 架构概览

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                     (Next.js + TypeScript)                   │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTP/WebSocket
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway (可选)                       │
│                   (Kong/Nginx/Traefik)                      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                         API层                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Routes      │  │  Middleware  │  │  Schemas     │      │
│  │  (FastAPI)   │  │  (Auth/CORS) │  │  (Pydantic)  │      │
│  └──────┬───────┘  └──────────────┘  └──────────────┘      │
│         │ Depends()                                          │
└─────────┼────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                      依赖注入容器                             │
│         (python-dependency-injector)                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Services │ Repositories │ AgentFactory │ Config    │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                      Service层                               │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │PresentationSvc   │  │  OutlineService  │                │
│  │  (业务编排)       │  │   (大纲生成)     │                │
│  └────────┬─────────┘  └──────────────────┘                │
│           │ 调用                                             │
└───────────┼──────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Agent网关层                              │
│              (agents/orchestrator/agent_gateway.py)         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  • 统一调用接口                                        │  │
│  │  • 强类型上下文传递 (AgentContext)                     │  │
│  │  • 结果解析与降级策略                                   │  │
│  │  • 异常处理与重试                                       │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                      Agent层                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  MasterCoordinator (1主5子架构)                        │  │
│  │  ├─ RequirementParser                                 │  │
│  │  ├─ FrameworkDesigner                                 │  │
│  │  ├─ OptimizedResearch                                 │  │
│  │  ├─ ContentGenerator                                  │  │
│  │  └─ PageRender                                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心原则

✅ **明确的职责分离**

- API层: 仅处理HTTP请求/响应，参数验证
- Service层: 业务逻辑编排，事务管理
- Agent网关层: Agent调用封装，结果解析
- Agent层: 具体任务执行

✅ **依赖倒置**

- 上层依赖接口，不依赖具体实现
- 使用依赖注入容器管理生命周期

✅ **类型安全**

- Agent间通信使用强类型数据类
- Pydantic Schema验证所有输入输出

✅ **可测试性**

- 所有依赖可mock
- Service和Agent可独立测试

---

## 2. 强类型Agent通信

### 2.1 现有问题

```python
# ❌ 问题: 使用字典传递数据，类型不安全
ctx.session.state["ppt_framework"] = {...}
framework = ctx.session.state.get("ppt_framework")  # 返回Any类型
```

### 2.2 解决方案: 强类型AgentContext

#### 文件: `domain/models/agent_context.py`

```python
"""
强类型Agent上下文模型
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ExecutionMode(str, Enum):
    """执行模式"""
    FULL = "full"              # 完整执行
    PHASE_1 = "phase_1"        # 仅阶段1-2
    PHASE_2 = "phase_2"        # 从checkpoint继续

class AgentStage(str, Enum):
    """Agent执行阶段"""
    REQUIREMENT_PARSING = "requirement_parsing"
    FRAMEWORK_DESIGN = "framework_design"
    RESEARCH = "research"
    CONTENT_GENERATION = "content_generation"
    PAGE_RENDERING = "page_rendering"
    QUALITY_CHECK = "quality_check"

@dataclass
class Requirement:
    """需求数据模型"""
    topic: str
    num_slides: int
    language: str = "中文"
    style: str = "professional"
    industry: Optional[str] = None
    target_audience: Optional[str] = None
    key_points: List[str] = field(default_factory=list)

@dataclass
class PPTFramework:
    """PPT框架模型"""
    title: str
    outline: List[Dict[str, Any]]
    total_slides: int
    structure_type: str  # "linear", "hierarchical", "matrix"

@dataclass
class ResearchResult:
    """研究结果模型"""
    topic: str
    content: str
    sources: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    confidence: float = 1.0

@dataclass
class SlideContent:
    """幻灯片内容模型"""
    slide_number: int
    title: str
    content: str
    layout_type: str
    images: List[str] = field(default_factory=list)
    notes: Optional[str] = None

@dataclass
class AgentContext:
    """
    强类型Agent上下文

    替代原来的 session.state 字典，提供类型安全的数据传递
    """
    # 基础信息
    request_id: str
    execution_mode: ExecutionMode = ExecutionMode.FULL
    current_stage: Optional[AgentStage] = None

    # 阶段数据（强类型）
    requirement: Optional[Requirement] = None
    framework: Optional[PPTFramework] = None
    research_results: List[ResearchResult] = field(default_factory=list)
    slide_contents: List[SlideContent] = field(default_factory=list)
    final_ppt_path: Optional[str] = None

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # 错误和重试
    errors: List[str] = field(default_factory=list)
    retry_count: int = 0

    # 扩展字段（向后兼容）
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于序列化）"""
        return {
            "request_id": self.request_id,
            "execution_mode": self.execution_mode.value,
            "current_stage": self.current_stage.value if self.current_stage else None,
            "requirement": self.requirement.__dict__ if self.requirement else None,
            "framework": self.framework.__dict__ if self.framework else None,
            "research_results": [r.__dict__ for r in self.research_results],
            "slide_contents": [s.__dict__ for s in self.slide_contents],
            "final_ppt_path": self.final_ppt_path,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "errors": self.errors,
            "retry_count": self.retry_count,
            "extra": self.extra,
        }
```

### 2.3 Agent结果封装

#### 文件: `domain/models/agent_result.py`

```python
"""
统一的Agent结果封装
"""
from dataclasses import dataclass
from typing import Optional, Any, List, Generic, TypeVar
from enum import Enum

T = TypeVar('T')

class ResultStatus(str, Enum):
    """结果状态"""
    SUCCESS = "success"
    PARTIAL = "partial"    # 部分成功（有降级）
    FAILURE = "failure"
    RETRY = "retry"        # 需要重试

@dataclass
class AgentResult(Generic[T]):
    """
    统一的Agent执行结果

    使用泛型支持不同类型的数据
    """
    status: ResultStatus
    data: Optional[T] = None
    message: str = ""
    errors: List[str] = None

    # 降级信息
    fallback_used: bool = False
    fallback_reason: Optional[str] = None

    # 性能指标
    execution_time: float = 0.0
    token_usage: int = 0

    @property
    def is_success(self) -> bool:
        return self.status in [ResultStatus.SUCCESS, ResultStatus.PARTIAL]

    @property
    def needs_retry(self) -> bool:
        return self.status == ResultStatus.RETRY
```

### 2.4 使用示例

```python
# ✅ 新方式: 强类型
from domain.models.agent_context import AgentContext, Requirement, ExecutionMode
from domain.models.agent_result import AgentResult, ResultStatus

# 创建上下文
context = AgentContext(
    request_id="req_123",
    execution_mode=ExecutionMode.FULL,
    requirement=Requirement(
        topic="人工智能发展趋势",
        num_slides=10,
        language="中文"
    )
)

# Agent返回强类型结果
result: AgentResult[PPTFramework] = await framework_agent.execute(context)

if result.is_success:
    context.framework = result.data
    # IDE会提供自动补全
    print(context.framework.title)  # ✅ 类型安全
```

---

## 3. 依赖注入容器

### 3.1 容器实现

#### 文件: `infrastructure/di/container.py`

```python
"""
依赖注入容器

使用 dependency-injector 管理所有依赖
"""
from dependency_injector import containers, providers
from infrastructure.config import Config
from infrastructure.database import Database
from infrastructure.llm import LLMProvider
from services.presentation_service import PresentationService
from services.outline_service import OutlineService
from agents.orchestrator.agent_gateway import AgentGateway

class Container(containers.DeclarativeContainer):
    """应用级依赖注入容器"""

    # 配置
    config = providers.Singleton(Config)

    # 基础设施
    database = providers.Singleton(
        Database,
        connection_string=config.provided.database_url
    )

    llm_provider = providers.Singleton(
        LLMProvider,
        provider=config.provided.llm_provider,
        api_key=config.provided.llm_api_key
    )

    # Agent网关
    agent_gateway = providers.Singleton(
        AgentGateway,
        llm_provider=llm_provider
    )

    # Services
    presentation_service = providers.Factory(
        PresentationService,
        agent_gateway=agent_gateway,
        database=database
    )

    outline_service = providers.Factory(
        OutlineService,
        agent_gateway=agent_gateway
    )
```

### 3.2 FastAPI集成

#### 文件: `api/dependencies.py`

```python
"""
FastAPI依赖注入
"""
from typing import Annotated
from fastapi import Depends, Request
from infrastructure.di.container import Container
from services.presentation_service import PresentationService
from services.outline_service import OutlineService

def get_container(request: Request) -> Container:
    """获取依赖注入容器"""
    return request.app.state.container

def get_presentation_service(
    container: Annotated[Container, Depends(get_container)]
) -> PresentationService:
    """获取演示文稿服务"""
    return container.presentation_service()

def get_outline_service(
    container: Annotated[Container, Depends(get_container)]
) -> OutlineService:
    """获取大纲服务"""
    return container.outline_service()

# 类型别名（简化使用）
PresentationServiceDep = Annotated[PresentationService, Depends(get_presentation_service)]
OutlineServiceDep = Annotated[OutlineService, Depends(get_outline_service)]
```

---

## 4. API层设计

### 4.1 统一错误处理

#### 文件: `api/middleware/error_handler.py`

```python
"""
统一异常处理中间件
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Union
import logging

logger = logging.getLogger(__name__)

class APIException(Exception):
    """API异常基类"""
    def __init__(self, message: str, status_code: int = 400, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "API_ERROR"

async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """处理API异常"""
    logger.error(f"API Error: {exc.message}", extra={
        "error_code": exc.error_code,
        "path": request.url.path
    })

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "path": request.url.path
            }
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理参数验证异常"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "请求参数验证失败",
                "details": exc.errors()
            }
        }
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理未捕获的异常"""
    logger.exception("Unhandled exception", extra={"path": request.url.path})

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误"
            }
        }
    )
```

### 4.2 统一响应Schema

#### 文件: `api/schemas/response.py`

```python
"""
统一响应Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, Generic, TypeVar, List
from datetime import datetime

T = TypeVar('T')

class ErrorDetail(BaseModel):
    """错误详情"""
    code: str
    message: str
    field: Optional[str] = None

class APIResponse(BaseModel, Generic[T]):
    """统一API响应"""
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None

class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: List[T]
    total: int
    page: int = 1
    page_size: int = 20
    has_more: bool = False
```

### 4.3 演示文稿API

#### 文件: `api/routes/presentations.py`

```python
"""
演示文稿API路由（统一版本）
"""
from fastapi import APIRouter, BackgroundTasks, status, WebSocket, WebSocketDisconnect
from api.dependencies import PresentationServiceDep
from api.schemas.presentation import (
    PresentationCreateRequest,
    PresentationCreateResponse,
    PresentationDetailResponse,
    PresentationListResponse,
    PresentationProgressResponse
)
from api.schemas.response import APIResponse
from typing import Optional
import logging

router = APIRouter(prefix="/api/v1/presentations", tags=["Presentations"])
logger = logging.getLogger(__name__)

@router.post(
    "",
    response_model=APIResponse[PresentationCreateResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="创建演示文稿",
    description="异步创建演示文稿，返回任务ID用于查询进度"
)
async def create_presentation(
    request: PresentationCreateRequest,
    background_tasks: BackgroundTasks,
    service: PresentationServiceDep
):
    """创建演示文稿（异步）"""

    # 创建任务
    presentation_id = await service.create_presentation_task(
        title=request.title,
        topic=request.topic,
        num_slides=request.num_slides,
        language=request.language,
        style=request.style
    )

    # 后台执行生成
    background_tasks.add_task(
        service.generate_presentation,
        presentation_id=presentation_id
    )

    return APIResponse(
        success=True,
        data=PresentationCreateResponse(
            presentation_id=presentation_id,
            status="queued",
            message="演示文稿生成任务已创建"
        )
    )

@router.get(
    "/{presentation_id}",
    response_model=APIResponse[PresentationDetailResponse],
    summary="获取演示文稿详情"
)
async def get_presentation(
    presentation_id: str,
    service: PresentationServiceDep
):
    """获取演示文稿详情"""
    presentation = await service.get_presentation(presentation_id)

    return APIResponse(
        success=True,
        data=presentation
    )

@router.get(
    "/{presentation_id}/progress",
    response_model=APIResponse[PresentationProgressResponse],
    summary="查询生成进度"
)
async def get_progress(
    presentation_id: str,
    service: PresentationServiceDep
):
    """查询演示文稿生成进度"""
    progress = await service.get_progress(presentation_id)

    return APIResponse(
        success=True,
        data=progress
    )

@router.websocket("/ws/{presentation_id}")
async def websocket_progress(
    websocket: WebSocket,
    presentation_id: str,
    service: PresentationServiceDep
):
    """WebSocket实时推送进度"""
    await websocket.accept()

    try:
        async for progress_event in service.stream_progress(presentation_id):
            await websocket.send_json(progress_event.dict())
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {presentation_id}")
    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal error")

@router.get(
    "",
    response_model=APIResponse[PresentationListResponse],
    summary="列出演示文稿"
)
async def list_presentations(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    service: PresentationServiceDep
):
    """列出演示文稿（分页）"""
    result = await service.list_presentations(
        page=page,
        page_size=page_size,
        status_filter=status_filter
    )

    return APIResponse(
        success=True,
        data=result
    )

@router.delete(
    "/{presentation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除演示文稿"
)
async def delete_presentation(
    presentation_id: str,
    service: PresentationServiceDep
):
    """删除演示文稿"""
    await service.delete_presentation(presentation_id)
    return None
```

---

## 5. Service层设计

### 5.1 重构后的PresentationService

#### 文件: `services/presentation_service.py`

```python
"""
演示文稿服务（重构版）

移除旧三阶段架构，统一使用MasterCoordinator
"""
from typing import Optional, AsyncIterator
from domain.models.agent_context import AgentContext, Requirement, ExecutionMode
from domain.models.agent_result import AgentResult
from agents.orchestrator.agent_gateway import AgentGateway
from infrastructure.database import Database
import uuid
import logging

logger = logging.getLogger(__name__)

class PresentationService:
    """演示文稿服务"""

    def __init__(self, agent_gateway: AgentGateway, database: Database):
        """
        初始化服务

        Args:
            agent_gateway: Agent网关（封装Agent调用）
            database: 数据库访问
        """
        self.agent_gateway = agent_gateway
        self.db = database

    async def create_presentation_task(
        self,
        title: str,
        topic: str,
        num_slides: int,
        language: str = "中文",
        style: str = "professional"
    ) -> str:
        """
        创建演示文稿生成任务

        Returns:
            presentation_id: 演示文稿ID
        """
        presentation_id = str(uuid.uuid4())

        # 保存到数据库
        await self.db.presentations.create({
            "id": presentation_id,
            "title": title,
            "topic": topic,
            "num_slides": num_slides,
            "language": language,
            "style": style,
            "status": "queued",
            "created_at": "now()"
        })

        logger.info(f"Created presentation task: {presentation_id}")
        return presentation_id

    async def generate_presentation(
        self,
        presentation_id: str,
        execution_mode: ExecutionMode = ExecutionMode.FULL
    ) -> AgentResult:
        """
        生成演示文稿（核心业务逻辑）

        Args:
            presentation_id: 演示文稿ID
            execution_mode: 执行模式（FULL/PHASE_1/PHASE_2）

        Returns:
            AgentResult: 执行结果
        """
        try:
            # 1. 获取任务信息
            presentation = await self.db.presentations.get(presentation_id)

            # 2. 更新状态
            await self.db.presentations.update(presentation_id, {
                "status": "generating"
            })

            # 3. 创建Agent上下文
            context = AgentContext(
                request_id=presentation_id,
                execution_mode=execution_mode,
                requirement=Requirement(
                    topic=presentation["topic"],
                    num_slides=presentation["num_slides"],
                    language=presentation["language"],
                    style=presentation["style"]
                )
            )

            # 4. 调用Agent网关执行（统一使用MasterCoordinator）
            result = await self.agent_gateway.execute_master_coordinator(context)

            # 5. 更新结果
            if result.is_success:
                await self.db.presentations.update(presentation_id, {
                    "status": "completed",
                    "ppt_path": context.final_ppt_path,
                    "completed_at": "now()"
                })
                logger.info(f"Presentation generated successfully: {presentation_id}")
            else:
                await self.db.presentations.update(presentation_id, {
                    "status": "failed",
                    "error_message": result.message
                })
                logger.error(f"Presentation generation failed: {presentation_id}")

            return result

        except Exception as e:
            logger.exception(f"Error generating presentation: {e}")
            await self.db.presentations.update(presentation_id, {
                "status": "failed",
                "error_message": str(e)
            })
            raise

    async def get_presentation(self, presentation_id: str) -> dict:
        """获取演示文稿详情"""
        return await self.db.presentations.get(presentation_id)

    async def get_progress(self, presentation_id: str) -> dict:
        """获取生成进度"""
        # TODO: 从缓存或数据库读取实时进度
        presentation = await self.db.presentations.get(presentation_id)

        return {
            "presentation_id": presentation_id,
            "status": presentation["status"],
            "progress": presentation.get("progress", 0),
            "current_stage": presentation.get("current_stage"),
            "message": presentation.get("message", "")
        }

    async def stream_progress(
        self,
        presentation_id: str
    ) -> AsyncIterator[dict]:
        """
        流式推送进度（WebSocket使用）

        Yields:
            进度事件
        """
        # TODO: 实现Redis Pub/Sub或Server-Sent Events
        pass

    async def list_presentations(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None
    ) -> dict:
        """列出演示文稿（分页）"""
        offset = (page - 1) * page_size

        query = self.db.presentations.query()
        if status_filter:
            query = query.filter(status=status_filter)

        total = await query.count()
        items = await query.limit(page_size).offset(offset).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": offset + page_size < total
        }

    async def delete_presentation(self, presentation_id: str):
        """删除演示文稿"""
        await self.db.presentations.delete(presentation_id)
        logger.info(f"Deleted presentation: {presentation_id}")
```

---

## 6. Agent网关层

### 6.1 Agent网关实现

#### 文件: `agents/orchestrator/agent_gateway.py`

```python
"""
Agent网关层

统一封装Agent调用，提供降级策略和异常处理
"""
from typing import Optional
from domain.models.agent_context import AgentContext, AgentStage
from domain.models.agent_result import AgentResult, ResultStatus
from agents.orchestrator.master_coordinator import MasterCoordinator
from infrastructure.llm import LLMProvider
import logging

logger = logging.getLogger(__name__)

class AgentGateway:
    """
    Agent网关

    职责：
    1. 统一Agent调用接口
    2. 强类型上下文传递
    3. 结果解析与降级策略
    4. 异常处理与重试
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
        self._master_coordinator = None

    @property
    def master_coordinator(self) -> MasterCoordinator:
        """懒加载MasterCoordinator"""
        if self._master_coordinator is None:
            self._master_coordinator = MasterCoordinator(
                llm_provider=self.llm_provider
            )
        return self._master_coordinator

    async def execute_master_coordinator(
        self,
        context: AgentContext,
        max_retries: int = 3
    ) -> AgentResult:
        """
        执行MasterCoordinator（1主5子架构）

        Args:
            context: 强类型Agent上下文
            max_retries: 最大重试次数

        Returns:
            AgentResult: 统一结果封装
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Executing MasterCoordinator (attempt {attempt + 1})")

                # 调用MasterCoordinator
                result = await self.master_coordinator.execute(context)

                if result.is_success:
                    return result

                if not result.needs_retry or attempt == max_retries - 1:
                    return result

                # 需要重试
                context.retry_count = attempt + 1
                logger.warning(f"Retrying MasterCoordinator: {result.message}")

            except Exception as e:
                logger.exception(f"Error in MasterCoordinator execution: {e}")

                if attempt == max_retries - 1:
                    # 最后一次尝试失败，返回失败结果
                    return AgentResult(
                        status=ResultStatus.FAILURE,
                        message=f"执行失败: {str(e)}",
                        errors=[str(e)]
                    )

                context.errors.append(str(e))

        # 不应该到达这里
        return AgentResult(
            status=ResultStatus.FAILURE,
            message="未知错误"
        )

    async def execute_with_fallback(
        self,
        context: AgentContext,
        fallback_strategy: Optional[callable] = None
    ) -> AgentResult:
        """
        执行Agent并提供降级策略

        Args:
            context: Agent上下文
            fallback_strategy: 降级策略函数

        Returns:
            AgentResult: 结果（可能使用了降级）
        """
        result = await self.execute_master_coordinator(context)

        if not result.is_success and fallback_strategy:
            logger.warning("Using fallback strategy")

            try:
                fallback_data = await fallback_strategy(context)
                return AgentResult(
                    status=ResultStatus.PARTIAL,
                    data=fallback_data,
                    message="使用降级策略",
                    fallback_used=True,
                    fallback_reason=result.message
                )
            except Exception as e:
                logger.exception(f"Fallback strategy failed: {e}")

        return result
```

---

## 7. 前后端协同

### 7.1 前端调用示例

```typescript
// frontend/src/lib/api/presentations.ts

interface CreatePresentationRequest {
  title: string;
  topic: string;
  num_slides: number;
  language?: string;
  style?: string;
}

interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
  timestamp: string;
}

export async function createPresentation(
  request: CreatePresentationRequest,
): Promise<string> {
  const response = await fetch("/api/v1/presentations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  const result: APIResponse<{ presentation_id: string }> =
    await response.json();

  if (!result.success) {
    throw new Error(result.error?.message || "Unknown error");
  }

  return result.data!.presentation_id;
}

// WebSocket实时进度
export function watchProgress(
  presentationId: string,
  onProgress: (progress: any) => void,
) {
  const ws = new WebSocket(
    `ws://localhost:8000/api/v1/presentations/ws/${presentationId}`,
  );

  ws.onmessage = (event) => {
    const progress = JSON.parse(event.data);
    onProgress(progress);
  };

  return () => ws.close();
}
```

### 7.2 数据流

```
Frontend                Backend                   Agent
   │                       │                        │
   │  POST /presentations  │                        │
   ├──────────────────────>│                        │
   │                       │                        │
   │  { presentation_id }  │                        │
   │<──────────────────────┤                        │
   │                       │                        │
   │  WS /ws/{id}          │                        │
   ├──────────────────────>│                        │
   │                       │  execute()             │
   │                       ├───────────────────────>│
   │                       │                        │
   │  { progress: 20% }    │  { stage: research }   │
   │<──────────────────────┤<───────────────────────┤
   │                       │                        │
   │  { progress: 50% }    │  { stage: generate }   │
   │<──────────────────────┤<───────────────────────┤
   │                       │                        │
   │  { status: completed }│  { result: success }   │
   │<──────────────────────┤<───────────────────────┤
   │                       │                        │
   │  GET /{id}            │                        │
   ├──────────────────────>│                        │
   │                       │                        │
   │  { ppt_path: ... }    │                        │
   │<──────────────────────┤                        │
```

---

## 8. 实施计划

### 阶段1: 基础架构 (1-2天)

- [x] 创建 `domain/models/agent_context.py` - 强类型上下文
- [x] 创建 `domain/models/agent_result.py` - 统一结果封装
- [ ] 创建 `infrastructure/di/container.py` - 依赖注入容器
- [ ] 创建 `api/middleware/error_handler.py` - 异常处理
- [ ] 创建 `api/dependencies.py` - FastAPI依赖注入

### 阶段2: Agent网关 (1-2天)

- [ ] 创建 `agents/orchestrator/agent_gateway.py`
- [ ] 重构 `MasterCoordinator` 支持强类型上下文
- [ ] 更新所有子Agent使用 `AgentContext`

### 阶段3: Service层重构 (2-3天)

- [ ] 重构 `services/presentation_service.py`
  - 移除旧三阶段代码
  - 使用依赖注入
  - 统一通过AgentGateway调用
- [ ] 重构 `services/outline_service.py`
- [ ] 添加单元测试

### 阶段4: API层统一 (1-2天)

- [ ] 合并 `api/routes/` 和 `api/endpoints/`
- [ ] 创建 `api/routes/presentations.py` (统一版本)
- [ ] 实现WebSocket进度推送
- [ ] 更新 `api/schemas/` 匹配前端需求

### 阶段5: 前端对接 (2-3天)

- [ ] 更新前端API调用（从Prisma直连改为调用后端API）
- [ ] 实现WebSocket进度展示
- [ ] 前后端集成测试

### 阶段6: 文档和测试 (1-2天)

- [x] 完成 `API_SERVICE_DESIGN.md`
- [ ] 编写API文档（OpenAPI/Swagger）
- [ ] 编写集成测试
- [ ] 性能测试和优化

---

## 9. 迁移清单

### 需要修改的文件

| 文件                                        | 修改内容                      | 优先级 |
| ------------------------------------------- | ----------------------------- | ------ |
| `services/presentation_service.py`          | 移除旧架构代码                | P0     |
| `agents/orchestrator/master_coordinator.py` | 支持强类型上下文              | P0     |
| `agents/core/*/`                            | 更新所有Agent使用AgentContext | P1     |
| `api/routes/presentations.py`               | 统一API实现                   | P0     |
| `api/endpoints/ppt_generation.py`           | 删除（合并到routes）          | P0     |
| `frontend/src/lib/api/*`                    | 改用后端API                   | P1     |

### 需要删除的代码

```python
# ❌ 删除: PresentationService中的旧架构分支
if self.use_master_coordinator:
    # 新架构
else:
    # 旧架构 - 删除这个分支

# ❌ 删除: 全局变量模式
_presentation_service: PresentationService = None
def set_presentation_service(service):
    global _presentation_service

# ❌ 删除: 硬编码Agent导入
from agents.orchestrator.master_coordinator import master_coordinator_agent
```

---

## 10. 最佳实践

### ✅ DO

1. **使用强类型**

   ```python
   context = AgentContext(requirement=Requirement(...))
   # IDE会提供自动补全和类型检查
   ```

2. **依赖注入**

   ```python
   @router.post("/")
   async def create(service: PresentationServiceDep):
       # service自动注入
   ```

3. **统一错误处理**

   ```python
   raise APIException("资源不存在", status_code=404, error_code="NOT_FOUND")
   ```

4. **结构化日志**
   ```python
   logger.info("Presentation created", extra={
       "presentation_id": id,
       "user_id": user.id
   })
   ```

### ❌ DON'T

1. **不要使用字典传递复杂数据**

   ```python
   # ❌ Bad
   ctx.session.state["data"] = {...}

   # ✅ Good
   context.requirement = Requirement(...)
   ```

2. **不要在Service层直接导入Agent**

   ```python
   # ❌ Bad
   from agents.orchestrator.master_coordinator import master_coordinator_agent

   # ✅ Good
   def __init__(self, agent_gateway: AgentGateway):
       self.agent_gateway = agent_gateway
   ```

3. **不要使用全局变量**

   ```python
   # ❌ Bad
   _service = None

   # ✅ Good
   container.presentation_service()
   ```

---

## 附录

### A. 相关文档

- [ARCHITECTURE.md](./ARCHITECTURE.md) - 整体架构设计
- [backend/README.md](./backend/README.md) - 后端目录说明
- FastAPI文档: https://fastapi.tiangolo.com/
- dependency-injector文档: https://python-dependency-injector.ets-labs.org/

### B. 技术栈

| 组件      | 技术                | 版本   |
| --------- | ------------------- | ------ |
| Web框架   | FastAPI             | 0.104+ |
| 依赖注入  | dependency-injector | 4.41+  |
| 数据验证  | Pydantic            | 2.0+   |
| 数据库ORM | SQLAlchemy          | 2.0+   |
| Agent框架 | Google ADK          | latest |
| WebSocket | FastAPI WebSocket   | -      |

### C. 性能指标

| 指标        | 目标    | 当前 |
| ----------- | ------- | ---- |
| API响应时间 | < 200ms | TBD  |
| PPT生成时间 | < 2min  | TBD  |
| 并发请求    | 100+    | TBD  |
| 错误率      | < 1%    | TBD  |

---

**版本历史**

- v2.0 (2026-02-03): 标准前后端分离架构，强类型Agent通信
- v1.0 (2025-12-xx): 初始版本，新旧架构并存
