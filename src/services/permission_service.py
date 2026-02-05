"""Permission service for role-based and resource-level access control."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.exceptions import InsufficientPermissionsError
from src.models.comment import Comment
from src.models.issue import Issue
from src.models.project import Project
from src.models.user import User, UserRole


class PermissionService:
    """Permission service for access control."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize permission service.

        Args:
            db: Database session
        """
        self.db = db

    async def can_create_project(self, user: User) -> bool:
        """Check if user can create projects.

        Args:
            user: User to check

        Returns:
            True if user can create projects
        """
        return user.role in [UserRole.MANAGER, UserRole.ADMIN]

    async def can_edit_project(self, user: User, project_id: uuid.UUID) -> bool:
        """Check if user can edit a project.

        Args:
            user: User to check
            project_id: Project ID

        Returns:
            True if user can edit the project
        """
        # Admin can edit any project
        if user.role == UserRole.ADMIN:
            return True

        # Get project
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            return False

        # Project creator or manager can edit
        return project.created_by == user.id or user.role == UserRole.MANAGER

    async def can_archive_project(self, user: User, project_id: uuid.UUID) -> bool:
        """Check if user can archive a project.

        Args:
            user: User to check
            project_id: Project ID

        Returns:
            True if user can archive the project
        """
        # Same as edit permissions
        return await self.can_edit_project(user, project_id)

    async def can_create_issue(self, user: User) -> bool:
        """Check if user can create issues.

        Args:
            user: User to check

        Returns:
            True if user can create issues
        """
        # All authenticated users can create issues
        return True

    async def can_edit_issue(self, user: User, issue_id: uuid.UUID) -> bool:
        """Check if user can edit an issue.

        Args:
            user: User to check
            issue_id: Issue ID

        Returns:
            True if user can edit the issue
        """
        # Admin can edit any issue
        if user.role == UserRole.ADMIN:
            return True

        # Get issue
        result = await self.db.execute(select(Issue).where(Issue.id == issue_id))
        issue = result.scalar_one_or_none()

        if not issue:
            return False

        # Reporter, assignee, or manager can edit
        return (
            issue.reporter_id == user.id
            or issue.assignee_id == user.id
            or user.role == UserRole.MANAGER
        )

    async def can_change_assignee(self, user: User, issue_id: uuid.UUID) -> bool:
        """Check if user can change issue assignee.

        Args:
            user: User to check
            issue_id: Issue ID

        Returns:
            True if user can change assignee
        """
        # Admin or manager can change assignee
        if user.role in [UserRole.ADMIN, UserRole.MANAGER]:
            return True

        # Get issue
        result = await self.db.execute(select(Issue).where(Issue.id == issue_id))
        issue = result.scalar_one_or_none()

        if not issue:
            return False

        # Reporter can change assignee
        return issue.reporter_id == user.id

    async def can_add_comment(self, user: User) -> bool:
        """Check if user can add comments.

        Args:
            user: User to check

        Returns:
            True if user can add comments
        """
        # All authenticated users can add comments
        return True

    async def can_edit_comment(self, user: User, comment_id: uuid.UUID) -> bool:
        """Check if user can edit a comment.

        Args:
            user: User to check
            comment_id: Comment ID

        Returns:
            True if user can edit the comment
        """
        # Admin can edit any comment
        if user.role == UserRole.ADMIN:
            return True

        # Get comment
        result = await self.db.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()

        if not comment:
            return False

        # Only author can edit their own comment
        return comment.author_id == user.id

    async def require_permission(
        self,
        user: User,
        action: str,
        resource_id: Optional[uuid.UUID] = None,
    ) -> None:
        """Require user to have permission for an action.

        Args:
            user: User to check
            action: Action to perform
            resource_id: Optional resource ID

        Raises:
            InsufficientPermissionsError: If user lacks permission
        """
        permission_map = {
            "create_project": self.can_create_project,
            "edit_project": self.can_edit_project,
            "archive_project": self.can_archive_project,
            "create_issue": self.can_create_issue,
            "edit_issue": self.can_edit_issue,
            "change_assignee": self.can_change_assignee,
            "add_comment": self.can_add_comment,
            "edit_comment": self.can_edit_comment,
        }

        check_func = permission_map.get(action)
        if not check_func:
            raise ValueError(f"Unknown action: {action}")

        # Call permission check function
        if resource_id:
            has_permission = await check_func(user, resource_id)
        else:
            has_permission = await check_func(user)

        if not has_permission:
            raise InsufficientPermissionsError(
                f"You do not have permission to {action.replace('_', ' ')}"
            )

    def require_role(self, user: User, *roles: UserRole) -> None:
        """Require user to have one of the specified roles.

        Args:
            user: User to check
            *roles: Required roles

        Raises:
            InsufficientPermissionsError: If user lacks required role
        """
        if user.role not in roles:
            raise InsufficientPermissionsError(
                f"This action requires one of the following roles: {', '.join(r.value for r in roles)}"
            )
