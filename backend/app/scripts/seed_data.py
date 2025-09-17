#!/usr/bin/env python3
"""Seed database with sample data for development"""

import asyncio
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, init_db
from app.models.database import (
    MCPProject,
    MCPTemplate,
    DockerContainer,
    BuildLog,
    MCPServer,
    ProjectFile,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def create_sample_templates(session: AsyncSession) -> List[MCPTemplate]:
    """Create sample MCP templates"""
    templates = [
        MCPTemplate(
            name="Basic Python MCP Server",
            description="A basic Python-based MCP server template with essential functionality",
            language="python",
            framework="fastapi",
            template_files={
                "main.py": "# Basic MCP Server\nfrom fastapi import FastAPI\n\napp = FastAPI()",
                "requirements.txt": "fastapi>=0.104.0\nuvicorn>=0.24.0",
                "Dockerfile": "FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\nCMD ['uvicorn', 'main:app', '--host', '0.0.0.0']"
            },
            default_config={
                "port": 8000,
                "environment": "development",
                "auto_reload": True
            },
            tags=["python", "fastapi", "basic"]
        ),
        MCPTemplate(
            name="Node.js MCP Server",
            description="Node.js-based MCP server with Express framework",
            language="javascript",
            framework="express",
            template_files={
                "server.js": "const express = require('express');\nconst app = express();\n\napp.listen(3000);",
                "package.json": '{"name": "mcp-server", "dependencies": {"express": "^4.18.0"}}',
                "Dockerfile": "FROM node:18-alpine\nWORKDIR /app\nCOPY . .\nRUN npm install\nCMD ['node', 'server.js']"
            },
            default_config={
                "port": 3000,
                "environment": "development"
            },
            tags=["nodejs", "express", "javascript"]
        ),
        MCPTemplate(
            name="Go MCP Server",
            description="High-performance Go-based MCP server",
            language="go",
            framework="gin",
            template_files={
                "main.go": "package main\n\nimport \"github.com/gin-gonic/gin\"\n\nfunc main() {\n\tr := gin.Default()\n\tr.Run()\n}",
                "go.mod": "module mcp-server\n\ngo 1.21\n\nrequire github.com/gin-gonic/gin v1.9.1",
                "Dockerfile": "FROM golang:1.21-alpine AS builder\nWORKDIR /app\nCOPY . .\nRUN go build -o server\n\nFROM alpine:latest\nRUN apk --no-cache add ca-certificates\nWORKDIR /root/\nCOPY --from=builder /app/server .\nCMD ['./server']"
            },
            default_config={
                "port": 8080,
                "environment": "development"
            },
            tags=["go", "gin", "performance"]
        )
    ]

    for template in templates:
        session.add(template)

    await session.commit()
    return templates


async def create_sample_projects(session: AsyncSession, templates: List[MCPTemplate]) -> List[MCPProject]:
    """Create sample MCP projects"""
    projects = [
        MCPProject(
            name="Demo Chat MCP",
            description="A demonstration chat MCP server for testing basic functionality",
            template_id=templates[0].id,
            config={
                "port": 8001,
                "environment": "development",
                "features": ["chat", "websocket", "auth"]
            },
            status="running",
            docker_image="demo-chat-mcp:latest",
            docker_config={
                "image": "demo-chat-mcp:latest",
                "ports": {"8001/tcp": 8001},
                "environment": ["ENV=development"]
            }
        ),
        MCPProject(
            name="File Manager MCP",
            description="MCP server for file management operations",
            template_id=templates[1].id,
            config={
                "port": 3001,
                "environment": "development",
                "features": ["file-upload", "file-management", "permissions"]
            },
            status="stopped",
            docker_image="file-manager-mcp:latest"
        ),
        MCPProject(
            name="High Performance API",
            description="Go-based high-performance MCP server for API operations",
            template_id=templates[2].id,
            config={
                "port": 8080,
                "environment": "production",
                "features": ["api", "rate-limiting", "metrics"]
            },
            status="building"
        )
    ]

    for project in projects:
        session.add(project)

    await session.commit()
    return projects


async def create_sample_containers(session: AsyncSession, projects: List[MCPProject]):
    """Create sample Docker containers"""
    containers = [
        DockerContainer(
            project_id=projects[0].id,
            container_id="demo_chat_mcp_001",
            name="demo-chat-mcp-container",
            image="demo-chat-mcp:latest",
            status="running",
            ports={"8001/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8001"}]},
            environment=["ENV=development", "PORT=8001"],
            created_at=datetime.utcnow() - timedelta(hours=2),
            started_at=datetime.utcnow() - timedelta(hours=2)
        ),
        DockerContainer(
            project_id=projects[1].id,
            container_id="file_manager_mcp_001",
            name="file-manager-mcp-container",
            image="file-manager-mcp:latest",
            status="exited",
            ports={"3001/tcp": [{"HostIp": "0.0.0.0", "HostPort": "3001"}]},
            environment=["ENV=development", "PORT=3001"],
            created_at=datetime.utcnow() - timedelta(days=1),
            started_at=datetime.utcnow() - timedelta(days=1),
            finished_at=datetime.utcnow() - timedelta(hours=6)
        )
    ]

    for container in containers:
        session.add(container)

    await session.commit()


