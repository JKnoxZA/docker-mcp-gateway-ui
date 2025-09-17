import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from app.core.celery_app import celery_app
from app.core.redis import redis_client
from app.models.schemas import BuildInfo, BuildStatus

logger = logging.getLogger(__name__)


class BuildManager:
    """Manager for Docker image builds and MCP project builds"""

    def __init__(self):
        self.redis = redis_client

    async def start_docker_build(
        self,
        context_path: str,
        image_tag: str,
        dockerfile: str = "Dockerfile",
        build_args: Optional[Dict] = None,
    ) -> str:
        """Start a Docker image build"""
        build_id = str(uuid.uuid4())

        try:
            # Create build job data
            build_data = {
                "build_id": build_id,
                "type": "docker_build",
                "context_path": context_path,
                "image_tag": image_tag,
                "dockerfile": dockerfile,
                "build_args": build_args or {},
                "status": BuildStatus.PENDING,
                "created_at": datetime.utcnow().isoformat(),
            }

            # Store build info in Redis
            await self.redis.set(f"build:{build_id}", build_data, expire=3600)

            # Queue build task
            celery_app.send_task(
                "app.tasks.build_tasks.build_docker_image",
                args=[build_id, build_data, context_path, image_tag, dockerfile],
                task_id=build_id,
            )

            logger.info(f"Started Docker build {build_id} for image {image_tag}")
            return build_id

        except Exception as e:
            logger.error(f"Failed to start Docker build: {e}")
            raise

    async def start_mcp_project_build(
        self,
        project_id: int,
        project_data: Dict,
        build_options: Optional[Dict] = None,
    ) -> str:
        """Start an MCP project build"""
        build_id = str(uuid.uuid4())

        try:
            # Create build job data
            build_data = {
                "build_id": build_id,
                "type": "mcp_project_build",
                "project_id": project_id,
                "project_data": project_data,
                "build_options": build_options or {},
                "status": BuildStatus.PENDING,
                "created_at": datetime.utcnow().isoformat(),
            }

            # Store build info in Redis
            await self.redis.set(f"build:{build_id}", build_data, expire=3600)

            # Queue build task
            celery_app.send_task(
                "app.tasks.build_tasks.build_mcp_project",
                args=[build_id, project_id, project_data, build_options],
                task_id=build_id,
            )

            logger.info(f"Started MCP project build {build_id} for project {project_id}")
            return build_id

        except Exception as e:
            logger.error(f"Failed to start MCP project build: {e}")
            raise

    async def get_build_status(self, build_id: str) -> Optional[Dict]:
        """Get build status by ID"""
        try:
            build_data = await self.redis.get(f"build:{build_id}")
            return build_data
        except Exception as e:
            logger.error(f"Failed to get build status for {build_id}: {e}")
            return None

    async def list_builds(
        self,
        status_filter: Optional[BuildStatus] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """List builds with optional status filter"""
        try:
            if not self.redis.redis:
                return []

            # Get all build keys
            build_keys = await self.redis.redis.keys("build:*")
            builds = []

            for key in build_keys:
                build_data = await self.redis.get(key)
                if build_data:
                    # Apply status filter if specified
                    if status_filter and build_data.get("status") != status_filter:
                        continue
                    builds.append(build_data)

            # Sort by creation time (newest first)
            builds.sort(
                key=lambda x: x.get("created_at", ""), reverse=True
            )

            return builds[:limit]

        except Exception as e:
            logger.error(f"Failed to list builds: {e}")
            return []

    async def cancel_build(self, build_id: str) -> bool:
        """Cancel a pending or running build"""
        try:
            # Get build status
            build_data = await self.redis.get(f"build:{build_id}")
            if not build_data:
                return False

            current_status = build_data.get("status")
            if current_status in [BuildStatus.SUCCESS, BuildStatus.FAILED]:
                return False  # Already completed

            # Revoke Celery task
            celery_app.control.revoke(build_id, terminate=True)

            # Update build status
            build_data.update({
                "status": BuildStatus.FAILED,
                "error": "Build cancelled by user",
                "completed_at": datetime.utcnow().isoformat(),
            })

            await self.redis.set(f"build:{build_id}", build_data, expire=3600)

            # Publish cancellation event
            await self.redis.publish_event(
                f"build:{build_id}",
                {
                    "type": "build_cancelled",
                    "build_id": build_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            logger.info(f"Cancelled build {build_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel build {build_id}: {e}")
            return False

    async def get_build_logs(self, build_id: str) -> List[str]:
        """Get build logs for a specific build"""
        try:
            build_data = await self.redis.get(f"build:{build_id}")
            if build_data:
                return build_data.get("logs", [])
            return []
        except Exception as e:
            logger.error(f"Failed to get build logs for {build_id}: {e}")
            return []

    async def get_queue_status(self) -> Dict:
        """Get build queue status"""
        try:
            # Use Celery task to get queue status
            result = celery_app.send_task("app.tasks.build_tasks.get_build_queue_status")
            return result.get(timeout=5)
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            return {"error": str(e)}

    async def cleanup_old_builds(self, days: int = 7) -> int:
        """Clean up builds older than specified days"""
        try:
            if not self.redis.redis:
                return 0

            # Get all build keys
            build_keys = await self.redis.redis.keys("build:*")
            cleanup_count = 0

            for key in build_keys:
                build_data = await self.redis.get(key)
                if build_data and isinstance(build_data, dict):
                    # Check if build is old enough
                    created_at = build_data.get("created_at")
                    if created_at:
                        from datetime import timedelta
                        created_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        if datetime.utcnow() - created_time > timedelta(days=days):
                            await self.redis.delete(key)
                            cleanup_count += 1

            logger.info(f"Cleaned up {cleanup_count} old builds")
            return cleanup_count

        except Exception as e:
            logger.error(f"Failed to cleanup old builds: {e}")
            return 0

    async def retry_failed_build(self, build_id: str) -> Optional[str]:
        """Retry a failed build"""
        try:
            # Get original build data
            build_data = await self.redis.get(f"build:{build_id}")
            if not build_data:
                return None

            if build_data.get("status") != BuildStatus.FAILED:
                return None  # Can only retry failed builds

            # Create new build with same parameters
            build_type = build_data.get("type")
            if build_type == "docker_build":
                return await self.start_docker_build(
                    build_data["context_path"],
                    build_data["image_tag"],
                    build_data.get("dockerfile", "Dockerfile"),
                    build_data.get("build_args"),
                )
            elif build_type == "mcp_project_build":
                return await self.start_mcp_project_build(
                    build_data["project_id"],
                    build_data["project_data"],
                    build_data.get("build_options"),
                )

            return None

        except Exception as e:
            logger.error(f"Failed to retry build {build_id}: {e}")
            return None


# Global build manager instance
build_manager = BuildManager()


def get_build_manager() -> BuildManager:
    """Dependency to get build manager"""
    return build_manager