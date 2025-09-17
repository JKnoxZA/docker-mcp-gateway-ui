# MCP Workflow Automation Backend
# This demonstrates the core backend logic for automating the MCP development workflow

import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional

import docker
import yaml
from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel

app = FastAPI(title="MCP Docker Gateway Manager")

# Docker client
docker_client = docker.from_env()


# Models for API
class MCPProject(BaseModel):
    name: str
    description: str
    tools: List[Dict[str, str]]
    python_version: str = "3.11"
    requirements: List[str] = []


class BuildStatus(BaseModel):
    project_name: str
    status: str  # "building", "success", "failed"
    build_id: str
    logs: List[str] = []


class DeploymentConfig(BaseModel):
    project_name: str
    image_tag: str
    registry_url: Optional[str] = None


class MCPServer(BaseModel):
    name: str
    description: str
    type: str  # "official", "custom", "remote"
    url: Optional[str] = None
    api_key: Optional[str] = None
    tools: List[Dict[str, str]] = []
    status: str = "disconnected"  # "connected", "disconnected", "error"
    transport: str = "stdio"  # "stdio", "sse", "websocket"


class LLMClient(BaseModel):
    name: str
    type: str  # "claude", "cursor", "lm_studio", "custom"
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    connected_servers: List[str] = []
    status: str = "disconnected"


class ToolPermission(BaseModel):
    tool_name: str
    server_name: str
    client_name: str
    permission: str  # "allowed", "denied", "pending"
    timestamp: str


class SecretStore(BaseModel):
    key: str
    description: str
    created_at: str
    used_by: List[str] = []


# In-memory storage (use Redis/DB in production)
projects: Dict[str, MCPProject] = {}
build_statuses: Dict[str, BuildStatus] = {}
mcp_servers: Dict[str, MCPServer] = {}
llm_clients: Dict[str, LLMClient] = {}
tool_permissions: List[ToolPermission] = []
secrets: Dict[str, str] = {}  # In production, use proper encryption
server_catalog: List[Dict[str, str]] = []


# Initialize with some default official servers
def initialize_server_catalog():
    global server_catalog
    server_catalog = [
        {
            "name": "brave-search",
            "description": "Search the web using Brave Search API",
            "type": "official",
            "tools": ["brave_web_search"],
            "requires_api_key": True,
        },
        {
            "name": "obsidian",
            "description": "Interact with Obsidian vaults",
            "type": "official",
            "tools": ["append_to_note", "search_notes", "create_note"],
            "requires_api_key": True,
        },
        {
            "name": "github",
            "description": "GitHub repository management",
            "type": "official",
            "tools": ["create_issue", "list_repos", "create_pr"],
            "requires_api_key": True,
        },
        {
            "name": "postgres",
            "description": "PostgreSQL database operations",
            "type": "official",
            "tools": ["query_db", "describe_tables"],
            "requires_api_key": False,
        },
    ]


# Initialize default LLM clients
def initialize_llm_clients():
    global llm_clients
    llm_clients = {
        "claude": LLMClient(name="Claude", type="claude", status="available"),
        "cursor": LLMClient(name="Cursor", type="cursor", status="available"),
        "lm_studio": LLMClient(
            name="LM Studio",
            type="lm_studio",
            endpoint="http://localhost:1234",
            status="available",
        ),
    }


