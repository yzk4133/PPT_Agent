"""
Tests for main_api module
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import tempfile
import os
import sys

# Add parent directory to path

# Mock OUTER_IP before importing main_api
os.environ.setdefault('OUTER_IP', 'http://127.0.0.1:10021')

@pytest.fixture
def client():
    """创建测试客户端"""
    # We need to mock the module before importing
    with patch.dict('sys.modules', {'ppt_generator': MagicMock()}):
        from utils.save_ppt import main_api

        # Mock the OUTER_IP variable
        main_api.OUTER_IP = "http://127.0.0.1:10021"

        # Create test client
        return TestClient(main_api.app)

@pytest.fixture
def valid_request_data():
    """有效的请求数据"""
    return {
        "sections": [
            {
                "id": "section1",
                "content": [
                    {"type": "h1", "children": [{"text": "第一章"}]},
                    {"type": "p", "children": [{"text": "段落内容"}]}
                ]
            }
        ],
        "references": ["参考文献1"]
    }

class TestPydanticModels:
    """测试Pydantic模型"""

    def test_root_image_model(self):
        """测试RootImage模型"""
        from utils.save_ppt.main_api import RootImage

        # Valid data
        img = RootImage(url="http://example.com/img.jpg", alt="测试图")
        assert img.url == "http://example.com/img.jpg"
        assert img.alt == "测试图"
        assert img.query is None
        assert img.background is False

        # With background
        img2 = RootImage(url="http://example.com/img.jpg", background=True)
        assert img2.background is True

    def test_content_child_model(self):
        """测试ContentChild模型"""
        from utils.save_ppt.main_api import ContentChild

        child = ContentChild(text="测试文本")
        assert child.text == "测试文本"

    def test_content_block_model(self):
        """测试ContentBlock模型"""
        from utils.save_ppt.main_api import ContentBlock

        block = ContentBlock(
            type="h1",
            children=[{"text": "标题"}]
        )
        assert block.type == "h1"
        assert len(block.children) == 1

    def test_section_data_model(self):
        """测试SectionData模型"""
        from utils.save_ppt.main_api import SectionData

        section = SectionData(
            id="section1",
            content=[
                {"type": "h1", "children": [{"text": "标题"}]}
            ],
            rootImage={
                "url": "http://example.com/img.jpg",
                "alt": "图片"
            }
        )
        assert section.id == "section1"
        assert section.rootImage is not None
        assert section.rootImage.url == "http://example.com/img.jpg"

    def test_ppt_input_model(self, valid_request_data):
        """测试PPTInput模型"""
        from utils.save_ppt.main_api import PPTInput

        ppt_input = PPTInput(**valid_request_data)
        assert len(ppt_input.sections) == 1
        assert ppt_input.sections[0].id == "section1"
        assert ppt_input.references is not None

class TestAPIEndpoints:
    """测试API端点"""

    def test_root_endpoint(self, client):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @patch('utils.save_ppt.main_api.start_generate_presentation')
    def test_generate_ppt_endpoint_success(self, mock_gen, client, valid_request_data):
        """测试PPT生成成功"""
        # Mock successful generation
        mock_gen.return_value = "output/test.pptx"

        response = client.post("/generate-ppt", json=valid_request_data)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "ppt_url" in data
        assert data["message"] == "PPT generated successfully"
        mock_gen.assert_called_once()

    @patch('utils.save_ppt.main_api.start_generate_presentation')
    def test_generate_ppt_endpoint_generation_failure(self, mock_gen, client, valid_request_data):
        """测试PPT生成失败"""
        # Mock failed generation
        mock_gen.return_value = None

        response = client.post("/generate-ppt", json=valid_request_data)

        assert response.status_code == 500

    def test_generate_ppt_endpoint_invalid_input_missing_sections(self, client):
        """测试缺少sections字段的无效输入"""
        response = client.post("/generate-ppt", json={})
        assert response.status_code == 422  # Validation error

    def test_generate_ppt_endpoint_invalid_input_wrong_type(self, client):
        """测试字段类型错误的无效输入"""
        response = client.post("/generate-ppt", json={
            "sections": "not a list"  # 应该是列表
        })
        assert response.status_code == 422

    def test_generate_ppt_endpoint_invalid_section_data(self, client):
        """测试无效的section数据"""
        response = client.post("/generate-ppt", json={
            "sections": [
                {
                    "id": "section1",
                    # 缺少content字段
                }
            ]
        })
        assert response.status_code == 422

    @patch('utils.save_ppt.main_api.start_generate_presentation')
    def test_generate_ppt_endpoint_with_references(self, mock_gen, client):
        """测试带参考文献的请求"""
        mock_gen.return_value = "output/test.pptx"

        request_data = {
            "sections": [
                {
                    "id": "section1",
                    "content": [
                        {"type": "h1", "children": [{"text": "标题"}]}
                    ]
                }
            ],
            "references": ["参考文献1", "参考文献2"]
        }

        response = client.post("/generate-ppt", json=request_data)

        assert response.status_code == 200
        mock_gen.assert_called_once()

    @patch('utils.save_ppt.main_api.start_generate_presentation')
    def test_generate_ppt_endpoint_with_images(self, mock_gen, client):
        """测试带图片的请求"""
        mock_gen.return_value = "output/test.pptx"

        request_data = {
            "sections": [
                {
                    "id": "section1",
                    "content": [
                        {"type": "h1", "children": [{"text": "标题"}]}
                    ],
                    "rootImage": {
                        "url": "http://example.com/img.jpg",
                        "alt": "测试图片",
                        "background": False
                    }
                }
            ]
        }

        response = client.post("/generate-ppt", json=request_data)

        assert response.status_code == 200
        mock_gen.assert_called_once()

    @patch('utils.save_ppt.main_api.start_generate_presentation')
    def test_generate_ppt_endpoint_exception_handling(self, mock_gen, client, valid_request_data):
        """测试异常处理"""
        # Mock抛出异常
        mock_gen.side_effect = Exception("Test exception")

        response = client.post("/generate-ppt", json=valid_request_data)

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

class TestStaticFiles:
    """测试静态文件服务"""

    def test_static_files_mount(self, client):
        """测试静态文件挂载"""
        # 检查应用是否有static_ppts路由
        routes = [route.path for route in client.app.routes]
        assert "/static_ppts/{path:path}" in routes or any("static_ppts" in r for r in routes)
