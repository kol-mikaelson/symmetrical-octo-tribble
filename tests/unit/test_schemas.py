"""Unit tests for Pydantic schemas."""
import pytest
from datetime import datetime
from pydantic import ValidationError

from src.schemas.user import UserCreate, UserResponse, UserLogin
from src.schemas.project import ProjectCreate, ProjectUpdate
from src.schemas.issue import IssueCreate, IssueUpdate
from src.schemas.comment import CommentCreate
from src.models.user import UserRole
from src.models.issue import IssuePriority, IssueStatus


class TestUserSchemas:
    """Test user-related schemas."""
    
    def test_user_create_valid(self):
        """Test valid user creation schema."""
        data = {
            "username": "johndoe",
            "email": "john@example.com",
            "password": "SecurePass@123",
            "role": "developer",
        }
        user = UserCreate(**data)
        
        assert user.username == "johndoe"
        assert user.email == "john@example.com"
        assert user.password == "SecurePass@123"
        assert user.role == "developer"
    
    def test_user_create_invalid_email(self):
        """Test user creation with invalid email."""
        data = {
            "username": "johndoe",
            "email": "invalid-email",
            "password": "SecurePass@123",
            "role": "developer",
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)
        
        assert "email" in str(exc_info.value).lower()
    
    def test_user_login_valid(self):
        """Test valid user login schema."""
        data = {
            "email": "john@example.com",
            "password": "SecurePass@123",
        }
        login = UserLogin(**data)
        
        assert login.email == "john@example.com"
        assert login.password == "SecurePass@123"
    
    def test_user_login_missing_password(self):
        """Test user login without password."""
        data = {
            "email": "john@example.com",
        }
        
        with pytest.raises(ValidationError):
            UserLogin(**data)


class TestProjectSchemas:
    """Test project-related schemas."""
    
    def test_project_create_valid(self):
        """Test valid project creation schema."""
        data = {
            "name": "Test Project",
            "description": "A test project",
            "key": "TEST",
        }
        project = ProjectCreate(**data)
        
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.key == "TEST"
    
    def test_project_create_missing_required(self):
        """Test project creation without required fields."""
        data = {
            "description": "A test project",
        }
        
        with pytest.raises(ValidationError):
            ProjectCreate(**data)
    
    def test_project_update_partial(self):
        """Test project update with partial data."""
        data = {
            "name": "Updated Project Name",
        }
        project = ProjectUpdate(**data)
        
        assert project.name == "Updated Project Name"
        assert project.description is None
        assert project.key is None


class TestIssueSchemas:
    """Test issue-related schemas."""
    
    def test_issue_create_valid(self):
        """Test valid issue creation schema."""
        data = {
            "title": "Test Issue",
            "description": "Issue description",
            "priority": "high",
            "issue_type": "bug",
        }
        issue = IssueCreate(**data)
        
        assert issue.title == "Test Issue"
        assert issue.description == "Issue description"
        assert issue.priority == "high"
        assert issue.issue_type == "bug"
    
    def test_issue_create_missing_title(self):
        """Test issue creation without title."""
        data = {
            "description": "Issue description",
            "priority": "high",
        }
        
        with pytest.raises(ValidationError):
            IssueCreate(**data)
    
    def test_issue_update_status(self):
        """Test issue update with status change."""
        data = {
            "status": "in_progress",
        }
        issue = IssueUpdate(**data)
        
        assert issue.status == "in_progress"
        assert issue.title is None


class TestCommentSchemas:
    """Test comment-related schemas."""
    
    def test_comment_create_valid(self):
        """Test valid comment creation schema."""
        data = {
            "content": "This is a test comment",
        }
        comment = CommentCreate(**data)
        
        assert comment.content == "This is a test comment"
    
    def test_comment_create_empty_content(self):
        """Test comment creation with empty content."""
        data = {
            "content": "",
        }
        
        # Should fail validation for empty content
        with pytest.raises(ValidationError):
            CommentCreate(**data)
    
    def test_comment_create_missing_content(self):
        """Test comment creation without content."""
        data = {}
        
        with pytest.raises(ValidationError):
            CommentCreate(**data)