class MCPWorkflowManager:
    def __init__(self, workspace_root="/tmp/mcp_workspace"):
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(exist_ok=True)

        # Configuration file paths
        self.config_root = Path("/config")  # Mounted volume in production
        self.catalogs_file = self.config_root / "catalogs.yaml"
        self.registry_file = self.config_root / "registry.yaml"
        self.gateway_config = self.config_root / "cloud_mcp_config.yaml"

    def create_project_directory(self, project: MCPProject) -> Path:
        """Step 1: Create directory and generate all required files"""
        project_dir = self.workspace_root / project.name
        project_dir.mkdir(exist_ok=True)

        # Generate Dockerfile
        dockerfile_content = f"""FROM python:{project.python_version}-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY {project.name}.py .
COPY README.md .

EXPOSE 8000

CMD ["python", "{project.name}.py"]
"""
        (project_dir / "Dockerfile").write_text(dockerfile_content)

        # Generate requirements.txt
        requirements_content = "\n".join(
            ["mcp>=0.1.0", *project.requirements]  # Base MCP framework
        )
        (project_dir / "requirements.txt").write_text(requirements_content)

        # Generate Python server template
        server_content = f'''#!/usr/bin/env python3
"""
{project.description}
"""

import asyncio
import logging
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from pydantic import AnyUrl
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create server instance
server = Server("{project.name}")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    tools = []
    
    # Add your tools here based on project configuration
    {self._generate_tool_handlers(project.tools)}
    
    return tools

async def main():
    """Main entry point for the MCP server."""
    # Import here to avoid issues with event loop
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="{project.name}",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={{}},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
'''
        (project_dir / f"{project.name}.py").write_text(server_content)

        # Generate README
        readme_content = f"""# {project.name}

{project.description}

## Tools

{self._generate_readme_tools(project.tools)}

## Usage

This MCP server provides the following functionality:
- Tool execution and management
- Resource access and manipulation
- Integration with MCP gateway

## Configuration

Add this server to your MCP catalog:

```yaml
- name: {project.name}
  description: {project.description}
  image: {project.name}:latest
  tools:
{self._generate_yaml_tools(project.tools)}
```
"""
        (project_dir / "README.md").write_text(readme_content)

        return project_dir

    def _generate_tool_handlers(self, tools: List[Dict[str, str]]) -> str:
        """Generate tool handler code"""
        handlers = []
        for i, tool in enumerate(tools):
            handler = f"""
    # Tool {i+1}: {tool.get('name', f'tool_{i+1}')}
    tools.append(types.Tool(
        name="{tool.get('name', f'tool_{i+1}')}",
        description="{tool.get('description', 'Auto-generated tool')}",
        inputSchema={{
            "type": "object",
            "properties": {{}},
            "required": []
        }}
    ))"""
            handlers.append(handler)
        return "\n".join(handlers)

    def _generate_readme_tools(self, tools: List[Dict[str, str]]) -> str:
        """Generate tool documentation for README"""
        tool_docs = []
        for tool in tools:
            tool_docs.append(
                f"- **{tool.get('name', 'Unnamed Tool')}**: {tool.get('description', 'No description provided')}"
            )
        return "\n".join(tool_docs)

    def _generate_yaml_tools(self, tools: List[Dict[str, str]]) -> str:
        """Generate YAML tool configuration"""
        yaml_tools = []
        for tool in tools:
            yaml_tools.append(f"    - name: {tool.get('name', 'unnamed_tool')}")
            yaml_tools.append(
                f"      description: {tool.get('description', 'No description')}"
            )
        return "\n".join(yaml_tools)

    async def build_docker_image(self, project_name: str) -> str:
        """Step 2: Build Docker image"""
        project_dir = self.workspace_root / project_name
        if not project_dir.exists():
            raise HTTPException(status_code=404, detail="Project not found")

        build_id = f"{project_name}_{asyncio.get_event_loop().time()}"
        build_status = BuildStatus(
            project_name=project_name, status="building", build_id=build_id
        )
        build_statuses[build_id] = build_status

        try:
            # Build image using Docker API
            image, build_logs = docker_client.images.build(
                path=str(project_dir), tag=f"{project_name}:latest", rm=True
            )

            # Capture build logs
            logs = []
            for log in build_logs:
                if "stream" in log:
                    logs.append(log["stream"].strip())

            build_status.status = "success"
            build_status.logs = logs

            return build_id

        except docker.errors.BuildError as e:
            build_status.status = "failed"
            build_status.logs = [str(e)]
            raise HTTPException(status_code=500, detail=f"Build failed: {e}")

    def update_catalog_yaml(self, project: MCPProject):
        """Step 3: Update catalogs.yaml"""
        # Load existing catalog or create new
        if self.catalogs_file.exists():
            with open(self.catalogs_file, "r") as f:
                catalog = yaml.safe_load(f) or []
        else:
            catalog = []

        # Check if project already exists
        existing_index = None
        for i, entry in enumerate(catalog):
            if entry.get("name") == project.name:
                existing_index = i
                break

        # Create new catalog entry
        new_entry = {
            "name": project.name,
            "description": project.description,
            "image": f"{project.name}:latest",
            "tools": [
                {
                    "name": tool.get("name", f"tool_{i+1}"),
                    "description": tool.get("description", "Auto-generated tool"),
                }
                for i, tool in enumerate(project.tools)
            ],
        }

        if existing_index is not None:
            catalog[existing_index] = new_entry
        else:
            catalog.append(new_entry)

        # Save updated catalog
        self.catalogs_file.parent.mkdir(exist_ok=True)
        with open(self.catalogs_file, "w") as f:
            yaml.dump(catalog, f, default_flow_style=False)

    def update_registry_yaml(self, project_name: str):
        """Step 4: Update registry.yaml"""
        # Load existing registry or create new
        if self.registry_file.exists():
            with open(self.registry_file, "r") as f:
                registry = yaml.safe_load(f) or []
        else:
            registry = []

        # Check if project already exists
        existing_index = None
        for i, entry in enumerate(registry):
            if entry.get("ref") == project_name:
                existing_index = i
                break

        # Create new registry entry
        new_entry = {"ref": project_name, "url": f"docker://{project_name}:latest"}

        if existing_index is not None:
            registry[existing_index] = new_entry
        else:
            registry.append(new_entry)

        # Save updated registry
        with open(self.registry_file, "w") as f:
            yaml.dump(registry, f, default_flow_style=False)

    async def restart_mcp_gateway(self):
        """Step 5: Restart MCP Gateway"""
        try:
            # Find running MCP gateway container
            containers = docker_client.containers.list(filters={"name": "mcp_gateway"})

            if containers:
                gateway_container = containers[0]
                gateway_container.restart()
                return {"status": "restarted", "container_id": gateway_container.id}
            else:
                # Start new gateway if none running
                # This would need your specific gateway image and config
                container = docker_client.containers.run(
                    "your_gateway_image",  # Replace with actual image
                    name="mcp_gateway",
                    ports={"8811/tcp": 8811},
                    volumes={str(self.config_root): {"bind": "/config", "mode": "rw"}},
                    detach=True,
                )
                return {"status": "started", "container_id": container.id}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gateway restart failed: {e}")


