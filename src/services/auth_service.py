"""Authentication service for user registration, login, and token management."""

import uuid
from datetime import datetime, timedelta

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.config import settings
from src.app.exceptions import (
    ConflictError,
    ForbiddenError,
    TokenExpiredError,
    UnauthorizedError,
)
from src.models.token_blacklist import TokenBlacklist
from src.models.user import User
from src.models.user_session import UserSession
from src.schemas.user import TokenResponse, UserLogin, UserRegister
from src.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class AuthService:
    """Authentication service for user management and token operations."""

    def __init__(self, db: AsyncSession, redis_client: redis.Redis) -> None:
        """Initialize authentication service.

        Args:
            db: Database session
            redis_client: Redis client
        """
        self.db = db
        self.redis = redis_client

    async def register_user(self, user_data: UserRegister, ip_address: str) -> User:
        """Register a new user.

        Args:
            user_data: User registration data
            ip_address: User's IP address

        Returns:
            Created user

        Raises:
            ConflictError: If username or email already exists
        """
        # Check if username exists
        result = await self.db.execute(select(User).where(User.username == user_data.username))
        if result.scalar_one_or_none():
            raise ConflictError("Username already exists")

        # Check if email exists
        result = await self.db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise ConflictError("Email already exists")

        # Create new user
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            role=user_data.role,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def login_user(
        self, credentials: UserLogin, ip_address: str, user_agent: str
    ) -> tuple[User, TokenResponse]:
        """Authenticate user and generate tokens.

        Args:
            credentials: User login credentials
            ip_address: User's IP address
            user_agent: User's user agent

        Returns:
            Tuple of (user, token_response)

        Raises:
            UnauthorizedError: If credentials are invalid
            ForbiddenError: If account is locked
        """
        # Get user by email
        result = await self.db.execute(select(User).where(User.email == credentials.email))
        user = result.scalar_one_or_none()

        if not user:
            raise UnauthorizedError("Invalid credentials")

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise ForbiddenError(f"Account is locked until {user.locked_until.isoformat()}")

        # Verify password
        if not verify_password(credentials.password, user.password_hash):
            # Increment failed login attempts
            user.failed_login_attempts += 1

            # Lock account if max attempts reached
            if user.failed_login_attempts >= settings.max_login_attempts:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=settings.account_lockout_duration_minutes
                )
                await self.db.commit()
                raise ForbiddenError(
                    f"Account locked due to too many failed login attempts. "
                    f"Try again after {settings.account_lockout_duration_minutes} minutes."
                )

            await self.db.commit()
            raise UnauthorizedError("Invalid credentials")

        # Check if user is active
        if not user.is_active:
            raise ForbiddenError("Account is inactive")

        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()

        # Generate tokens
        access_token, access_jti = create_access_token(user.id, user.role.value)
        refresh_token, refresh_jti = create_refresh_token(user.id, user.role.value)

        # Create user session
        session = UserSession(
            user_id=user.id,
            refresh_token_jti=refresh_jti,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days),
        )
        self.db.add(session)

        await self.db.commit()

        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",  # nosec B106
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

        return user, token_response

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New token response

        Raises:
            UnauthorizedError: If refresh token is invalid
            TokenExpiredError: If refresh token has expired
        """
        # Decode refresh token
        try:
            payload = decode_token(refresh_token)
        except (TokenExpiredError, UnauthorizedError) as e:
            raise e

        # Verify token type
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")

        # Check if token is blacklisted
        jti = payload.get("jti")
        if await self.is_token_blacklisted(jti):
            raise UnauthorizedError("Token has been revoked")

        # Get user
        user_id = uuid.UUID(payload.get("sub"))
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        # Generate new access token
        access_token, access_jti = create_access_token(user.id, user.role.value)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # Return same refresh token
            token_type="bearer",  # nosec B106
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    async def logout_user(self, access_token: str, refresh_token: str) -> None:
        """Logout user by blacklisting tokens.

        Args:
            access_token: Access token to blacklist
            refresh_token: Refresh token to blacklist
        """
        # Decode tokens to get JTIs and expiry
        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)

        # Blacklist access token
        access_blacklist = TokenBlacklist(
            jti=access_payload["jti"],
            token_type="access",  # nosec B106
            expires_at=datetime.fromtimestamp(access_payload["exp"]),
        )
        self.db.add(access_blacklist)

        # Blacklist refresh token
        refresh_blacklist = TokenBlacklist(
            jti=refresh_payload["jti"],
            token_type="refresh",  # nosec B106
            expires_at=datetime.fromtimestamp(refresh_payload["exp"]),
        )
        self.db.add(refresh_blacklist)

        # Delete user session
        await self.db.execute(
            select(UserSession).where(UserSession.refresh_token_jti == refresh_payload["jti"])
        )

        await self.db.commit()

    async def logout_all_devices(self, user_id: uuid.UUID) -> None:
        """Logout user from all devices.

        Args:
            user_id: User ID
        """
        # Get all user sessions
        result = await self.db.execute(select(UserSession).where(UserSession.user_id == user_id))
        sessions = result.scalars().all()

        # Blacklist all refresh tokens
        for session in sessions:
            blacklist = TokenBlacklist(
                jti=session.refresh_token_jti,
                token_type="refresh",  # nosec B106
                expires_at=session.expires_at,
            )
            self.db.add(blacklist)

        # Delete all sessions
        await self.db.execute(select(UserSession).where(UserSession.user_id == user_id))

        await self.db.commit()

    async def is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted.

        Args:
            jti: JWT ID

        Returns:
            True if blacklisted, False otherwise
        """
        # Check in database
        result = await self.db.execute(select(TokenBlacklist).where(TokenBlacklist.jti == jti))
        return result.scalar_one_or_none() is not None

    async def get_current_user(self, token: str) -> User:
        """Get current user from access token.

        Args:
            token: Access token

        Returns:
            Current user

        Raises:
            UnauthorizedError: If token is invalid or user not found
        """
        # Decode token
        payload = decode_token(token)

        # Verify token type
        if payload.get("type") != "access":
            raise UnauthorizedError("Invalid token type")

        # Check if token is blacklisted
        jti = payload.get("jti")
        if await self.is_token_blacklisted(jti):
            raise UnauthorizedError("Token has been revoked")

        # Get user
        user_id = uuid.UUID(payload.get("sub"))
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        return user
