"""
Flat Slide Outline API Service - 扁平化大纲生成服务

端口：10002（原始服务在 10001）
架构：3阶段 Sequential（需求分析→并行调研→大纲生成）
"""

import logging
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# 配置日志
logfile = os.path.join("flat_outline_api.log")
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
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
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
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

# 添加 backend 目录到模块搜索路径
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from infrastructure.config.common_config import get_config

# 导入 flat_outline_agent
from agents.orchestrator.flat_outline_agent import create_flat_outline_agent

# 导入 MCP 工具加载器
slide_outline_path = os.path.abspath(
    os.path.join(backend_path, "archive", "slide_outline")
)
if slide_outline_path not in sys.path:
    sys.path.insert(0, slide_outline_path)

from load_mcp import load_mcp_tools

# 导入 ADKAgentExecutor
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
    default=10002,
    help="服务器监听的端口号（默认为 10002，原服务在 10001）",
)
@click.option(
    "--model",
    "model_name",
    default="deepseek-chat",
    help="使用的模型名称（如 deepseek-chat, claude-sonnet-4-20250514, gpt-4o）",
)
@click.option(
    "--provider",
    "provider",
    default="deepseek",
    type=click.Choice(["google", "openai", "deepseek", "ali", "claude"]),
    help="模型提供方名称（如 deepseek、openai 等）",
)
@click.option(
    "--mcp_config",
    "mcp_config_path",
    default="../archive/slide_outline/mcp_config.json",
    help="MCP 配置文件路径（默认复用 slide_outline 的 mcp_config.json）",
)
@click.option(
    "--agent_url",
    "agent_url",
    default="",
    help="Agent Card中对外展示和访问的地址",
)
@click.option(
    "--max_concurrency",
    "max_concurrency",
    default=3,
    help="并行调研最大并发数（默认 3）",
)
def main(
    host: str,
    port: int,
    model_name: str,
    provider: str,
    mcp_config_path: str,
    agent_url: str = "",
    max_concurrency: int = 3,
):
    """
    启动 Flat Slide Outline API 服务

    改进点：
    1. 使用扁平化 3 阶段架构（vs 原始单一 LlmAgent）
    2. 并行调研 + Semaphore 控制并发
    3. 统一配置管理（通过 common/config.py）
    4. JSON 解析降级 + 部分失败处理
    5. 模型降级（通过 ModelFactory）
    """
    logger.info("=" * 60)
    logger.info(f"启动 Flat Slide Outline Service（扁平化架构）")
    logger.info(f"端口：{port}（原服务：10001）")
    logger.info(f"模型：{model_name}（{provider}）")
    logger.info(f"最大并发：{max_concurrency}")
    logger.info("=" * 60)

    # 1. 加载配置
    config = get_config()

    # 2. 加载 MCP 工具
    logger.info(f"加载 MCP 工具：{mcp_config_path}")
    mcp_tools = load_mcp_tools(mcp_config_path=mcp_config_path)
    logger.info(f"已加载 {len(mcp_tools)} 个 MCP 工具")

    # 3. 创建扁平化大纲 Agent
    flat_outline_agent = create_flat_outline_agent(
        model_name=model_name,
        provider=provider,
        mcp_tools=mcp_tools,
        max_concurrency=max_concurrency,
    )

    # 4. 配置 Agent Card
    agent_card_name = "Flat PPT Outline Agent"
    agent_name = "flat_ppt_outline_agent"
    agent_description = "扁平化PPT大纲生成Agent（3阶段：需求分析→并行调研→大纲生成）"

    skill = AgentSkill(
        id=agent_name,
        name=agent_name,
        description=agent_description,
        tags=["ppt", "outline", "flat_architecture", "parallel_research"],
        examples=[
            "生成关于人工智能的PPT大纲",
            "生成特斯拉汽车介绍的PPT大纲",
            "生成量子计算原理的PPT大纲",
        ],
    )

    agent_card = AgentCard(
        name=agent_card_name,
        description=agent_description,
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )

    # 5. 创建 ADK Runner
    streaming = os.environ.get("STREAMING", "true").lower() == "true"

    runner = Runner(
        app_name=agent_card.name,
        agent=flat_outline_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )

    # 6. 创建 ADKAgentExecutor
    executor = ADKAgentExecutor(
        runner=runner,
        agent_id=agent_name,
        streaming=streaming,
    )

    # 7. 创建 A2A Starlette 应用
    task_store = InMemoryTaskStore()

    # 健康检查路由
    async def health_check(request):
        from starlette.responses import JSONResponse

        return JSONResponse(
            {
                "status": "healthy",
                "agent": agent_name,
                "architecture": "flat_3_stage_sequential",
                "stages": [
                    "Stage1: RequirementAnalysis",
                    "Stage2: ParallelResearch",
                    "Stage3: OutlineComposer",
                ],
                "model": f"{model_name} ({provider})",
                "max_concurrency": max_concurrency,
                "port": port,
            }
        )

    app = A2AStarletteApplication(
        agents=[agent_card],
        task_store=task_store,
        request_handler=DefaultRequestHandler(executor),
        routes=[
            Route("/health", endpoint=health_check, methods=["GET"]),
        ],
    )

    # 8. 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 9. 启动服务
    logger.info(f"服务启动成功：http://{host}:{port}")
    logger.info(f"健康检查：http://{host}:{port}/health")
    logger.info(f"Agent Card：http://{host}:{port}/.well-known/agent.json")
    logger.info("=" * 60)

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
