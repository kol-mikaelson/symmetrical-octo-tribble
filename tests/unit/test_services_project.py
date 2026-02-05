import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock
from src.services.project_service import ProjectService
from src.schemas.project import ProjectCreate, ProjectUpdate
from src.models.project import Project
from src.models.user import User
from src.app.exceptions import NotFoundError, ForbiddenError

@pytest.fixture
def project_service(mock_db_session):
    return ProjectService(mock_db_session)

@pytest.fixture
def mock_user():
    return User(id=uuid.uuid4(), username="owner", email="owner@test.com")

@pytest.mark.asyncio
async def test_create_project(project_service, mock_db_session, mock_user):
    """Test creating a project."""
    project_data = ProjectCreate(name="Test Project", description="Test Description")
    
    project = await project_service.create_project(project_data, mock_user)
    
    assert project.name == project_data.name
    assert project.description == project_data.description
    assert project.created_by == mock_user.id
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_project_found(project_service, mock_db_session):
    """Test retrieving an existing project."""
    project_id = uuid.uuid4()
    mock_project = Project(id=project_id, name="Found Project")
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_project
    
    result = await project_service.get_project(project_id)
    assert result == mock_project

@pytest.mark.asyncio
async def test_get_project_not_found(project_service, mock_db_session):
    """Test retrieving a non-existent project."""
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
    
    with pytest.raises(NotFoundError):
        await project_service.get_project(uuid.uuid4())

@pytest.mark.asyncio
async def test_update_project_success(project_service, mock_db_session, mock_user):
    """Test updating a project successfully."""
    project_id = uuid.uuid4()
    mock_project = Project(id=project_id, name="Old Name", created_by=mock_user.id)
    
    # First call is get_project (returns project), Second call is check name conflict (returns None)
    mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [mock_project, None]
    
    update_data = ProjectUpdate(name="New Name")
    # Signature: update_project(project_id, project_data)
    result = await project_service.update_project(project_id, update_data)
    
    assert result.name == "New Name"
    mock_db_session.commit.assert_called_once()
