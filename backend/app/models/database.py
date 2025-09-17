from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class ProjectStatusEnum(enum.Enum):
    """Project status enumeration"""
    CREATED = "created"
    BUILDING = "building"
    BUILD_FAILED = "build_failed"
    BUILT = "built"
    DEPLOYED = "deployed"
    DEPLOY_FAILED = "deploy_failed"


class ServerStatusEnum(enum.Enum):
    """Server status enumeration"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class TransportTypeEnum(enum.Enum):
    """Transport type enumeration"""
    STDIO = "stdio"
    SSE = "sse"
    WEBSOCKET = "websocket"


class PermissionStatusEnum(enum.Enum):
    """Permission status enumeration"""
    ALLOWED = "allowed"
    DENIED = "denied"
    PENDING = "pending"


class User(Base):
    """User table"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    projects = relationship("MCPProject", back_populates="owner")


class MCPProject(Base):
    """MCP Project table"""
    __tablename__ = "mcp_projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    python_version = Column(String(10), default="3.11")
    tools = Column(JSON, default=list)  # Store tool configurations as JSON
    requirements = Column(JSON, default=list)  # Store Python requirements as JSON
    status = Column(Enum(ProjectStatusEnum), default=ProjectStatusEnum.CREATED)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="projects")
    builds = relationship("BuildHistory", back_populates="project")


class MCPServer(Base):
    """MCP Server table"""
    __tablename__ = "mcp_servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)
    server_type = Column(String(50), default="custom")  # official, custom, remote
    url = Column(String(500))  # For remote servers
    transport = Column(Enum(TransportTypeEnum), default=TransportTypeEnum.STDIO)
    tools = Column(JSON, default=list)  # Store available tools as JSON
    config = Column(JSON, default=dict)  # Store server configuration as JSON
    status = Column(Enum(ServerStatusEnum), default=ServerStatusEnum.DISCONNECTED)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    connections = relationship("ClientConnection", back_populates="server")
    permissions = relationship("ToolPermission", back_populates="server")


class LLMClient(Base):
    """LLM Client table"""
    __tablename__ = "llm_clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    client_type = Column(String(50), nullable=False)  # claude, cursor, lm_studio, custom
    endpoint = Column(String(500))  # For custom clients
    config = Column(JSON, default=dict)  # Store client configuration as JSON
    status = Column(String(50), default="available")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    connections = relationship("ClientConnection", back_populates="client")
    permissions = relationship("ToolPermission", back_populates="client")


class ClientConnection(Base):
    """Client-Server connection table"""
    __tablename__ = "client_connections"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("llm_clients.id"), nullable=False)
    server_id = Column(Integer, ForeignKey("mcp_servers.id"), nullable=False)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    client = relationship("LLMClient", back_populates="connections")
    server = relationship("MCPServer", back_populates="connections")


class ToolPermission(Base):
    """Tool permission table"""
    __tablename__ = "tool_permissions"

    id = Column(Integer, primary_key=True, index=True)
    tool_name = Column(String(100), nullable=False)
    client_id = Column(Integer, ForeignKey("llm_clients.id"), nullable=False)
    server_id = Column(Integer, ForeignKey("mcp_servers.id"), nullable=False)
    permission = Column(Enum(PermissionStatusEnum), default=PermissionStatusEnum.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    client = relationship("LLMClient", back_populates="permissions")
    server = relationship("MCPServer", back_populates="permissions")


class Secret(Base):
    """Secret storage table"""
    __tablename__ = "secrets"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), nullable=False, unique=True, index=True)
    encrypted_value = Column(Text, nullable=False)  # Store encrypted secret value
    description = Column(Text, default="")
    used_by = Column(JSON, default=list)  # Store list of services using this secret
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class BuildHistory(Base):
    """Build history table"""
    __tablename__ = "build_history"

    id = Column(Integer, primary_key=True, index=True)
    build_id = Column(String(100), nullable=False, unique=True, index=True)
    project_id = Column(Integer, ForeignKey("mcp_projects.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, building, success, failed
    logs = Column(JSON, default=list)  # Store build logs as JSON array
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    project = relationship("MCPProject", back_populates="builds")


class AuditLog(Base):
    """Audit log table for tracking user actions"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)  # create, update, delete, execute, etc.
    resource_type = Column(String(50), nullable=False)  # project, server, client, etc.
    resource_id = Column(String(100))  # ID of the affected resource
    details = Column(JSON, default=dict)  # Additional details about the action
    ip_address = Column(String(45))  # IPv4 or IPv6 address
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")


class UserSession(Base):
    """User session table"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")