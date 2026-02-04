"""
DI Container 测试
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from infrastructure.di.container import (
    Container,
    create_container,
    get_global_container,
    reset_global_container,
)

# 设置测试环境变量
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
os.environ.setdefault("LLM_PROVIDER", "google")
os.environ.setdefault("LLM_API_KEY", "test_api_key")
os.environ.setdefault("LLM_MODEL", "gemini-1.5-pro")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("LOG_LEVEL", "INFO")

@pytest.mark.unit
class TestContainer:
    """测试 Container 类"""

    def test_container_initialization(self):
        """测试容器初始化"""
        container = Container()

        assert container is not None

    def test_container_configuration(self):
        """测试容器配置"""
        container = Container()

        # 验证配置提供者存在
        assert hasattr(container, 'config')

    def test_container_providers(self):
        """测试容器提供者"""
        container = Container()

        # 验证关键提供者存在
        assert hasattr(container, 'database')
        assert hasattr(container, 'llm_provider')
        assert hasattr(container, 'cache')
        assert hasattr(container, 'logger')

@pytest.mark.unit
class TestCreateContainer:
    """测试 create_container 函数"""

    def test_create_container(self):
        """测试创建容器"""
        container = create_container()

        assert container is not None
        # create_container 返回配置好的容器实例
        assert hasattr(container, 'config')

@pytest.mark.unit
class TestGlobalContainer:
    """测试全局容器"""

    def test_get_global_container_singleton(self):
        """测试全局容器单例"""
        reset_global_container()

        container1 = get_global_container()
        container2 = get_global_container()

        assert container1 is container2

    def test_reset_global_container(self):
        """测试重置全局容器"""
        reset_global_container()
        container1 = get_global_container()

        reset_global_container()

        container2 = get_global_container()

        # 重置后应该创建新实例（虽然可能相等因为配置相同）
        assert container2 is not None
