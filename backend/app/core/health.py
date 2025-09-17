"""Health check utilities for the MCP Gateway application"""

import asyncio
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import text

from app.core.database import AsyncSessionLocal, engine
from app.core.docker_manager import docker_manager
from app.core.redis import redis_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def check_database_health() -> Dict[str, Any]:
    """Check database connectivity and basic functionality"""
    try:
        async with AsyncSessionLocal() as session:
            # Simple query to test connection
            result = await session.execute(text("SELECT 1"))
            await session.commit()

        return {
            "status": "healthy",
            "message": "Database connection successful",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }


async def check_redis_health() -> Dict[str, Any]:
    """Check Redis connectivity"""
    try:
        if not redis_client.redis:
            await redis_client.connect()

        # Test basic Redis operations
        test_key = "health_check_test"
        await redis_client.set(test_key, "test_value", expire=5)
        value = await redis_client.get(test_key)
        await redis_client.delete(test_key)

        if value == "test_value":
            return {
                "status": "healthy",
                "message": "Redis connection and operations successful",
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            return {
                "status": "unhealthy",
                "message": "Redis operations failed",
                "timestamp": datetime.utcnow().isoformat(),
            }
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }


async def check_docker_health() -> Dict[str, Any]:
    """Check Docker daemon connectivity"""
    try:
        if not docker_manager.is_connected():
            return {
                "status": "unhealthy",
                "message": "Docker daemon not accessible",
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Get basic Docker info
        info = await docker_manager.get_system_info()

        return {
            "status": "healthy",
            "message": "Docker daemon accessible",
            "info": {
                "containers": info.get("containers", 0),
                "images": info.get("images", 0),
                "server_version": info.get("server_version", "unknown"),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error("Docker health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "message": f"Docker health check failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }


async def get_comprehensive_health() -> Dict[str, Any]:
    """Get comprehensive health status of all system components"""

    # Run all health checks concurrently
    results = await asyncio.gather(
        check_database_health(),
        check_redis_health(),
        check_docker_health(),
        return_exceptions=True,
    )
    database_health, redis_health, docker_health = results[0], results[1], results[2]

    # Handle any exceptions from health checks
    def format_health_result(result, component_name):
        if isinstance(result, Exception):
            return {
                "status": "unhealthy",
                "message": f"{component_name} health check raised exception: {str(result)}",
                "timestamp": datetime.utcnow().isoformat(),
            }
        return result

    formatted_database_health: Dict[str, Any] = format_health_result(
        database_health, "Database"
    )
    formatted_redis_health: Dict[str, Any] = format_health_result(redis_health, "Redis")
    formatted_docker_health: Dict[str, Any] = format_health_result(
        docker_health, "Docker"
    )

    # Determine overall health status
    components = {
        "database": formatted_database_health,
        "redis": formatted_redis_health,
        "docker": formatted_docker_health,
    }

    all_healthy = all(
        component["status"] == "healthy" for component in components.values()
    )

    overall_status = "healthy" if all_healthy else "unhealthy"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "components": components,
        "version": "1.0.0",  # TODO: Get from app config
        "environment": "development",  # TODO: Get from app config
    }