# Initialize workflow manager
workflow_manager = MCPWorkflowManager()

# API Endpoints


@app.post("/api/projects/")
async def create_mcp_project(project: MCPProject):
    """Create a new MCP project with all required files"""
    projects[project.name] = project

    # Step 1: Create directory and files
    project_dir = workflow_manager.create_project_directory(project)

    return {
        "message": f"Project {project.name} created successfully",
        "project_path": str(project_dir),
        "files_created": [
            "Dockerfile",
            "requirements.txt",
            f"{project.name}.py",
            "README.md",
        ],
    }


@app.post("/api/projects/{project_name}/build")
async def build_mcp_project(project_name: str):
    """Build Docker image for MCP project"""
    if project_name not in projects:
        raise HTTPException(status_code=404, detail="Project not found")

    # Step 2: Build Docker image
    build_id = await workflow_manager.build_docker_image(project_name)

    return {"build_id": build_id, "status": "building"}


@app.post("/api/projects/{project_name}/deploy")
async def deploy_mcp_project(project_name: str):
    """Deploy MCP project (update configs and restart gateway)"""
    if project_name not in projects:
        raise HTTPException(status_code=404, detail="Project not found")

    project = projects[project_name]

    # Steps 3-5: Update configs and restart gateway
    workflow_manager.update_catalog_yaml(project)
    workflow_manager.update_registry_yaml(project_name)
    gateway_status = await workflow_manager.restart_mcp_gateway()

    return {
        "message": f"Project {project_name} deployed successfully",
        "configs_updated": ["catalogs.yaml", "registry.yaml"],
        "gateway_status": gateway_status,
    }


