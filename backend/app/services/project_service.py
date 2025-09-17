import asyncio
import logging
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.database import MCPProject, ProjectFile, BuildHistory, User
from app.models.schemas import (
    MCPProjectCreate,
    MCPProject as MCPProjectSchema,
    MCPProjectResponse,
    ProjectStatus,
    BuildStatus,
)
from app.utils.logging_config import get_logger, PerformanceLogger, audit_log

logger = get_logger(__name__)


class ProjectService:
    """Service for managing MCP projects"""

    @staticmethod
    async def create_project(
        project_data: MCPProjectCreate,
        owner_id: int,
        db: AsyncSession
    ) -> MCPProject:
        """Create a new MCP project"""
        project_logger = logger.bind(
            owner_id=owner_id,
            project_name=project_data.name,
            operation="create_project"
        )

        with PerformanceLogger("create_project", project_logger,
                             project_name=project_data.name, owner_id=owner_id):
            try:
                project_logger.info("Starting project creation",
                                   description=project_data.description,
                                   python_version=project_data.python_version,
                                   tools_count=len(project_data.tools))

                # Create the project
                db_project = MCPProject(
                    name=project_data.name,
                    description=project_data.description,
                    python_version=project_data.python_version,
                    tools=project_data.tools,
                    requirements=project_data.requirements,
                    owner_id=owner_id,
                )

                db.add(db_project)
                await db.commit()
                await db.refresh(db_project)

                project_logger = project_logger.bind(project_id=db_project.id)
                project_logger.info("Project created in database")

                # Generate default project files
                await ProjectService._generate_default_files(db_project.id, project_data, db)

                # Audit log
                audit_log(
                    action="create",
                    resource_type="mcp_project",
                    resource_id=str(db_project.id),
                    user_id=str(owner_id),
                    details={
                        "project_name": db_project.name,
                        "python_version": db_project.python_version,
                        "tools_count": len(project_data.tools)
                    }
                )

                project_logger.info("Project creation completed successfully")
                return db_project

            except Exception as e:
                await db.rollback()
                project_logger.error("Failed to create project", error=str(e), error_type=type(e).__name__)
                raise

    @staticmethod
    async def get_project(project_id: int, db: AsyncSession) -> Optional[MCPProject]:
        """Get a project by ID"""
        try:
            result = await db.execute(
                select(MCPProject)
                .options(selectinload(MCPProject.files))
                .options(selectinload(MCPProject.builds))
                .where(MCPProject.id == project_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            raise

    @staticmethod
    async def list_projects(
        owner_id: Optional[int] = None,
        db: AsyncSession = None
    ) -> List[MCPProject]:
        """List all projects, optionally filtered by owner"""
        try:
            query = select(MCPProject).options(selectinload(MCPProject.files))

            if owner_id:
                query = query.where(MCPProject.owner_id == owner_id)

            result = await db.execute(query.order_by(MCPProject.created_at.desc()))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            raise

    @staticmethod
    async def update_project(
        project_id: int,
        project_data: dict,
        db: AsyncSession
    ) -> Optional[MCPProject]:
        """Update a project"""
        try:
            result = await db.execute(
                select(MCPProject).where(MCPProject.id == project_id)
            )
            project = result.scalar_one_or_none()

            if not project:
                return None

            # Update allowed fields
            for field, value in project_data.items():
                if hasattr(project, field):
                    setattr(project, field, value)

            project.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(project)

            logger.info(f"Updated project {project_id}")
            return project

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update project {project_id}: {e}")
            raise

    @staticmethod
    async def delete_project(project_id: int, db: AsyncSession) -> bool:
        """Delete a project and all associated data"""
        try:
            result = await db.execute(
                select(MCPProject).where(MCPProject.id == project_id)
            )
            project = result.scalar_one_or_none()

            if not project:
                return False

            await db.delete(project)
            await db.commit()

            logger.info(f"Deleted project {project_id}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to delete project {project_id}: {e}")
            raise

    @staticmethod
    async def start_build(
        project_id: int,
        db: AsyncSession
    ) -> Optional[str]:
        """Start a build for the project"""
        try:
            # Check if project exists
            result = await db.execute(
                select(MCPProject).where(MCPProject.id == project_id)
            )
            project = result.scalar_one_or_none()

            if not project:
                return None

            # Generate build ID
            build_id = str(uuid.uuid4())

            # Create build history record
            build_history = BuildHistory(
                build_id=build_id,
                project_id=project_id,
                status="pending",
                logs=[],
            )

            db.add(build_history)

            # Update project status
            project.status = ProjectStatus.BUILDING

            await db.commit()

            # TODO: Start actual build process asynchronously
            # For now, just return the build ID
            logger.info(f"Started build {build_id} for project {project_id}")
            return build_id

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to start build for project {project_id}: {e}")
            raise

    @staticmethod
    async def get_project_files(
        project_id: int,
        db: AsyncSession
    ) -> List[ProjectFile]:
        """Get all files for a project"""
        try:
            result = await db.execute(
                select(ProjectFile)
                .where(ProjectFile.project_id == project_id)
                .order_by(ProjectFile.file_path)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get files for project {project_id}: {e}")
            raise

    @staticmethod
    async def create_or_update_file(
        project_id: int,
        file_path: str,
        file_content: str,
        db: AsyncSession
    ) -> ProjectFile:
        """Create or update a project file"""
        try:
            # Check if file exists
            result = await db.execute(
                select(ProjectFile)
                .where(ProjectFile.project_id == project_id)
                .where(ProjectFile.file_path == file_path)
            )
            project_file = result.scalar_one_or_none()

            if project_file:
                # Update existing file
                project_file.file_content = file_content
                project_file.file_size = len(file_content.encode('utf-8'))
                project_file.updated_at = datetime.utcnow()
            else:
                # Create new file
                project_file = ProjectFile(
                    project_id=project_id,
                    file_path=file_path,
                    file_content=file_content,
                    file_size=len(file_content.encode('utf-8')),
                )
                db.add(project_file)

            await db.commit()
            await db.refresh(project_file)

            logger.info(f"Saved file {file_path} for project {project_id}")
            return project_file

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to save file {file_path} for project {project_id}: {e}")
            raise

    @staticmethod
    async def _generate_default_files(
        project_id: int,
        project_data: MCPProjectCreate,
        db: AsyncSession
    ):
        """Generate default project files"""
        try:
            # Generate server.py
            server_content = ProjectService._generate_server_file(project_data)
            await ProjectService.create_or_update_file(
                project_id, "server.py", server_content, db
            )

            # Generate requirements.txt
            requirements_content = ProjectService._generate_requirements_file(project_data)
            await ProjectService.create_or_update_file(
                project_id, "requirements.txt", requirements_content, db
            )

            # Generate Dockerfile
            dockerfile_content = ProjectService._generate_dockerfile(project_data)
            await ProjectService.create_or_update_file(
                project_id, "Dockerfile", dockerfile_content, db
            )

            # Generate README.md
            readme_content = ProjectService._generate_readme(project_data)
            await ProjectService.create_or_update_file(
                project_id, "README.md", readme_content, db
            )

        except Exception as e:
            logger.error(f"Failed to generate default files for project {project_id}: {e}")
            raise

    @staticmethod
    def _generate_server_file(project_data: MCPProjectCreate) -> str:
        """Generate the main server.py file"""
        return f'''#!/usr/bin/env python3
"""
{project_data.name} - MCP Server
{project_data.description}
"""

import asyncio
import logging
from typing import Any, Dict, List

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create server instance
server = Server("{project_data.name}")


@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools"""
    tools = []

    # Add your tools here
    # Example:
    # tools.append(types.Tool(
    #     name="example_tool",
    #     description="An example tool",
    #     inputSchema={{
    #         "type": "object",
    #         "properties": {{
    #             "message": {{
    #                 "type": "string",
    #                 "description": "Message to process"
    #             }}
    #         }},
    #         "required": ["message"]
    #     }}
    # ))

    return tools


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Dict[str, Any]
) -> List[types.TextContent]:
    """Handle tool execution"""

    # Add your tool implementations here
    # Example:
    # if name == "example_tool":
    #     message = arguments.get("message", "")
    #     result = f"Processed: {{message}}"
    #     return [types.TextContent(type="text", text=result)]

    raise ValueError(f"Unknown tool: {{name}}")


async def main():
    """Main entry point"""
    # Initialize and run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="{project_data.name}",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={{}},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
'''

    @staticmethod
    def _generate_requirements_file(project_data: MCPProjectCreate) -> str:
        """Generate requirements.txt file"""
        base_requirements = [
            "mcp>=1.0.0",
            "asyncio",
        ]

        # Add user-specified requirements
        all_requirements = base_requirements + project_data.requirements

        return "\\n".join(sorted(set(all_requirements)))

    @staticmethod
    def _generate_dockerfile(project_data: MCPProjectCreate) -> str:
        """Generate Dockerfile"""
        return f'''FROM python:{project_data.python_version}-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the server
CMD ["python", "server.py"]
'''

    @staticmethod
    def _generate_readme(project_data: MCPProjectCreate) -> str:
        """Generate README.md file"""
        return f'''# {project_data.name}

{project_data.description}

## Overview

This is an MCP (Model Context Protocol) server that provides tools and functionality for AI models.

## Requirements

- Python {project_data.python_version}+
- MCP compatible client

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   python server.py
   ```

## Tools

This server provides the following tools:

{chr(10).join(f"- {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}" for tool in project_data.tools)}

## Configuration

Configure this server in your MCP client configuration file (e.g., `~/.config/Claude/claude_desktop_config.json`):

```json
{{
  "mcpServers": {{
    "{project_data.name}": {{
      "command": "python",
      "args": ["/path/to/server.py"]
    }}
  }}
}}
```

## Development

Generated using the MCP Docker Gateway Frontend.
'''