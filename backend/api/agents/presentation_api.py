"""
Flat Slide Agent API 服务

新的扁平化架构服务入口，端口 10012
与原 slide_agent (端口 10011) 并存
"""

import logging
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# 配置日志
logfile = os.path.join("flat_api.log")
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s -  %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(logfile, mode="w", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

import click
import uvicorn

# 导入基础设施
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from infrastructure.config import get_config

# 导入 ADK 相关
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# 导入持久化记忆系统
try:
    from persistent_memory import PostgresSessionService, get_db
    PERSISTENT_MEMORY_AVAILABLE = True
except ImportError:
    PERSISTENT_MEMORY_AVAILABLE = False
    logger.warning("Persistent memory not available, using in-memory services")

from starlette.routing import Route
from google.adk.agents.run_config import RunConfig, StreamingMode
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from starlette.middleware.cors import CORSMiddleware
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

# 导入扁平化 Agent
from agents.orchestrator.flat_root_agent import flat_root_agent

# 导入 ADKAgentExecutor
archive_path = os.path.abspath(os.path.join(backend_path, "..", "archive", "slide_agent"))
if archive_path not in sys.path:
    sys.path.insert(0, archive_path)

from adk_agent_executor import ADKAgentExecutor


@click.command()
@click.option(
    "--host",
    "host",
    default="localhost",
    help="服务器绑定的主机名（默认为 localhost）",
)
@click.option(
    "--port",
    "port",
    default=10012,
    help="服务器监听的端口号（默认为 10012，与原服务10011不冲突）"
)
@click.option(
    "--agent_url",
    "agent_url",
    default="",
    help="Agent Card中对外展示和访问的地址"
)
def main(host, port, agent_url=""):
    config = get_config()

    logger.info("=" * 60)
    logger.info(" Flat Slide Agent API 启动中...")
    logger.info(f"   架构模式: 扁平化 (3阶段)")
    logger.info(f"   端口: {port} (原服务: 10011)")
    logger.info(f"   持久化记忆: {' 启用' if config.features.use_persistent_memory else ' 禁用'}")
    logger.info(f"   向量缓存: {' 启用' if config.features.enable_vector_cache else ' 禁用'}")
    logger.info(f"   质量检查: {' 启用' if config.features.enable_quality_check else ' 禁用'}")
    logger.info(f"   并发限制: {config.research_agent.max_concurrency}")
    logger.info("=" * 60)

    # 配置流式输出
    streaming = False
    show_agent = ["FlatPPTGenerationAgent", "PPTWriterSubAgent"]

    # Agent Card 配置
    agent_card_name = "Flat PPT Agent"
    agent_name = "flat_ppt_agent"
    agent_description = "扁平化架构的 PPT 生成 Agent（3阶段优化版本）"

    skill = AgentSkill(
        id=agent_name,
        name=agent_card_name,
        description=agent_description,
        tags=["ppt", "flat", "optimized"],
        examples=["生成关于AI的PPT", "创建医疗主题的幻灯片"],
    )

    agent_card = AgentCard(
        id=agent_name,
        name=agent_card_name,
        description=agent_description,
        url=agent_url if agent_url else f"http://{host}:{port}",
        capabilities=AgentCapabilities(streaming=streaming),
        skills=[skill],
    )

    # 选择 Session Service
    if config.features.use_persistent_memory and PERSISTENT_MEMORY_AVAILABLE:
        try:
            db_manager = get_db()
            db_manager.health_check()
            session_service = PostgresSessionService(
                db_manager=db_manager,
                enable_cache=True,
                cache_ttl_seconds=3600
            )
            logger.info(" 使用 PostgreSQL Session Service")
        except Exception as e:
            logger.error(f"  PostgreSQL 不可用: {e}，降级到内存模式")
            session_service = InMemorySessionService()
    else:
        session_service = InMemorySessionService()
        logger.info(" 使用 In-Memory Session Service")

    # 创建 Runner
    runner = Runner(
        agent=flat_root_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=session_service,
        memory_service=InMemoryMemoryService(),
    )

    # 创建执行器
    executor = ADKAgentExecutor(
        runner=runner,
        run_config=RunConfig(
            streaming_mode=StreamingMode.STREAMING if streaming else StreamingMode.NON_STREAMING
        ),
        show_agent=show_agent,
    )

    # 创建 A2A 应用
    app = A2AStarletteApplication(
        request_handler=DefaultRequestHandler(
            agent_card=agent_card,
            agent_executor=executor,
        ),
        task_store=InMemoryTaskStore(),
        routes=[
            Route("/health", lambda request: __import__("starlette.responses", fromlist=["JSONResponse"]).JSONResponse({"status": "healthy", "architecture": "flat", "port": port}))
        ],
    )

    # 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info(f" Flat Slide Agent 启动成功: http://{host}:{port}")
    logger.info(f"   健康检查: http://{host}:{port}/health")
    logger.info(f"   Agent Card: http://{host}:{port}/.well-known/agent.json")

    # 启动服务
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
