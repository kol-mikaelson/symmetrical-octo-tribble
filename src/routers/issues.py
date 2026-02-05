"""Issues router for CRUD operations."""

import uuid
from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.dependencies import get_client_ip, get_current_active_user
from src.database.database import get_db
from src.models.issue import IssuePriority, IssueStatus
from src.models.user import User
from src.schemas.issue import (
    IssueCreate,
    IssueListResponse,
    IssueResponse,
    IssueUpdate,
)
from src.services.audit_service import AuditService
from src.services.issue_service import IssueService
from src.services.permission_service import PermissionService
from src.services.project_service import ProjectService

router = APIRouter(prefix="/projects/{project_id}/issues", tags=["Issues"])
issues_router = APIRouter(prefix="/issues", tags=["Issues"])


async def get_issue_service(db: AsyncSession = Depends(get_db)) -> IssueService:
    """Get issue service dependency."""
    return IssueService(db)


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
    response_model=IssueListResponse,
    summary="List issues for project",
    description="Get a paginated list of issues for a specific project",
)
async def list_project_issues(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    status: Optional[IssueStatus] = Query(None, description="Filter by status"),
    priority: Optional[IssuePriority] = Query(None, description="Filter by priority"),
    assignee_id: Optional[uuid.UUID] = Query(None, description="Filter by assignee"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_desc: bool = Query(True, description="Sort descending"),
    current_user: User = Depends(get_current_active_user),
    issue_service: IssueService = Depends(get_issue_service),
    project_service: ProjectService = Depends(get_project_service),
) -> IssueListResponse:
    """List issues for a project.

    Args:
        project_id: Project ID
        page: Page number
        limit: Items per page
        search: Search term
        status: Filter by status
        priority: Filter by priority
        assignee_id: Filter by assignee
        sort_by: Sort field
        sort_desc: Sort descending
        current_user: Current user
        issue_service: Issue service
        project_service: Project service

    Returns:
        Paginated list of issues
    """
    # Verify project exists
    await project_service.get_project(project_id)

    issues, total = await issue_service.list_issues(
        project_id=project_id,
        page=page,
        limit=limit,
        search=search,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    issue_responses = []
    for issue in issues:
        issue_dict = IssueResponse.model_validate(issue).model_dump()
        issue_dict["comment_count"] = issue.comment_count
        issue_responses.append(IssueResponse(**issue_dict))

    total_pages = ceil(total / limit) if total > 0 else 0

    return IssueListResponse(
        items=issue_responses,
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=IssueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create issue",
    description="Create a new issue in a project",
)
async def create_issue(
    project_id: uuid.UUID,
    issue_data: IssueCreate,
    current_user: User = Depends(get_current_active_user),
    ip_address: str = Depends(get_client_ip),
    issue_service: IssueService = Depends(get_issue_service),
    project_service: ProjectService = Depends(get_project_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> IssueResponse:
    """Create a new issue.

    Args:
        project_id: Project ID
        issue_data: Issue creation data
        current_user: Current user
        ip_address: Client IP address
        issue_service: Issue service
        project_service: Project service
        audit_service: Audit service

    Returns:
        Created issue
    """
    # Verify project exists
    await project_service.get_project(project_id)

    issue = await issue_service.create_issue(project_id, issue_data, current_user)

    # Log issue creation
    await audit_service.log_action(
        user=current_user,
        action="ISSUE_CREATED",
        resource=f"issue:{issue.id}",
        status="success",
        new_value=issue.title,
        ip_address=ip_address,
    )

    response = IssueResponse.model_validate(issue)
    response.comment_count = 0
    return response


@issues_router.get(
    "/{issue_id}",
    response_model=IssueResponse,
    summary="Get issue",
    description="Get an issue by ID",
)
async def get_issue(
    issue_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    issue_service: IssueService = Depends(get_issue_service),
) -> IssueResponse:
    """Get an issue by ID.

    Args:
        issue_id: Issue ID
        current_user: Current user
        issue_service: Issue service

    Returns:
        Issue details
    """
    issue = await issue_service.get_issue(issue_id)

    response = IssueResponse.model_validate(issue)
    response.comment_count = issue.comment_count
    return response


@issues_router.patch(
    "/{issue_id}",
    response_model=IssueResponse,
    summary="Update issue",
    description="Update an issue (reporter/assignee/manager/admin)",
)
async def update_issue(
    issue_id: uuid.UUID,
    issue_data: IssueUpdate,
    current_user: User = Depends(get_current_active_user),
    ip_address: str = Depends(get_client_ip),
    issue_service: IssueService = Depends(get_issue_service),
    permission_service: PermissionService = Depends(get_permission_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> IssueResponse:
    """Update an issue.

    Args:
        issue_id: Issue ID
        issue_data: Issue update data
        current_user: Current user
        ip_address: Client IP address
        issue_service: Issue service
        permission_service: Permission service
        audit_service: Audit service

    Returns:
        Updated issue
    """
    # Check permission
    await permission_service.require_permission(current_user, "edit_issue", issue_id)

    # Get old issue for audit
    old_issue = await issue_service.get_issue(issue_id)

    # Update issue
    issue = await issue_service.update_issue(issue_id, issue_data)

    # Log state transition if status changed
    if issue_data.status and issue_data.status != old_issue.status:
        await audit_service.log_state_transition(
            user=current_user,
            resource=f"issue:{issue.id}",
            old_state=old_issue.status.value,
            new_state=issue.status.value,
            ip_address=ip_address,
        )
    else:
        # Log general update
        await audit_service.log_action(
            user=current_user,
            action="ISSUE_UPDATED",
            resource=f"issue:{issue.id}",
            status="success",
            ip_address=ip_address,
        )

    response = IssueResponse.model_validate(issue)
    response.comment_count = issue.comment_count
    return response
