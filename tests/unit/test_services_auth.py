import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.auth_service import AuthService
from src.schemas.user import UserRegister, UserLogin
from src.models.user import User, UserRole
from src.app.exceptions import ConflictError, UnauthorizedError

@pytest.fixture
def auth_service(mock_db_session, mock_redis):
    return AuthService(mock_db_session, mock_redis)

@pytest.mark.asyncio
async def test_register_user_success(auth_service, mock_db_session):
    """Test successful user registration."""
    # Setup mocks
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = None  # No existing user
    
    user_data = UserRegister(
        email="test@example.com",
        username="testuser",
        password="StrongPassword123!",
        role=UserRole.DEVELOPER
    )
    
    user = await auth_service.register_user(user_data, "127.0.0.1")
    
    assert user.email == user_data.email
    assert user.username == user_data.username
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_register_user_existing_email(auth_service, mock_db_session):
    """Test registration with existing email."""
    # First check (username) returns None, Second check (email) returns User
    mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [None, User()]
    
    user_data = UserRegister(
        email="existing@example.com",
        username="newuser",
        password="StrongPassword123!",
        role=UserRole.DEVELOPER
    )
    
    with pytest.raises(ConflictError):
        await auth_service.register_user(user_data, "127.0.0.1")

@pytest.mark.asyncio
async def test_login_user_success(auth_service, mock_db_session):
    """Test successful login."""
    # Mock user found
    user = User(
        id=MagicMock(),
        email="test@example.com",
        password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6PHs5.W5/X5J5.Y5.Y5.Y5", # Mock hash
        role=UserRole.DEVELOPER,
        is_active=True,
        failed_login_attempts=0
    )
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = user
    
    # Mock password verification (need to match what verify_password expects or mock it)
    with patch("src.services.auth_service.verify_password", return_value=True):
        credentials = UserLogin(email="test@example.com", password="Password123!")
        user_result, token = await auth_service.login_user(credentials, "127.0.0.1", "user-agent")
        
        assert user_result == user
        assert token.access_token is not None

from unittest.mock import patch