@app.post("/api/projects/{project_name}/full-deploy")
async def full_deploy_mcp_project(project_name: str):
    """Complete workflow: build and deploy MCP project"""
    if project_name not in projects:
        raise HTTPException(status_code=404, detail="Project not found")

    # Execute complete workflow
    build_result = await build_mcp_project(project_name)

    # Wait for build to complete (in production, use proper async handling)
    build_id = build_result["build_id"]
    while build_statuses[build_id].status == "building":
        await asyncio.sleep(1)

    if build_statuses[build_id].status == "failed":
        raise HTTPException(status_code=500, detail="Build failed")

    deploy_result = await deploy_mcp_project(project_name)

    return {
        "message": f"Full deployment of {project_name} completed",
        "build_id": build_id,
        "deployment": deploy_result,
    }


@app.get("/api/builds/{build_id}")
async def get_build_status(build_id: str):
    """Get build status and logs"""
    if build_id not in build_statuses:
        raise HTTPException(status_code=404, detail="Build not found")

    return build_statuses[build_id]


@app.websocket("/ws/build/{build_id}")
async def websocket_build_logs(websocket: WebSocket, build_id: str):
    """WebSocket endpoint for real-time build logs"""
    await websocket.accept()

    if build_id not in build_statuses:
        await websocket.send_json({"error": "Build not found"})
        return

    build_status = build_statuses[build_id]

    # Send existing logs
    for log in build_status.logs:
        await websocket.send_json({"log": log})

    # Monitor for new logs (simplified - use proper pub/sub in production)
    while build_status.status == "building":
        await asyncio.sleep(0.5)
        # Send any new logs

    await websocket.send_json(
        {"status": build_status.status, "message": f"Build {build_status.status}"}
    )


@app.get("/api/projects/")
async def list_projects():
    """List all MCP projects"""
    return {"projects": list(projects.keys())}


@app.get("/api/containers/")
async def list_containers():
    """List Docker containers (Docker Desktop functionality)"""
    containers = []
    for container in docker_client.containers.list(all=True):
        containers.append(
            {
                "id": container.id[:12],
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "status": container.status,
                "created": container.attrs["Created"],
                "ports": container.ports,
            }
        )
    return {"containers": containers}


# =============================================================================
# DOCKER DESKTOP MCP UI FEATURE ENDPOINTS
# =============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize default data on startup"""
    initialize_server_catalog()
    initialize_llm_clients()


# Server Catalog Management
@app.get("/api/mcp/catalog/")
async def get_server_catalog():
    """Get available MCP servers from catalog"""
    return {"servers": server_catalog}


@app.post("/api/mcp/servers/")
async def add_mcp_server(server: MCPServer):
    """Add a new MCP server (official, custom, or remote)"""
    # Validate API key if required
    if server.api_key:
        secrets[f"{server.name}_api_key"] = server.api_key
        server.api_key = None  # Don't store in server object

    mcp_servers[server.name] = server
    return {"message": f"MCP server {server.name} added successfully"}


@app.get("/api/mcp/servers/")
async def list_mcp_servers():
    """List all configured MCP servers"""
    return {"servers": list(mcp_servers.values())}


@app.get("/api/mcp/servers/{server_name}")
async def get_mcp_server(server_name: str):
    """Get details of a specific MCP server"""
    if server_name not in mcp_servers:
        raise HTTPException(status_code=404, detail="Server not found")
    return mcp_servers[server_name]


@app.delete("/api/mcp/servers/{server_name}")
async def remove_mcp_server(server_name: str):
    """Remove an MCP server"""
    if server_name not in mcp_servers:
        raise HTTPException(status_code=404, detail="Server not found")

    # Remove associated secrets
    if f"{server_name}_api_key" in secrets:
        del secrets[f"{server_name}_api_key"]

    del mcp_servers[server_name]
    return {"message": f"Server {server_name} removed successfully"}


