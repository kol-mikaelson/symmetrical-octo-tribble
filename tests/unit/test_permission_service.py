"""Unit tests for permission service."""
import pytest
from unittest.mock import Mock
from uuid import uuid4

from src.services.permission_service import PermissionService
from src.models.user import User, UserRole
from src.models.project import Project
from src.models.issue import Issue
from src.models.comment import Comment
from src.app.exceptions import ForbiddenError


@pytest.fixture
def permission_service():
    """Create permission service instance."""
    return PermissionService()


@pytest.fixture
def developer_user():
    """Create a developer user."""
    return User(
        id=uuid4(),
        username="developer",
        email="dev@example.com",
        role=UserRole.DEVELOPER,
        is_active=True,
    )


@pytest.fixture
def manager_user():
    """Create a manager user."""
    return User(
        id=uuid4(),
        username="manager",
        email="manager@example.com",
        role=UserRole.MANAGER,
        is_active=True,
    )


@pytest.fixture
def admin_user():
    """Create an admin user."""
    return User(
        id=uuid4(),
        username="admin",
        email="admin@example.com",
        role=UserRole.ADMIN,
        is_active=True,
    )


@pytest.fixture
def sample_project(manager_user):
    """Create a sample project."""
    return Project(
        id=uuid4(),
        name="Test Project",
        key="TEST",
        owner_id=manager_user.id,
    )


@pytest.fixture
def sample_issue(developer_user, sample_project):
    """Create a sample issue."""
    return Issue(
        id=uuid4(),
        title="Test Issue",
        project_id=sample_project.id,
        reporter_id=developer_user.id,
    )


class TestProjectPermissions:
    """Test project-related permissions."""
    
    def test_can_create_project_manager(self, permission_service, manager_user):
        """Test that managers can create projects."""
        assert permission_service.can_create_project(manager_user) is True
    
    def test_can_create_project_admin(self, permission_service, admin_user):
        """Test that admins can create projects."""
        assert permission_service.can_create_project(admin_user) is True
    
    def test_cannot_create_project_developer(self, permission_service, developer_user):
        """Test that developers cannot create projects."""
        assert permission_service.can_create_project(developer_user) is False
    
    def test_can_edit_project_owner(self, permission_service, manager_user, sample_project):
        """Test that project owner can edit project."""
        assert permission_service.can_edit_project(manager_user, sample_project) is True
    
    def test_can_edit_project_admin(self, permission_service, admin_user, sample_project):
        """Test that admins can edit any project."""
        assert permission_service.can_edit_project(admin_user, sample_project) is True
    
    def test_cannot_edit_project_non_owner(self, permission_service, developer_user, sample_project):
        """Test that non-owners cannot edit project."""
        assert permission_service.can_edit_project(developer_user, sample_project) is False
    
    def test_can_view_project_all_users(self, permission_service, developer_user, sample_project):
        """Test that all users can view projects."""
        assert permission_service.can_view_project(developer_user, sample_project) is True


class TestIssuePermissions:
    """Test issue-related permissions."""
    
    def test_can_create_issue_all_users(self, permission_service, developer_user, sample_project):
        """Test that all users can create issues."""
        assert permission_service.can_create_issue(developer_user, sample_project) is True
    
    def test_can_edit_issue_reporter(self, permission_service, developer_user, sample_issue):
        """Test that issue reporter can edit issue."""
        assert permission_service.can_edit_issue(developer_user, sample_issue) is True
    
    def test_can_edit_issue_manager(self, permission_service, manager_user, sample_issue):
        """Test that managers can edit any issue."""
        assert permission_service.can_edit_issue(manager_user, sample_issue) is True
    
    def test_can_edit_issue_admin(self, permission_service, admin_user, sample_issue):
        """Test that admins can edit any issue."""
        assert permission_service.can_edit_issue(admin_user, sample_issue) is True
    
    def test_can_edit_issue_assignee(self, permission_service, sample_issue):
        """Test that assignee can edit issue."""
        assignee = User(
            id=uuid4(),
            username="assignee",
            email="assignee@example.com",
            role=UserRole.DEVELOPER,
        )
        sample_issue.assignee_id = assignee.id
        
        assert permission_service.can_edit_issue(assignee, sample_issue) is True
    
    def test_cannot_edit_issue_other_user(self, permission_service, sample_issue):
        """Test that other users cannot edit issue."""
        other_user = User(
            id=uuid4(),
            username="other",
            email="other@example.com",
            role=UserRole.DEVELOPER,
        )
        
        assert permission_service.can_edit_issue(other_user, sample_issue) is False


class TestCommentPermissions:
    """Test comment-related permissions."""
    
    def test_can_edit_comment_author(self, permission_service, developer_user):
        """Test that comment author can edit comment."""
        comment = Comment(
            id=uuid4(),
            content="Test comment",
            author_id=developer_user.id,
        )
        
        assert permission_service.can_edit_comment(developer_user, comment) is True
    
    def test_can_edit_comment_admin(self, permission_service, admin_user, developer_user):
        """Test that admins can edit any comment."""
        comment = Comment(
            id=uuid4(),
            content="Test comment",
            author_id=developer_user.id,
        )
        
        assert permission_service.can_edit_comment(admin_user, comment) is True
    
    def test_cannot_edit_comment_other_user(self, permission_service, developer_user):
        """Test that other users cannot edit comment."""
        other_user = User(
            id=uuid4(),
            username="other",
            email="other@example.com",
            role=UserRole.DEVELOPER,
        )
        comment = Comment(
            id=uuid4(),
            content="Test comment",
            author_id=developer_user.id,
        )
        
        assert permission_service.can_edit_comment(other_user, comment) is False


class TestRoleChecks:
    """Test role-based checks."""
    
    def test_is_admin(self, permission_service, admin_user):
        """Test admin role check."""
        assert permission_service.is_admin(admin_user) is True
    
    def test_is_not_admin(self, permission_service, developer_user):
        """Test non-admin role check."""
        assert permission_service.is_admin(developer_user) is False
    
    def test_is_manager_or_admin_manager(self, permission_service, manager_user):
        """Test manager role check."""
        assert permission_service.is_manager_or_admin(manager_user) is True
    
    def test_is_manager_or_admin_admin(self, permission_service, admin_user):
        """Test admin passes manager check."""
        assert permission_service.is_manager_or_admin(admin_user) is True
    
    def test_is_not_manager_or_admin(self, permission_service, developer_user):
        """Test developer fails manager check."""
        assert permission_service.is_manager_or_admin(developer_user) is False
