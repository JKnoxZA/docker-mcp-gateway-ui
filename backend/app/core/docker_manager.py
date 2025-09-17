import docker
import docker.errors
import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import json

from app.config.settings import settings

logger = logging.getLogger(__name__)


class DockerManager:
    """Docker operations manager for container and image management"""

    def __init__(self):
        self.client: Optional[docker.DockerClient] = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Docker client"""
        try:
            # Try to connect to Docker daemon
            self.client = docker.from_env(timeout=settings.DOCKER_TIMEOUT)
            # Test connection
            self.client.ping()
            logger.info("Docker client initialized successfully")
        except docker.errors.DockerException as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None

    def is_connected(self) -> bool:
        """Check if Docker client is connected"""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except docker.errors.DockerException:
            return False

    # Container Management Methods
    async def list_containers(self, all_containers: bool = True) -> List[Dict[str, Any]]:
        """List Docker containers"""
        if not self.client:
            raise docker.errors.DockerException("Docker client not available")

        try:
            containers = await asyncio.to_thread(
                self.client.containers.list, all=all_containers
            )

            container_list = []
            for container in containers:
                container_info = {
                    "id": container.id[:12],
                    "name": container.name,
                    "image": container.image.tags[0] if container.image.tags else "unknown",
                    "status": container.status,
                    "created": container.attrs["Created"],
                    "ports": container.ports,
                    "labels": container.labels,
                    "state": container.attrs.get("State", {}),
                    "mounts": [mount["Source"] + ":" + mount["Destination"]
                              for mount in container.attrs.get("Mounts", [])]
                }
                container_list.append(container_info)

            return container_list
        except docker.errors.DockerException as e:
            logger.error(f"Error listing containers: {e}")
            raise

    async def get_container(self, container_id: str) -> Dict[str, Any]:
        """Get detailed container information"""
        if not self.client:
            raise docker.errors.DockerException("Docker client not available")

        try:
            container = await asyncio.to_thread(
                self.client.containers.get, container_id
            )

            return {
                "id": container.id,
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "status": container.status,
                "created": container.attrs["Created"],
                "started": container.attrs["State"].get("StartedAt"),
                "ports": container.ports,
                "environment": container.attrs["Config"].get("Env", []),
                "mounts": container.attrs.get("Mounts", []),
                "network_settings": container.attrs.get("NetworkSettings", {}),
                "state": container.attrs.get("State", {}),
                "logs_path": container.attrs.get("LogPath", "")
            }
        except docker.errors.NotFound:
            raise docker.errors.NotFound(f"Container {container_id} not found")
        except docker.errors.DockerException as e:
            logger.error(f"Error getting container {container_id}: {e}")
            raise

    async def start_container(self, container_id: str) -> Dict[str, str]:
        """Start a Docker container"""
        if not self.client:
            raise docker.errors.DockerException("Docker client not available")

        try:
            container = await asyncio.to_thread(
                self.client.containers.get, container_id
            )
            await asyncio.to_thread(container.start)

            return {
                "container_id": container_id,
                "status": "started",
                "message": f"Container {container_id} started successfully"
            }
        except docker.errors.NotFound:
            raise docker.errors.NotFound(f"Container {container_id} not found")
        except docker.errors.DockerException as e:
            logger.error(f"Error starting container {container_id}: {e}")
            raise

    async def stop_container(self, container_id: str, timeout: int = 10) -> Dict[str, str]:
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
                "message": f"Container {container_id} stopped successfully"
            }
        except docker.errors.NotFound:
            raise docker.errors.NotFound(f"Container {container_id} not found")
        except docker.errors.DockerException as e:
            logger.error(f"Error stopping container {container_id}: {e}")
            raise

    async def restart_container(self, container_id: str, timeout: int = 10) -> Dict[str, str]:
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
                "message": f"Container {container_id} restarted successfully"
            }
        except docker.errors.NotFound:
            raise docker.errors.NotFound(f"Container {container_id} not found")
        except docker.errors.DockerException as e:
            logger.error(f"Error restarting container {container_id}: {e}")
            raise

    async def remove_container(self, container_id: str, force: bool = False) -> Dict[str, str]:
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
                "message": f"Container {container_id} removed successfully"
            }
        except docker.errors.NotFound:
            raise docker.errors.NotFound(f"Container {container_id} not found")
        except docker.errors.DockerException as e:
            logger.error(f"Error removing container {container_id}: {e}")
            raise

    async def get_container_logs(self, container_id: str, tail: int = 100, follow: bool = False) -> AsyncGenerator[str, None]:
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
                    yield log_line.decode('utf-8').strip()
            else:
                # Get static logs
                logs = await asyncio.to_thread(
                    container.logs, tail=tail, timestamps=True
                )
                for line in logs.decode('utf-8').split('\n'):
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
                    "os": image.attrs.get("Os", "unknown")
                }
                image_list.append(image_info)

            return image_list
        except docker.errors.DockerException as e:
            logger.error(f"Error listing images: {e}")
            raise

    async def build_image(self, path: str, tag: str, dockerfile: str = "Dockerfile") -> AsyncGenerator[Dict[str, Any], None]:
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
                decode=True
            )

            for log_entry in build_logs:
                if 'stream' in log_entry:
                    yield {
                        "status": "building",
                        "message": log_entry['stream'].strip(),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                elif 'error' in log_entry:
                    yield {
                        "status": "error",
                        "message": log_entry['error'],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    return

            yield {
                "status": "completed",
                "message": f"Image {tag} built successfully",
                "timestamp": datetime.utcnow().isoformat()
            }

        except docker.errors.BuildError as e:
            logger.error(f"Error building image {tag}: {e}")
            yield {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        except docker.errors.DockerException as e:
            logger.error(f"Docker error building image {tag}: {e}")
            yield {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def remove_image(self, image_id: str, force: bool = False) -> Dict[str, str]:
        """Remove a Docker image"""
        if not self.client:
            raise docker.errors.DockerException("Docker client not available")

        try:
            await asyncio.to_thread(
                self.client.images.remove, image_id, force=force
            )

            return {
                "image_id": image_id,
                "status": "removed",
                "message": f"Image {image_id} removed successfully"
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
                    "containers": list(network.attrs.get("Containers", {}).keys())
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
                    "scope": volume.attrs["Scope"]
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
                "storage_driver": info.get("Driver", "unknown")
            }
        except docker.errors.DockerException as e:
            logger.error(f"Error getting system info: {e}")
            raise


# Global Docker manager instance
docker_manager = DockerManager()


def get_docker_manager() -> DockerManager:
    """Dependency to get Docker manager"""
    return docker_manager