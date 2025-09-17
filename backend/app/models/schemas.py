from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    """Project status enumeration"""

    CREATED = "created"
    BUILDING = "building"
    BUILD_FAILED = "build_failed"
    BUILT = "built"
    DEPLOYED = "deployed"
    DEPLOY_FAILED = "deploy_failed"


class ServerStatus(str, Enum):
    """Server status enumeration"""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class TransportType(str, Enum):
    """Transport type enumeration"""

    STDIO = "stdio"
    SSE = "sse"
    WEBSOCKET = "websocket"


# MCP Project Models
class MCPProjectBase(BaseModel):
    """Base MCP project model"""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    python_version: str = Field(default="3.11", pattern=r"^3\.(8|9|10|11|12)$")


class MCPProjectCreate(MCPProjectBase):
    """MCP project creation model"""

    tools: List[Dict[str, Any]] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list)


class MCPProject(MCPProjectBase):
    """Full MCP project model"""

    id: int
    tools: List[Dict[str, Any]] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list)
    status: ProjectStatus = ProjectStatus.CREATED
    created_at: datetime
    updated_at: datetime


class MCPProjectResponse(BaseModel):
    """MCP project response model"""

    id: int
    name: str
    description: str
    status: ProjectStatus
    tools_count: int = 0
    created_at: Optional[datetime] = None


# MCP Server Models
class MCPServerBase(BaseModel):
    """Base MCP server model"""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    server_type: str = Field(default="custom", alias="type")
    transport: TransportType = TransportType.STDIO


class MCPServerCreate(MCPServerBase):
    """MCP server creation model"""

    url: Optional[str] = None
    api_key: Optional[str] = None


class MCPServer(MCPServerBase):
    """Full MCP server model"""

    id: int
    url: Optional[str] = None
    tools: List[Dict[str, Any]] = Field(default_factory=list)
    status: ServerStatus = ServerStatus.DISCONNECTED
    created_at: datetime
    updated_at: datetime


class MCPServerResponse(BaseModel):
    """MCP server response model"""

    id: int
    name: str
    description: str
    server_type: str
    status: ServerStatus
    tools_count: int = 0
    transport: TransportType


# LLM Client Models
class LLMClientBase(BaseModel):
    """Base LLM client model"""

    name: str = Field(..., min_length=1, max_length=100)
    client_type: str = Field(..., alias="type")


class LLMClient(LLMClientBase):
    """Full LLM client model"""

    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    connected_servers: List[str] = Field(default_factory=list)
    status: str = "available"


class LLMClientResponse(BaseModel):
    """LLM client response model"""

    name: str
    client_type: str
    status: str
    connected_servers_count: int = 0


# Tool Permission Models
class PermissionStatus(str, Enum):
    """Permission status enumeration"""

    ALLOWED = "allowed"
    DENIED = "denied"
    PENDING = "pending"


class ToolPermission(BaseModel):
    """Tool permission model"""

    tool_name: str
    server_name: str
    client_name: str
    permission: PermissionStatus
    timestamp: datetime


class ToolPermissionCreate(BaseModel):
    """Tool permission creation model"""

    tool_name: str
    server_name: str
    client_name: str


# Secret Management Models
class SecretCreate(BaseModel):
    """Secret creation model"""

    key: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., min_length=1)
    description: str = Field(default="", max_length=500)


class SecretResponse(BaseModel):
    """Secret response model (without value)"""

    key: str
    description: str
    created_at: datetime
    used_by: List[str] = Field(default_factory=list)


# Docker Container Models
class ContainerStatus(str, Enum):
    """Container status enumeration"""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    RESTARTING = "restarting"
    REMOVING = "removing"
    EXITED = "exited"
    DEAD = "dead"


class ContainerInfo(BaseModel):
    """Docker container information"""

    id: str
    name: str
    image: str
    status: str
    created: str
    ports: Dict[str, Any] = Field(default_factory=dict)
    labels: Dict[str, str] = Field(default_factory=dict)
    state: Dict[str, Any] = Field(default_factory=dict)
    mounts: List[str] = Field(default_factory=list)


class ContainerDetails(ContainerInfo):
    """Detailed Docker container information"""

    started: Optional[str] = None
    environment: List[str] = Field(default_factory=list)
    network_settings: Dict[str, Any] = Field(default_factory=dict)
    logs_path: str = ""


class ContainerAction(BaseModel):
    """Container action request"""

    timeout: Optional[int] = Field(default=10, ge=1, le=300)
    force: Optional[bool] = False


class ContainerActionResponse(BaseModel):
    """Container action response"""

    container_id: str
    status: str
    message: str


# Docker Image Models
class ImageInfo(BaseModel):
    """Docker image information"""

    id: str
    tags: List[str] = Field(default_factory=list)
    created: str
    size: int
    labels: Dict[str, str] = Field(default_factory=dict)
    architecture: str = "unknown"
    os: str = "unknown"


class ImageBuildRequest(BaseModel):
    """Image build request"""

    path: str = Field(..., description="Build context path")
    tag: str = Field(..., description="Image tag")
    dockerfile: str = Field(default="Dockerfile", description="Dockerfile name")


class ImageBuildResponse(BaseModel):
    """Image build response"""

    status: str
    message: str
    timestamp: str


class ImageActionResponse(BaseModel):
    """Image action response"""

    image_id: str
    status: str
    message: str


# Docker Network Models
class NetworkInfo(BaseModel):
    """Docker network information"""

    id: str
    name: str
    driver: str
    scope: str
    created: str
    containers: List[str] = Field(default_factory=list)


# Docker Volume Models
class VolumeInfo(BaseModel):
    """Docker volume information"""

    name: str
    driver: str
    mountpoint: str
    created: str
    labels: Dict[str, str] = Field(default_factory=dict)
    scope: str


# Docker System Models
class SystemInfo(BaseModel):
    """Docker system information"""

    containers: int = 0
    containers_running: int = 0
    containers_paused: int = 0
    containers_stopped: int = 0
    images: int = 0
    server_version: str = "unknown"
    architecture: str = "unknown"
    os: str = "unknown"
    total_memory: int = 0
    cpu_count: int = 0
    storage_driver: str = "unknown"


# Build Models
class BuildStatus(str, Enum):
    """Build status enumeration"""

    PENDING = "pending"
    BUILDING = "building"
    SUCCESS = "success"
    FAILED = "failed"


class BuildInfo(BaseModel):
    """Build information model"""

    build_id: str
    project_name: str
    status: BuildStatus
    logs: List[str] = Field(default_factory=list)
    started_at: datetime
    completed_at: Optional[datetime] = None


# Gateway Status Models
class GatewayStatus(BaseModel):
    """Gateway status model"""

    status: str
    uptime: str
    connected_servers: int
    active_clients: int
    container_id: Optional[str] = None


# Response wrapper models
class APIResponse(BaseModel):
    """Generic API response wrapper"""

    message: str
    data: Optional[Any] = None
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response model"""

    message: str
    detail: Optional[str] = None
    success: bool = False
