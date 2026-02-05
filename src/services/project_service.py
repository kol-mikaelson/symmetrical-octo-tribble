"""Project service for business logic."""

import uuid
from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.project import Project
from src.models.user import User
from src.schemas.project import ProjectCreate, ProjectUpdate
from src.app.exceptions import NotFoundError, ConflictError
from src.app.config import settings


class ProjectService:
    """Project service for business logic."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize project service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_project(self, project_data: ProjectCreate, creator: User) -> Project:
        """Create a new project.

        Args:
            project_data: Project creation data
            creator: User creating the project

        Returns:
            Created project

        Raises:
            ConflictError: If project name already exists
        """
        # Check if project name exists
        result = await self.db.execute(select(Project).where(Project.name == project_data.name))
        if result.scalar_one_or_none():
            raise ConflictError(f"Project with name '{project_data.name}' already exists")

        # Create project
        project = Project(
            name=project_data.name,
            description=project_data.description,
            created_by=creator.id,
        )

        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project, ["creator"])

        return project

    async def get_project(self, project_id: uuid.UUID) -> Project:
        """Get a project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project

        Raises:
            NotFoundError: If project not found
        """
        result = await self.db.execute(
            select(Project).where(Project.id == project_id).options(selectinload(Project.creator))
        )
        project = result.scalar_one_or_none()

        if not project:
            raise NotFoundError(f"Project with ID {project_id} not found")

        return project

    async def list_projects(
        self,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        is_archived: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Tuple[List[Project], int]:
        """List projects with pagination and filtering.

        Args:
            page: Page number (1-indexed)
            limit: Items per page
            search: Search term for name/description
            is_archived: Filter by archived status
            sort_by: Field to sort by
            sort_desc: Sort descending

        Returns:
            Tuple of (projects, total_count)
        """
        # Build query
        query = select(Project).options(selectinload(Project.creator))

        # Apply filters
        if search:
            query = query.where(
                or_(
                    Project.name.ilike(f"%{search}%"),
                    Project.description.ilike(f"%{search}%"),
                )
            )

        if is_archived is not None:
            query = query.where(Project.is_archived == is_archived)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply sorting
        sort_column = getattr(Project, sort_by, Project.created_at)
        if sort_desc:
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        projects = result.scalars().all()

        return list(projects), total

    async def update_project(self, project_id: uuid.UUID, project_data: ProjectUpdate) -> Project:
        """Update a project.

        Args:
            project_id: Project ID
            project_data: Project update data

        Returns:
            Updated project

        Raises:
            NotFoundError: If project not found
            ConflictError: If new name conflicts
        """
        project = await self.get_project(project_id)

        # Check name conflict if changing name
        if project_data.name and project_data.name != project.name:
            result = await self.db.execute(select(Project).where(Project.name == project_data.name))
            if result.scalar_one_or_none():
                raise ConflictError(f"Project with name '{project_data.name}' already exists")

        # Update fields
        update_data = project_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        await self.db.commit()
        await self.db.refresh(project, ["creator"])

        return project

    async def archive_project(self, project_id: uuid.UUID) -> Project:
        """Archive a project (soft delete).

        Args:
            project_id: Project ID

        Returns:
            Archived project

        Raises:
            NotFoundError: If project not found
        """
        project = await self.get_project(project_id)
        project.is_archived = True

        await self.db.commit()
        await self.db.refresh(project)

        return project
