import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import (
    MCPProject,
    MCPProjectCreate,
    MCPProjectResponse,
    ProjectStatus,
    APIResponse,
)
from app.services.project_service import ProjectService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[MCPProjectResponse])
async def list_projects(
    owner_id: Optional[int] = Query(None, description="Filter by owner ID"),
    db: AsyncSession = Depends(get_db)
):
    """List all MCP projects"""
    try:
        projects = await ProjectService.list_projects(owner_id=owner_id, db=db)

        # Convert to response models
        project_responses = []
        for project in projects:
            project_responses.append(MCPProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                status=project.status,
                tools_count=len(project.tools) if project.tools else 0,
                created_at=project.created_at,
            ))

        return project_responses
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve projects")


@router.post("/", response_model=MCPProjectResponse)
async def create_project(
    project: MCPProjectCreate,
    owner_id: int = Query(..., description="Owner user ID"),
    db: AsyncSession = Depends(get_db)
):
    """Create a new MCP project"""
    try:
        logger.info(f"Creating project: {project.name}")

        db_project = await ProjectService.create_project(
            project_data=project,
            owner_id=owner_id,
            db=db
        )

        return MCPProjectResponse(
            id=db_project.id,
            name=db_project.name,
            description=db_project.description,
            status=db_project.status,
            tools_count=len(db_project.tools) if db_project.tools else 0,
            created_at=db_project.created_at,
        )
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail="Failed to create project")


@router.get("/{project_id}", response_model=MCPProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific project"""
    try:
        project = await ProjectService.get_project(project_id, db)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        return MCPProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            tools_count=len(project.tools) if project.tools else 0,
            created_at=project.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve project")


@router.put("/{project_id}", response_model=MCPProjectResponse)
async def update_project(
    project_id: int,
    project_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Update a project"""
    try:
        project = await ProjectService.update_project(project_id, project_data, db)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        return MCPProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            tools_count=len(project.tools) if project.tools else 0,
            created_at=project.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update project")


@router.delete("/{project_id}", response_model=APIResponse)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a project"""
    try:
        success = await ProjectService.delete_project(project_id, db)

        if not success:
            raise HTTPException(status_code=404, detail="Project not found")

        return APIResponse(message=f"Project {project_id} deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete project")


@router.post("/{project_id}/build", response_model=APIResponse)
async def build_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Build Docker image for the project"""
    try:
        logger.info(f"Building project: {project_id}")

        build_id = await ProjectService.start_build(project_id, db)

        if not build_id:
            raise HTTPException(status_code=404, detail="Project not found")

        return APIResponse(
            message="Build started successfully",
            data={"build_id": build_id, "project_id": project_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start build for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start build")


@router.post("/{project_id}/deploy", response_model=APIResponse)
async def deploy_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Deploy the project to MCP gateway"""
    try:
        logger.info(f"Deploying project: {project_id}")

        # Check if project exists
        project = await ProjectService.get_project(project_id, db)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # TODO: Implement actual deployment logic
        # For now, just return success
        return APIResponse(
            message="Deployment started successfully",
            data={"project_id": project_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deploy project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start deployment")


@router.get("/{project_id}/files")
async def get_project_files(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all files for a project"""
    try:
        files = await ProjectService.get_project_files(project_id, db)

        # Convert to response format
        file_data = []
        for file in files:
            file_data.append({
                "id": file.id,
                "file_path": file.file_path,
                "file_size": file.file_size,
                "mime_type": file.mime_type,
                "created_at": file.created_at,
                "updated_at": file.updated_at,
            })

        return {"files": file_data}
    except Exception as e:
        logger.error(f"Failed to get files for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve project files")


@router.get("/{project_id}/files/{file_path:path}")
async def get_project_file_content(
    project_id: int,
    file_path: str,
    db: AsyncSession = Depends(get_db)
):
    """Get content of a specific project file"""
    try:
        files = await ProjectService.get_project_files(project_id, db)

        # Find the specific file
        project_file = None
        for file in files:
            if file.file_path == file_path:
                project_file = file
                break

        if not project_file:
            raise HTTPException(status_code=404, detail="File not found")

        return {
            "file_path": project_file.file_path,
            "content": project_file.file_content,
            "mime_type": project_file.mime_type,
            "updated_at": project_file.updated_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file {file_path} for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file content")


@router.put("/{project_id}/files/{file_path:path}")
async def update_project_file(
    project_id: int,
    file_path: str,
    file_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Update or create a project file"""
    try:
        content = file_data.get("content", "")

        project_file = await ProjectService.create_or_update_file(
            project_id, file_path, content, db
        )

        return {
            "file_path": project_file.file_path,
            "file_size": project_file.file_size,
            "updated_at": project_file.updated_at,
        }
    except Exception as e:
        logger.error(f"Failed to update file {file_path} for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update file")
