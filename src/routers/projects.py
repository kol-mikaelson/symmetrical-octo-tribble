"""Projects router for CRUD operations."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from math import ceil

from src.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
)
from src.services.project_service import ProjectService
from src.services.permission_service import PermissionService
from src.services.audit_service import AuditService
from src.models.user import User, UserRole
from src.app.dependencies import (
    get_current_active_user,
    get_client_ip,
    require_role,
)
from src.app.config import settings
from src.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/projects", tags=["Projects"])


async def get_project_service(db: AsyncSession = Depends(get_db)) -> ProjectService:
    """Get project service dependency."""
    return ProjectService(db)


async def get_permission_service(db: AsyncSession = Depends(get_db)) -> PermissionService:
    """Get permission service dependency."""
    return PermissionService(db)


async def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    """Get audit service dependency."""
    return AuditService(db)


@router.get(
    "",
    response_model=ProjectListResponse,
    summary="List projects",
    description="Get a paginated list of projects with optional filtering and search",
)
async def list_projects(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    is_archived: Optional[bool] = Query(None, description="Filter by archived status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_desc: bool = Query(True, description="Sort descending"),
    current_user: User = Depends(get_current_active_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectListResponse:
    """List projects with pagination.

    Args:
        page: Page number
        limit: Items per page
        search: Search term
        is_archived: Filter by archived status
        sort_by: Sort field
        sort_desc: Sort descending
        current_user: Current user
        project_service: Project service

    Returns:
        Paginated list of projects
    """
    projects, total = await project_service.list_projects(
        page=page,
        limit=limit,
        search=search,
        is_archived=is_archived,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    # Add issue count to each project
    project_responses = []
    for project in projects:
        project_dict = ProjectResponse.model_validate(project).model_dump()
        project_dict["issue_count"] = len(project.issues) if project.issues else 0
        project_responses.append(ProjectResponse(**project_dict))

    total_pages = ceil(total / limit) if total > 0 else 0

    return ProjectListResponse(
        items=project_responses,
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create project",
    description="Create a new project (manager/admin only)",
)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(require_role(UserRole.MANAGER, UserRole.ADMIN)),
    ip_address: str = Depends(get_client_ip),
    project_service: ProjectService = Depends(get_project_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> ProjectResponse:
    """Create a new project.

    Args:
        project_data: Project creation data
        current_user: Current user (manager/admin)
        ip_address: Client IP address
        project_service: Project service
        audit_service: Audit service

    Returns:
        Created project
    """
    project = await project_service.create_project(project_data, current_user)

    # Log project creation
    await audit_service.log_action(
        user=current_user,
        action="PROJECT_CREATED",
        resource=f"project:{project.id}",
        status="success",
        new_value=project.name,
        ip_address=ip_address,
    )

    response = ProjectResponse.model_validate(project)
    response.issue_count = 0
    return response


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project",
    description="Get a project by ID",
)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Get a project by ID.

    Args:
        project_id: Project ID
        current_user: Current user
        project_service: Project service

    Returns:
        Project details
    """
    project = await project_service.get_project(project_id)

    response = ProjectResponse.model_validate(project)
    response.issue_count = len(project.issues) if project.issues else 0
    return response


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
    description="Update a project (owner/admin only)",
)
async def update_project(
    project_id: uuid.UUID,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    ip_address: str = Depends(get_client_ip),
    project_service: ProjectService = Depends(get_project_service),
    permission_service: PermissionService = Depends(get_permission_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> ProjectResponse:
    """Update a project.

    Args:
        project_id: Project ID
        project_data: Project update data
        current_user: Current user
        ip_address: Client IP address
        project_service: Project service
        permission_service: Permission service
        audit_service: Audit service

    Returns:
        Updated project
    """
    # Check permission
    await permission_service.require_permission(
        current_user, "edit_project", project_id
    )

    # Get old project for audit
    old_project = await project_service.get_project(project_id)

    # Update project
    project = await project_service.update_project(project_id, project_data)

    # Log update
    await audit_service.log_action(
        user=current_user,
        action="PROJECT_UPDATED",
        resource=f"project:{project.id}",
        status="success",
        old_value=old_project.name,
        new_value=project.name,
        ip_address=ip_address,
    )

    response = ProjectResponse.model_validate(project)
    response.issue_count = len(project.issues) if project.issues else 0
    return response


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive project",
    description="Archive a project (soft delete, owner/admin only)",
)
async def archive_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    ip_address: str = Depends(get_client_ip),
    project_service: ProjectService = Depends(get_project_service),
    permission_service: PermissionService = Depends(get_permission_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> None:
    """Archive a project (soft delete).

    Args:
        project_id: Project ID
        current_user: Current user
        ip_address: Client IP address
        project_service: Project service
        permission_service: Permission service
        audit_service: Audit service
    """
    # Check permission
    await permission_service.require_permission(
        current_user, "archive_project", project_id
    )

    # Archive project
    project = await project_service.archive_project(project_id)

    # Log archival
    await audit_service.log_action(
        user=current_user,
        action="PROJECT_ARCHIVED",
        resource=f"project:{project.id}",
        status="success",
        new_value="archived",
        ip_address=ip_address,
    )
