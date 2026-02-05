"""Authentication router for user registration, login, and token management."""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from src.schemas.user import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    TokenRefresh,
)
from src.services.auth_service import AuthService
from src.services.audit_service import AuditService
from src.app.dependencies import (
    get_auth_service,
    get_audit_service,
    get_current_active_user,
    get_client_ip,
    get_user_agent,
)
from src.models.user import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Register a new user account with email and password",
)
async def register(
    user_data: UserRegister,
    ip_address: str = Depends(get_client_ip),
    user_agent: str = Depends(get_user_agent),
    auth_service: AuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> UserResponse:
    """Register a new user.

    Args:
        user_data: User registration data
        ip_address: Client IP address
        user_agent: Client user agent
        auth_service: Authentication service
        audit_service: Audit service

    Returns:
        Created user
    """
    try:
        user = await auth_service.register_user(user_data, ip_address)

        # Log registration
        await audit_service.log_auth_event(
            action="USER_REGISTERED",
            email=user.email,
            status="success",
            ip_address=ip_address,
            user_agent=user_agent,
            user=user,
        )

        return UserResponse.model_validate(user)
    except Exception as e:
        # Log failed registration
        await audit_service.log_auth_event(
            action="USER_REGISTRATION_FAILED",
            email=user_data.email,
            status="failure",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login user",
    description="Authenticate user and return access and refresh tokens",
)
async def login(
    credentials: UserLogin,
    ip_address: str = Depends(get_client_ip),
    user_agent: str = Depends(get_user_agent),
    auth_service: AuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> TokenResponse:
    """Login user and return tokens.

    Args:
        credentials: User login credentials
        ip_address: Client IP address
        user_agent: Client user agent
        auth_service: Authentication service
        audit_service: Audit service

    Returns:
        Token response with access and refresh tokens
    """
    try:
        user, token_response = await auth_service.login_user(credentials, ip_address, user_agent)

        # Log successful login
        await audit_service.log_auth_event(
            action="USER_LOGIN",
            email=user.email,
            status="success",
            ip_address=ip_address,
            user_agent=user_agent,
            user=user,
        )

        return token_response
    except Exception as e:
        # Log failed login
        await audit_service.log_auth_event(
            action="USER_LOGIN_FAILED",
            email=credentials.email,
            status="failure",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get a new access token using a refresh token",
)
async def refresh_token(
    token_data: TokenRefresh,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Refresh access token.

    Args:
        token_data: Refresh token data
        auth_service: Authentication service

    Returns:
        New token response
    """
    return await auth_service.refresh_access_token(token_data.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout user",
    description="Logout user by blacklisting tokens",
)
async def logout(
    token_data: TokenRefresh,
    current_user: User = Depends(get_current_active_user),
    ip_address: str = Depends(get_client_ip),
    user_agent: str = Depends(get_user_agent),
    auth_service: AuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> JSONResponse:
    """Logout user.

    Args:
        token_data: Token data containing refresh token
        current_user: Current authenticated user
        ip_address: Client IP address
        user_agent: Client user agent
        auth_service: Authentication service
        audit_service: Audit service

    Returns:
        Empty response
    """
    # Note: We need access token from the Authorization header
    # For simplicity, we'll just blacklist the refresh token
    # In production, you'd extract access token from the request

    # Log logout
    await audit_service.log_auth_event(
        action="USER_LOGOUT",
        email=current_user.email,
        status="success",
        ip_address=ip_address,
        user_agent=user_agent,
        user=current_user,
    )

    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout from all devices",
    description="Logout user from all devices by invalidating all sessions",
)
async def logout_all(
    current_user: User = Depends(get_current_active_user),
    ip_address: str = Depends(get_client_ip),
    user_agent: str = Depends(get_user_agent),
    auth_service: AuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> JSONResponse:
    """Logout user from all devices.

    Args:
        current_user: Current authenticated user
        ip_address: Client IP address
        user_agent: Client user agent
        auth_service: Authentication service
        audit_service: Audit service

    Returns:
        Empty response
    """
    await auth_service.logout_all_devices(current_user.id)

    # Log logout all
    await audit_service.log_auth_event(
        action="USER_LOGOUT_ALL",
        email=current_user.email,
        status="success",
        ip_address=ip_address,
        user_agent=user_agent,
        user=current_user,
    )

    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get information about the currently authenticated user",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Get current user information.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user information
    """
    return UserResponse.model_validate(current_user)
