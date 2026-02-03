"""
PPT Generation Service - PPT 生成服务

从 api/routes/ppt_generation.py 的 Agent 包装器迁移而来
封装 PPT 生成相关的业务逻辑。
"""

import logging
import os
import sys
import uuid
from typing import Optional, Dict, Any, List, AsyncGenerator

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

# 导入工厂
from agents.factory import get_agent_factory

# 导入工具管理器
from infrastructure.tools.tool_manager import UnifiedToolManager

# 导入配置
from infrastructure.config.common_config import get_config

logger = logging.getLogger(__name__)


class PptGenerationService:
    """
    PPT 生成服务

    封装所有 PPT 生成相关的业务逻辑
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化服务

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.agent_factory = get_agent_factory(config)

        # 会话服务
        self._session_service = InMemorySessionService()

        # 配置
        self._config = get_config()
        self._model_name = os.environ.get("OUTLINE_MODEL", "deepseek-chat")
        self._provider = os.environ.get("OUTLINE_PROVIDER", "deepseek")
        self._max_concurrency = int(os.environ.get("MAX_CONCURRENCY", "3"))

        # Runner 实例（延迟初始化）
        self._outline_runner: Optional[Runner] = None
        self._ppt_runner: Optional[Runner] = None
        self._outline_agent = None

    # ==================== 大纲生成 ====================

    async def _initialize_outline_runner(self):
        """延迟初始化大纲 Runner"""
        if self._outline_runner is not None:
            return

        try:
            # 加载 MCP 工具
            mcp_config_path = os.path.join(
                os.path.dirname(__file__), "..", "archive", "slide_outline", "mcp_config.json"
            )
            tool_manager = UnifiedToolManager()
            mcp_tools = tool_manager.load_tools_from_config(mcp_config_path)

            # 创建 Agent
            self._outline_agent = self.agent_factory.create_outline_agent(
                model_name=self._model_name,
                provider=self._provider,
                mcp_tools=mcp_tools,
                max_concurrency=self._max_concurrency
            )

            # 创建 Runner
            self._outline_runner = Runner(
                app_name="outline_generation",
                agent=self._outline_agent,
                artifact_service=InMemoryArtifactService(),
                session_service=self._session_service,
                memory_service=InMemoryMemoryService(),
            )

            logger.info(f"OutlineRunner 初始化成功: {self._model_name} ({self._provider})")

        except Exception as e:
            logger.error(f"OutlineRunner 初始化失败: {e}", exc_info=True)
            raise

    async def generate_outline(
        self,
        user_input: str,
        language: str = "zh-CN",
        model_name: str = None,
        provider: str = None
    ) -> AsyncGenerator[str, None]:
        """
        生成大纲

        Args:
            user_input: 用户输入
            language: 语言
            model_name: 模型名称（可选，覆盖默认配置）
            provider: 提供商（可选，覆盖默认配置）

        Yields:
            生成的文本片段
        """
        # 延迟初始化 Runner
        await self._initialize_outline_runner()

        # 创建会话
        session_id = f"outline_{uuid.uuid4().hex}"
        user_id = f"user_{uuid.uuid4().hex[:8]}"

        # 执行
        invocation_ctx = self._outline_runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_input,
        )

        # 流式返回
        try:
            async for event in invocation_ctx:
                if hasattr(event, "content") and event.content:
                    yield event.content
                elif hasattr(event, "text") and event.text:
                    yield event.text
        except Exception as e:
            logger.error(f"大纲生成失败: {e}", exc_info=True)
            yield f"Error: {str(e)}"

    # ==================== PPT 生成 ====================

    async def _initialize_ppt_runner(self):
        """延迟初始化 PPT Runner"""
        if self._ppt_runner is not None:
            return

        try:
            agent = self.agent_factory.create_ppt_generation_agent()

            self._ppt_runner = Runner(
                app_name="ppt_generation",
                agent=agent,
                artifact_service=InMemoryArtifactService(),
                session_service=self._session_service,
                memory_service=InMemoryMemoryService(),
            )

            logger.info("PPTRunner 初始化成功")

        except Exception as e:
            logger.error(f"PPTRunner 初始化失败: {e}", exc_info=True)
            raise

    async def generate_slides(
        self,
        title: str,
        outline: List[str],
        language: str = "en-US",
        tone: str = "professional",
        num_slides: int = 10
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        生成幻灯片

        Args:
            title: 标题
            outline: 大纲列表
            language: 语言
            tone: 语气
            num_slides: 幻灯片数量

        Yields:
            事件数据字典
        """
        # 延迟初始化 Runner
        await self._initialize_ppt_runner()

        # 构建用户输入
        user_input = f"""Please generate a presentation with the following details:
Title: {title}
Language: {language}
Tone for images: {tone}
Number of slides: {num_slides}

Outline:
{chr(10).join(f'{i+1}. {item}' for i, item in enumerate(outline))}
"""

        # 创建会话
        session_id = f"ppt_{uuid.uuid4().hex}"
        user_id = f"user_{uuid.uuid4().hex[:8]}"

        # 执行
        invocation_ctx = self._ppt_runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_input,
        )

        # 流式返回
        async for event in invocation_ctx:
            event_data = {"type": "unknown"}

            if hasattr(event, "content") and event.content:
                event_data["type"] = "status-update"
                event_data["data"] = event.content
                event_data["metadata"] = ""
            elif hasattr(event, "text") and event.text:
                event_data["type"] = "status-update"
                event_data["data"] = event.text
                event_data["metadata"] = ""

            # 检查 artifact
            if hasattr(event, "actions"):
                event_data["type"] = "artifact-update"
                if hasattr(event.actions, "artifact"):
                    event_data["data"] = str(event.actions.artifact)

            yield event_data

    # ==================== 完整 PPT 生成（使用主协调器） ====================

    async def generate_ppt_full(
        self,
        user_input: str,
        user_id: str = "anonymous",
        enable_page_pipeline: bool = True,
        execution_mode: str = "full"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        完整生成 PPT（使用主协调器）

        Args:
            user_input: 用户输入
            user_id: 用户ID
            enable_page_pipeline: 是否启用页面级流水线
            execution_mode: 执行模式 (full, phase_1, phase_2)

        Yields:
            事件数据字典
        """
        from infrastructure.checkpoint import CheckpointManager, InMemoryCheckpointBackend

        # 创建 checkpoint 管理器
        checkpoint_manager = CheckpointManager(InMemoryCheckpointBackend())

        # 创建主协调器
        coordinator = self.agent_factory.create_master_coordinator(
            checkpoint_manager=checkpoint_manager,
            enable_page_pipeline=enable_page_pipeline
        )

        # 创建 Runner
        runner = Runner(
            app_name="full_ppt_generation",
            agent=coordinator,
            artifact_service=InMemoryArtifactService(),
            session_service=self._session_service,
            memory_service=InMemoryMemoryService(),
        )

        # 创建会话
        session_id = f"ppt_full_{uuid.uuid4().hex}"

        # 设置执行模式
        from google.adk.sessions import Session
        session = self._session_service.create_session(
            user_id=user_id,
            session_id=session_id,
            state={"execution_mode": execution_mode}
        )

        # 执行
        invocation_ctx = runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_input,
        )

        # 流式返回
        async for event in invocation_ctx:
            event_data = {"type": "unknown"}

            if hasattr(event, "content") and event.content:
                event_data["type"] = "content"
                event_data["data"] = event.content
            elif hasattr(event, "text") and event.text:
                event_data["type"] = "content"
                event_data["data"] = event.text

            # 检查 artifact
            if hasattr(event, "actions"):
                event_data["type"] = "artifact-update"
                if hasattr(event.actions, "artifact"):
                    event_data["data"] = str(event.actions.artifact)

            yield event_data


# 全局服务实例
_global_service: Optional[PptGenerationService] = None


def get_ppt_generation_service(config: Optional[Dict[str, Any]] = None) -> PptGenerationService:
    """获取全局 PPT 生成服务实例"""
    global _global_service
    if _global_service is None:
        _global_service = PptGenerationService(config)
    return _global_service


def reset_ppt_generation_service():
    """重置全局 PPT 生成服务实例（主要用于测试）"""
    global _global_service
    _global_service = None
