"""Unit tests for authentication service."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from src.services.auth_service import AuthService
from src.models.user import User, UserRole
from src.schemas.user import UserCreate, UserLogin
from src.app.exceptions import (
    UnauthorizedError,
    BadRequestError,
    NotFoundError,
)


@pytest.fixture
def auth_service():
    """Create auth service instance."""
    return AuthService()


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock()


@pytest.fixture
def sample_user():
    """Create a sample user."""
    return User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password="$2b$12$hashedpassword",
        role=UserRole.DEVELOPER,
        is_active=True,
        failed_login_attempts=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


class TestAuthServiceRegistration:
    """Test user registration."""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, mock_db):
        """Test successful user registration."""
        user_data = UserCreate(
            username="newuser",
            email="new@example.com",
            password="SecurePass@123",
            role="developer",
        )
        
        # Mock database queries
        mock_db.execute = AsyncMock(return_value=Mock(scalar_one_or_none=Mock(return_value=None)))
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        with patch("src.services.auth_service.hash_password", return_value="hashed"):
            user = await auth_service.register_user(mock_db, user_data)
        
        assert mock_db.add.called
        assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, auth_service, mock_db, sample_user):
        """Test registration with duplicate email."""
        user_data = UserCreate(
            username="newuser",
            email="test@example.com",
            password="SecurePass@123",
            role="developer",
        )
        
        # Mock existing user
        mock_db.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=sample_user))
        )
        
        with pytest.raises(BadRequestError) as exc_info:
            await auth_service.register_user(mock_db, user_data)
        
        assert "already registered" in str(exc_info.value).lower()


class TestAuthServiceLogin:
    """Test user login."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, mock_db, sample_user):
        """Test successful login."""
        login_data = UserLogin(
            email="test@example.com",
            password="SecurePass@123",
        )
        
        # Mock database query
        mock_db.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=sample_user))
        )
        mock_db.commit = AsyncMock()
        
        with patch("src.services.auth_service.verify_password", return_value=True):
            with patch("src.services.auth_service.create_access_token", return_value="access_token"):
                with patch("src.services.auth_service.create_refresh_token", return_value="refresh_token"):
                    tokens = await auth_service.login(mock_db, login_data)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, auth_service, mock_db, sample_user):
        """Test login with invalid credentials."""
        login_data = UserLogin(
            email="test@example.com",
            password="WrongPassword",
        )
        
        # Mock database query
        mock_db.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=sample_user))
        )
        mock_db.commit = AsyncMock()
        
        with patch("src.services.auth_service.verify_password", return_value=False):
            with pytest.raises(UnauthorizedError) as exc_info:
                await auth_service.login(mock_db, login_data)
        
        assert "invalid" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_login_user_not_found(self, auth_service, mock_db):
        """Test login with non-existent user."""
        login_data = UserLogin(
            email="nonexistent@example.com",
            password="SecurePass@123",
        )
        
        # Mock no user found
        mock_db.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=None))
        )
        
        with pytest.raises(UnauthorizedError):
            await auth_service.login(mock_db, login_data)
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(self, auth_service, mock_db, sample_user):
        """Test login with inactive user."""
        sample_user.is_active = False
        login_data = UserLogin(
            email="test@example.com",
            password="SecurePass@123",
        )
        
        # Mock database query
        mock_db.execute = AsyncMock(
            return_value=Mock(scalar_one_or_none=Mock(return_value=sample_user))
        )
        
        with pytest.raises(UnauthorizedError) as exc_info:
            await auth_service.login(mock_db, login_data)
        
        assert "inactive" in str(exc_info.value).lower() or "locked" in str(exc_info.value).lower()


class TestAuthServiceTokenManagement:
    """Test token management."""
    
    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, auth_service, mock_db, sample_user):
        """Test successful token refresh."""
        refresh_token = "valid_refresh_token"
        
        # Mock token verification
        with patch("src.services.auth_service.verify_token", return_value={"sub": str(sample_user.id)}):
            # Mock database query
            mock_db.execute = AsyncMock(
                return_value=Mock(scalar_one_or_none=Mock(return_value=sample_user))
            )
            
            # Mock blacklist check
            with patch.object(auth_service, "is_token_blacklisted", return_value=False):
                with patch("src.services.auth_service.create_access_token", return_value="new_access_token"):
                    new_token = await auth_service.refresh_access_token(mock_db, refresh_token)
        
        assert new_token == "new_access_token"
    
    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, auth_service, mock_db):
        """Test token refresh with invalid token."""
        refresh_token = "invalid_token"
        
        # Mock token verification failure
        with patch("src.services.auth_service.verify_token", return_value=None):
            with pytest.raises(UnauthorizedError):
                await auth_service.refresh_access_token(mock_db, refresh_token)
    
    @pytest.mark.asyncio
    async def test_logout_success(self, auth_service, mock_db):
        """Test successful logout."""
        access_token = "valid_access_token"
        
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        
        await auth_service.logout(mock_db, access_token)
        
        assert mock_db.add.called
        assert mock_db.commit.called