@app.post("/api/mcp/servers/{server_name}/test")
async def test_mcp_server(server_name: str):
    """Test connection to an MCP server"""
    if server_name not in mcp_servers:
        raise HTTPException(status_code=404, detail="Server not found")

    server = mcp_servers[server_name]

    # Simulate connection test
    try:
        # In real implementation, would actually test the connection
        await asyncio.sleep(1)  # Simulate network delay
        server.status = "connected"
        return {
            "status": "success",
            "message": f"Successfully connected to {server_name}",
        }
    except Exception as e:
        server.status = "error"
        return {"status": "error", "message": f"Failed to connect: {str(e)}"}


# LLM Client Management
@app.get("/api/mcp/clients/")
async def list_llm_clients():
    """List available LLM clients"""
    return {"clients": list(llm_clients.values())}


@app.post("/api/mcp/clients/{client_name}/connect")
async def connect_client_to_servers(client_name: str, server_names: List[str]):
    """Connect an LLM client to MCP servers"""
    if client_name not in llm_clients:
        raise HTTPException(status_code=404, detail="Client not found")

    client = llm_clients[client_name]

    # Validate all servers exist
    for server_name in server_names:
        if server_name not in mcp_servers:
            raise HTTPException(
                status_code=404, detail=f"Server {server_name} not found"
            )

    client.connected_servers = server_names
    client.status = "connected"

    return {"message": f"Client {client_name} connected to {len(server_names)} servers"}


@app.post("/api/mcp/clients/")
async def add_custom_client(client: LLMClient):
    """Add a custom LLM client"""
    llm_clients[client.name] = client
    return {"message": f"Client {client.name} added successfully"}


# Tool Permissions Management
@app.get("/api/mcp/permissions/")
async def get_tool_permissions():
    """Get all tool permissions"""
    return {"permissions": tool_permissions}


@app.post("/api/mcp/permissions/")
async def handle_tool_permission(permission: ToolPermission):
    """Handle tool permission request"""
    tool_permissions.append(permission)

    # In real implementation, would notify the client about permission status
    return {
        "message": "Permission recorded",
        "permission_id": len(tool_permissions) - 1,
    }


@app.put("/api/mcp/permissions/{permission_id}")
async def update_tool_permission(permission_id: int, action: str):
    """Update tool permission (allow/deny)"""
    if permission_id >= len(tool_permissions):
        raise HTTPException(status_code=404, detail="Permission not found")

    if action not in ["allowed", "denied"]:
        raise HTTPException(status_code=400, detail="Invalid action")

    tool_permissions[permission_id].permission = action
    return {"message": f"Permission {action}"}


# Secrets Management
@app.post("/api/mcp/secrets/")
async def store_secret(key: str, value: str, description: str = ""):
    """Store a secret securely"""
    # In production, use proper encryption
    secrets[key] = value

    secret_info = SecretStore(
        key=key, description=description, created_at=asyncio.get_event_loop().time()
    )

    return {"message": f"Secret {key} stored successfully"}


@app.get("/api/mcp/secrets/")
async def list_secrets():
    """List secret keys (without values)"""
    return {
        "secrets": [
            {
                "key": key,
                "created_at": "2024-01-15",  # Simplified for demo
                "used_by": [],  # Would track which servers use this secret
            }
            for key in secrets.keys()
        ]
    }


@app.delete("/api/mcp/secrets/{key}")
async def delete_secret(key: str):
    """Delete a secret"""
    if key not in secrets:
        raise HTTPException(status_code=404, detail="Secret not found")

    del secrets[key]
    return {"message": f"Secret {key} deleted"}


