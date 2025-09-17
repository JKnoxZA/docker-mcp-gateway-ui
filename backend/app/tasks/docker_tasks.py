import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from celery import Task

from app.core.celery_app import celery_app
from app.core.docker_manager import docker_manager
from app.core.redis import redis_client

logger = logging.getLogger(__name__)


class DockerTask(Task):
    """Custom Celery task class for Docker operations"""

    def on_success(self, retval, task_id, args, kwargs):
        """Called on task success"""
        logger.info(f"Docker task {task_id} completed successfully")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called on task failure"""
        logger.error(f"Docker task {task_id} failed: {exc}")


@celery_app.task(base=DockerTask, bind=True)
def cleanup_docker_resources(self):
    """Clean up unused Docker resources"""
    logger.info("Starting Docker resource cleanup")

    async def _cleanup():
        try:
            cleanup_summary = {
                "images_removed": 0,
                "containers_removed": 0,
                "volumes_removed": 0,
                "networks_removed": 0,
                "space_reclaimed": 0,
            }

            # Clean up stopped containers older than 24 hours
            containers = await docker_manager.list_containers(all_containers=True)
            for container in containers:
                if container["status"] in ["exited", "dead"]:
                    # Check if container is old enough
                    created_time = datetime.fromisoformat(
                        container["created"].replace("Z", "+00:00")
                    )
                    if datetime.utcnow() - created_time > timedelta(hours=24):
                        try:
                            await docker_manager.remove_container(
                                container["id"], force=True
                            )
                            cleanup_summary["containers_removed"] += 1
                            logger.info(f"Removed old container: {container['name']}")
                        except Exception as e:
                            logger.warning(f"Failed to remove container {container['name']}: {e}")

            # Clean up dangling images
            images = await docker_manager.list_images()
            for image in images:
                if not image["tags"] or image["tags"] == ["<none>:<none>"]:
                    try:
                        await docker_manager.remove_image(image["id"], force=True)
                        cleanup_summary["images_removed"] += 1
                        logger.info(f"Removed dangling image: {image['id']}")
                    except Exception as e:
                        logger.warning(f"Failed to remove image {image['id']}: {e}")

            # Log cleanup summary
            logger.info(f"Docker cleanup completed: {cleanup_summary}")

            # Store cleanup report in Redis
            await redis_client.set(
                "docker:last_cleanup",
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "summary": cleanup_summary,
                },
                expire=86400,  # 24 hours
            )

            return cleanup_summary

        except Exception as e:
            logger.error(f"Error during Docker cleanup: {e}")
            raise

    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_cleanup())
    finally:
        loop.close()


@celery_app.task(base=DockerTask, bind=True)
def monitor_container_health(self, container_id: str):
    """Monitor container health and send alerts if needed"""

    async def _monitor():
        try:
            container = await docker_manager.get_container(container_id)

            # Check container health
            state = container.get("state", {})
            health = state.get("Health", {})

            if health:
                status = health.get("Status", "unknown")
                if status == "unhealthy":
                    # Send health alert
                    alert_data = {
                        "type": "container_unhealthy",
                        "container_id": container_id,
                        "container_name": container["name"],
                        "timestamp": datetime.utcnow().isoformat(),
                        "health_status": status,
                    }

                    await redis_client.publish_event("health_alerts", alert_data)
                    logger.warning(f"Container {container['name']} is unhealthy")

            # Store health status
            await redis_client.set(
                f"health:container:{container_id}",
                {
                    "status": state.get("Status", "unknown"),
                    "health": health.get("Status", "unknown") if health else "no_healthcheck",
                    "last_check": datetime.utcnow().isoformat(),
                },
                expire=300,  # 5 minutes
            )

        except Exception as e:
            logger.error(f"Error monitoring container {container_id}: {e}")
            raise

    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_monitor())
    finally:
        loop.close()


@celery_app.task(base=DockerTask, bind=True)
def collect_docker_metrics(self):
    """Collect Docker system metrics"""

    async def _collect_metrics():
        try:
            # Get system info
            system_info = await docker_manager.get_system_info()

            # Get containers
            containers = await docker_manager.list_containers(all_containers=True)

            # Get images
            images = await docker_manager.list_images()

            # Calculate metrics
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "system": system_info,
                "containers": {
                    "total": len(containers),
                    "running": len([c for c in containers if c["status"] == "running"]),
                    "stopped": len([c for c in containers if c["status"] in ["exited", "dead"]]),
                    "paused": len([c for c in containers if c["status"] == "paused"]),
                },
                "images": {
                    "total": len(images),
                    "dangling": len([i for i in images if not i["tags"] or i["tags"] == ["<none>:<none>"]]),
                    "total_size": sum(i["size"] for i in images),
                },
            }

            # Store metrics in Redis
            await redis_client.set(
                "docker:metrics",
                metrics,
                expire=300,  # 5 minutes
            )

            # Keep historical metrics (last 24 hours)
            metric_key = f"docker:metrics:history:{int(datetime.utcnow().timestamp())}"
            await redis_client.set(metric_key, metrics, expire=86400)

            logger.info("Docker metrics collected successfully")
            return metrics

        except Exception as e:
            logger.error(f"Error collecting Docker metrics: {e}")
            raise

    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_collect_metrics())
    finally:
        loop.close()


@celery_app.task(base=DockerTask, bind=True)
def backup_container_data(self, container_id: str, backup_path: str):
    """Backup container data"""

    async def _backup():
        try:
            # Get container info
            container = await docker_manager.get_container(container_id)

            backup_info = {
                "container_id": container_id,
                "container_name": container["name"],
                "backup_path": backup_path,
                "started_at": datetime.utcnow().isoformat(),
                "status": "in_progress",
            }

            # Store backup status
            backup_key = f"backup:container:{container_id}:{int(datetime.utcnow().timestamp())}"
            await redis_client.set(backup_key, backup_info, expire=3600)

            # TODO: Implement actual backup logic
            # This would involve creating container snapshots, volume backups, etc.

            # For now, just simulate backup completion
            backup_info.update({
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "size": "1.2GB",  # Placeholder
            })

            await redis_client.set(backup_key, backup_info, expire=86400)

            logger.info(f"Container backup completed for {container['name']}")
            return backup_info

        except Exception as e:
            logger.error(f"Error backing up container {container_id}: {e}")
            raise

    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_backup())
    finally:
        loop.close()


@celery_app.task(base=DockerTask, bind=True)
def scan_image_vulnerabilities(self, image_id: str):
    """Scan Docker image for security vulnerabilities"""

    async def _scan():
        try:
            scan_info = {
                "image_id": image_id,
                "started_at": datetime.utcnow().isoformat(),
                "status": "scanning",
            }

            # Store scan status
            scan_key = f"security:scan:{image_id}:{int(datetime.utcnow().timestamp())}"
            await redis_client.set(scan_key, scan_info, expire=3600)

            # TODO: Implement actual vulnerability scanning
            # This would integrate with tools like Trivy, Clair, etc.

            # For now, simulate scan results
            scan_results = {
                "vulnerabilities": {
                    "critical": 0,
                    "high": 2,
                    "medium": 5,
                    "low": 10,
                },
                "packages_scanned": 156,
                "scan_duration": "45s",
            }

            scan_info.update({
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "results": scan_results,
            })

            await redis_client.set(scan_key, scan_info, expire=86400)

            logger.info(f"Vulnerability scan completed for image {image_id}")
            return scan_info

        except Exception as e:
            logger.error(f"Error scanning image {image_id}: {e}")
            raise

    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_scan())
    finally:
        loop.close()


@celery_app.task(base=DockerTask)
def get_docker_stats():
    """Get current Docker statistics"""

    async def _get_stats():
        try:
            stats = {
                "timestamp": datetime.utcnow().isoformat(),
                "system_info": await docker_manager.get_system_info(),
                "containers": len(await docker_manager.list_containers()),
                "images": len(await docker_manager.list_images()),
                "networks": len(await docker_manager.list_networks()),
                "volumes": len(await docker_manager.list_volumes()),
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting Docker stats: {e}")
            return {"error": str(e)}

    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_get_stats())
    finally:
        loop.close()