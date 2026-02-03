#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for MCP Tools

This module contains tests for all MCP tools:
- web_search
- fetch_url
- search_images
- create_pptx
- state_store
- vector_search
"""

import pytest
import asyncio
import json
from pathlib import Path


class TestWebSearch:
    """Tests for web_search tool"""

    @pytest.mark.asyncio
    async def test_web_search_missing_api_key(self, monkeypatch):
        """Test web_search fails gracefully without API key"""
        from backend.agents.tools.mcp.web_search import web_search

        # Remove API key
        monkeypatch.setenv("BING_SEARCH_API_KEY", "")

        result = await web_search(
            query="test query",
            num_results=5
        )

        data = json.loads(result)
        assert data["success"] == False
        assert "API_KEY" in data["error"].get("code", "")

    @pytest.mark.asyncio
    async def test_web_search_invalid_engine(self):
        """Test web_search with invalid search engine"""
        from backend.agents.tools.mcp.web_search import web_search

        # Set dummy API key to avoid missing key error
        import os
        os.environ["BING_SEARCH_API_KEY"] = "dummy_key"

        result = await web_search(
            query="test",
            search_engine="invalid_engine"
        )

        data = json.loads(result)
        assert data["success"] == False
        assert "UNSUPPORTED_ENGINE" in data["error"].get("code", "")


class TestFetchUrl:
    """Tests for fetch_url tool"""

    @pytest.mark.asyncio
    async def test_fetch_url_invalid_url(self):
        """Test fetch_url with invalid URL"""
        from backend.agents.tools.mcp.fetch_url import fetch_url

        result = await fetch_url(
            url="not-a-valid-url",
            timeout=5,
            use_cache=False
        )

        data = json.loads(result)
        # Should fail with error
        assert data["success"] == False or "error" in data

    @pytest.mark.asyncio
    async def test_fetch_url_timeout(self):
        """Test fetch_url with timeout"""
        from backend.agents.tools.mcp.fetch_url import fetch_url

        result = await fetch_url(
            url="http://httpbin.org/delay/20",  # 20 second delay
            timeout=2,  # 2 second timeout
            use_cache=False
        )

        data = json.loads(result)
        assert data["success"] == False
        assert "timeout" in data["error"].get("message", "").lower() or "TIMEOUT" in data["error"].get("code", "")


class TestSearchImages:
    """Tests for search_images tool"""

    @pytest.mark.asyncio
    async def test_search_images_missing_api_key(self, monkeypatch):
        """Test search_images fails gracefully without API key"""
        from backend.agents.tools.mcp.search_images import search_images

        # Remove API keys
        monkeypatch.setenv("UNSPLASH_ACCESS_KEY", "")
        monkeypatch.setenv("PEXELS_API_KEY", "")

        result = await search_images(
            query="test",
            num_results=5
        )

        data = json.loads(result)
        assert data["success"] == False
        assert "API_KEY" in data["error"].get("code", "")

    @pytest.mark.asyncio
    async def test_search_images_invalid_source(self):
        """Test search_images with invalid source"""
        from backend.agents.tools.mcp.search_images import search_images

        # Set dummy API key to avoid missing key error
        import os
        os.environ["UNSPLASH_ACCESS_KEY"] = "dummy_key"

        result = await search_images(
            query="test",
            source="invalid_source"
        )

        data = json.loads(result)
        assert data["success"] == False
        assert "UNSUPPORTED_SOURCE" in data["error"].get("code", "")


class TestCreatePptx:
    """Tests for create_pptx tool"""

    @pytest.mark.asyncio
    async def test_create_pptx_basic(self, tmp_path):
        """Test create_pptx with basic slides"""
        from backend.agents.tools.mcp.create_pptx import create_pptx

        output_path = tmp_path / "test.pptx"

        slides = [
            {
                "layout": "Title",
                "title": "Test Presentation"
            },
            {
                "layout": "Title and Content",
                "title": "Slide 1",
                "content": ["Point 1", "Point 2", "Point 3"]
            }
        ]

        result = await create_pptx(
            slides=slides,
            output_path=str(output_path)
        )

        data = json.loads(result)
        assert data["success"] == True
        assert output_path.exists()

        # Check file size
        file_size = output_path.stat().st_size
        assert file_size > 0

    @pytest.mark.asyncio
    async def test_create_pptx_with_images(self, tmp_path):
        """Test create_pptx with image URLs"""
        from backend.agents.tools.mcp.create_pptx import create_pptx

        output_path = tmp_path / "test_with_images.pptx"

        slides = [
            {
                "layout": "Title and Content",
                "title": "Slide with Image",
                "content": ["Point 1"],
                "images": ["https://example.com/image.jpg"]
            }
        ]

        result = await create_pptx(
            slides=slides,
            output_path=str(output_path)
        )

        data = json.loads(result)
        assert data["success"] == True


class TestStateStore:
    """Tests for state_store tool"""

    @pytest.mark.asyncio
    async def test_state_store_set_and_get(self, tmp_path):
        """Test state_store set and get operations"""
        from backend.agents.tools.mcp.state_store import state_store
        import os

        # Set custom state directory
        os.environ["MCP_STATE_DIR"] = str(tmp_path)

        # Set a value
        set_result = await state_store(
            operation="set",
            key="test_key",
            value={"test": "data"},
            namespace="test_namespace"
        )

        set_data = json.loads(set_result)
        assert set_data["success"] == True

        # Get the value back
        get_result = await state_store(
            operation="get",
            key="test_key",
            namespace="test_namespace"
        )

        get_data = json.loads(get_result)
        assert get_data["success"] == True
        assert get_data["result"]["value"]["test"] == "data"

    @pytest.mark.asyncio
    async def test_state_store_list(self, tmp_path):
        """Test state_store list operation"""
        from backend.agents.tools.mcp.state_store import state_store
        import os

        os.environ["MCP_STATE_DIR"] = str(tmp_path)

        # Set multiple values
        await state_store(
            operation="set",
            key="key1",
            value="value1",
            namespace="test_list"
        )
        await state_store(
            operation="set",
            key="key2",
            value="value2",
            namespace="test_list"
        )

        # List keys
        list_result = await state_store(
            operation="list",
            namespace="test_list"
        )

        list_data = json.loads(list_result)
        assert list_data["success"] == True
        assert set(list_data["result"]["keys"]) == {"key1", "key2"}

    @pytest.mark.asyncio
    async def test_state_store_delete(self, tmp_path):
        """Test state_store delete operation"""
        from backend.agents.tools.mcp.state_store import state_store
        import os

        os.environ["MCP_STATE_DIR"] = str(tmp_path)

        # Set a value
        await state_store(
            operation="set",
            key="delete_me",
            value="temp",
            namespace="test_delete"
        )

        # Delete it
        delete_result = await state_store(
            operation="delete",
            key="delete_me",
            namespace="test_delete"
        )

        delete_data = json.loads(delete_result)
        assert delete_data["success"] == True
        assert delete_data["result"]["deleted"] == True

        # Verify it's gone
        get_result = await state_store(
            operation="get",
            key="delete_me",
            namespace="test_delete"
        )

        get_data = json.loads(get_result)
        assert get_data["result"]["value"] is None


class TestVectorSearch:
    """Tests for vector_search tool"""

    @pytest.mark.asyncio
    async def test_vector_search_no_service(self):
        """Test vector_search handles missing service gracefully"""
        from backend.agents.tools.mcp.vector_search import vector_search

        result = await vector_search(
            query="test query",
            collection="test",
            top_k=5
        )

        data = json.loads(result)
        # Should either succeed (if service available) or fail gracefully
        assert "success" in data
        if not data["success"]:
            # Should fail with service unavailable message
            assert "SERVICE" in data.get("error", {}).get("code", "")


class TestMCPToolsIntegration:
    """Integration tests for MCP tools"""

    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Test that MCP tools are registered in UnifiedToolRegistry"""
        from backend.agents.tools.registry.unified_registry import get_unified_registry

        registry = get_unified_registry()

        # Check that MCP tools are registered
        mcp_tools = [
            "web_search",
            "fetch_url",
            "search_images",
            "create_pptx",
            "state_store",
            "vector_search"
        ]

        for tool_name in mcp_tools:
            tool = registry.get_tool(tool_name)
            assert tool is not None, f"Tool {tool_name} not registered"
            assert tool.metadata.enabled == True, f"Tool {tool_name} is not enabled"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
