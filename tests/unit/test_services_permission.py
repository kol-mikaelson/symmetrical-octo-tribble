import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock
from src.services.permission_service import PermissionService
from src.models.user import User, UserRole
from src.models.project import Project
from src.models.issue import Issue
from src.app.exceptions import InsufficientPermissionsError

@pytest.fixture
def permission_service(mock_db_session):
    return PermissionService(mock_db_session)

@pytest.fixture
def admin_user():
    return User(id=uuid.uuid4(), role=UserRole.ADMIN)

@pytest.fixture
def manager_user():
    return User(id=uuid.uuid4(), role=UserRole.MANAGER)

@pytest.fixture
def dev_user():
    return User(id=uuid.uuid4(), role=UserRole.DEVELOPER)

@pytest.mark.asyncio
async def test_can_create_project(permission_service, admin_user, manager_user, dev_user):
    """Test project creation permissions."""
    assert await permission_service.can_create_project(admin_user) is True
    assert await permission_service.can_create_project(manager_user) is True
    assert await permission_service.can_create_project(dev_user) is False

@pytest.mark.asyncio
async def test_can_edit_project(permission_service, mock_db_session, admin_user, manager_user, dev_user):
    """Test project edit permissions."""
    project_id = uuid.uuid4()
    mock_project = Project(id=project_id, created_by=manager_user.id)
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_project
    
    # Admin can always edit
    assert await permission_service.can_edit_project(admin_user, project_id) is True
    
    # Creator (manager) can edit
    assert await permission_service.can_edit_project(manager_user, project_id) is True
    
    # Random dev cannot edit
    assert await permission_service.can_edit_project(dev_user, project_id) is False

@pytest.mark.asyncio
async def test_require_permission(permission_service, dev_user):
    """Test require_permission raises exception."""
    # Dev cannot create project
    with pytest.raises(InsufficientPermissionsError):
        await permission_service.require_permission(dev_user, "create_project")
    
    # Dev can create issue
    await permission_service.require_permission(dev_user, "create_issue")

@pytest.mark.asyncio
async def test_require_role(permission_service, dev_user):
    """Test require_role check."""
    # User is Developer
    permission_service.require_role(dev_user, UserRole.DEVELOPER)
    
    # User is NOT Admin
    with pytest.raises(InsufficientPermissionsError):
        permission_service.require_role(dev_user, UserRole.ADMIN)