async def create_sample_servers(session: AsyncSession, projects: List[MCPProject]):
    """Create sample MCP servers"""
    servers = [
        MCPServer(
            project_id=projects[0].id,
            name="Demo Chat Server",
            url="http://localhost:8001",
            status="running",
            config={
                "transport": "http",
                "capabilities": ["chat", "websocket"],
                "auth": {"type": "bearer"}
            },
            last_health_check=datetime.utcnow() - timedelta(minutes=5),
            health_status="healthy"
        ),
        MCPServer(
            project_id=projects[1].id,
            name="File Manager Server",
            url="http://localhost:3001",
            status="stopped",
            config={
                "transport": "http",
                "capabilities": ["file-ops", "permissions"],
                "auth": {"type": "api-key"}
            },
            last_health_check=datetime.utcnow() - timedelta(hours=6),
            health_status="unhealthy"
        )
    ]

    for server in servers:
        session.add(server)

    await session.commit()


async def create_sample_build_logs(session: AsyncSession, projects: List[MCPProject]):
    """Create sample build logs"""
    logs = [
        BuildLog(
            project_id=projects[0].id,
            build_id="build_001",
            stage="setup",
            message="Starting build process...",
            level="info",
            timestamp=datetime.utcnow() - timedelta(hours=3)
        ),
        BuildLog(
            project_id=projects[0].id,
            build_id="build_001",
            stage="dependencies",
            message="Installing Python dependencies...",
            level="info",
            timestamp=datetime.utcnow() - timedelta(hours=3, minutes=-2)
        ),
        BuildLog(
            project_id=projects[0].id,
            build_id="build_001",
            stage="build",
            message="Building Docker image...",
            level="info",
            timestamp=datetime.utcnow() - timedelta(hours=3, minutes=-5)
        ),
        BuildLog(
            project_id=projects[0].id,
            build_id="build_001",
            stage="complete",
            message="Build completed successfully",
            level="success",
            timestamp=datetime.utcnow() - timedelta(hours=3, minutes=-8)
        ),
        BuildLog(
            project_id=projects[2].id,
            build_id="build_002",
            stage="setup",
            message="Starting Go build process...",
            level="info",
            timestamp=datetime.utcnow() - timedelta(minutes=30)
        ),
        BuildLog(
            project_id=projects[2].id,
            build_id="build_002",
            stage="compile",
            message="Compiling Go modules...",
            level="info",
            timestamp=datetime.utcnow() - timedelta(minutes=25)
        )
    ]

    for log in logs:
        session.add(log)

    await session.commit()


async def create_sample_files(session: AsyncSession, projects: List[MCPProject]):
    """Create sample project files"""
    files = [
        ProjectFile(
            project_id=projects[0].id,
            file_path="main.py",
            file_content="""# Demo Chat MCP Server
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Demo Chat MCP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Demo Chat MCP Server"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("Connected to Demo Chat MCP")
""",
            file_size=512,
            mime_type="text/x-python"
        ),
        ProjectFile(
            project_id=projects[0].id,
            file_path="requirements.txt",
            file_content="""fastapi>=0.104.0
uvicorn>=0.24.0
websockets>=11.0.0
""",
            file_size=64,
            mime_type="text/plain"
        ),
        ProjectFile(
            project_id=projects[1].id,
            file_path="server.js",
            file_content="""const express = require('express');
const multer = require('multer');
const app = express();

const storage = multer.diskStorage({
  destination: './uploads/',
  filename: (req, file, cb) => {
    cb(null, Date.now() + '-' + file.originalname);
  }
});

const upload = multer({ storage });

app.post('/upload', upload.single('file'), (req, res) => {
  res.json({ success: true, file: req.file });
});

app.listen(3001, () => {
  console.log('File Manager MCP running on port 3001');
});
""",
            file_size=432,
            mime_type="application/javascript"
        )
    ]

    for file in files:
        session.add(file)

    await session.commit()


async def seed_database():
    """Main seeding function"""
    logger.info("Starting database seeding...")

    try:
        # Initialize database
        await init_db()

        async with AsyncSessionLocal() as session:
            # Create sample data
            logger.info("Creating sample templates...")
            templates = await create_sample_templates(session)

            logger.info("Creating sample projects...")
            projects = await create_sample_projects(session, templates)

            logger.info("Creating sample containers...")
            await create_sample_containers(session, projects)

            logger.info("Creating sample servers...")
            await create_sample_servers(session, projects)

            logger.info("Creating sample build logs...")
            await create_sample_build_logs(session, projects)

            logger.info("Creating sample files...")
            await create_sample_files(session, projects)

        logger.info("Database seeding completed successfully!")

    except Exception as e:
        logger.error("Database seeding failed", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(seed_database())