"""
核心Agent基础类（简化版）

提供统一的Agent基础实现，抽取公共逻辑：
- 模型创建和配置
- LangChain链管理
- 错误处理和降级策略
- 日志记录规范
- MCP工具集成（BaseToolAgent）

简化说明：
- 移除了复杂的 memory 系统依赖
- 保留了核心的 LangChain 集成
- 适合简单的多 Agent 场景
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

from infrastructure.config import get_llm_config

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    所有Agent的基础类（简化版）

    职责：
    1. 提供统一的模型初始化
    2. 标准化日志记录
    3. 错误处理模板

    特性：
    - 使用 LangChain ChatOpenAI
    - 支持自定义温度参数
    - 简化的接口设计
    """

    def __init__(
        self,
        model: Optional[ChatOpenAI] = None,
        temperature: float = 0.0,
        agent_name: str = "BaseAgent",
        enable_memory: bool = False,  # 保留参数但不使用
    ):
        """
        初始化Agent

        Args:
            model: LangChain LLM实例（可选，默认创建 gpt-4o-mini）
            temperature: 温度参数
            agent_name: Agent名称（用于日志）
            enable_memory: 是否启用记忆（保留兼容性，但不使用）
        """
        self.model = model or ChatOpenAI(
            **get_llm_config(temperature=temperature).to_langchain_config()
        )
        self.temperature = temperature
        self.agent_name = agent_name
        self.has_memory = False  # 简化版本不支持记忆

        logger.info(
            f"[{self.agent_name}] Initialized with model: {self.model.model_name}, "
            f"temperature: {self.temperature}"
        )

    @abstractmethod
    async def run(self, *args, **kwargs):
        """
        Agent 的主要执行方法（子类必须实现）

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Agent执行结果
        """
        pass

    def _log_start(self, message: str = ""):
        """记录任务开始"""
        logger.info(f"[{self.agent_name}] Task started: {message}")

    def _log_progress(self, message: str = ""):
        """记录任务进度"""
        logger.info(f"[{self.agent_name}] In progress: {message}")

    def _log_complete(self, message: str = ""):
        """记录任务完成"""
        logger.info(f"[{self.agent_name}] Task completed: {message}")

    def _log_error(self, error: Exception, message: str = ""):
        """记录错误"""
        logger.error(
            f"[{self.agent_name}] Error: {message} - {str(error)}",
            exc_info=True
        )


