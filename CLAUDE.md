# MCP Docker Gateway Frontend - Project Guide

This document provides essential context for Claude Code sessions working on the MCP Docker Gateway Frontend project.

## IMPORTANT!!
- **always read project-docs/PLANNING.md at the start of every new conversation**
- **check project-docs/TASKS.md before starting your work**
  - **mark completed tasks immediately**
  - **add newly discovered tasks**

## Project Overview

**Mission**: Create a comprehensive web-based management platform for Model Context Protocol (MCP) servers that combines custom MCP development tools with Docker Desktop-like functionality for headless Linux Docker environments.

**Key Value Proposition**: Transform complex command-line MCP workflows into simple, automated web-based processes while providing enterprise-grade security and monitoring.

**Target Users**:
- MCP Developers building custom servers
- DevOps Engineers managing MCP infrastructure  
- AI Product Managers connecting LLMs to tools
- Security Administrators managing permissions and secrets

---

## Technical Architecture

### Stack Overview
```
Frontend: React 18 + TypeScript + Tailwind CSS + Monaco Editor
Backend: FastAPI + Python 3.11+ + Docker SDK + WebSockets
Database: PostgreSQL (production) / SQLite (development) + Redis
Infrastructure: Docker + Kubernetes (optional) + NGINX
```

### System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │  Backend API    │    │ Docker Engine   │
│   (React/TS)    │◄──►│  (FastAPI)      │◄──►│   (Docker API)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │   Database      │              │
         └──────────────►│ (PostgreSQL)   │◄─────────────┘
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │   Redis Cache   │
                        │   & Job Queue   │
                        └─────────────────┘
```

### Core Technologies
- **Docker SDK**: Primary interface for container management
- **WebSockets**: Real-time updates for builds, logs, and system events
- **Monaco Editor**: Code editing with syntax highlighting
- **Pydantic**: Data validation and API schema definition
- **React Query**: Frontend state management and API caching
- **Tailwind CSS**: Utility-first styling framework

---

## Core Features & Components

### 1. MCP Development Studio
**Purpose**: Enable rapid creation and deployment of custom MCP servers

**Key Components**:
- Project creation wizard with templates
- Integrated code editor (Monaco) with Python/YAML/Dockerfile syntax highlighting
- Automated file generation (Dockerfile, requirements.txt, server.py, README.md)
- One-click Docker build pipeline with real-time logs
- Testing environment for MCP server validation

**File Structure**:
```
/src/components/development/
├── ProjectWizard.tsx          # New project creation
├── CodeEditor.tsx             # Monaco editor integration
├── FileExplorer.tsx           # Project file navigation
├── BuildPipeline.tsx          # Build process management
└── TestEnvironment.tsx        # MCP server testing
```

### 2. MCP Server Management
**Purpose**: Replicate Docker Desktop MCP functionality for headless systems

**Key Components**:
- Server catalog browsing and search
- Server lifecycle management (add/configure/start/stop/remove)
- Configuration management (catalogs.yaml, registry.yaml editors)
- Health monitoring and status tracking
- Remote server support (SSE, WebSocket transports)

**File Structure**:
```
/src/components/servers/
├── ServerCatalog.tsx          # Browse available servers
├── ServerManagement.tsx       # Server CRUD operations
├── ServerMonitoring.tsx       # Health and status tracking
├── ConfigurationEditor.tsx    # YAML configuration editing
└── RemoteServerSetup.tsx      # Remote server integration
```

### 3. Client & Permission Management
**Purpose**: Manage LLM client connections and tool permissions

**Key Components**:
- LLM client integration (Claude, Cursor, LM Studio)
- Client-server connection mapping
- Tool permission approval workflows
- Permission audit trails

**File Structure**:
```
/src/components/clients/
├── ClientManagement.tsx       # LLM client configuration
├── ConnectionMatrix.tsx       # Client-server mapping
├── PermissionManager.tsx      # Tool permission controls
└── AuditLog.tsx              # Permission audit trail
```

### 4. Gateway Operations
**Purpose**: Monitor and manage the MCP gateway and Docker infrastructure

**Key Components**:
- Gateway status dashboard
- Container management interface
- Log aggregation and streaming
- Performance monitoring

**File Structure**:
```
/src/components/gateway/
├── GatewayDashboard.tsx       # Status overview
├── ContainerManager.tsx       # Docker container operations
├── LogViewer.tsx              # Real-time log streaming
└── Monitoring.tsx             # Performance metrics
```

### 5. Security & Secrets
**Purpose**: Secure management of API keys and access controls

**Key Components**:
- Encrypted secrets storage
- Secret rotation and usage tracking
- Role-based access control
- Authentication integration

**File Structure**:
```
/src/components/security/
├── SecretsManager.tsx         # Secret CRUD operations
├── AccessControl.tsx          # RBAC management
├── AuthProvider.tsx           # Authentication handling
└── SecurityAudit.tsx          # Security event logging
```

---

## API Design

### REST API Endpoints
```python
# MCP Development
POST   /api/projects/                    # Create MCP project
GET    /api/projects/                    # List projects
POST   /api/projects/{id}/build          # Build Docker image
POST   /api/projects/{id}/deploy         # Deploy to gateway

