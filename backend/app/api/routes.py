from fastapi import APIRouter

from app.api.auth.routes import router as auth_router
from app.api.clients.routes import router as clients_router
from app.api.docker.routes import router as docker_router

# Import route modules
from app.api.projects.routes import router as projects_router
from app.api.servers.routes import router as servers_router

# Main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(servers_router, prefix="/mcp/servers", tags=["mcp-servers"])
api_router.include_router(clients_router, prefix="/mcp/clients", tags=["mcp-clients"])
api_router.include_router(docker_router, prefix="/docker", tags=["docker"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
