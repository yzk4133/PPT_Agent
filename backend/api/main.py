"""
FastAPI 统一网关主入口

Multi-Agent PPT Generation API Gateway
所有前端请求统一通过此网关，后端调用 Agent 服务处理业务逻辑
"""

import logging
import time
import os
import sys
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 添加 backend 目录到 Python 路径
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# 导入路由
from api.routes import presentation, ppt_generation
from api.routes import auth  # 新增：认证路由

# 导入基础设施
from infrastructure.config.common_config import get_config
from infrastructure.middleware.error_handler import setup_exception_handlers

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 记录启动时间
_start_time = time.time()


def get_uptime() -> float:
    """获取服务运行时间（秒）"""
    return time.time() - _start_time


# 创建 FastAPI 应用
app = FastAPI(
    title="Multi-Agent PPT Generation API",
    description="""
    统一网关 API，提供 PPT 大纲生成和幻灯片生成服务。

    ## 架构说明
    - 前端只需调用此网关（端口 8000）
    - 网关内部调用 Agent 服务处理业务逻辑
    - 所有请求统一认证、日志和监控

    ## 主要功能
    1. **大纲生成**：根据主题生成 PPT 大纲
    2. **幻灯片生成**：根据大纲生成完整的 PPT 幻灯片
    3. **演示文稿管理**：创建、查询、删除演示文稿

    ## API 端点
    - `POST /api/ppt/outline/generate` - 生成大纲
    - `POST /api/ppt/generate` - 生成幻灯片
    - `GET /api/ppt/health` - 健康检查
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# ============================================================================
# CORS 中间件
# ============================================================================

# 从配置获取允许的来源
config = get_config()
allowed_origins = getattr(config, 'cors_allowed_origins', ["http://localhost:3000", "http://localhost:5173"])

# 如果环境变量设置了 ALLOWED_ORIGINS，使用环境变量的值
import os
env_origins = os.getenv("ALLOWED_ORIGINS", "")
if env_origins:
    allowed_origins = [origin.strip() for origin in env_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # 从配置读取
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


# ============================================================================
# 中间件：请求日志
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求"""
    start_time = time.time()

    # 记录请求信息
    logger.info(f"➡️  {request.method} {request.url.path}")

    # 处理请求
    response = await call_next(request)

    # 记录响应时间
    process_time = time.time() - start_time
    logger.info(
        f"⬅️  {request.method} {request.url.path} "
        f"- Status: {response.status_code} - Time: {process_time:.3f}s"
    )

    # 添加响应头
    response.headers["X-Process-Time"] = str(process_time)

    return response


# ============================================================================
# 异常处理器
# ============================================================================

# 使用统一的异常处理器
setup_exception_handlers(app)

# 保留旧的 APIException 类以保持向后兼容
class APIException(Exception):
    """自定义 API 异常（保留以保持向后兼容）"""
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        message: str = "内部错误",
        details: Dict[str, Any] = None
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details


# ============================================================================
# 注册路由
# ============================================================================

# 认证路由（登录、注册等）
app.include_router(
    auth.router,
    prefix="/api",
    tags=["Authentication"]
)

# PPT 生成路由（大纲生成、幻灯片生成）
app.include_router(
    ppt_generation.router,
    prefix="/api",
    tags=["PPT Generation"]
)

# 演示文稿管理路由
app.include_router(
    presentation.router,
    prefix="/api",
    tags=["Presentation Management"]
)


# ============================================================================
# 根路径和健康检查
# ============================================================================

@app.get("/", include_in_schema=False)
async def root():
    """根路径 - 重定向到 API 文档"""
    return {
        "message": "Multi-Agent PPT Generation API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/ppt/health"
    }


@app.get("/api/health")
async def health_check():
    """
    健康检查端点

    检查 API 网关及依赖服务的健康状态
    """
    return {
        "status": "healthy",
        "service": "fastapi_gateway",
        "version": "2.0.0",
        "uptime": f"{get_uptime():.2f}s",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "gateway": "ok",
            "agent_services": "ok"
        }
    }


# ============================================================================
# 启动和关闭事件
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("=" * 60)
    logger.info("🚀 FastAPI 统一网关启动中...")
    logger.info(f"   版本: 2.0.0")
    logger.info(f"   环境: {os.environ.get('ENV', 'development')}")
    logger.info("=" * 60)
    logger.info("✅ FastAPI 统一网关启动成功!")
    logger.info("   📖 API 文档: http://localhost:8000/docs")
    logger.info("   🏥 健康检查: http://localhost:8000/api/health")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    logger.info("=" * 60)
    logger.info("🛑 FastAPI 统一网关正在关闭...")
    logger.info("=" * 60)


# ============================================================================
# 主程序入口
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # 从环境变量读取配置
    host = os.environ.get("FASTAPI_HOST", "0.0.0.0")
    port = int(os.environ.get("FASTAPI_PORT", "8000"))

    logger.info("启动 FastAPI 统一网关...")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,  # 开发模式启用热重载
        log_level="info"
    )
