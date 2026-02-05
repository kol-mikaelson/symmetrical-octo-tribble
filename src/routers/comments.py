"""Comments router for CRUD operations."""

import uuid
from fastapi import APIRouter, Depends, Query, status
from math import ceil

from src.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentListResponse,
)
from src.services.comment_service import CommentService
from src.services.issue_service import IssueService
from src.services.permission_service import PermissionService
from src.services.audit_service import AuditService
from src.models.user import User
from src.app.dependencies import get_current_active_user, get_client_ip
from src.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/issues/{issue_id}/comments", tags=["Comments"])
comments_router = APIRouter(prefix="/comments", tags=["Comments"])


async def get_comment_service(db: AsyncSession = Depends(get_db)) -> CommentService:
    """Get comment service dependency."""
    return CommentService(db)


async def get_issue_service(db: AsyncSession = Depends(get_db)) -> IssueService:
    """Get issue service dependency."""
    return IssueService(db)


async def get_permission_service(db: AsyncSession = Depends(get_db)) -> PermissionService:
    """Get permission service dependency."""
    return PermissionService(db)


async def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    """Get audit service dependency."""
    return AuditService(db)


@router.get(
    "",
    response_model=CommentListResponse,
    summary="List comments for issue",
    description="Get a paginated list of comments for a specific issue",
)
async def list_issue_comments(
    issue_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    comment_service: CommentService = Depends(get_comment_service),
    issue_service: IssueService = Depends(get_issue_service),
) -> CommentListResponse:
    """List comments for an issue.

    Args:
        issue_id: Issue ID
        page: Page number
        limit: Items per page
        current_user: Current user
        comment_service: Comment service
        issue_service: Issue service

    Returns:
        Paginated list of comments
    """
    # Verify issue exists
    await issue_service.get_issue(issue_id)

    comments, total = await comment_service.list_comments(
        issue_id=issue_id,
        page=page,
        limit=limit,
    )

    comment_responses = [CommentResponse.model_validate(c) for c in comments]
    total_pages = ceil(total / limit) if total > 0 else 0

    return CommentListResponse(
        items=comment_responses,
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add comment",
    description="Add a new comment to an issue",
)
async def create_comment(
    issue_id: uuid.UUID,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_active_user),
    ip_address: str = Depends(get_client_ip),
    comment_service: CommentService = Depends(get_comment_service),
    issue_service: IssueService = Depends(get_issue_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> CommentResponse:
    """Add a new comment to an issue.

    Args:
        issue_id: Issue ID
        comment_data: Comment creation data
        current_user: Current user
        ip_address: Client IP address
        comment_service: Comment service
        issue_service: Issue service
        audit_service: Audit service

    Returns:
        Created comment
    """
    # Verify issue exists
    await issue_service.get_issue(issue_id)

    comment = await comment_service.create_comment(issue_id, comment_data, current_user)

    # Log comment creation
    await audit_service.log_action(
        user=current_user,
        action="COMMENT_CREATED",
        resource=f"comment:{comment.id}",
        status="success",
        ip_address=ip_address,
    )

    return CommentResponse.model_validate(comment)


@comments_router.patch(
    "/{comment_id}",
    response_model=CommentResponse,
    summary="Update comment",
    description="Update a comment (author only)",
)
async def update_comment(
    comment_id: uuid.UUID,
    comment_data: CommentUpdate,
    current_user: User = Depends(get_current_active_user),
    ip_address: str = Depends(get_client_ip),
    comment_service: CommentService = Depends(get_comment_service),
    permission_service: PermissionService = Depends(get_permission_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> CommentResponse:
    """Update a comment.

    Args:
        comment_id: Comment ID
        comment_data: Comment update data
        current_user: Current user
        ip_address: Client IP address
        comment_service: Comment service
        permission_service: Permission service
        audit_service: Audit service

    Returns:
        Updated comment
    """
    # Check permission
    await permission_service.require_permission(current_user, "edit_comment", comment_id)

    # Get old comment for audit
    old_comment = await comment_service.get_comment(comment_id)

    # Update comment
    comment = await comment_service.update_comment(comment_id, comment_data)

    # Log update
    await audit_service.log_action(
        user=current_user,
        action="COMMENT_UPDATED",
        resource=f"comment:{comment.id}",
        status="success",
        old_value=old_comment.content[:50],
        new_value=comment.content[:50],
        ip_address=ip_address,
    )

    return CommentResponse.model_validate(comment)
