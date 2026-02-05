import pytest
from pydantic import ValidationError
from src.schemas.user import UserRegister, UserLogin, UserUpdate, UserResponse, UserRole
from src.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from src.schemas.issue import IssueCreate, IssueUpdate, IssueResponse, IssueStatus, IssuePriority
from datetime import datetime
import uuid

# User Schema Tests
def test_user_register_schema_valid():
    """Test valid user registration data."""
    data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "StrongPassword123!",
        "role": "developer"
    }
    user = UserRegister(**data)
    assert user.email == data["email"]
    assert user.role == UserRole.DEVELOPER

def test_user_register_schema_invalid_email():
    """Test invalid email in registration."""
    data = {
        "email": "invalid-email",
        "username": "testuser",
        "password": "StrongPassword123!",
    }
    with pytest.raises(ValidationError):
        UserRegister(**data)

def test_user_register_schema_weak_password():
    """Test weak password in registration."""
    data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "weak",
    }
    with pytest.raises(ValidationError):
        UserRegister(**data)

# Project Schema Tests
def test_project_create_schema():
    """Test project creation schema."""
    data = {
        "name": "Test Project",
        "description": "Test Description",
        "key": "TEST"
    }
    project = ProjectCreate(**data)
    # Check if 'key' exists, if not check 'name' or whatever is in schema
    # Based on view_file result, I will adjust this assertion
    assert project.name == "Test Project"

# Issue Schema Tests
def test_issue_create_schema():
    """Test issue creation schema."""
    data = {
        "title": "Bug found",
        "description": "Found a bug in the system",
        "priority": "high",
        "project_id": str(uuid.uuid4()),
        "assignee_id": str(uuid.uuid4())
    }
    issue = IssueCreate(**data)
    assert issue.priority == IssuePriority.HIGH

def test_issue_response_schema():
    """Test issue response schema."""
    data = {
        "id": uuid.uuid4(),
        "title": "Bug found",
        "description": "Found a bug",
        "status": "open",
        "priority": "high",
        "project_id": uuid.uuid4(),
        "reporter_id": uuid.uuid4(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    # Mocking lazy loaded relationships might be needed if validation touches them
    # But usually Pydantic from_attributes=True works on dicts too if structure matches
    issue = IssueResponse(**data)
    assert issue.id == data["id"]
    assert issue.status == IssueStatus.OPEN
