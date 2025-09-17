import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app
from app.core.docker_manager import DockerManager

client = TestClient(app)


@pytest.fixture
def mock_docker_manager():
    """Mock Docker manager for testing"""
    with patch('app.api.docker.routes.get_docker_manager') as mock_get_manager:
        mock_manager = AsyncMock(spec=DockerManager)
        mock_get_manager.return_value = mock_manager
        yield mock_manager


class TestContainerEndpoints:
    """Test container management endpoints"""

    def test_list_containers_success(self, mock_docker_manager):
        """Test successful container listing"""
        # Mock data
        mock_containers = [
            {
                "id": "abc123",
                "name": "test-container",
                "image": "nginx:latest",
                "status": "running",
                "created": "2024-01-01T00:00:00Z",
                "ports": {"80/tcp": [{"HostPort": "8080"}]},
                "labels": {"app": "test"},
                "state": {"Status": "running"},
                "mounts": []
            }
        ]
        mock_docker_manager.list_containers.return_value = mock_containers

        # Make request
        response = client.get("/api/docker/containers/")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "test-container"
        mock_docker_manager.list_containers.assert_called_once_with(True)

    def test_list_containers_filter_running_only(self, mock_docker_manager):
        """Test listing containers with running only filter"""
        mock_docker_manager.list_containers.return_value = []

        response = client.get("/api/docker/containers/?all_containers=false")

        assert response.status_code == status.HTTP_200_OK
        mock_docker_manager.list_containers.assert_called_once_with(False)

    def test_get_container_details_success(self, mock_docker_manager):
        """Test successful container details retrieval"""
        mock_container = {
            "id": "abc123",
            "name": "test-container",
            "image": "nginx:latest",
            "status": "running",
            "created": "2024-01-01T00:00:00Z",
            "started": "2024-01-01T00:01:00Z",
            "ports": {},
            "environment": ["PATH=/usr/bin"],
            "mounts": [],
            "network_settings": {},
            "state": {"Status": "running"},
            "logs_path": "/var/log/container.log"
        }
        mock_docker_manager.get_container.return_value = mock_container

        response = client.get("/api/docker/containers/abc123")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "test-container"
        mock_docker_manager.get_container.assert_called_once_with("abc123")

    def test_get_container_not_found(self, mock_docker_manager):
        """Test container not found error"""
        import docker.errors
        mock_docker_manager.get_container.side_effect = docker.errors.NotFound("Container not found")

        response = client.get("/api/docker/containers/nonexistent")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]

    def test_start_container_success(self, mock_docker_manager):
        """Test successful container start"""
        mock_result = {
            "container_id": "abc123",
            "status": "started",
            "message": "Container abc123 started successfully"
        }
        mock_docker_manager.start_container.return_value = mock_result

        response = client.post("/api/docker/containers/abc123/start")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "started"
        mock_docker_manager.start_container.assert_called_once_with("abc123")

    def test_stop_container_success(self, mock_docker_manager):
        """Test successful container stop"""
        mock_result = {
            "container_id": "abc123",
            "status": "stopped",
            "message": "Container abc123 stopped successfully"
        }
        mock_docker_manager.stop_container.return_value = mock_result

        response = client.post("/api/docker/containers/abc123/stop", json={"timeout": 30})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "stopped"
        mock_docker_manager.stop_container.assert_called_once_with("abc123", 30)

    def test_restart_container_success(self, mock_docker_manager):
        """Test successful container restart"""
        mock_result = {
            "container_id": "abc123",
            "status": "restarted",
            "message": "Container abc123 restarted successfully"
        }
        mock_docker_manager.restart_container.return_value = mock_result

        response = client.post("/api/docker/containers/abc123/restart", json={"timeout": 15})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "restarted"
        mock_docker_manager.restart_container.assert_called_once_with("abc123", 15)

    def test_remove_container_success(self, mock_docker_manager):
        """Test successful container removal"""
        mock_result = {
            "container_id": "abc123",
            "status": "removed",
            "message": "Container abc123 removed successfully"
        }
        mock_docker_manager.remove_container.return_value = mock_result

        response = client.delete("/api/docker/containers/abc123", json={"force": True})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "removed"
        mock_docker_manager.remove_container.assert_called_once_with("abc123", True)

    def test_get_container_logs_success(self, mock_docker_manager):
        """Test successful container logs retrieval"""
        async def mock_logs_generator():
            yield "Log line 1"
            yield "Log line 2"
            yield "Log line 3"

        mock_docker_manager.get_container_logs.return_value = mock_logs_generator()

        response = client.get("/api/docker/containers/abc123/logs?tail=100&follow=false")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "logs" in data
        # Note: In real async test, we'd need to handle the async generator properly


