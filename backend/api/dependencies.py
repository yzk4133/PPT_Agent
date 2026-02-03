"""
FastAPI依赖注入

提供便捷的依赖注入函数，用于FastAPI路由
"""

from typing import Annotated
from fastapi import Depends, Request
from infrastructure.di.container import Container


def get_container(request: Request) -> Container:
    """
    获取依赖注入容器

    从FastAPI应用状态中获取容器实例
    """
    return request.app.state.container


def get_presentation_service(container: Annotated[Container, Depends(get_container)]):
    """获取演示文稿服务"""
    return container.presentation_service()


def get_outline_service(container: Annotated[Container, Depends(get_container)]):
    """获取大纲服务"""
    return container.outline_service()


def get_agent_gateway(container: Annotated[Container, Depends(get_container)]):
    """获取Agent网关"""
    return container.agent_gateway()


def get_database(container: Annotated[Container, Depends(get_container)]):
    """获取数据库连接"""
    return container.database()


# ========== 类型别名（简化使用） ==========

# 使用示例:
# @router.post("/")
# async def create(service: PresentationServiceDep):
#     ...

PresentationServiceDep = Annotated[object, Depends(get_presentation_service)]
OutlineServiceDep = Annotated[object, Depends(get_outline_service)]
AgentGatewayDep = Annotated[object, Depends(get_agent_gateway)]
DatabaseDep = Annotated[object, Depends(get_database)]
