"""Tests for application structure and imports"""

import importlib.util
import os


def test_app_module_exists():
    """Test that the app module can be imported"""
    spec = importlib.util.find_spec("app")
    assert spec is not None, "app module should be importable"


def test_app_directory_structure():
    """Test that required app directories exist"""
    app_dir = "app"
    required_dirs = ["api", "core", "models", "utils"]

    for dir_name in required_dirs:
        dir_path = os.path.join(app_dir, dir_name)
        assert os.path.isdir(dir_path), f"{dir_name} directory should exist in app/"


def test_key_files_exist():
    """Test that key application files exist"""
    key_files = [
        "app/__init__.py",
        "app/main.py",
        "app/models/database.py",
        "app/core/database.py",
    ]

    for file_path in key_files:
        assert os.path.isfile(file_path), f"{file_path} should exist"


def test_requirements_file_exists():
    """Test that requirements.txt exists"""
    assert os.path.isfile("requirements.txt"), "requirements.txt should exist"
