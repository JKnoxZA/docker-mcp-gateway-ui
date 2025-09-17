import logging
from typing import List, Optional

import docker.errors
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.docker_manager import DockerManager, get_docker_manager
from app.models.schemas import (
    ContainerAction,
    ContainerActionResponse,
    ContainerDetails,
    ContainerInfo,
    ImageActionResponse,
    ImageBuildRequest,
    ImageBuildResponse,
    ImageInfo,
    NetworkInfo,
    SystemInfo,
    VolumeInfo,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# Container Management Endpoints
@router.get("/containers/", response_model=List[ContainerInfo])
async def list_containers(
    all_containers: bool = Query(default=True, description="Include stopped containers"),
    docker_manager: DockerManager = Depends(get_docker_manager),
):
    """List Docker containers"""
    try:
        containers = await docker_manager.list_containers(all_containers)
        return containers
    except docker.errors.DockerException as e:
        logger.error(f"Error listing containers: {e}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")


@router.get("/containers/{container_id}", response_model=ContainerDetails)
async def get_container_details(
    container_id: str,
    docker_manager: DockerManager = Depends(get_docker_manager),
):
    """Get detailed container information"""
    try:
        container = await docker_manager.get_container(container_id)
        return container
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Container {container_id} not found")
    except docker.errors.DockerException as e:
        logger.error(f"Error getting container {container_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")


@router.post("/containers/{container_id}/start", response_model=ContainerActionResponse)
async def start_container(
    container_id: str,
    docker_manager: DockerManager = Depends(get_docker_manager),
):
    """Start a Docker container"""
    try:
        result = await docker_manager.start_container(container_id)
        return result
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Container {container_id} not found")
    except docker.errors.DockerException as e:
        logger.error(f"Error starting container {container_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")


@router.post("/containers/{container_id}/stop", response_model=ContainerActionResponse)
async def stop_container(
    container_id: str,
    action: ContainerAction = ContainerAction(),
    docker_manager: DockerManager = Depends(get_docker_manager),
):
    """Stop a Docker container"""
    try:
        result = await docker_manager.stop_container(container_id, action.timeout)
        return result
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Container {container_id} not found")
    except docker.errors.DockerException as e:
        logger.error(f"Error stopping container {container_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")


@router.post("/containers/{container_id}/restart", response_model=ContainerActionResponse)
async def restart_container(
    container_id: str,
    action: ContainerAction = ContainerAction(),
    docker_manager: DockerManager = Depends(get_docker_manager),
):
    """Restart a Docker container"""
    try:
        result = await docker_manager.restart_container(container_id, action.timeout)
        return result
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Container {container_id} not found")
    except docker.errors.DockerException as e:
        logger.error(f"Error restarting container {container_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")


@router.delete("/containers/{container_id}", response_model=ContainerActionResponse)
async def remove_container(
    container_id: str,
    action: ContainerAction = ContainerAction(),
    docker_manager: DockerManager = Depends(get_docker_manager),
):
    """Remove a Docker container"""
    try:
        result = await docker_manager.remove_container(container_id, action.force)
        return result
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Container {container_id} not found")
    except docker.errors.DockerException as e:
        logger.error(f"Error removing container {container_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")


@router.get("/containers/{container_id}/logs")
async def get_container_logs(
    container_id: str,
    tail: int = Query(default=100, ge=1, le=10000, description="Number of lines to tail"),
    follow: bool = Query(default=False, description="Follow logs in real-time"),
    docker_manager: DockerManager = Depends(get_docker_manager),
):
    """Get container logs"""
    try:
        if follow:
            # Stream logs in real-time
            async def log_generator():
                async for log_line in docker_manager.get_container_logs(
                    container_id, tail=tail, follow=True
                ):
                    yield f"{log_line}\n"

            return StreamingResponse(
                log_generator(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache"},
            )
        else:
            # Get static logs
            logs = []
            async for log_line in docker_manager.get_container_logs(
                container_id, tail=tail, follow=False
            ):
                logs.append(log_line)
            return {"logs": logs}

    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Container {container_id} not found")
    except docker.errors.DockerException as e:
        logger.error(f"Error getting logs for container {container_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")


# Image Management Endpoints
@router.get("/images/", response_model=List[ImageInfo])
async def list_images(
    docker_manager: DockerManager = Depends(get_docker_manager),
):
    """List Docker images"""
    try:
        images = await docker_manager.list_images()
        return images
    except docker.errors.DockerException as e:
        logger.error(f"Error listing images: {e}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")


@router.post("/images/build")
async def build_image(
    build_request: ImageBuildRequest,
    docker_manager: DockerManager = Depends(get_docker_manager),
):
    """Build Docker image from path"""
    try:
        # Stream build output
        async def build_generator():
            async for build_log in docker_manager.build_image(
                build_request.path, build_request.tag, build_request.dockerfile
            ):
                import json
                yield f"data: {json.dumps(build_log)}\n\n"

        return StreamingResponse(
            build_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )

    except docker.errors.DockerException as e:
        logger.error(f"Error building image {build_request.tag}: {e}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")


@router.delete("/images/{image_id}", response_model=ImageActionResponse)
async def remove_image(
    image_id: str,
    force: bool = Query(default=False, description="Force removal of image"),
    docker_manager: DockerManager = Depends(get_docker_manager),
):
    """Remove a Docker image"""
    try:
        result = await docker_manager.remove_image(image_id, force)
        return result
    except docker.errors.ImageNotFound:
        raise HTTPException(status_code=404, detail=f"Image {image_id} not found")
    except docker.errors.DockerException as e:
        logger.error(f"Error removing image {image_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")


# Network Management Endpoints
@router.get("/networks/", response_model=List[NetworkInfo])
async def list_networks(
    docker_manager: DockerManager = Depends(get_docker_manager),
):
    """List Docker networks"""
    try:
        networks = await docker_manager.list_networks()
        return networks
    except docker.errors.DockerException as e:
        logger.error(f"Error listing networks: {e}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")


# Volume Management Endpoints
@router.get("/volumes/", response_model=List[VolumeInfo])
async def list_volumes(
    docker_manager: DockerManager = Depends(get_docker_manager),
):
    """List Docker volumes"""
    try:
        volumes = await docker_manager.list_volumes()
        return volumes
    except docker.errors.DockerException as e:
        logger.error(f"Error listing volumes: {e}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")


# System Information Endpoints
@router.get("/system/info", response_model=SystemInfo)
async def get_system_info(
    docker_manager: DockerManager = Depends(get_docker_manager),
):
    """Get Docker system information"""
    try:
        info = await docker_manager.get_system_info()
        return info
    except docker.errors.DockerException as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")


@router.get("/health")
async def docker_health_check(
    docker_manager: DockerManager = Depends(get_docker_manager),
):
    """Check Docker daemon health"""
    is_connected = docker_manager.is_connected()
    if is_connected:
        return {"status": "healthy", "message": "Docker daemon is accessible"}
    else:
        raise HTTPException(
            status_code=503, detail="Docker daemon is not accessible"
        )