# Gateway Management and Monitoring
@app.get("/api/mcp/gateway/status")
async def get_gateway_status():
    """Get MCP gateway status and connected servers"""
    try:
        gateway_container = docker_client.containers.get("mcp_gateway")

        return {
            "status": "running",
            "container_id": gateway_container.id[:12],
            "uptime": gateway_container.attrs["State"]["StartedAt"],
            "connected_servers": len(mcp_servers),
            "active_clients": len(
                [c for c in llm_clients.values() if c.status == "connected"]
            ),
        }
    except docker.errors.NotFound:
        return {"status": "stopped", "connected_servers": 0, "active_clients": 0}


@app.get("/api/mcp/gateway/logs")
async def get_gateway_logs():
    """Get MCP gateway logs"""
    try:
        gateway_container = docker_client.containers.get("mcp_gateway")
        logs = gateway_container.logs(tail=100).decode("utf-8").split("\n")
        return {"logs": logs}
    except docker.errors.NotFound:
        return {"logs": ["Gateway container not found"]}


@app.post("/api/mcp/gateway/restart")
async def restart_gateway():
    """Restart MCP gateway with current configuration"""
    try:
        result = await workflow_manager.restart_mcp_gateway()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Tool Execution and Monitoring
@app.post("/api/mcp/tools/execute")
async def execute_tool(
    tool_name: str, server_name: str, client_name: str, parameters: dict = {}
):
    """Execute a tool from an MCP server (requires permission)"""

    # Check if tool execution is allowed
    has_permission = any(
        p.tool_name == tool_name
        and p.server_name == server_name
        and p.client_name == client_name
        and p.permission == "allowed"
        for p in tool_permissions
    )

    if not has_permission:
        # Create pending permission request
        permission = ToolPermission(
            tool_name=tool_name,
            server_name=server_name,
            client_name=client_name,
            permission="pending",
            timestamp=str(asyncio.get_event_loop().time()),
        )
        tool_permissions.append(permission)

        return {
            "status": "permission_required",
            "message": f"Permission required to execute {tool_name}",
            "permission_id": len(tool_permissions) - 1,
        }

    # Simulate tool execution
    return {
        "status": "success",
        "tool": tool_name,
        "server": server_name,
        "result": f"Tool {tool_name} executed successfully",
        "execution_time": "0.5s",
    }


@app.get("/api/mcp/tools/")
async def list_all_tools():
    """List all available tools from all connected servers"""
    all_tools = []

    for server_name, server in mcp_servers.items():
        if server.status == "connected":
            for tool in server.tools:
                all_tools.append(
                    {
                        "name": tool.get("name"),
                        "description": tool.get("description"),
                        "server": server_name,
                        "server_type": server.type,
                    }
                )

    return {"tools": all_tools}


# Remote MCP Server Support
@app.post("/api/mcp/servers/remote")
async def add_remote_server(name: str, url: str, transport: str = "sse"):
    """Add a remote MCP server via URL"""

    if transport not in ["sse", "websocket", "http"]:
        raise HTTPException(status_code=400, detail="Invalid transport type")

    remote_server = MCPServer(
        name=name,
        description=f"Remote MCP server at {url}",
        type="remote",
        url=url,
        transport=transport,
        status="disconnected",
    )

    mcp_servers[name] = remote_server

    # Test connection in background
    # In real implementation, would actually test the remote connection

    return {"message": f"Remote server {name} added successfully"}


# WebSocket for real-time updates
@app.websocket("/ws/mcp/events")
async def websocket_mcp_events(websocket: WebSocket):
    """WebSocket for real-time MCP events"""
    await websocket.accept()

    try:
        while True:
            # Send periodic updates about MCP status
            status_update = {
                "timestamp": asyncio.get_event_loop().time(),
                "servers_connected": len(
                    [s for s in mcp_servers.values() if s.status == "connected"]
                ),
                "clients_active": len(
                    [c for c in llm_clients.values() if c.status == "connected"]
                ),
                "pending_permissions": len(
                    [p for p in tool_permissions if p.permission == "pending"]
                ),
            }

            await websocket.send_json(status_update)
            await asyncio.sleep(5)  # Update every 5 seconds

    except Exception as e:
        print(f"WebSocket error: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
