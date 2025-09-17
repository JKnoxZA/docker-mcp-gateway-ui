"""
Application settings with environment-specific configurations.

This module provides a centralized configuration system that supports
different environments (development, testing, staging, production).
"""

import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class LegacySettings(BaseSettings):
    """Legacy settings for backward compatibility"""

    # Application
    APP_NAME: str = "MCP Docker Gateway"
    DEBUG: bool = True
    VERSION: str = "1.0.0"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./mcp_gateway.db"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: Optional[str] = None

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Docker
    DOCKER_SOCKET: str = "unix:///var/run/docker.sock"
    DOCKER_TIMEOUT: int = 60

    # MCP Gateway Configuration
    MCP_CONFIG_PATH: str = "/config"
    MCP_WORKSPACE_PATH: str = "/tmp/mcp_workspace"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_legacy_settings() -> LegacySettings:
    """Get legacy settings for backward compatibility"""
    return LegacySettings()


# Create settings instance based on environment
try:
    # Try to use environment-specific settings
    from app.config.environments import create_settings
    settings = create_settings()
except ImportError:
    # Fallback to legacy settings if environment config is not available
    settings = get_legacy_settings()
except Exception as e:
    # Fallback to legacy settings if environment config fails
    import logging
    logging.warning(f"Failed to load environment settings: {e}. Using legacy settings.")
    settings = get_legacy_settings()


# Export commonly used settings for convenience
APP_NAME = settings.APP_NAME
DEBUG = getattr(settings, 'DEBUG', False)
LOG_LEVEL = getattr(settings, 'LOG_LEVEL', 'INFO')
DATABASE_URL = settings.DATABASE_URL
REDIS_URL = getattr(settings, 'REDIS_URL', 'redis://localhost:6379')
SECRET_KEY = getattr(settings, 'SECRET_KEY', 'default-secret-key')
ALLOWED_HOSTS = getattr(settings, 'ALLOWED_HOSTS', ['*'])
