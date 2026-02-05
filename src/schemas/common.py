"""Common schemas for error responses and pagination."""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Schema for error detail."""

    field: str = Field(..., description="Field name that caused the error")
    issue: str = Field(..., description="Description of the issue")


class ErrorResponse(BaseModel):
    """Schema for unified error response."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: List[ErrorDetail] = Field(default_factory=list, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class PaginationParams(BaseModel):
    """Schema for pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current timestamp")
