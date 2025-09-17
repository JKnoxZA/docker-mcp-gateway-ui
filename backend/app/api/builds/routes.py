import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.build_manager import BuildManager, get_build_manager
from app.models.schemas import BuildInfo, BuildStatus

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[dict])
async def list_builds(
    status: Optional[BuildStatus] = Query(None, description="Filter by build status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of builds to return"),
    build_manager: BuildManager = Depends(get_build_manager),
):
    """List builds with optional status filter"""
    try:
        builds = await build_manager.list_builds(status_filter=status, limit=limit)
        return builds
    except Exception as e:
        logger.error(f"Error listing builds: {e}")
        raise HTTPException(status_code=500, detail="Failed to list builds")


@router.get("/{build_id}")
async def get_build_status(
    build_id: str,
    build_manager: BuildManager = Depends(get_build_manager),
):
    """Get build status by ID"""
    try:
        build_data = await build_manager.get_build_status(build_id)
        if not build_data:
            raise HTTPException(status_code=404, detail="Build not found")
        return build_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting build status for {build_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get build status")


@router.get("/{build_id}/logs")
async def get_build_logs(
    build_id: str,
    build_manager: BuildManager = Depends(get_build_manager),
):
    """Get build logs for a specific build"""
    try:
        logs = await build_manager.get_build_logs(build_id)
        return {"build_id": build_id, "logs": logs}
    except Exception as e:
        logger.error(f"Error getting build logs for {build_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get build logs")


@router.post("/{build_id}/cancel")
async def cancel_build(
    build_id: str,
    build_manager: BuildManager = Depends(get_build_manager),
):
    """Cancel a pending or running build"""
    try:
        success = await build_manager.cancel_build(build_id)
        if not success:
            raise HTTPException(
                status_code=400, detail="Build cannot be cancelled or not found"
            )
        return {"message": f"Build {build_id} cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling build {build_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel build")


@router.post("/{build_id}/retry")
async def retry_build(
    build_id: str,
    build_manager: BuildManager = Depends(get_build_manager),
):
    """Retry a failed build"""
    try:
        new_build_id = await build_manager.retry_failed_build(build_id)
        if not new_build_id:
            raise HTTPException(
                status_code=400, detail="Build cannot be retried or not found"
            )
        return {
            "message": "Build retry started",
            "original_build_id": build_id,
            "new_build_id": new_build_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying build {build_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retry build")


@router.get("/queue/status")
async def get_queue_status(
    build_manager: BuildManager = Depends(get_build_manager),
):
    """Get build queue status"""
    try:
        status = await build_manager.get_queue_status()
        return status
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get queue status")


@router.delete("/cleanup")
async def cleanup_old_builds(
    days: int = Query(7, ge=1, le=365, description="Delete builds older than this many days"),
    build_manager: BuildManager = Depends(get_build_manager),
):
    """Clean up builds older than specified days"""
    try:
        cleaned_count = await build_manager.cleanup_old_builds(days)
        return {
            "message": f"Cleaned up {cleaned_count} old builds",
            "days": days,
            "cleaned_count": cleaned_count,
        }
    except Exception as e:
        logger.error(f"Error cleaning up old builds: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup old builds")