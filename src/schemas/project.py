"""Project schemas for request/response validation."""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from src.schemas.user import UserResponse


class ProjectBase(BaseModel):
    """Base project schema with common fields."""

    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: str = Field(..., min_length=1, description="Project description")


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1)
    is_archived: Optional[bool] = None


class ProjectResponse(ProjectBase):
    """Schema for project response."""

    id: uuid.UUID
    is_archived: bool
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    creator: Optional[UserResponse] = None
    issue_count: int = Field(default=0, description="Number of issues in project")

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    """Schema for paginated project list response."""

    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