# Server Management  
GET    /api/mcp/catalog/                 # Get server catalog
POST   /api/mcp/servers/                 # Add MCP server
GET    /api/mcp/servers/                 # List servers
DELETE /api/mcp/servers/{name}           # Remove server
POST   /api/mcp/servers/{name}/test      # Test connection

# Client Management
GET    /api/mcp/clients/                 # List LLM clients
POST   /api/mcp/clients/{name}/connect   # Connect to servers

# Permissions & Security
GET    /api/mcp/permissions/             # Get permissions
POST   /api/mcp/permissions/             # Request permission
POST   /api/mcp/secrets/                 # Store secret
DELETE /api/mcp/secrets/{key}            # Delete secret

# Gateway Operations
GET    /api/mcp/gateway/status           # Gateway health
GET    /api/mcp/gateway/logs             # Gateway logs
POST   /api/mcp/gateway/restart          # Restart gateway
```

### WebSocket Endpoints
```python
/ws/build/{build_id}       # Build progress updates
/ws/logs/{container_id}    # Container log streaming  
/ws/gateway/events         # Gateway events
/ws/mcp/events            # MCP system events
```

---

## Development Guidelines

### Code Organization
```
mcp-docker-frontend/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── core/             # Core business logic
│   │   ├── models/           # Pydantic models
│   │   ├── services/         # External service integrations
│   │   └── utils/            # Utility functions
│   ├── tests/                # Backend tests
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── services/         # API service layer
│   │   ├── types/            # TypeScript type definitions
│   │   └── utils/            # Utility functions
│   ├── public/               # Static assets
│   └── package.json          # Node dependencies
├── docker-compose.yml        # Development environment
└── README.md                 # Project documentation
```

### Naming Conventions
- **Components**: PascalCase (e.g., `ProjectWizard.tsx`)
- **Files**: camelCase for utilities, PascalCase for components
- **API Endpoints**: snake_case following FastAPI conventions
- **Database**: snake_case for tables and columns
- **Environment Variables**: UPPER_SNAKE_CASE

### State Management
- **React Query** for server state and API caching
- **useState/useReducer** for local component state  
- **Context API** for global app state (auth, theme)
- **WebSocket hooks** for real-time updates

### Error Handling
- **Frontend**: Error boundaries, toast notifications, graceful degradation
- **Backend**: Structured error responses, proper HTTP status codes
- **Docker**: Fallback mechanisms for Docker API failures
- **WebSocket**: Connection retry logic and offline handling

---

## Key User Workflows

### 1. Create Custom MCP Server (5 minutes)
```
1. Click "New Project" → Select template → Fill project details
2. Auto-generated files appear in editor → Customize server.py
3. Click "Build" → Watch real-time build logs → Build succeeds  
4. Click "Deploy" → Configs updated → Gateway restarted
5. Server appears in active servers list with "Running" status
```

### 2. Connect LLM Client to Servers
```
1. Navigate to Clients tab → Select "Claude"
2. Click "Configure" → Check desired servers → Save
3. Permission requests appear → Approve tool permissions
4. Client shows "Connected" with server count
5. Test tool execution through permission interface
```

### 3. Browse and Add Official Server
```
1. Navigate to Server Catalog → Search for "github"
2. Click "Add Server" → Enter API key → Configure settings
3. Test connection → Success → Server added to active list
4. Configure client connections → Set permissions
5. Server ready for use
```

---

## Development Priorities

### Phase 1: Foundation (Months 1-3)
1. **Docker Integration**: Core Docker SDK integration for container management
2. **Project Creation**: Basic MCP project wizard and file generation
3. **Build Pipeline**: Docker image building with real-time logs
4. **Container UI**: Basic container listing and management interface

### Phase 2: MCP Features (Months 4-6)
1. **Server Catalog**: Integration with MCP server catalog
2. **Client Management**: LLM client connection interface
3. **Permission System**: Tool permission approval workflows
4. **Configuration UI**: YAML editors for MCP configs

### Phase 3: Production Ready (Months 7-9)
1. **Authentication**: User login and session management
2. **Security**: Secrets management and access controls
3. **Monitoring**: Advanced monitoring and alerting
4. **Performance**: Optimization and scaling improvements

---

## Testing Strategy

### Frontend Testing
- **Unit Tests**: Jest + React Testing Library for components
- **Integration Tests**: API integration and user workflows
- **E2E Tests**: Cypress for critical user paths
- **Visual Tests**: Storybook for component documentation

### Backend Testing
- **Unit Tests**: pytest for business logic and utilities
- **API Tests**: FastAPI TestClient for endpoint testing
- **Integration Tests**: Docker container integration tests
- **Load Tests**: Performance testing for concurrent users

### Docker Integration Testing
- **Container Tests**: Verify Docker API integration
- **Build Tests**: Test image building and deployment
- **Network Tests**: Container networking and communication
- **Volume Tests**: Data persistence and volume management

---

## Security Considerations

### Data Protection
- **Secrets**: Encrypt sensitive data (API keys, passwords) at rest
- **Transport**: HTTPS/TLS for all API communication
- **WebSocket**: Secure WebSocket connections (WSS)
- **Docker**: Secure Docker socket access and container isolation

### Access Control
- **Authentication**: JWT tokens with refresh mechanism
- **Authorization**: Role-based access control (RBAC)
- **API Security**: Rate limiting and input validation
- **Audit Trail**: Log all security-relevant operations

### Container Security
- **Isolation**: Proper container resource limits and isolation
- **Images**: Scan container images for vulnerabilities
- **Networks**: Secure container networking configuration
- **Volumes**: Secure volume mounting and access controls

---

## Performance Requirements

### Response Times
- **UI Interactions**: < 200ms for all user interface actions
- **API Responses**: < 500ms for 95th percentile API calls
- **Build Times**: < 2 minutes for typical MCP server builds
- **WebSocket**: < 100ms latency for real-time updates

### Scalability Targets
- **Concurrent Users**: 100+ simultaneous users per instance
- **Container Management**: 500+ Docker containers per instance
- **WebSocket Connections**: 1000+ concurrent WebSocket connections
- **Database**: Support for 10M+ records with sub-second queries

### Resource Usage
- **Backend Memory**: < 2GB RAM under normal load
- **Frontend Bundle**: < 5MB compressed JavaScript bundle
- **Database**: Efficient indexing for fast queries
- **Docker**: Minimal resource overhead for container operations

---

## Deployment Configuration

### Development Environment
```yaml
# docker-compose.yml
services:
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    volumes: ["./frontend:/app"]
    
  backend:
    build: ./backend  
    ports: ["8000:8000"]
    volumes: ["./backend:/app", "/var/run/docker.sock:/var/run/docker.sock"]
    environment:
      - DATABASE_URL=sqlite:///./app.db
      - REDIS_URL=redis://redis:6379
      
  redis:
    image: redis:alpine
    ports: ["6379:6379"]
    
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=mcp_manager
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=password
    ports: ["5432:5432"]
