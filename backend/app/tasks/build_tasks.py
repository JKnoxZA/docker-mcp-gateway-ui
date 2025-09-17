import asyncio
import logging
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from typing import Dict, List

from celery import Task

from app.core.celery_app import celery_app
from app.core.docker_manager import docker_manager
from app.core.redis import redis_client
from app.models.schemas import BuildStatus

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Custom Celery task class with callback support"""

    def on_success(self, retval, task_id, args, kwargs):
        """Called on task success"""
        logger.info(f"Task {task_id} completed successfully")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called on task failure"""
        logger.error(f"Task {task_id} failed: {exc}")


@celery_app.task(base=CallbackTask, bind=True)
def build_docker_image(
    self,
    build_id: str,
    project_data: Dict,
    build_context_path: str,
    image_tag: str,
    dockerfile_name: str = "Dockerfile",
):
    """Build Docker image asynchronously"""
    logger.info(f"Starting build {build_id} for image {image_tag}")

    async def _build_image():
        try:
            # Update build status to building
            await redis_client.update_build_status(
                build_id,
                {
                    "status": BuildStatus.BUILDING,
                    "started_at": datetime.utcnow().isoformat(),
                    "progress": 0,
                    "logs": [],
                },
            )

            # Publish build started event
            await redis_client.publish_event(
                f"build:{build_id}",
                {
                    "type": "build_started",
                    "build_id": build_id,
                    "image_tag": image_tag,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            build_logs = []

            # Build the image and collect logs
            async for log_entry in docker_manager.build_image(
                build_context_path, image_tag, dockerfile_name
            ):
                build_logs.append(log_entry)

                # Update status with latest logs
                await redis_client.update_build_status(
                    build_id,
                    {
                        "status": BuildStatus.BUILDING,
                        "logs": build_logs[-100:],  # Keep last 100 log entries
                        "updated_at": datetime.utcnow().isoformat(),
                    },
                )

                # Publish build log event
                await redis_client.publish_event(
                    f"build:{build_id}",
                    {
                        "type": "build_log",
                        "build_id": build_id,
                        "log_entry": log_entry,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

                # Check for error
                if log_entry.get("status") == "error":
                    await redis_client.update_build_status(
                        build_id,
                        {
                            "status": BuildStatus.FAILED,
                            "error": log_entry.get("message", "Unknown error"),
                            "completed_at": datetime.utcnow().isoformat(),
                            "logs": build_logs,
                        },
                    )

                    # Publish build failed event
                    await redis_client.publish_event(
                        f"build:{build_id}",
                        {
                            "type": "build_failed",
                            "build_id": build_id,
                            "error": log_entry.get("message", "Unknown error"),
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )
                    return False

            # Build completed successfully
            await redis_client.update_build_status(
                build_id,
                {
                    "status": BuildStatus.SUCCESS,
                    "completed_at": datetime.utcnow().isoformat(),
                    "image_tag": image_tag,
                    "logs": build_logs,
                },
            )

            # Publish build completed event
            await redis_client.publish_event(
                f"build:{build_id}",
                {
                    "type": "build_completed",
                    "build_id": build_id,
                    "image_tag": image_tag,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            logger.info(f"Build {build_id} completed successfully")
            return True

        except Exception as e:
            logger.error(f"Build {build_id} failed with exception: {e}")

            # Update build status to failed
            await redis_client.update_build_status(
                build_id,
                {
                    "status": BuildStatus.FAILED,
                    "error": str(e),
                    "completed_at": datetime.utcnow().isoformat(),
                },
            )

            # Publish build failed event
            await redis_client.publish_event(
                f"build:{build_id}",
                {
                    "type": "build_failed",
                    "build_id": build_id,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            raise

    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_build_image())
    finally:
        loop.close()


@celery_app.task(base=CallbackTask, bind=True)
def build_mcp_project(
    self,
    build_id: str,
    project_id: int,
    project_data: Dict,
    build_options: Dict = None,
):
    """Build MCP project with generated files"""
    logger.info(f"Starting MCP project build {build_id} for project {project_id}")

    async def _build_mcp_project():
        try:
            build_options = build_options or {}

            # Update build status
            await redis_client.update_build_status(
                build_id,
                {
                    "status": BuildStatus.BUILDING,
                    "project_id": project_id,
                    "started_at": datetime.utcnow().isoformat(),
                    "stage": "preparing",
                },
            )

            # Create temporary build directory
            with tempfile.TemporaryDirectory() as temp_dir:
                build_context = os.path.join(temp_dir, "build_context")
                os.makedirs(build_context, exist_ok=True)

                # Generate MCP project files
                await _generate_project_files(project_data, build_context)

                # Build Docker image
                image_tag = f"mcp-project-{project_id}:latest"

                # Update status to building
                await redis_client.update_build_status(
                    build_id,
                    {"stage": "building", "image_tag": image_tag},
                )

                # Build the image
                success = await celery_app.send_task(
                    "build_docker_image",
                    args=[build_id, project_data, build_context, image_tag],
                ).get()

                if success:
                    # Update project status in database here
                    # TODO: Add database update logic
                    pass

                return success

        except Exception as e:
            logger.error(f"MCP project build {build_id} failed: {e}")
            await redis_client.update_build_status(
                build_id,
                {
                    "status": BuildStatus.FAILED,
                    "error": str(e),
                    "completed_at": datetime.utcnow().isoformat(),
                },
            )
            raise

    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_build_mcp_project())
    finally:
        loop.close()


async def _generate_project_files(project_data: Dict, build_context: str):
    """Generate MCP project files in build context"""

    # Generate Dockerfile
    dockerfile_content = _generate_dockerfile(project_data)
    with open(os.path.join(build_context, "Dockerfile"), "w") as f:
        f.write(dockerfile_content)

    # Generate requirements.txt
    requirements = project_data.get("requirements", [])
    requirements_content = "\n".join(requirements)
    if "mcp" not in requirements_content:
        requirements_content += "\nmcp>=0.1.0"

    with open(os.path.join(build_context, "requirements.txt"), "w") as f:
        f.write(requirements_content)

    # Generate server.py
    server_content = _generate_server_code(project_data)
    with open(os.path.join(build_context, "server.py"), "w") as f:
        f.write(server_content)

    # Generate README.md
    readme_content = _generate_readme(project_data)
    with open(os.path.join(build_context, "README.md"), "w") as f:
        f.write(readme_content)

    logger.info(f"Generated project files in {build_context}")


def _generate_dockerfile(project_data: Dict) -> str:
    """Generate Dockerfile content"""
    python_version = project_data.get("python_version", "3.11")

    return f"""FROM python:{python_version}-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .
COPY README.md .

# Create non-root user
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

# Expose port for MCP server
EXPOSE 8080

# Run the MCP server
CMD ["python", "server.py"]
"""


def _generate_server_code(project_data: Dict) -> str:
    """Generate MCP server code"""
    name = project_data.get("name", "mcp-server")
    description = project_data.get("description", "Custom MCP Server")
    tools = project_data.get("tools", [])

    tool_functions = []
    tool_registrations = []

    for tool in tools:
        tool_name = tool.get("name", "unknown")
        tool_description = tool.get("description", "")

        # Generate tool function
        tool_functions.append(f"""
@server.call_tool()
async def {tool_name}(arguments: dict) -> list[types.TextContent]:
    \"\"\"
    {tool_description}
    \"\"\"
    # TODO: Implement {tool_name} functionality
    result = f"Executed {tool_name} with arguments: {{arguments}}"
    return [types.TextContent(type="text", text=result)]
""")

        # Generate tool registration
        tool_registrations.append(f"""
    types.Tool(
        name="{tool_name}",
        description="{tool_description}",
        inputSchema={{
            "type": "object",
            "properties": {{
                "query": {{
                    "type": "string",
                    "description": "Input for {tool_name}"
                }}
            }},
            "required": ["query"]
        }}
    )""")

    tools_code = ",".join(tool_registrations) if tool_registrations else ""
    functions_code = "\n".join(tool_functions)

    return f"""#!/usr/bin/env python3
\"\"\"
{name}
{description}
\"\"\"

import asyncio
import logging
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create server instance
server = Server("{name}")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    \"\"\"
    List available tools.
    \"\"\"
    return [{tools_code}]

{functions_code}

async def main():
    # Run the server using stdio
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="{name}",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={{}},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
"""


def _generate_readme(project_data: Dict) -> str:
    """Generate README content"""
    name = project_data.get("name", "MCP Server")
    description = project_data.get("description", "Custom MCP Server")
    tools = project_data.get("tools", [])

    tools_section = ""
    if tools:
        tools_list = "\n".join([f"- **{tool.get('name', 'unknown')}**: {tool.get('description', '')}" for tool in tools])
        tools_section = f"""
## Available Tools

{tools_list}
"""

    return f"""# {name}

{description}

This is a custom Model Context Protocol (MCP) server generated by the MCP Docker Gateway.

{tools_section}

## Installation

1. Build the Docker image:
   ```bash
   docker build -t {name.lower().replace(' ', '-')} .
   ```

2. Run the container:
   ```bash
   docker run -p 8080:8080 {name.lower().replace(' ', '-')}
   ```

## Usage

This MCP server can be connected to any MCP-compatible client such as Claude Desktop, Cursor, or LM Studio.

## Development

To modify this server:
1. Edit the `server.py` file
2. Rebuild the Docker image
3. Test with your MCP client

## Generated by MCP Docker Gateway

This server was automatically generated by the MCP Docker Gateway platform.
"""


@celery_app.task(base=CallbackTask)
def cleanup_expired_builds():
    """Clean up expired build data from Redis"""

    async def _cleanup():
        try:
            # Get all build keys
            if not redis_client.redis:
                return

            build_keys = await redis_client.redis.keys("build:*")
            cleanup_count = 0

            for key in build_keys:
                build_data = await redis_client.get(key)
                if build_data and isinstance(build_data, dict):
                    # Check if build is older than 24 hours
                    started_at = build_data.get("started_at")
                    if started_at:
                        start_time = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                        if datetime.utcnow() - start_time > timedelta(hours=24):
                            await redis_client.delete(key)
                            cleanup_count += 1

            logger.info(f"Cleaned up {cleanup_count} expired builds")

        except Exception as e:
            logger.error(f"Error during build cleanup: {e}")

    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_cleanup())
    finally:
        loop.close()


@celery_app.task(base=CallbackTask)
def get_build_queue_status():
    """Get status of build queue"""

    async def _get_status():
        try:
            if not redis_client.redis:
                return {"queue_length": 0, "active_builds": 0}

            # Get queue length
            queue_length = await redis_client.redis.llen("build_queue")

            # Get active builds (building status)
            build_keys = await redis_client.redis.keys("build:*")
            active_builds = 0

            for key in build_keys:
                build_data = await redis_client.get(key)
                if build_data and build_data.get("status") == BuildStatus.BUILDING:
                    active_builds += 1

            return {
                "queue_length": queue_length,
                "active_builds": active_builds,
                "total_builds": len(build_keys),
            }

        except Exception as e:
            logger.error(f"Error getting build queue status: {e}")
            return {"error": str(e)}

    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_get_status())
    finally:
        loop.close()