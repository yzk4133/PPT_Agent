"""
依赖注入模块

导出容器和工厂函数
"""

from .container import (
    Container,
    create_container,
    get_global_container,
    reset_global_container,
)

__all__ = [
    "Container",
    "create_container",
    "get_global_container",
    "reset_global_container",
]
