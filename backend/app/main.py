import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import api_router
from app.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting MCP Docker Gateway Backend")

    # Initialize database
    from app.core.database import close_db, init_db

    await init_db()
    logger.info("Database initialized")

    # Initialize Redis
    from app.core.redis import close_redis, init_redis

    try:
        await init_redis()
        logger.info("Redis initialized")
    except Exception as e:
        logger.warning(f"Redis initialization failed: {e}")

    # Check Docker connection
    from app.core.docker_manager import docker_manager

    if docker_manager.is_connected():
        logger.info("Docker connection established")
    else:
        logger.warning("Docker connection failed")

    yield

    # Shutdown
    logger.info("Shutting down MCP Docker Gateway Backend")

    # Close database connections
    await close_db()
    logger.info("Database connections closed")

    # Close Redis connections
    try:
        await close_redis()
        logger.info("Redis connections closed")
    except Exception as e:
        logger.warning(f"Redis cleanup failed: {e}")


def create_application() -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title="MCP Docker Gateway API",
        description="Backend API for MCP Docker Gateway Manager",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router, prefix="/api")

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return JSONResponse(
            status_code=200,
            content={"status": "healthy", "service": "mcp-docker-gateway-backend"},
        )

    return app


app = create_application()


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
