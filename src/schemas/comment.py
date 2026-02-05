"""Comment schemas for request/response validation."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from src.schemas.user import UserResponse


class CommentBase(BaseModel):
    """Base comment schema with common fields."""

    content: str = Field(..., min_length=1, max_length=2000, description="Comment content")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate comment content is not empty after stripping whitespace."""
        if not v.strip():
            raise ValueError("Comment content cannot be empty")
        return v.strip()


class CommentCreate(CommentBase):
    """Schema for creating a comment."""

    pass


class CommentUpdate(BaseModel):
    """Schema for updating a comment."""

    content: str = Field(..., min_length=1, max_length=2000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate comment content is not empty after stripping whitespace."""
        if not v.strip():
            raise ValueError("Comment content cannot be empty")
        return v.strip()


class CommentResponse(CommentBase):
    """Schema for comment response."""

    id: uuid.UUID
    issue_id: uuid.UUID
    author_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    author: Optional[UserResponse] = None

    model_config = {"from_attributes": True}


class CommentListResponse(BaseModel):
    """Schema for paginated comment list response."""

    items: list[CommentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
