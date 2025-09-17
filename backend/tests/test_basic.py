"""Basic tests to ensure pytest runs successfully"""


def test_always_passes():
    """A test that always passes to ensure pytest finds at least one test"""
    assert True == True


def test_basic_operations():
    """Test basic Python operations"""
    # Test arithmetic
    assert 1 + 1 == 2
    assert 5 * 2 == 10

    # Test string operations
    assert "hello" + " world" == "hello world"

    # Test list operations
    test_list = [1, 2, 3]
    assert len(test_list) == 3
    assert test_list[0] == 1


def test_imports_work():
    """Test that basic imports work"""
    import json
    import os
    import sys

    # Test json module works
    data = {"test": "value"}
    json_str = json.dumps(data)
    parsed = json.loads(json_str)
    assert parsed["test"] == "value"
