"""单元测试框架和工具

提供测试基础设施和常用测试工具
"""

import pytest
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, AsyncMock, patch
import asyncio


class AgentTestContext:
    """Agent测试上下文

    提供测试Agent所需的通用工具和Mock对象
    """

    def __init__(self):
        self.messages = []
        self.mock_llm_responses = {}

    def create_mock_message(self, from_agent: str, to_agent: str, content: Dict[str, Any]) -> Dict:
        """创建测试消息"""
        return {
            "id": "test-msg-1",
            "from_agent": from_agent,
            "to_agent": to_agent,
            "content": content,
            "timestamp": 1234567890.0
        }

    def set_mock_llm_response(self, prompt_key: str, response: str):
        """设置Mock的LLM响应"""
        self.mock_llm_responses[prompt_key] = response

    def get_mock_llm_response(self, prompt: str) -> str:
        """获取Mock的LLM响应"""
        # 简单匹配，实际可以用更复杂的策略
        for key, value in self.mock_llm_responses.items():
            if key in prompt:
                return value
        return "Default mock response"

    def create_mock_agent(self, agent_type: str, config: Dict = None):
        """创建Mock Agent"""
        mock = Mock()
        mock.config = config or {"name": f"test_{agent_type}"}
        mock.process = AsyncMock(return_value=self.create_mock_message(
            agent_type, "coordinator", {"status": "success"}
        ))
        return mock


class APITestCase:
    """API测试基类"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from fastapi.testclient import TestClient
        from main import app  # 假设主应用在main.py
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """创建认证头"""
        return {"Authorization": "Bearer test_token"}

    def assert_success_response(self, response):
        """断言成功响应"""
        assert response.status_code == 200
        assert response.json()["success"] is True

    def assert_error_response(self, response, expected_code: str):
        """断言错误响应"""
        assert response.status_code not in [200, 201]
        data = response.json()
        assert "error_code" in data
        assert data["error_code"] == expected_code


class IntegrationTestHelpers:
    """集成测试辅助工具"""

    @staticmethod
    async def run_full_pipeline(user_input: str) -> Dict[str, Any]:
        """运行完整的PPT生成流程"""
        # 模拟完整流程
        results = {
            "outline": {"slides": []},
            "content": {},
            "design": {},
            "code": ""
        }
        return results

    @staticmethod
    def create_test_requirements() -> Dict[str, Any]:
        """创建测试用的需求数据"""
        return {
            "topic": "AI技术在教育领域的应用",
            "audience": "教育工作者",
            "duration": 30,
            "style": "professional"
        }


# 性能测试工具
class PerformanceTestHelpers:
    """性能测试辅助工具"""

    @staticmethod
    def measure_execution_time(func, *args, **kwargs) -> float:
        """测量函数执行时间（秒）"""
        import time
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        return duration

    @staticmethod
    @pytest.mark.asyncio
    async def measure_async_execution_time(coro) -> float:
        """测量异步函数执行时间（秒）"""
        import time
        start = time.time()
        await coro
        duration = time.time() - start
        return duration


# 测试数据生成器
class TestDataGenerator:
    """测试数据生成器"""

    @staticmethod
    def random_topic() -> str:
        """生成随机主题"""
        topics = [
            "人工智能的未来",
            "气候变化的影响",
            "区块链技术应用",
            "远程办公趋势"
        ]
        import random
        return random.choice(topics)

    @staticmethod
    def generate_slides_data(count: int = 5) -> List[Dict]:
        """生成幻灯片测试数据"""
        return [
            {
                "title": f"幻灯片 {i+1}",
                "content": [f"要点 {i+1}.1", f"要点 {i+1}.2"],
                "layout": 1
            }
            for i in range(count)
        ]
