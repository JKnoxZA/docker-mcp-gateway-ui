import asyncio
import json
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

import docker
import docker.errors

from app.config.settings import settings
from app.utils.docker_exceptions import (
    map_docker_error,
    is_recoverable_error,
    DockerConnectionError,
    DockerManagerException,
)
from app.utils.retry import retry_async, circuit_breaker

logger = logging.getLogger(__name__)


class DockerManager:
    """Docker operations manager for container and image management"""

    def __init__(self):
        self.client: Optional[docker.DockerClient] = None
        self._connection_retry_count = 0
        self._max_connection_retries = 3
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Docker client with retry logic"""
        for attempt in range(self._max_connection_retries):
            try:
                # Try to connect to Docker daemon
                self.client = docker.from_env(timeout=settings.DOCKER_TIMEOUT)
                # Test connection
                self.client.ping()
                logger.info("Docker client initialized successfully")
                self._connection_retry_count = 0
                return
            except docker.errors.DockerException as e:
                self._connection_retry_count += 1
                mapped_error = map_docker_error(e)

                if attempt < self._max_connection_retries - 1:
                    delay = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        f"Docker connection attempt {attempt + 1} failed: {mapped_error}. "
                        f"Retrying in {delay}s..."
                    )
                    import time
                    time.sleep(delay)
                else:
                    logger.error(f"Failed to initialize Docker client after {self._max_connection_retries} attempts: {mapped_error}")
                    self.client = None

    @retry_async(
        max_attempts=3,
        delay=1.0,
        exceptions=(docker.errors.DockerException, docker.errors.APIError),
        condition=is_recoverable_error
    )
    async def _ensure_connection(self):
        """Ensure Docker client is connected, reconnect if necessary"""
        if not self.client:
            raise DockerConnectionError("Docker client not initialized")

        try:
            # Test connection with ping
            await asyncio.to_thread(self.client.ping)
        except docker.errors.DockerException as e:
            logger.warning(f"Docker connection test failed: {e}, attempting reconnection...")
            self._initialize_client()
            if not self.client:
                raise DockerConnectionError("Failed to reconnect to Docker daemon")

    def is_connected(self) -> bool:
        """Check if Docker client is connected"""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except docker.errors.DockerException as e:
            logger.debug(f"Docker connection check failed: {e}")
            return False

    # Container Management Methods
    @circuit_breaker(failure_threshold=5, recovery_timeout=60.0)
    @retry_async(
        max_attempts=3,
        delay=1.0,
        exceptions=(docker.errors.APIError, docker.errors.DockerException),
        condition=is_recoverable_error
    )
    async def list_containers(
        self, all_containers: bool = True
    ) -> List[Dict[str, Any]]:
        """List Docker containers with enhanced error handling"""
        try:
            await self._ensure_connection()

            containers = await asyncio.to_thread(
                self.client.containers.list, all=all_containers
            )

            container_list = []
            for container in containers:
                try:
                    # Safely extract container information
                    container_info = {
                        "id": container.id[:12] if container.id else "unknown",
                        "name": container.name or "unnamed",
                        "image": self._safe_get_image_name(container),
                        "status": container.status or "unknown",
                        "created": container.attrs.get("Created", "unknown"),
                        "ports": container.ports or {},
                        "labels": container.labels or {},
                        "state": container.attrs.get("State", {}),
                        "mounts": self._safe_get_mounts(container),
                    }
                    container_list.append(container_info)
                except Exception as e:
                    logger.warning(f"Error extracting info for container {container.id}: {e}")
                    # Include minimal info for problematic containers
                    container_list.append({
                        "id": getattr(container, 'id', 'unknown')[:12],
                        "name": getattr(container, 'name', 'error'),
                        "image": "error",
                        "status": "error",
                        "created": "unknown",
                        "ports": {},
                        "labels": {},
                        "state": {},
                        "mounts": [],
                    })

            return container_list

        except docker.errors.DockerException as e:
            mapped_error = map_docker_error(e)
            logger.error(f"Error listing containers: {mapped_error}")
            raise mapped_error

    def _safe_get_image_name(self, container) -> str:
        """Safely extract image name from container"""
        try:
            if hasattr(container, 'image') and container.image:
                if hasattr(container.image, 'tags') and container.image.tags:
                    return container.image.tags[0]
                elif hasattr(container.image, 'id'):
                    return container.image.id[:12]
            return "unknown"
        except Exception:
            return "error"

    def _safe_get_mounts(self, container) -> List[str]:
        """Safely extract mount information from container"""
        try:
            mounts = container.attrs.get("Mounts", [])
            return [
                f"{mount.get('Source', 'unknown')}:{mount.get('Destination', 'unknown')}"
                for mount in mounts
                if isinstance(mount, dict) and mount.get('Source') and mount.get('Destination')
            ]
        except Exception:
            return []

    @retry_async(
        max_attempts=3,
        delay=0.5,
        exceptions=(docker.errors.APIError,),
        condition=is_recoverable_error
    )
    async def get_container(self, container_id: str) -> Dict[str, Any]:
        """Get detailed container information with enhanced error handling"""
        try:
            await self._ensure_connection()

            container = await asyncio.to_thread(
                self.client.containers.get, container_id
            )

            # Safely extract detailed container information
            return {
                "id": container.id or "unknown",
                "name": container.name or "unnamed",
                "image": self._safe_get_image_name(container),
                "status": container.status or "unknown",
                "created": container.attrs.get("Created", "unknown"),
                "started": container.attrs.get("State", {}).get("StartedAt", "unknown"),
                "ports": container.ports or {},
                "environment": container.attrs.get("Config", {}).get("Env", []),
                "mounts": container.attrs.get("Mounts", []),
                "network_settings": container.attrs.get("NetworkSettings", {}),
                "state": container.attrs.get("State", {}),
                "logs_path": container.attrs.get("LogPath", ""),
            }

        except docker.errors.NotFound:
            raise docker.errors.NotFound(f"Container {container_id} not found")
        except docker.errors.DockerException as e:
            mapped_error = map_docker_error(e)
            logger.error(f"Error getting container {container_id}: {mapped_error}")
            raise mapped_error

    @retry_async(
        max_attempts=2,
        delay=1.0,
        exceptions=(docker.errors.APIError,),
        condition=is_recoverable_error
    )
    async def start_container(self, container_id: str) -> Dict[str, str]:
        """Start a Docker container with enhanced error handling"""
        try:
            await self._ensure_connection()

            container = await asyncio.to_thread(
                self.client.containers.get, container_id
            )

            # Check current status before attempting to start
            current_status = container.status
            if current_status == "running":
                logger.info(f"Container {container_id} is already running")
                return {
                    "container_id": container_id,
                    "status": "already_running",
                    "message": f"Container {container_id} is already running",
                }

            await asyncio.to_thread(container.start)

            # Verify the container started successfully
            await asyncio.sleep(0.5)  # Brief delay to allow container to start
            container.reload()
            final_status = container.status

            return {
                "container_id": container_id,
                "status": "started" if final_status == "running" else "start_attempted",
                "message": f"Container {container_id} start {'successful' if final_status == 'running' else 'attempted'} (status: {final_status})",
            }

        except docker.errors.NotFound:
            raise docker.errors.NotFound(f"Container {container_id} not found")
        except docker.errors.DockerException as e:
            mapped_error = map_docker_error(e)
            logger.error(f"Error starting container {container_id}: {mapped_error}")
            raise mapped_error

    async def stop_container(
        self, container_id: str, timeout: int = 10
    ) -> Dict[str, str]:
        """Stop a Docker container"""
        if not self.client:
            raise docker.errors.DockerException("Docker client not available")

        try:
            container = await asyncio.to_thread(
                self.client.containers.get, container_id
            )
            await asyncio.to_thread(container.stop, timeout=timeout)

            return {
                "container_id": container_id,
                "status": "stopped",
                "message": f"Container {container_id} stopped successfully",
            }
        except docker.errors.NotFound:
            raise docker.errors.NotFound(f"Container {container_id} not found")
        except docker.errors.DockerException as e:
            logger.error(f"Error stopping container {container_id}: {e}")
            raise

    async def restart_container(
        self, container_id: str, timeout: int = 10
    ) -> Dict[str, str]:
        """Restart a Docker container"""
        if not self.client:
            raise docker.errors.DockerException("Docker client not available")

        try:
            container = await asyncio.to_thread(
                self.client.containers.get, container_id
            )
            await asyncio.to_thread(container.restart, timeout=timeout)

            return {
                "container_id": container_id,
                "status": "restarted",
                "message": f"Container {container_id} restarted successfully",
            }
        except docker.errors.NotFound:
            raise docker.errors.NotFound(f"Container {container_id} not found")
        except docker.errors.DockerException as e:
            logger.error(f"Error restarting container {container_id}: {e}")
            raise

    async def remove_container(
        self, container_id: str, force: bool = False
    ) -> Dict[str, str]:
        """Remove a Docker container"""
        if not self.client:
            raise docker.errors.DockerException("Docker client not available")

        try:
            container = await asyncio.to_thread(
                self.client.containers.get, container_id
            )
            await asyncio.to_thread(container.remove, force=force)

            return {
                "container_id": container_id,
                "status": "removed",
                "message": f"Container {container_id} removed successfully",
            }
        except docker.errors.NotFound:
            raise docker.errors.NotFound(f"Container {container_id} not found")
        except docker.errors.DockerException as e:
            logger.error(f"Error removing container {container_id}: {e}")
            raise

    async def get_container_logs(
        self, container_id: str, tail: int = 100, follow: bool = False
    ) -> AsyncGenerator[str, None]:
        """Get container logs"""
        if not self.client:
            raise docker.errors.DockerException("Docker client not available")

        try:
            container = await asyncio.to_thread(
                self.client.containers.get, container_id
            )

            if follow:
                # Stream logs in real-time
                logs_generator = container.logs(stream=True, follow=True, tail=tail)
                for log_line in logs_generator:
                    yield log_line.decode("utf-8").strip()
            else:
                # Get static logs
                logs = await asyncio.to_thread(
                    container.logs, tail=tail, timestamps=True
                )
                for line in logs.decode("utf-8").split("\n"):
                    if line.strip():
                        yield line.strip()

        except docker.errors.NotFound:
            raise docker.errors.NotFound(f"Container {container_id} not found")
        except docker.errors.DockerException as e:
            logger.error(f"Error getting logs for container {container_id}: {e}")
            raise

    # Image Management Methods
    async def list_images(self) -> List[Dict[str, Any]]:
        """List Docker images"""
        if not self.client:
            raise docker.errors.DockerException("Docker client not available")

        try:
            images = await asyncio.to_thread(self.client.images.list)

            image_list = []
            for image in images:
                image_info = {
                    "id": image.id[:12],
                    "tags": image.tags,
                    "created": image.attrs["Created"],
                    "size": image.attrs["Size"],
                    "labels": image.attrs["Config"].get("Labels") or {},
                    "architecture": image.attrs.get("Architecture", "unknown"),
                    "os": image.attrs.get("Os", "unknown"),
                }
                image_list.append(image_info)

            return image_list
        except docker.errors.DockerException as e:
            logger.error(f"Error listing images: {e}")
            raise

    async def build_image(
        self, path: str, tag: str, dockerfile: str = "Dockerfile"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Build Docker image from path"""
        if not self.client:
            raise docker.errors.DockerException("Docker client not available")

        try:
            # Build image with streaming output
            build_logs = self.client.api.build(
                path=path,
                tag=tag,
                dockerfile=dockerfile,
                rm=True,
                stream=True,
                decode=True,
            )

            for log_entry in build_logs:
                if "stream" in log_entry:
                    yield {
                        "status": "building",
                        "message": log_entry["stream"].strip(),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                elif "error" in log_entry:
                    yield {
                        "status": "error",
                        "message": log_entry["error"],
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    return

            yield {
                "status": "completed",
                "message": f"Image {tag} built successfully",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except docker.errors.BuildError as e:
            logger.error(f"Error building image {tag}: {e}")
            yield {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except docker.errors.DockerException as e:
            logger.error(f"Docker error building image {tag}: {e}")
            yield {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def remove_image(self, image_id: str, force: bool = False) -> Dict[str, str]:
        """Remove a Docker image"""
        if not self.client:
            raise docker.errors.DockerException("Docker client not available")

        try:
            await asyncio.to_thread(self.client.images.remove, image_id, force=force)

            return {
                "image_id": image_id,
                "status": "removed",
                "message": f"Image {image_id} removed successfully",
            }
        except docker.errors.ImageNotFound:
            raise docker.errors.ImageNotFound(f"Image {image_id} not found")
        except docker.errors.DockerException as e:
            logger.error(f"Error removing image {image_id}: {e}")
            raise

    # Network Management Methods
    async def list_networks(self) -> List[Dict[str, Any]]:
        """List Docker networks"""
        if not self.client:
            raise docker.errors.DockerException("Docker client not available")

        try:
            networks = await asyncio.to_thread(self.client.networks.list)

            network_list = []
            for network in networks:
                network_info = {
                    "id": network.id[:12],
                    "name": network.name,
                    "driver": network.attrs["Driver"],
                    "scope": network.attrs["Scope"],
                    "created": network.attrs["Created"],
                    "containers": list(network.attrs.get("Containers", {}).keys()),
                }
                network_list.append(network_info)

            return network_list
        except docker.errors.DockerException as e:
            logger.error(f"Error listing networks: {e}")
            raise

    # Volume Management Methods
    async def list_volumes(self) -> List[Dict[str, Any]]:
        """List Docker volumes"""
        if not self.client:
            raise docker.errors.DockerException("Docker client not available")

        try:
            volumes = await asyncio.to_thread(self.client.volumes.list)

            volume_list = []
            for volume in volumes:
                volume_info = {
                    "name": volume.name,
                    "driver": volume.attrs["Driver"],
                    "mountpoint": volume.attrs["Mountpoint"],
                    "created": volume.attrs["CreatedAt"],
                    "labels": volume.attrs.get("Labels") or {},
                    "scope": volume.attrs["Scope"],
                }
                volume_list.append(volume_info)

            return volume_list
        except docker.errors.DockerException as e:
            logger.error(f"Error listing volumes: {e}")
            raise

    # System Information Methods
    async def get_system_info(self) -> Dict[str, Any]:
        """Get Docker system information"""
        if not self.client:
            raise docker.errors.DockerException("Docker client not available")

        try:
            info = await asyncio.to_thread(self.client.info)
            return {
                "containers": info.get("Containers", 0),
                "containers_running": info.get("ContainersRunning", 0),
                "containers_paused": info.get("ContainersPaused", 0),
                "containers_stopped": info.get("ContainersStopped", 0),
                "images": info.get("Images", 0),
                "server_version": info.get("ServerVersion", "unknown"),
                "architecture": info.get("Architecture", "unknown"),
                "os": info.get("OperatingSystem", "unknown"),
                "total_memory": info.get("MemTotal", 0),
                "cpu_count": info.get("NCPU", 0),
                "storage_driver": info.get("Driver", "unknown"),
            }
        except docker.errors.DockerException as e:
            logger.error(f"Error getting system info: {e}")
            raise


# Global Docker manager instance
docker_manager = DockerManager()


def get_docker_manager() -> DockerManager:
    """Dependency to get Docker manager"""
    return docker_manager
