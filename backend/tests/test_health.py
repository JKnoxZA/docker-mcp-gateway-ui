"""Basic health check tests"""

import pytest


def test_basic_assertion():
    """Basic test to ensure pytest is working"""
    assert True


def test_simple_math():
    """Test basic math operations"""
    assert 2 + 2 == 4
    assert 10 - 5 == 5


@pytest.mark.asyncio
async def test_async_function():
    """Test async functionality works"""

    async def sample_async():
        return "async works"

    result = await sample_async()
    assert result == "async works"
