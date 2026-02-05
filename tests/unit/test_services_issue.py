import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock
from src.services.issue_service import IssueService
from src.schemas.issue import IssueCreate, IssueUpdate, IssueStatus, IssuePriority
from src.models.issue import Issue
from src.models.project import Project
from src.models.user import User, UserRole
from src.app.exceptions import NotFoundError, ForbiddenError

@pytest.fixture
def issue_service(mock_db_session):
    return IssueService(mock_db_session)

@pytest.fixture
def mock_user_reporter():
    return User(id=uuid.uuid4(), username="reporter", role=UserRole.DEVELOPER)

@pytest.fixture
def mock_user_dev():
    return User(id=uuid.uuid4(), username="dev", role=UserRole.DEVELOPER)

@pytest.mark.asyncio
async def test_create_issue(issue_service, mock_db_session, mock_user_reporter):
    """Test creating an issue."""
    # Mock project exists
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = Project(id=uuid.uuid4())
    
    project_id = uuid.uuid4()
    issue_data = IssueCreate(
        title="Bug", 
        description="Desc", 
        priority=IssuePriority.HIGH,
        project_id=project_id  # This is in data, but service might need it passed explicitly if signature demands
    )
    
    # Signature: create_issue(project_id, issue_data, reporter)
    issue = await issue_service.create_issue(project_id, issue_data, mock_user_reporter)
    
    assert issue.title == "Bug"
    assert issue.reporter_id == mock_user_reporter.id
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_update_issue_status(issue_service, mock_db_session, mock_user_dev):
    """Test updating issue status."""
    issue_id = uuid.uuid4()
    mock_issue = Issue(
        id=issue_id, 
        title="Bug", 
        status=IssueStatus.OPEN, 
        priority=IssuePriority.MEDIUM
    )
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_issue
    
    update_data = IssueUpdate(status=IssueStatus.IN_PROGRESS)
    # Signature: update_issue(issue_id, issue_data) - user not needed unless logic uses it
    # Looking at view_file result, update_issue takes (self, issue_id, issue_data)
    result = await issue_service.update_issue(issue_id, update_data)
    
    assert result.status == IssueStatus.IN_PROGRESS
    mock_db_session.commit.assert_called_once()
