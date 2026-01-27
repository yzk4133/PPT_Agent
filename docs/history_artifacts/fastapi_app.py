"""FastAPI主应用

提供Web API接口
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import asyncio

from .config import get_config, SystemConfig
from .coordinator import TaskCoordinator
from .agent_base import AgentConfig
from .content_agent import ContentGeneratorAgent
from .design_agent import DesignAgent
from .code_generator_agent import CodeGeneratorAgent
from .exceptions import PPTSystemException, handle_exception


# Pydantic模型
class PPTRequest(BaseModel):
    """PPT生成请求"""
    topic: str = Field(..., description="PPT主题")
    audience: str = Field(default="通用", description="目标受众")
    duration: int = Field(default=30, description="预计时长（分钟）")
    style: str = Field(default="business", description="风格偏好")
    template_id: Optional[str] = Field(None, description="模板ID")


class PPTResponse(BaseModel):
    """PPT生成响应"""
    success: bool
    task_id: str
    status: str
    message: str
    download_url: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str


# 创建FastAPI应用
app = FastAPI(
    title="MultiAgent PPT API",
    description="基于多Agent协作的智能PPT生成系统",
    version="0.1.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局状态
coordinator: Optional[TaskCoordinator] = None


@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    global coordinator

    # 加载配置
    config = get_config()

    # 初始化协调器
    coordinator = TaskCoordinator()

    # 注册Agent
    coordinator.register_agent(
        "content_generator",
        ContentGeneratorAgent(AgentConfig(
            name="content_generator",
            role="内容生成",
            model_provider="anthropic"
        ))
    )

    coordinator.register_agent(
        "design_agent",
        DesignAgent(AgentConfig(
            name="design_agent",
            role="设计建议",
            model_provider="anthropic"
        ))
    )

    coordinator.register_agent(
        "code_generator",
        CodeGeneratorAgent(AgentConfig(
            name="code_generator",
            role="代码生成",
            model_provider="anthropic"
        ))
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    return HealthResponse(
        status="healthy",
        version="0.1.0"
    )


@app.post("/api/v1/generate", response_model=PPTResponse)
async def generate_ppt(
    request: PPTRequest,
    background_tasks: BackgroundTasks
):
    """生成PPT的主端点"""
    try:
        # 分解任务
        tasks = coordinator.decompose_requirement(request.topic)

        # 在后台执行任务
        task_id = f"task_{hash(request.topic)}"

        background_tasks.add_task(
            execute_generation,
            task_id,
            request
        )

        return PPTResponse(
            success=True,
            task_id=task_id,
            status="processing",
            message="PPT生成任务已启动"
        )

    except Exception as e:
        if isinstance(e, PPTSystemException):
            raise HTTPException(status_code=400, detail=handle_exception(e))
        else:
            raise HTTPException(status_code=500, detail=str(e))


async def execute_generation(task_id: str, request: PPTRequest):
    """后台执行PPT生成任务"""
    try:
        # 这里实现实际的生成逻辑
        await asyncio.sleep(2)  # 模拟处理

    except Exception as e:
        # 记录错误
        pass


@app.get("/api/v1/status/{task_id}")
async def get_task_status(task_id: str):
    """查询任务状态"""
    return {
        "task_id": task_id,
        "status": "completed",
        "progress": 100
    }


@app.get("/api/v1/templates")
async def list_templates(category: Optional[str] = None):
    """列出可用模板"""
    from .template_system import get_template_library

    library = get_template_library()

    if category:
        templates = library.list_templates(category)
    else:
        templates = library.list_templates()

    return {
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "category": t.category.value,
                "description": t.description
            }
            for t in templates
        ]
    }


if __name__ == "__main__":
    import uvicorn
    config = get_config()
    uvicorn.run(
        "fastapi_app:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.debug
    )
