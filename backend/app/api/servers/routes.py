import logging
from typing import List

from fastapi import APIRouter, HTTPException

from app.models.schemas import MCPServer, MCPServerCreate, MCPServerResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[MCPServerResponse])
async def list_servers():
    """List all MCP servers"""
    # TODO: Implement database query
    return []


@router.post("/", response_model=MCPServerResponse)
async def add_server(server: MCPServerCreate):
    """Add a new MCP server"""
    # TODO: Implement server addition logic
    logger.info(f"Adding server: {server.name}")
    return MCPServerResponse(
        id=1, name=server.name, description=server.description, status="disconnected"
    )


@router.get("/{server_name}", response_model=MCPServerResponse)
async def get_server(server_name: str):
    """Get details of a specific MCP server"""
    # TODO: Implement database query
    raise HTTPException(status_code=404, detail="Server not found")


@router.delete("/{server_name}")
async def remove_server(server_name: str):
    """Remove an MCP server"""
    # TODO: Implement server removal logic
    logger.info(f"Removing server: {server_name}")
    return {"message": f"Server {server_name} removed successfully"}


@router.post("/{server_name}/test")
async def test_server(server_name: str):
    """Test connection to an MCP server"""
    # TODO: Implement connection testing
    logger.info(f"Testing server: {server_name}")
    return {"status": "success", "message": "Connection successful"}
