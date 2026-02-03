"""
Agent网关层

统一封装Agent调用，提供降级策略和异常处理
"""

from typing import Optional, Callable
from domain.models.agent_context import AgentContext, AgentStage
from domain.models.agent_result import AgentResult, ResultStatus
import logging
import time

logger = logging.getLogger(__name__)


class AgentGateway:
    """
    Agent网关

    职责：
    1. 统一Agent调用接口
    2. 强类型上下文传递（AgentContext）
    3. 结果解析与降级策略
    4. 异常处理与重试
    5. 性能监控和日志记录

    使用示例:
        >>> gateway = AgentGateway(llm_provider=llm)
        >>> context = AgentContext(request_id="req_123", ...)
        >>> result = await gateway.execute_master_coordinator(context)
        >>> if result.is_success:
        ...     print(context.final_ppt_path)
    """

    def __init__(self, llm_provider):
        """
        初始化Agent网关

        Args:
            llm_provider: LLM提供者（用于创建Agent）
        """
        self.llm_provider = llm_provider
        self._master_coordinator = None

    @property
    def master_coordinator(self):
        """
        懒加载MasterCoordinator

        延迟导入避免循环依赖
        """
        if self._master_coordinator is None:
            try:
                from agents.orchestrator.agents.master_coordinator import MasterCoordinator

                self._master_coordinator = MasterCoordinator(
                    llm_provider=self.llm_provider
                )
                logger.info("MasterCoordinator initialized")
            except ImportError as e:
                logger.error(f"Failed to import MasterCoordinator: {e}")
                raise RuntimeError("MasterCoordinator不可用") from e

        return self._master_coordinator

    async def execute_master_coordinator(
        self, context: AgentContext, max_retries: int = 3
    ) -> AgentResult:
        """
        执行MasterCoordinator（1主5子架构）

        Args:
            context: 强类型Agent上下文
            max_retries: 最大重试次数

        Returns:
            AgentResult: 统一结果封装
        """
        start_time = time.time()

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Executing MasterCoordinator (attempt {attempt + 1}/{max_retries})",
                    extra={
                        "request_id": context.request_id,
                        "execution_mode": context.execution_mode.value,
                    },
                )

                # 调用MasterCoordinator
                result = await self.master_coordinator.execute(context)

                # 记录性能指标
                execution_time = time.time() - start_time
                result.execution_time = execution_time

                if result.is_success:
                    logger.info(
                        f"MasterCoordinator executed successfully in {execution_time:.2f}s",
                        extra={
                            "request_id": context.request_id,
                            "fallback_used": result.fallback_used,
                        },
                    )
                    return result

                if not result.needs_retry or attempt == max_retries - 1:
                    logger.warning(
                        f"MasterCoordinator execution failed: {result.message}",
                        extra={
                            "request_id": context.request_id,
                            "status": result.status.value,
                            "errors": result.errors,
                        },
                    )
                    return result

                # 需要重试
                context.retry_count = attempt + 1
                logger.warning(
                    f"Retrying MasterCoordinator (attempt {attempt + 2}): {result.message}"
                )

            except Exception as e:
                logger.exception(
                    f"Error in MasterCoordinator execution (attempt {attempt + 1}): {e}",
                    extra={"request_id": context.request_id},
                )

                if attempt == max_retries - 1:
                    # 最后一次尝试失败，返回失败结果
                    execution_time = time.time() - start_time
                    return AgentResult.failure(
                        message=f"执行失败: {str(e)}",
                        errors=[str(e)],
                        execution_time=execution_time,
                    )

                context.add_error(str(e))

        # 不应该到达这里
        execution_time = time.time() - start_time
        return AgentResult.failure(message="未知错误", execution_time=execution_time)

    async def execute_with_fallback(
        self, context: AgentContext, fallback_strategy: Optional[Callable] = None
    ) -> AgentResult:
        """
        执行Agent并提供降级策略

        Args:
            context: Agent上下文
            fallback_strategy: 降级策略函数（可选）
                接收context，返回降级数据

        Returns:
            AgentResult: 结果（可能使用了降级）

        使用示例:
            >>> async def fallback(ctx):
            ...     return {"default": "content"}
            >>> result = await gateway.execute_with_fallback(context, fallback)
        """
        result = await self.execute_master_coordinator(context)

        if not result.is_success and fallback_strategy:
            logger.warning(
                "Using fallback strategy",
                extra={
                    "request_id": context.request_id,
                    "original_error": result.message,
                },
            )

            try:
                fallback_data = await fallback_strategy(context)
                return AgentResult.partial(
                    data=fallback_data,
                    fallback_reason=result.message,
                    message="使用降级策略",
                    execution_time=result.execution_time,
                )
            except Exception as e:
                logger.exception(
                    f"Fallback strategy failed: {e}",
                    extra={"request_id": context.request_id},
                )

        return result

    async def execute_single_agent(
        self, agent_name: str, context: AgentContext
    ) -> AgentResult:
        """
        执行单个Agent（用于独立调用某个Agent）

        Args:
            agent_name: Agent名称（如"requirement_parser"）
            context: Agent上下文

        Returns:
            AgentResult: 执行结果
        """
        start_time = time.time()

        try:
            logger.info(
                f"Executing single agent: {agent_name}",
                extra={"request_id": context.request_id},
            )

            # 根据名称动态导入Agent
            agent = self._get_agent_by_name(agent_name)

            # 执行Agent
            result = await agent.execute(context)

            execution_time = time.time() - start_time
            result.execution_time = execution_time

            logger.info(
                f"Agent '{agent_name}' executed in {execution_time:.2f}s",
                extra={"request_id": context.request_id, "status": result.status.value},
            )

            return result

        except Exception as e:
            logger.exception(
                f"Error executing agent '{agent_name}': {e}",
                extra={"request_id": context.request_id},
            )

            execution_time = time.time() - start_time
            return AgentResult.failure(
                message=f"Agent执行失败: {str(e)}",
                errors=[str(e)],
                execution_time=execution_time,
            )

    def _get_agent_by_name(self, agent_name: str):
        """
        根据名称获取Agent实例

        Args:
            agent_name: Agent名称

        Returns:
            Agent实例
        """
        # Agent名称到模块路径的映射
        agent_map = {
            "requirement_parser": "agents.core.planning.requirement_parser",
            "framework_designer": "agents.core.planning.framework_designer",
            "research": "agents.core.research.optimized_research",
            "content_generator": "agents.core.generation.content_generator",
            "page_render": "agents.core.rendering.page_render",
        }

        if agent_name not in agent_map:
            raise ValueError(f"Unknown agent: {agent_name}")

        # 动态导入
        module_path = agent_map[agent_name]
        module_parts = module_path.rsplit(".", 1)
        module = __import__(module_parts[0], fromlist=[module_parts[1]])

        # 获取Agent实例
        # 假设每个模块都有一个默认的agent实例
        agent_instance_name = f"{agent_name}_agent"
        if hasattr(module, agent_instance_name):
            return getattr(module, agent_instance_name)

        raise RuntimeError(
            f"Agent instance '{agent_instance_name}' not found in module"
        )
