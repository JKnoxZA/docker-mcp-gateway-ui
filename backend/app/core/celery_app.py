import logging
from celery import Celery

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "mcp_gateway",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.build_tasks", "app.tasks.docker_tasks"],
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "app.tasks.build_tasks.*": {"queue": "build_queue"},
        "app.tasks.docker_tasks.*": {"queue": "docker_queue"},
    },
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task result expiration
    result_expires=3600,  # 1 hour
    # Task acknowledgment
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Task retry configuration
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    # Beat schedule (for periodic tasks)
    beat_schedule={
        "cleanup-expired-builds": {
            "task": "app.tasks.build_tasks.cleanup_expired_builds",
            "schedule": 300.0,  # Every 5 minutes
        },
        "cleanup-docker-resources": {
            "task": "app.tasks.docker_tasks.cleanup_docker_resources",
            "schedule": 3600.0,  # Every hour
        },
    },
)

# Configure logging
celery_app.conf.worker_log_format = (
    "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
)
celery_app.conf.worker_task_log_format = (
    "[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s"
)

if __name__ == "__main__":
    celery_app.start()