import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from src.app.main import app
from src.app.dependencies import get_auth_service, get_db
from src.schemas.user import UserResponse, TokenResponse
from src.models.user import User, UserRole
import uuid

# We need to override dependencies
client = TestClient(app)

@pytest.fixture
def mock_auth_service_dependency():
    mock_service = AsyncMock()
    app.dependency_overrides[get_auth_service] = lambda: mock_service
    yield mock_service
    app.dependency_overrides = {}

from src.app.dependencies import get_auth_service, get_db, get_audit_service

@pytest.fixture
def mock_audit_service_dependency():
    mock_service = AsyncMock()
    app.dependency_overrides[get_audit_service] = lambda: mock_service
    yield mock_service
    # app.dependency_overrides is cleared/managed by other fixtures usually, 
    # but strictly we should clean up. Since we share client, it persists.
    
@pytest.fixture
def mock_db_dependency(mock_db_session):
    app.dependency_overrides[get_db] = lambda: mock_db_session
    yield mock_db_session

def test_register_endpoint(mock_auth_service_dependency, mock_db_dependency, mock_audit_service_dependency):
    """Test /auth/register endpoint."""
    user_id = uuid.uuid4()
    mock_user_response = UserResponse(
        id=user_id,
        username="newuser",
        email="test@example.com",
        role=UserRole.DEVELOPER,
        is_active=True,
        created_at="2024-01-01T00:00:00"
    )
    mock_auth_service_dependency.register_user.return_value = mock_user_response
    
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "username": "newuser",
        "password": "StrongPassword123!",
        "role": "developer"
    })
    
    assert response.status_code == 201
    assert response.json()["username"] == "newuser"

def test_login_endpoint(mock_auth_service_dependency, mock_db_dependency, mock_audit_service_dependency):
    """Test /auth/login endpoint."""
    mock_token = TokenResponse(
        access_token="access",
        refresh_token="refresh",
        token_type="bearer",
        expires_in=3600
    )
    
    # Return a MagicMock for user to be safe
    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    mock_user.id = uuid.uuid4()
    mock_user.is_active = True
    mock_user.role = UserRole.DEVELOPER
    
    # login_user returns (user, token) tuple
    mock_auth_service_dependency.login_user.return_value = (mock_user, mock_token)
    
    response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "Password123!"
    })
    
    assert response.status_code == 200
    assert response.json()["access_token"] == "access"
