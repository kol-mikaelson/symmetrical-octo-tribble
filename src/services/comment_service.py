"""Comment service for business logic."""

import uuid
from typing import List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.comment import Comment
from src.models.user import User
from src.schemas.comment import CommentCreate, CommentUpdate
from src.app.exceptions import NotFoundError


class CommentService:
    """Comment service for business logic."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize comment service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_comment(
        self, issue_id: uuid.UUID, comment_data: CommentCreate, author: User
    ) -> Comment:
        """Create a new comment.

        Args:
            issue_id: Issue ID
            comment_data: Comment creation data
            author: User creating the comment

        Returns:
            Created comment
        """
        comment = Comment(
            content=comment_data.content,
            issue_id=issue_id,
            author_id=author.id,
        )

        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment, ["author", "issue"])

        return comment

    async def get_comment(self, comment_id: uuid.UUID) -> Comment:
        """Get a comment by ID.

        Args:
            comment_id: Comment ID

        Returns:
            Comment

        Raises:
            NotFoundError: If comment not found
        """
        result = await self.db.execute(
            select(Comment)
            .where(Comment.id == comment_id)
            .options(selectinload(Comment.author), selectinload(Comment.issue))
        )
        comment = result.scalar_one_or_none()

        if not comment:
            raise NotFoundError(f"Comment with ID {comment_id} not found")

        return comment

    async def list_comments(
        self,
        issue_id: uuid.UUID,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[Comment], int]:
        """List comments for an issue with pagination.

        Args:
            issue_id: Issue ID
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Tuple of (comments, total_count)
        """
        # Build query
        query = (
            select(Comment)
            .where(Comment.issue_id == issue_id)
            .options(selectinload(Comment.author))
            .order_by(Comment.created_at.asc())
        )

        # Get total count
        count_query = select(func.count()).where(Comment.issue_id == issue_id)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        comments = result.scalars().all()

        return list(comments), total

    async def update_comment(self, comment_id: uuid.UUID, comment_data: CommentUpdate) -> Comment:
        """Update a comment.

        Args:
            comment_id: Comment ID
            comment_data: Comment update data

        Returns:
            Updated comment

        Raises:
            NotFoundError: If comment not found
        """
        comment = await self.get_comment(comment_id)

        # Update content
        comment.content = comment_data.content

        await self.db.commit()
        await self.db.refresh(comment, ["author", "issue"])

        return comment
