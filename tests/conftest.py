import pytest
import sys
from unittest.mock import MagicMock, AsyncMock, patch

# Problem: We need to mock create_async_engine to avoid DB connection,
# but we need AsyncSession to be the real class (or close to it) for type checking/SQLAlchemy internals.

# Strategy: Allow import of sqlalchemy.ext.asyncio, but patch create_async_engine inside it
# BEFORE src.database.database is imported.

# We can't easily patch it before import unless we use sys.modules trick but better.
# Let's try to mock only the function.

with patch("sqlalchemy.ext.asyncio.create_async_engine") as mock_create_engine:
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine
    # Now import the modules that trigger DB init
    from src.database.database import Base, get_db
    
    # Import all models to ensure registry is populated
    from src.models.user import User
    from src.models.project import Project
    from src.models.issue import Issue
    from src.models.comment import Comment
    from src.models.user_session import UserSession
    from src.models.audit_log import AuditLog
    
    # We also need to fix dependencies that might import it differently
    pass

# Better approach for conftest: use an autouse fixture that patches it?
# Too late, imports happen at collection time.
# We must use sys.modules or careful patching.

# Let's restore real module but patch the function
import sqlalchemy.ext.asyncio
original_create = sqlalchemy.ext.asyncio.create_async_engine
sqlalchemy.ext.asyncio.create_async_engine = MagicMock()

import redis
redis.Redis = MagicMock()
import redis.asyncio
redis.asyncio.Redis = MagicMock()

@pytest.fixture
def mock_db_session():
    """Fixture for a mocked database session."""
    session = AsyncMock()
    # Mock execute/scalar_one_or_none/scalars/all chain
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    result_mock.scalars.return_value.all.return_value = []
    session.execute.return_value = result_mock
    return session

@pytest.fixture
def mock_redis():
    """Fixture for a mocked Redis client."""
    redis = AsyncMock()
    return redis

@pytest.fixture
def mock_settings(monkeypatch):
    """Fixture to override settings."""
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

    """Fixture for a mocked database session."""
    session = AsyncMock()
    # Mock execute/scalar_one_or_none/scalars/all chain
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    result_mock.scalars.return_value.all.return_value = []
    session.execute.return_value = result_mock
    return session

@pytest.fixture
def mock_redis():
    """Fixture for a mocked Redis client."""
    redis = AsyncMock()
    return redis

@pytest.fixture
def mock_settings(monkeypatch):
    """Fixture to override settings."""
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