class BaseToolAgent(BaseAgent):
    """
    支持工具的 Agent 基类

    职责：
    1. 继承 BaseAgent 的所有功能
    2. 集成 LangChain Agent 框架
    3. 自动加载和配置 LangChain 原生工具
    4. 提供 ReAct Agent 执行接口

    特性：
    - 支持 ReAct Agent 模式
    - 按类别自动加载工具（SEARCH/MEDIA/UTILITY/VECTOR/DATABASE）
    - LLM 自主决定是否使用工具
    - 完整的错误处理和日志记录
    """

    # 默认的 ReAct prompt 模板
    DEFAULT_TOOL_PROMPT = """你是一个有帮助的助手。使用可用的工具来回答问题。

可用的工具：
{tools}

工具名称：
{tool_names}

请按照以下格式思考：

Question: 输入的问题
Thought: 我应该思考什么
Action: 要使用的工具名称（必须是 [{tool_names}] 中的一个）
Action Input: 工具的输入参数
Observation: 工具返回的结果
... (可以重复 Thought/Action/Action Input/Observation 多次)
Thought: 我现在知道最终答案了
Final Answer: 对原始问题的最终答案

开始！

Question: {input}
Thought: {agent_scratchpad}"""

    def __init__(
        self,
        model: Optional[ChatOpenAI] = None,
        temperature: float = 0.0,
        tool_categories: Optional[List[str]] = None,
        tool_names: Optional[List[str]] = None,
        agent_name: str = "BaseToolAgent",
        enable_memory: bool = False,
        max_iterations: int = 5,
        verbose: bool = True,
    ):
        """
        初始化支持工具的 Agent

        Args:
            model: LLM 实例
            temperature: 温度参数
            tool_categories: 工具类别列表 (SEARCH/MEDIA/UTILITY/VECTOR/DATABASE/SKILL)
            tool_names: 工具名称列表（优先级高于 tool_categories）
            agent_name: Agent 名称
            enable_memory: 是否启用记忆
            max_iterations: Agent 执行的最大迭代次数
            verbose: 是否输出详细日志
        """
        # 先初始化基类
        super().__init__(
            model=model,
            temperature=temperature,
            agent_name=agent_name,
            enable_memory=enable_memory
        )

        # 设置工具参数
        self.tool_categories = tool_categories or []
        self.tool_names = tool_names or []  # 新增：工具名称列表
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.agent_executor: Optional[AgentExecutor] = None
        self._loaded_tools: List = []

        # 始终设置工具
        self._setup_tools()

    def _setup_tools(self):
        """设置工具并创建 Agent Executor"""
        try:
            # 导入原生工具注册表（延迟导入，避免循环依赖）
            from backend.tools.application.tool_registry import get_native_registry

            registry = get_native_registry()

            # 收集工具
            tools = []

            # 优先级1: 如果指定了工具名称，按名称加载
            if self.tool_names:
                logger.info(f"[{self.agent_name}] Loading tools by name: {self.tool_names}")
                for tool_name in self.tool_names:
                    tool = registry.get_tool(tool_name)
                    if tool:
                        tools.append(tool)
                        logger.info(f"[{self.agent_name}]   ✓ Loaded: {tool_name}")
                    else:
                        logger.warning(f"[{self.agent_name}]   ✗ Tool not found: {tool_name}")

            # 优先级2: 否则按类别加载
            elif self.tool_categories:
                valid_categories = [
                    registry.SEARCH, registry.MEDIA, registry.UTILITY,
                    registry.VECTOR, registry.DATABASE, registry.SKILL
                ]

                logger.info(f"[{self.agent_name}] Loading tools by categories: {self.tool_categories}")
                for category in self.tool_categories:
                    if category.upper() in valid_categories:
                        category_tools = registry.get_tools_by_category(category.upper())
                        tools.extend(category_tools)
                        logger.info(
                            f"[{self.agent_name}]   ✓ Loaded {len(category_tools)} {category} tools"
                        )
                    else:
                        logger.warning(
                            f"[{self.agent_name}]   ✗ Invalid tool category '{category}', skipping"
                        )

            # 检查是否成功加载工具
            if not tools:
                logger.warning(
                    f"[{self.agent_name}] No tools loaded! "
                    f"tool_names={self.tool_names}, tool_categories={self.tool_categories}"
                )
                self.agent_executor = None
                return

            # 保存工具列表
            self._loaded_tools = tools

            # 创建 ReAct Agent prompt
            tool_names = [tool.name for tool in tools]
            prompt_template = PromptTemplate.from_template(
                self.DEFAULT_TOOL_PROMPT.format(
                    tools="\n".join([f"- {tool.name}: {tool.description}" for tool in tools]),
                    tool_names=", ".join(tool_names)
                )
            )

            # 创建 ReAct Agent
            agent = create_react_agent(
                llm=self.model,
                tools=tools,
                prompt=prompt_template
            )

            # 创建 Agent Executor
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=self.verbose,
                handle_parsing_errors=True,
                max_iterations=self.max_iterations,
                return_intermediate_steps=False
            )

            logger.info(
                f"[{self.agent_name}] AgentExecutor initialized successfully. "
                f"Total tools: {len(tool_names)}, Tools: {', '.join(tool_names)}"
            )

        except ImportError as e:
            logger.error(f"[{self.agent_name}] Failed to import tools: {e}")
            logger.error(f"[{self.agent_name}] Make sure backend.tools module is available")
            self.agent_executor = None

        except Exception as e:
            logger.error(f"[{self.agent_name}] Failed to setup tools: {e}", exc_info=True)
            self.agent_executor = None

    async def execute_with_tools(self, query: str) -> str:
        """
        使用工具执行查询（LLM 自主判断是否使用工具）

        Args:
            query: 用户查询或任务描述

        Returns:
            执行结果字符串

        Raises:
            RuntimeError: 如果工具配置失败
        """
        if not self.agent_executor:
            raise RuntimeError(
                f"[{self.agent_name}] AgentExecutor not configured. "
                f"Check logs for setup errors."
            )

        try:
            logger.info(f"[{self.agent_name}] Executing with tools: {query[:100]}...")

            # 执行 Agent（LLM 自主决定是否使用工具）
            result = await self.agent_executor.ainvoke({
                "input": query
            })

            # 提取输出
            output = result.get("output", "")

            logger.info(
                f"[{self.agent_name}] Tool execution completed. "
                f"Output length: {len(output)}"
            )

            return output

        except Exception as e:
            logger.error(f"[{self.agent_name}] Tool execution failed: {e}", exc_info=True)
            raise

    def has_tools(self) -> bool:
        """
        检查 Agent 是否配置了工具

        Returns:
            True 如果工具配置成功
        """
        return self.agent_executor is not None

    def get_loaded_tools(self) -> List[str]:
        """
        获取已加载的工具名称列表

        Returns:
            工具名称列表
        """
        if not self._loaded_tools:
            return []
        return [tool.name for tool in self._loaded_tools]

    def get_tool_count(self) -> int:
        """
        获取已加载的工具数量

        Returns:
            工具数量
        """
        return len(self._loaded_tools)

    @abstractmethod
    async def run(self, *args, **kwargs):
        """
        Agent 的主要执行方法（子类必须实现）

        BaseToolAgent 仍然需要子类实现具体的 run 方法，
        因为不同的 Agent 有不同的执行逻辑。
        """
        pass
