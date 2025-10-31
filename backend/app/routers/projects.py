import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from datetime import datetime
from app.middleware.auth_middleware import require_permissions, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])


class Project(BaseModel):
    id: str
    name: str
    description: str
    status: str
    created_by: str
    created_at: datetime
    approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class CreateProjectRequest(BaseModel):
    name: str
    description: str


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


projects_db = {}


@router.get("")
@require_permissions(["Read"])
async def list_projects(request: Request, current_user: dict):
    """
    Get all projects (Read permission required)
    """
    return {
        "projects": list(projects_db.values()),
        "user": current_user['email']
    }


@router.get("/{project_id}")
@require_permissions(["Read"])
async def get_project(request: Request, project_id: str, current_user: dict):
    """
    Get a specific project (Read permission required)
    """
    if project_id not in projects_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return {
        "project": projects_db[project_id],
        "user": current_user['email']
    }


@router.post("")
@require_permissions(["Write"])
async def create_project(request: Request, data: CreateProjectRequest, current_user: dict):
    """
    Create a new project (Write permission required)
    """
    import uuid

    project_id = str(uuid.uuid4())

    project = {
        "id": project_id,
        "name": data.name,
        "description": data.description,
        "status": "draft",
        "created_by": current_user['email'],
        "created_at": datetime.now().isoformat(),
        "approved": False,
        "approved_by": None,
        "approved_at": None
    }

    projects_db[project_id] = project

    logger.info(f"Project created by {current_user['email']}: {project_id}")

    return {
        "message": "Project created successfully",
        "project": project
    }


@router.put("/{project_id}")
@require_permissions(["Write"])
async def update_project(
    request: Request,
    project_id: str,
    data: UpdateProjectRequest,
    current_user: dict
):
    """
    Update a project (Write permission required)
    """
    if project_id not in projects_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    project = projects_db[project_id]

    if data.name:
        project['name'] = data.name
    if data.description:
        project['description'] = data.description
    if data.status:
        project['status'] = data.status

    logger.info(f"Project updated by {current_user['email']}: {project_id}")

    return {
        "message": "Project updated successfully",
        "project": project
    }


@router.post("/{project_id}/approve")
@require_permissions(["Approve"])
async def approve_project(request: Request, project_id: str, current_user: dict):
    """
    Approve a project (Approve permission required)
    """
    if project_id not in projects_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    project = projects_db[project_id]

    if project['approved']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project is already approved"
        )

    project['approved'] = True
    project['approved_by'] = current_user['email']
    project['approved_at'] = datetime.now().isoformat()
    project['status'] = 'approved'

    logger.info(f"Project approved by {current_user['email']}: {project_id}")

    return {
        "message": "Project approved successfully",
        "project": project
    }


@router.delete("/{project_id}")
@require_permissions(["Admin"])
async def delete_project(request: Request, project_id: str, current_user: dict):
    """
    Delete a project (Admin permission required)
    """
    if project_id not in projects_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    deleted_project = projects_db.pop(project_id)

    logger.info(f"Project deleted by {current_user['email']}: {project_id}")

    return {
        "message": "Project deleted successfully",
        "project": deleted_project
    }
