# MCP Docker Gateway Frontend

A comprehensive web-based management platform for Model Context Protocol (MCP) servers with Docker integration.

## 🎯 Overview

This application provides a Docker Desktop-like interface for managing MCP servers in headless Linux environments, along with powerful tools for developing custom MCP servers. It transforms complex command-line workflows into intuitive visual experiences.

## ✨ Features

- **MCP Development Studio**: Create and deploy custom MCP servers with templates
- **Server Management**: Browse, add, and manage MCP servers from catalog
- **Client Integration**: Connect LLM clients (Claude, Cursor, LM Studio) to MCP servers
- **Permission Management**: Control tool access with approval workflows
- **Container Management**: Docker Desktop-like interface for containers
- **Secrets Management**: Secure storage for API keys and credentials
- **Gateway Monitoring**: Real-time monitoring of MCP gateway status
- **Build Pipeline**: Automated Docker builds with real-time logs

## 🏗️ Architecture

### Tech Stack
- **Frontend**: React 18 + TypeScript + Tailwind CSS + Vite
- **Backend**: FastAPI + Python 3.11+ + SQLAlchemy + Redis
- **Database**: PostgreSQL (production) / SQLite (development)
- **Infrastructure**: Docker + Docker Compose

### Key Components
- MCP Development Studio with Monaco Editor
- Real-time WebSocket updates for builds and logs
- Docker SDK integration for container management
- Redis-based caching and job queues
- React Query for optimized API state management

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd docker-mcp-gateway-ui
   ```

2. **Set up environment variables**
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Development Setup

1. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Database Setup**
   ```bash
   cd backend
   alembic upgrade head
   ```

## 📁 Project Structure

```
docker-mcp-gateway-ui/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Business logic
│   │   ├── models/         # Database models
│   │   └── services/       # External services
│   ├── alembic/            # Database migrations
│   └── requirements.txt
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # React Query hooks
│   │   ├── pages/          # Route components
│   │   ├── services/       # API services
│   │   └── types/          # TypeScript types
│   └── package.json
├── docker-compose.yml      # Development environment
└── README.md
```

## 🔗 API Endpoints

### Core APIs
- `GET /api/projects/` - List MCP projects
- `POST /api/projects/` - Create new project
- `POST /api/projects/{id}/build` - Build project
- `GET /api/mcp/servers/` - List MCP servers
- `POST /api/mcp/servers/` - Add MCP server
- `GET /api/mcp/clients/` - List LLM clients
- `GET /api/docker/containers/` - List containers
- `GET /api/mcp/gateway/status` - Gateway status

### WebSocket Endpoints
- `/ws/build/{build_id}` - Build progress updates
- `/ws/logs/{container_id}` - Container logs
- `/ws/mcp/events` - MCP system events

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
pytest --cov=app --cov-report=html
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

## 🚀 Deployment

### Production Build
```bash
# Build frontend
cd frontend
npm run build

# Build backend
cd backend
docker build -t mcp-gateway-backend .

# Deploy with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables
See `.env.example` files for required configuration.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Guidelines
- Follow TypeScript strict mode
- Use React Query for server state
- Follow Tailwind CSS patterns
- Write tests for new features
- Update documentation

## 📊 Monitoring

The application includes built-in monitoring:
- Health checks for all services
- Real-time gateway status
- Container resource monitoring
- Build process tracking
- API performance metrics

## 🔒 Security

- JWT-based authentication
- Role-based access control
- Encrypted secrets storage
- Input validation and sanitization
- CORS configuration
- Container isolation

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- Documentation: See project-docs/ directory
- Issues: Create GitHub issue
- Development: Check CLAUDE.md for AI assistant context

## 🗂️ Related Documentation

- [Planning Document](project-docs/PLANNING.md) - Technical architecture and planning
- [Task Breakdown](project-docs/TASKS.md) - Detailed implementation tasks
- [Claude Context](project-docs/CLAUDE.md) - AI assistant project context