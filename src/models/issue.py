"""Issue model for bug tracking."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
import enum
from sqlalchemy import String, DateTime, Text, ForeignKey, Enum as SQLEnum, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.database import Base

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.project import Project
    from src.models.comment import Comment


class IssueStatus(str, enum.Enum):
    """Issue status enumeration."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class IssuePriority(str, enum.Enum):
    """Issue priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Issue(Base):
    """Issue model for bug tracking."""

    __tablename__ = "issues"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, index=True
    )

    # Basic Information
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Status and Priority
    status: Mapped[IssueStatus] = mapped_column(
        SQLEnum(IssueStatus, name="issue_status", native_enum=False),
        default=IssueStatus.OPEN,
        nullable=False,
        index=True,
    )
    priority: Mapped[IssuePriority] = mapped_column(
        SQLEnum(IssuePriority, name="issue_priority", native_enum=False),
        default=IssuePriority.MEDIUM,
        nullable=False,
        index=True,
    )

    # Foreign Keys
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assignee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project", back_populates="issues"
    )
    reporter: Mapped["User"] = relationship(
        "User", back_populates="reported_issues", foreign_keys=[reporter_id]
    )
    assignee: Mapped[Optional["User"]] = relationship(
        "User", back_populates="assigned_issues", foreign_keys=[assignee_id]
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="issue", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of Issue."""
        return f"<Issue(id={self.id}, title={self.title}, status={self.status}, priority={self.priority})>"

    @property
    def comment_count(self) -> int:
        """Get the number of comments on this issue."""
        return len(self.comments) if self.comments else 0