```

### Production Considerations
- **Load Balancing**: Multiple backend instances behind NGINX
- **Database**: PostgreSQL with read replicas for scaling
- **Caching**: Redis cluster for distributed caching
- **Monitoring**: Prometheus/Grafana for metrics and alerting
- **Logging**: Centralized logging with ELK stack or similar

---

## Common Implementation Patterns

### React Component Pattern
```typescript
// Standard component structure
interface ComponentProps {
  data: DataType;
  onAction: (id: string) => void;
}

const Component: React.FC<ComponentProps> = ({ data, onAction }) => {
  const [loading, setLoading] = useState(false);
  const queryClient = useQueryClient();
  
  const mutation = useMutation({
    mutationFn: apiService.updateData,
    onSuccess: () => {
      queryClient.invalidateQueries(['data']);
      toast.success('Updated successfully');
    },
    onError: (error) => {
      toast.error(error.message);
    }
  });
  
  return (
    <div className="p-6 bg-white rounded-lg shadow">
      {/* Component content */}
    </div>
  );
};
```

### FastAPI Endpoint Pattern
```python
# Standard endpoint structure
@router.post("/", response_model=ResponseModel)
async def create_resource(
    data: CreateResourceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ResponseModel:
    try:
        # Validate permissions
        if not current_user.can_create_resource():
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Business logic
        result = await service.create_resource(db, data)
        
        # Audit log
        await audit.log_action(current_user.id, "create_resource", result.id)
        
        return result
    except ServiceException as e:
        logger.error(f"Service error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
```

### WebSocket Handler Pattern
```python
# WebSocket connection management
@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    
    try:
        # Subscribe to events
        await event_manager.subscribe(connection_id, websocket)
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await event_manager.unsubscribe(connection_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011)
```

---

## Troubleshooting Guide

### Common Issues
1. **Docker Connection**: Verify Docker socket permissions and daemon status
2. **WebSocket Failures**: Check CORS settings and network connectivity  
3. **Build Failures**: Validate Dockerfile syntax and dependency availability
4. **Permission Errors**: Verify user roles and access control configuration

### Debug Commands
```bash
# Backend debugging
docker logs mcp-backend
docker exec -it mcp-backend python -m pytest
docker exec -it mcp-backend python -c "import docker; print(docker.from_env().info())"

# Frontend debugging  
npm run test
npm run lint
npm run build

# Database debugging
docker exec -it postgres psql -U admin -d mcp_manager
```

---

## Future Considerations

### Extensibility Points
- **Plugin System**: Architecture for third-party plugins and extensions  
- **API Versioning**: Strategy for backward-compatible API evolution
- **Theme System**: Customizable UI themes and branding
- **Webhook Integration**: External system integration capabilities

### Scaling Considerations
- **Microservices**: Potential service decomposition for large deployments
- **Multi-tenancy**: Tenant isolation and resource management
- **Edge Deployment**: Support for edge computing scenarios
- **Federation**: Multi-cluster and multi-region deployments

---

This guide should be referenced for all development decisions and implementation details. Keep it updated as the project evolves and new patterns emerge.