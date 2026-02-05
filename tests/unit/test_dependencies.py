import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException, status
from src.app.dependencies import get_current_user, get_current_active_user
from src.models.user import User
from src.app.exceptions import UnauthorizedError
from src.utils.security import create_access_token
import uuid

@pytest.fixture
def mock_auth_service():
    return AsyncMock()

@pytest.fixture
def mock_request():
    request = MagicMock()
    request.headers.get.return_value = "Bearer valid_token"
    return request

@pytest.mark.asyncio
async def test_get_current_user_valid(mock_db_session, mock_settings):
    """Test get_current_user with valid token."""
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, username="test", is_active=True)
    
    # dependencies.get_current_user calls auth_service.get_current_user
    # We need to mock the auth_service dependency that is injected
    mock_auth_service = AsyncMock()
    mock_auth_service.get_current_user.return_value = mock_user
    
    # We pass the mocked auth_service directly
    credentials = MagicMock()
    credentials.credentials = "valid_token"
    
    user = await get_current_user(credentials, mock_auth_service)
    assert user.id == user_id

@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """Test get_current_user with invalid token."""
    mock_auth_service = AsyncMock()
    mock_auth_service.get_current_user.side_effect = UnauthorizedError("Invalid")
    
    credentials = MagicMock()
    credentials.credentials = "invalid"

    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials, mock_auth_service)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_get_current_active_user():
    """Test get_current_active_user."""
    active_user = User(is_active=True)
    assert await get_current_active_user(active_user) == active_user
    
    inactive_user = User(is_active=False)
    with pytest.raises(HTTPException) as exc:
        await get_current_active_user(inactive_user)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
