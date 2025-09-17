"""Environment-specific configuration settings"""

import os
from typing import Dict, List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class BaseEnvironmentSettings(BaseSettings):
    """Base settings common to all environments"""

    # Application
    APP_NAME: str = "MCP Docker Gateway"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = Field(min_length=32)

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    RELOAD: bool = False

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_DECODE_RESPONSES: bool = True

    # Docker
    DOCKER_TIMEOUT: int = 30
    DOCKER_API_VERSION: str = "auto"
    DOCKER_TLS_VERIFY: bool = False

    # Security
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "detailed"
    LOG_TO_FILE: bool = True
    LOG_ROTATION_SIZE: str = "10 MB"
    LOG_RETENTION_DAYS: int = 30

    # MCP Configuration
    MCP_CONFIG_PATH: str = "/config"
    MCP_WORKSPACE_PATH: str = "/tmp/mcp_workspace"
    MCP_SERVER_TIMEOUT: int = 30

    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    HEALTH_CHECK_INTERVAL: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


class DevelopmentSettings(BaseEnvironmentSettings):
    """Development environment settings"""

    DEBUG: bool = True
    RELOAD: bool = True
    LOG_LEVEL: str = "DEBUG"
    DATABASE_ECHO: bool = True

    # Relaxed security for development
    SECRET_KEY: str = "development-secret-key-change-in-production-minimum-32-chars"
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Development database
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"

    # Enable all development features
    ENABLE_METRICS: bool = True
    LOG_TO_FILE: bool = True

    class Config:
        env_prefix = "DEV_"


class TestingSettings(BaseEnvironmentSettings):
    """Testing environment settings"""

    DEBUG: bool = True
    LOG_LEVEL: str = "WARNING"  # Reduce log noise in tests
    DATABASE_ECHO: bool = False

    # Test database
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"

    # Test security
    SECRET_KEY: str = "test-secret-key-minimum-32-characters-long"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5  # Short-lived tokens for tests

    # Disable external services in tests
    ENABLE_METRICS: bool = False
    LOG_TO_FILE: bool = False

    # Fast timeouts for tests
    DOCKER_TIMEOUT: int = 5
    MCP_SERVER_TIMEOUT: int = 5

    class Config:
        env_prefix = "TEST_"


class StagingSettings(BaseEnvironmentSettings):
    """Staging environment settings"""

    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    WORKERS: int = 2

    # Staging security
    ALLOWED_HOSTS: List[str] = ["staging.example.com", "*.staging.example.com"]
    CORS_ORIGINS: List[str] = ["https://staging.example.com"]

    # Production-like database
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Enhanced monitoring
    ENABLE_METRICS: bool = True
    LOG_TO_FILE: bool = True
    LOG_RETENTION_DAYS: int = 7  # Shorter retention for staging

    class Config:
        env_prefix = "STAGING_"


class ProductionSettings(BaseEnvironmentSettings):
    """Production environment settings"""

    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    WORKERS: int = Field(default=4, ge=1, le=16)

    # Production security - must be provided
    SECRET_KEY: str = Field(min_length=32)
    ALLOWED_HOSTS: List[str] = Field(min_items=1)
    CORS_ORIGINS: List[str] = Field(min_items=1)

    # Production database settings
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_ECHO: bool = False

    # Redis connection pooling
    REDIS_MAX_CONNECTIONS: int = 50

    # Enhanced security
    CORS_CREDENTIALS: bool = True
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Production logging
    LOG_TO_FILE: bool = True
    LOG_RETENTION_DAYS: int = 90
    LOG_ROTATION_SIZE: str = "100 MB"

    # Production monitoring
    ENABLE_METRICS: bool = True
    HEALTH_CHECK_INTERVAL: int = 60

    # Longer timeouts for production stability
    DOCKER_TIMEOUT: int = 60
    MCP_SERVER_TIMEOUT: int = 60

    class Config:
        env_prefix = "PROD_"


# Environment mapping
ENVIRONMENT_CONFIGS: Dict[str, type] = {
    "development": DevelopmentSettings,
    "testing": TestingSettings,
    "staging": StagingSettings,
    "production": ProductionSettings,
}


def get_settings(environment: Optional[str] = None) -> BaseEnvironmentSettings:
    """Get settings for the specified environment"""

    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development").lower()

    if environment not in ENVIRONMENT_CONFIGS:
        raise ValueError(
            f"Unknown environment: {environment}. "
            f"Valid environments: {list(ENVIRONMENT_CONFIGS.keys())}"
        )

    settings_class = ENVIRONMENT_CONFIGS[environment]
    return settings_class()


def validate_environment_config(settings: BaseEnvironmentSettings) -> None:
    """Validate environment-specific configuration"""

    # Validate database URL
    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL must be provided")

    # Validate secret key in production
    if isinstance(settings, ProductionSettings):
        if "change" in settings.SECRET_KEY.lower() or "default" in settings.SECRET_KEY.lower():
            raise ValueError("Production SECRET_KEY must be changed from default value")

        if len(settings.ALLOWED_HOSTS) == 1 and settings.ALLOWED_HOSTS[0] == "*":
            raise ValueError("Production ALLOWED_HOSTS must not use wildcard")

    # Validate Redis URL
    if not settings.REDIS_URL.startswith(("redis://", "rediss://")):
        raise ValueError("REDIS_URL must be a valid Redis URL")

    # Validate ports
    if not (1 <= settings.PORT <= 65535):
        raise ValueError("PORT must be between 1 and 65535")

    if settings.ENABLE_METRICS and not (1 <= settings.METRICS_PORT <= 65535):
        raise ValueError("METRICS_PORT must be between 1 and 65535")


# Create default settings instance
def create_settings() -> BaseEnvironmentSettings:
    """Create and validate settings for current environment"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    settings = get_settings(environment)
    validate_environment_config(settings)
    return settings