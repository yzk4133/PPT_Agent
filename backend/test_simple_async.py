"""Simple async test to verify setup"""
import pytest

@pytest.mark.asyncio
async def test_simple_async():
    """Test that async tests work"""
    assert True

@pytest.mark.asyncio
async def test_simple_async_with_await():
    """Test that await works in tests"""
    import asyncio
    await asyncio.sleep(0.01)
    assert True
