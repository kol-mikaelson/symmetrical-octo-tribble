"""Issue schemas for request/response validation."""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from src.models.issue import IssueStatus, IssuePriority
from src.schemas.user import UserResponse


class IssueBase(BaseModel):
    """Base issue schema with common fields."""

    title: str = Field(..., min_length=1, max_length=200, description="Issue title")
    description: str = Field(..., min_length=1, description="Issue description")


class IssueCreate(IssueBase):
    """Schema for creating an issue."""

    priority: IssuePriority = Field(default=IssuePriority.MEDIUM, description="Issue priority")
    assignee_id: Optional[uuid.UUID] = Field(None, description="Assignee user ID")


class IssueUpdate(BaseModel):
    """Schema for updating an issue."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    status: Optional[IssueStatus] = None
    priority: Optional[IssuePriority] = None
    assignee_id: Optional[uuid.UUID] = None


class IssueResponse(IssueBase):
    """Schema for issue response."""

    id: uuid.UUID
    status: IssueStatus
    priority: IssuePriority
    project_id: uuid.UUID
    reporter_id: uuid.UUID
    assignee_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    reporter: Optional[UserResponse] = None
    assignee: Optional[UserResponse] = None
    comment_count: int = Field(default=0, description="Number of comments")

    model_config = {"from_attributes": True}


class IssueListResponse(BaseModel):
    """Schema for paginated issue list response."""

    items: list[IssueResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
