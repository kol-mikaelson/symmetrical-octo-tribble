"""Custom exception classes for the application."""
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status


class APIException(HTTPException):
    """Base exception class for API errors."""

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Initialize API exception.

        Args:
            status_code: HTTP status code
            error_code: Application-specific error code
            message: Human-readable error message
            details: Optional list of error details
        """
        self.error_code = error_code
        self.message = message
        self.details = details or []
        super().__init__(status_code=status_code, detail=message)


class ValidationError(APIException):
    """Raised when request validation fails."""

    def __init__(
        self, message: str = "Validation error", details: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Initialize validation error."""
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            message=message,
            details=details,
        )


class InvalidStateTransitionError(APIException):
    """Raised when an invalid state transition is attempted."""

    def __init__(
        self, message: str = "Invalid state transition", details: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Initialize invalid state transition error."""
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_STATE_TRANSITION",
            message=message,
            details=details,
        )


class UnauthorizedError(APIException):
    """Raised when authentication fails."""

    def __init__(
        self, message: str = "Unauthorized", details: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Initialize unauthorized error."""
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
            message=message,
            details=details,
        )


class TokenExpiredError(APIException):
    """Raised when JWT token has expired."""

    def __init__(
        self, message: str = "Token has expired", details: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Initialize token expired error."""
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="TOKEN_EXPIRED",
            message=message,
            details=details,
        )


class ForbiddenError(APIException):
    """Raised when user lacks permission for an action."""

    def __init__(
        self, message: str = "Forbidden", details: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Initialize forbidden error."""
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
            message=message,
            details=details,
        )


class InsufficientPermissionsError(APIException):
    """Raised when user has insufficient permissions."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Initialize insufficient permissions error."""
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="INSUFFICIENT_PERMISSIONS",
            message=message,
            details=details,
        )


class NotFoundError(APIException):
    """Raised when a resource is not found."""

    def __init__(
        self, message: str = "Resource not found", details: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Initialize not found error."""
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            message=message,
            details=details,
        )


class ConflictError(APIException):
    """Raised when a resource conflict occurs."""

    def __init__(
        self, message: str = "Resource conflict", details: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Initialize conflict error."""
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            message=message,
            details=details,
        )


class RateLimitError(APIException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Initialize rate limit error."""
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            message=message,
            details=details,
        )


class InternalError(APIException):
    """Raised when an internal server error occurs."""

    def __init__(
        self,
        message: str = "Internal server error",
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Initialize internal error."""
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_ERROR",
            message=message,
            details=details,
        )
