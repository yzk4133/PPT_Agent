"""
依赖注入容器

使用 dependency-injector 管理所有依赖，确保可测试性和可维护性
"""

from dependency_injector import containers, providers
from typing import Optional


class Container(containers.DeclarativeContainer):
    """
    应用级依赖注入容器

    管理所有服务、Agent、Repository等依赖的生命周期

    使用示例:
        >>> container = Container()
        >>> presentation_service = container.presentation_service()
        >>> result = await presentation_service.generate_presentation(...)
    """

    # ========== 配置 ==========
    config = providers.Configuration()

    # ========== 基础设施层 ==========

    # 数据库（延迟导入避免循环依赖）
    database = providers.Singleton(
        lambda: __import__("infrastructure.database", fromlist=["Database"]).Database,
        connection_string=config.database_url,
    )

    # LLM提供者
    llm_provider = providers.Singleton(
        lambda: __import__("infrastructure.llm", fromlist=["LLMProvider"]).LLMProvider,
        provider=config.llm_provider,
        api_key=config.llm_api_key,
        model=config.llm_model,
    )

    # 缓存
    cache = providers.Singleton(
        lambda: __import__("infrastructure.cache", fromlist=["Cache"]).Cache,
        redis_url=config.redis_url,
    )

    # 日志
    logger = providers.Singleton(
        lambda: __import__(
            "infrastructure.logging", fromlist=["setup_logger"]
        ).setup_logger,
        level=config.log_level,
    )

    # ========== Agent层 ==========

    # Agent网关
    agent_gateway = providers.Singleton(
        lambda: __import__(
            "agents.orchestrator.agent_gateway", fromlist=["AgentGateway"]
        ).AgentGateway,
        llm_provider=llm_provider,
    )

    # ========== Service层 ==========

    # 演示文稿服务
    presentation_service = providers.Factory(
        lambda: __import__(
            "services.presentation_service", fromlist=["PresentationService"]
        ).PresentationService,
        agent_gateway=agent_gateway,
        database=database,
        cache=cache,
    )

    # 大纲服务
    outline_service = providers.Factory(
        lambda: __import__(
            "services.outline_service", fromlist=["OutlineService"]
        ).OutlineService,
        agent_gateway=agent_gateway,
        database=database,
    )

    # ========== Repository层（如果需要） ==========

    presentation_repository = providers.Factory(
        lambda: __import__(
            "infrastructure.database.repositories", fromlist=["PresentationRepository"]
        ).PresentationRepository,
        database=database,
    )


def create_container() -> Container:
    """
    创建并配置容器

    Returns:
        配置好的Container实例
    """
    container = Container()

    # 从环境变量或配置文件加载配置
    container.config.from_dict(
        {
            "database_url": "postgresql://localhost/multiagent_ppt",
            "llm_provider": "google",
            "llm_api_key": "your_api_key",
            "llm_model": "gemini-1.5-pro",
            "redis_url": "redis://localhost:6379",
            "log_level": "INFO",
        }
    )

    # 可以从环境变量覆盖
    container.config.from_env()

    return container


# 全局容器实例（用于FastAPI应用）
_global_container: Optional[Container] = None


def get_global_container() -> Container:
    """获取全局容器实例"""
    global _global_container
    if _global_container is None:
        _global_container = create_container()
    return _global_container


def reset_global_container():
    """重置全局容器（用于测试）"""
    global _global_container
    _global_container = None
