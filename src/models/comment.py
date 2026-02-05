"""Comment model for issue discussions."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.database import Base

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.issue import Issue


class Comment(Base):
    """Comment model for issue discussions."""

    __tablename__ = "comments"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Foreign Keys
    issue_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
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

    # Relationships
    issue: Mapped["Issue"] = relationship("Issue", back_populates="comments")
    author: Mapped["User"] = relationship("User", back_populates="comments")

    # Constraints
    __table_args__ = (
        CheckConstraint("LENGTH(content) > 0", name="comment_content_not_empty"),
        CheckConstraint("LENGTH(content) <= 2000", name="comment_content_max_length"),
    )

    def __repr__(self) -> str:
        """String representation of Comment."""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Comment(id={self.id}, author_id={self.author_id}, content='{content_preview}')>"
