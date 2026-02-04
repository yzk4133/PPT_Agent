"""
MCP Loader 测试
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from infrastructure.mcp.mcp_loader import (
    load_mcp_config_from_file,
    load_mcp_tools,
    load_mcp_tools_from_config,
    MCPManager,
    get_mcp_manager,
)

@pytest.mark.unit
class TestLoadMCPConfigFromFile:
    """测试从文件加载 MCP 配置"""

    def test_load_valid_config(self):
        """测试加载有效配置"""
        config_data = {
            "mcpServers": {
                "test_server": {
                    "command": "node",
                    "args": ["server.js"],
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            config = load_mcp_config_from_file(temp_path)

            assert config == config_data
            assert "mcpServers" in config
        finally:
            os.unlink(temp_path)

    def test_load_config_file_not_found(self):
        """测试配置文件不存在"""
        with pytest.raises(FileNotFoundError):
            load_mcp_config_from_file("nonexistent.json")

    def test_load_config_invalid_json(self):
        """测试无效 JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                load_mcp_config_from_file(temp_path)
        finally:
            os.unlink(temp_path)

@pytest.mark.unit
class TestLoadMCPTools:
    """测试加载 MCP 工具"""

    @patch('infrastructure.mcp.mcp_loader.MCPToolset')
    def test_load_mcp_tools_from_file(self, mock_toolset):
        """测试从文件加载 MCP 工具"""
        config_data = {
            "mcpServers": {
                "sse_server": {
                    "url": "http://localhost:3000/sse",
                },
                "stdio_server": {
                    "command": "python",
                    "args": ["server.py"],
                    "env": {"PYTHONPATH": "/app"},
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            mock_toolset_instance = MagicMock()
            mock_toolset.return_value = mock_toolset_instance

            tools = load_mcp_tools(temp_path)

            assert len(tools) == 2
        finally:
            os.unlink(temp_path)

    def test_load_mcp_tools_file_not_exists(self):
        """测试配置文件不存在"""
        with pytest.raises(AssertionError, match="配置文件不存在"):
            load_mcp_tools("nonexistent.json")

    @patch('infrastructure.mcp.mcp_loader.MCPToolset')
    def test_load_mcp_tools_from_config(self, mock_toolset):
        """测试从配置字典加载 MCP 工具"""
        config = {
            "mcpServers": {
                "test_server": {
                    "url": "http://localhost:3000",
                }
            }
        }

        mock_toolset_instance = MagicMock()
        mock_toolset.return_value = mock_toolset_instance

        tools = load_mcp_tools_from_config(config)

        assert len(tools) == 1

    @patch('infrastructure.mcp.mcp_loader.MCPToolset')
    def test_load_mcp_tools_invalid_config(self, mock_toolset):
        """测试无效的 MCP 配置"""
        config = {
            "mcpServers": {
                "invalid_server": {
                    # 缺少 url 和 command
                }
            }
        }

        with pytest.raises(ValueError, match="无效的MCP配置"):
            load_mcp_tools_from_config(config)

@pytest.mark.unit
class TestMCPManager:
    """测试 MCPManager 类"""

    def test_initialization(self):
        """测试初始化"""
        manager = MCPManager()

        assert manager.tools == []
        assert manager.config_path is None

    def test_initialization_with_config_path(self):
        """测试带配置路径初始化"""
        config_path = "test_config.json"
        manager = MCPManager(config_path=config_path)

        assert manager.config_path == config_path

    @patch('infrastructure.mcp.mcp_loader.load_mcp_tools_from_config')
    def test_load_from_config(self, mock_load):
        """测试从配置加载"""
        mock_load.return_value = []

        config = {"mcpServers": {}}
        manager = MCPManager()

        manager.load_from_config(config)

        mock_load.assert_called_once_with(config)

    @patch('infrastructure.mcp.mcp_loader.load_mcp_tools')
    def test_load_from_file(self, mock_load):
        """测试从文件加载"""
        mock_load.return_value = []

        config_path = "test_config.json"
        manager = MCPManager()

        with patch('os.path.exists', return_value=True):
            manager.load_from_file(config_path)

        mock_load.assert_called_once_with(config_path)

    def test_get_tools(self):
        """测试获取工具"""
        manager = MCPManager()
        manager.tools = ["tool1", "tool2"]

        tools = manager.get_tools()

        assert tools == ["tool1", "tool2"]

    def test_clear(self):
        """测试清空工具"""
        manager = MCPManager()
        manager.tools = ["tool1", "tool2"]

        manager.clear()

        assert manager.tools == []

@pytest.mark.unit
class TestGlobalMCPManager:
    """测试全局 MCP 管理器"""

    def test_get_mcp_manager_singleton(self):
        """测试全局 MCP 管理器单例"""
        manager1 = get_mcp_manager()
        manager2 = get_mcp_manager()

        assert manager1 is manager2
