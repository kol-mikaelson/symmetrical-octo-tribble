"""Issue service for business logic."""
import uuid
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.issue import Issue, IssueStatus, IssuePriority
from src.models.user import User
from src.schemas.issue import IssueCreate, IssueUpdate
from src.app.exceptions import NotFoundError
from src.utils.validators import validate_state_transition, validate_critical_issue_closure


class IssueService:
    """Issue service for business logic."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize issue service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_issue(
        self, project_id: uuid.UUID, issue_data: IssueCreate, reporter: User
    ) -> Issue:
        """Create a new issue.

        Args:
            project_id: Project ID
            issue_data: Issue creation data
            reporter: User creating the issue

        Returns:
            Created issue
        """
        issue = Issue(
            title=issue_data.title,
            description=issue_data.description,
            priority=issue_data.priority,
            project_id=project_id,
            reporter_id=reporter.id,
            assignee_id=issue_data.assignee_id,
        )

        self.db.add(issue)
        await self.db.commit()
        await self.db.refresh(issue, ["reporter", "assignee", "project"])

        return issue

    async def get_issue(self, issue_id: uuid.UUID) -> Issue:
        """Get an issue by ID.

        Args:
            issue_id: Issue ID

        Returns:
            Issue

        Raises:
            NotFoundError: If issue not found
        """
        result = await self.db.execute(
            select(Issue)
            .where(Issue.id == issue_id)
            .options(
                selectinload(Issue.reporter),
                selectinload(Issue.assignee),
                selectinload(Issue.project),
                selectinload(Issue.comments),
            )
        )
        issue = result.scalar_one_or_none()

        if not issue:
            raise NotFoundError(f"Issue with ID {issue_id} not found")

        return issue

    async def list_issues(
        self,
        project_id: Optional[uuid.UUID] = None,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[IssueStatus] = None,
        priority: Optional[IssuePriority] = None,
        assignee_id: Optional[uuid.UUID] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Tuple[List[Issue], int]:
        """List issues with pagination and filtering.

        Args:
            project_id: Filter by project ID
            page: Page number (1-indexed)
            limit: Items per page
            search: Search term for title/description
            status: Filter by status
            priority: Filter by priority
            assignee_id: Filter by assignee
            sort_by: Field to sort by
            sort_desc: Sort descending

        Returns:
            Tuple of (issues, total_count)
        """
        # Build query
        query = select(Issue).options(
            selectinload(Issue.reporter),
            selectinload(Issue.assignee),
            selectinload(Issue.project),
        )

        # Apply filters
        if project_id:
            query = query.where(Issue.project_id == project_id)

        if search:
            query = query.where(
                or_(
                    Issue.title.ilike(f"%{search}%"),
                    Issue.description.ilike(f"%{search}%"),
                )
            )

        if status:
            query = query.where(Issue.status == status)

        if priority:
            query = query.where(Issue.priority == priority)

        if assignee_id:
            query = query.where(Issue.assignee_id == assignee_id)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply sorting
        sort_column = getattr(Issue, sort_by, Issue.created_at)
        if sort_desc:
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        issues = result.scalars().all()

        return list(issues), total

    async def update_issue(
        self, issue_id: uuid.UUID, issue_data: IssueUpdate
    ) -> Issue:
        """Update an issue.

        Args:
            issue_id: Issue ID
            issue_data: Issue update data

        Returns:
            Updated issue

        Raises:
            NotFoundError: If issue not found
            InvalidStateTransitionError: If state transition is invalid
        """
        issue = await self.get_issue(issue_id)

        # Validate state transition if status is being changed
        if issue_data.status and issue_data.status != issue.status:
            validate_state_transition(issue.status, issue_data.status)

            # Validate critical issue closure
            if issue_data.status == IssueStatus.CLOSED:
                validate_critical_issue_closure(
                    issue.priority.value,
                    issue_data.status,
                    issue.comment_count,
                )

            # Update resolved_at/closed_at timestamps
            if issue_data.status == IssueStatus.RESOLVED:
                issue.resolved_at = datetime.utcnow()
            elif issue_data.status == IssueStatus.CLOSED:
                issue.closed_at = datetime.utcnow()
            elif issue_data.status == IssueStatus.REOPENED:
                issue.resolved_at = None
                issue.closed_at = None

        # Update fields
        update_data = issue_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(issue, field, value)

        await self.db.commit()
        await self.db.refresh(issue, ["reporter", "assignee", "project", "comments"])

        return issue
