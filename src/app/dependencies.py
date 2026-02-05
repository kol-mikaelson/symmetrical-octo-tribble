"""FastAPI dependency injection functions."""

from collections.abc import AsyncGenerator
from typing import Optional

import redis.asyncio as redis
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.config import settings
from src.app.exceptions import InsufficientPermissionsError
from src.database.database import get_db
from src.models.user import User, UserRole
from src.services.audit_service import AuditService
from src.services.auth_service import AuthService
from src.services.permission_service import PermissionService

# HTTP Bearer token scheme
security = HTTPBearer()


# Redis client (singleton)
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """Get Redis client.

    Yields:
        Redis client
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            password=settings.redis_password if settings.redis_password else None,
            decode_responses=True,
        )

    try:
        yield _redis_client
    finally:
        pass  # Keep connection alive


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()


async def get_auth_service(
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> AuthService:
    """Get authentication service.

    Args:
        db: Database session
        redis_client: Redis client

    Returns:
        Authentication service
    """
    return AuthService(db, redis_client)


async def get_permission_service(
    db: AsyncSession = Depends(get_db),
) -> PermissionService:
    """Get permission service.

    Args:
        db: Database session

    Returns:
        Permission service
    """
    return PermissionService(db)


async def get_audit_service(
    db: AsyncSession = Depends(get_db),
) -> AuditService:
    """Get audit service.

    Args:
        db: Database session

    Returns:
        Audit service
    """
    return AuditService(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Get current authenticated user.

    Args:
        credentials: HTTP authorization credentials
        auth_service: Authentication service

    Returns:
        Current user

    Raises:
        UnauthorizedError: If authentication fails
    """
    try:
        token = credentials.credentials
        user = await auth_service.get_current_user(token)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user.

    Args:
        current_user: Current user

    Returns:
        Current active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def require_role(*roles: UserRole):
    """Dependency to require specific user roles.

    Args:
        *roles: Required roles

    Returns:
        Dependency function
    """

    async def role_checker(
        current_user: User = Depends(get_current_active_user),
        permission_service: PermissionService = Depends(get_permission_service),
    ) -> User:
        """Check if user has required role.

        Args:
            current_user: Current user
            permission_service: Permission service

        Returns:
            Current user

        Raises:
            HTTPException: If user lacks required role
        """
        try:
            permission_service.require_role(current_user, *roles)
            return current_user
        except InsufficientPermissionsError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )

    return role_checker


async def get_client_ip(
    x_forwarded_for: Optional[str] = Header(None),
    x_real_ip: Optional[str] = Header(None),
) -> str:
    """Get client IP address from headers.

    Args:
        x_forwarded_for: X-Forwarded-For header
        x_real_ip: X-Real-IP header

    Returns:
        Client IP address
    """
    if x_forwarded_for:
        # Get first IP from X-Forwarded-For
        return x_forwarded_for.split(",")[0].strip()
    elif x_real_ip:
        return x_real_ip
    else:
        return "unknown"


async def get_user_agent(
    user_agent: Optional[str] = Header(None),
) -> str:
    """Get user agent from headers.

    Args:
        user_agent: User-Agent header

    Returns:
        User agent string
    """
    return user_agent or "unknown"