class TestImageEndpoints:
    """Test image management endpoints"""

    def test_list_images_success(self, mock_docker_manager):
        """Test successful image listing"""
        mock_images = [
            {
                "id": "img123",
                "tags": ["nginx:latest"],
                "created": "2024-01-01T00:00:00Z",
                "size": 1024000,
                "labels": {"version": "1.0"},
                "architecture": "amd64",
                "os": "linux"
            }
        ]
        mock_docker_manager.list_images.return_value = mock_images

        response = client.get("/api/docker/images/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["tags"] == ["nginx:latest"]
        mock_docker_manager.list_images.assert_called_once()

    def test_remove_image_success(self, mock_docker_manager):
        """Test successful image removal"""
        mock_result = {
            "image_id": "img123",
            "status": "removed",
            "message": "Image img123 removed successfully"
        }
        mock_docker_manager.remove_image.return_value = mock_result

        response = client.delete("/api/docker/images/img123?force=true")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "removed"
        mock_docker_manager.remove_image.assert_called_once_with("img123", True)

    def test_remove_image_not_found(self, mock_docker_manager):
        """Test image not found error"""
        import docker.errors
        mock_docker_manager.remove_image.side_effect = docker.errors.ImageNotFound("Image not found")

        response = client.delete("/api/docker/images/nonexistent")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]


class TestNetworkAndVolumeEndpoints:
    """Test network and volume endpoints"""

    def test_list_networks_success(self, mock_docker_manager):
        """Test successful network listing"""
        mock_networks = [
            {
                "id": "net123",
                "name": "bridge",
                "driver": "bridge",
                "scope": "local",
                "created": "2024-01-01T00:00:00Z",
                "containers": ["abc123"]
            }
        ]
        mock_docker_manager.list_networks.return_value = mock_networks

        response = client.get("/api/docker/networks/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "bridge"

    def test_list_volumes_success(self, mock_docker_manager):
        """Test successful volume listing"""
        mock_volumes = [
            {
                "name": "vol123",
                "driver": "local",
                "mountpoint": "/var/lib/docker/volumes/vol123",
                "created": "2024-01-01T00:00:00Z",
                "labels": {},
                "scope": "local"
            }
        ]
        mock_docker_manager.list_volumes.return_value = mock_volumes

        response = client.get("/api/docker/volumes/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "vol123"


class TestSystemEndpoints:
    """Test system information endpoints"""

    def test_get_system_info_success(self, mock_docker_manager):
        """Test successful system info retrieval"""
        mock_info = {
            "containers": 10,
            "containers_running": 5,
            "containers_paused": 1,
            "containers_stopped": 4,
            "images": 20,
            "server_version": "20.10.0",
            "architecture": "x86_64",
            "os": "linux",
            "total_memory": 8589934592,
            "cpu_count": 4,
            "storage_driver": "overlay2"
        }
        mock_docker_manager.get_system_info.return_value = mock_info

        response = client.get("/api/docker/system/info")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["containers"] == 10
        assert data["server_version"] == "20.10.0"

    def test_docker_health_check_success(self, mock_docker_manager):
        """Test successful Docker health check"""
        mock_docker_manager.is_connected.return_value = True

        response = client.get("/api/docker/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"

    def test_docker_health_check_failure(self, mock_docker_manager):
        """Test Docker health check failure"""
        mock_docker_manager.is_connected.return_value = False

        response = client.get("/api/docker/health")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "not accessible" in response.json()["detail"]


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_docker_exception_handling(self, mock_docker_manager):
        """Test general Docker exception handling"""
        import docker.errors
        mock_docker_manager.list_containers.side_effect = docker.errors.DockerException("Docker daemon error")

        response = client.get("/api/docker/containers/")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Docker error" in response.json()["detail"]

    def test_unexpected_exception_handling(self, mock_docker_manager):
        """Test unexpected exception handling"""
        mock_docker_manager.list_containers.side_effect = Exception("Unexpected error")

        response = client.get("/api/docker/containers/")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR