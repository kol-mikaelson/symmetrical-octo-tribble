"""Main FastAPI application."""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime

from src.app.config import settings
from src.app.exceptions import APIException
from src.database.database import init_db, close_db
from src.app.dependencies import close_redis
from src.routers import auth, projects, issues, comments
from src.schemas.common import HealthResponse, ErrorResponse, ErrorDetail
from src.utils.security import generate_request_id


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager.

    Args:
        app: FastAPI application

    Yields:
        None
    """
    # Startup
    logger.info("Starting up application...")
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await close_db()
    await close_redis()
    logger.info("Application shut down")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-ready Bug Reporting System API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# Global exception handlers
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handle custom API exceptions.

    Args:
        request: Request object
        exc: API exception

    Returns:
        JSON error response
    """
    request_id = generate_request_id()

    # Log error
    logger.error(
        f"API Exception: {exc.error_code} - {exc.message}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        },
    )

    error_response = ErrorResponse(
        code=exc.error_code,
        message=exc.message,
        details=exc.details,
        request_id=request_id,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors.

    Args:
        request: Request object
        exc: Validation error

    Returns:
        JSON error response
    """
    request_id = generate_request_id()

    # Convert Pydantic errors to our format
    details = [
        ErrorDetail(
            field=".".join(str(loc) for loc in error["loc"]),
            issue=error["msg"],
        )
        for error in exc.errors()
    ]

    error_response = ErrorResponse(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        details=details,
        request_id=request_id,
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response.model_dump(),
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions.

    Args:
        request: Request object
        exc: Exception

    Returns:
        JSON error response
    """
    request_id = generate_request_id()

    # Log error with full traceback
    logger.exception(
        f"Unhandled exception: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        },
    )

    error_response = ErrorResponse(
        code="INTERNAL_ERROR",
        message="An internal server error occurred" if settings.is_production else str(exc),
        details=[],
        request_id=request_id,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
        headers={"X-Request-ID": request_id},
    )


# Health check endpoint
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check",
    description="Check if the API is running",
)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
    )


# Include routers
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(projects.router, prefix=settings.api_prefix)
app.include_router(issues.router, prefix=settings.api_prefix)
app.include_router(issues.issues_router, prefix=settings.api_prefix)
app.include_router(comments.router, prefix=settings.api_prefix)
app.include_router(comments.comments_router, prefix=settings.api_prefix)


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root endpoint.

    Returns:
        Welcome message
    """
    return {
        "message": "Bug Reporting System API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
