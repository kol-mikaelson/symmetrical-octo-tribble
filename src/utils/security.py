"""Security utilities for password hashing and JWT token management."""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
import jwt
from passlib.context import CryptContext
import bleach

from src.app.config import settings
from src.app.exceptions import TokenExpiredError, UnauthorizedError


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def load_rsa_key(key_path: str, is_private: bool = False) -> str:
    """Load RSA key from file.

    Args:
        key_path: Path to key file
        is_private: Whether this is a private key

    Returns:
        Key content as string

    Raises:
        FileNotFoundError: If key file doesn't exist
    """
    path = Path(key_path)
    if not path.exists():
        raise FileNotFoundError(
            f"{'Private' if is_private else 'Public'} key not found at {key_path}. "
            f"Generate keys with: openssl genrsa -out private_key.pem 2048 && "
            f"openssl rsa -in private_key.pem -pubout -out public_key.pem"
        )
    return path.read_text()


def create_access_token(
    user_id: uuid.UUID,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, str]:
    """Create a JWT access token.

    Args:
        user_id: User ID
        role: User role
        expires_delta: Token expiry duration

    Returns:
        Tuple of (token, jti)
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)

    jti = str(uuid.uuid4())
    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": jti,
        "type": "access",
    }

    private_key = load_rsa_key(settings.jwt_private_key_path, is_private=True)
    encoded_jwt = jwt.encode(to_encode, private_key, algorithm=settings.jwt_algorithm)

    return encoded_jwt, jti


def create_refresh_token(
    user_id: uuid.UUID,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, str]:
    """Create a JWT refresh token.

    Args:
        user_id: User ID
        role: User role
        expires_delta: Token expiry duration

    Returns:
        Tuple of (token, jti)
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.jwt_refresh_token_expire_days)

    jti = str(uuid.uuid4())
    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": jti,
        "type": "refresh",
    }

    private_key = load_rsa_key(settings.jwt_private_key_path, is_private=True)
    encoded_jwt = jwt.encode(to_encode, private_key, algorithm=settings.jwt_algorithm)

    return encoded_jwt, jti


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and verify a JWT token.

    Args:
        token: JWT token

    Returns:
        Decoded token payload

    Raises:
        TokenExpiredError: If token has expired
        UnauthorizedError: If token is invalid
    """
    try:
        public_key = load_rsa_key(settings.jwt_public_key_path, is_private=False)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise UnauthorizedError(f"Invalid token: {str(e)}")


def sanitize_html(content: str) -> str:
    """Sanitize HTML content to prevent XSS attacks.

    Args:
        content: HTML content to sanitize

    Returns:
        Sanitized HTML content
    """
    allowed_tags = [
        "p", "br", "strong", "em", "u", "h1", "h2", "h3", "h4", "h5", "h6",
        "ul", "ol", "li", "a", "code", "pre", "blockquote",
    ]
    allowed_attributes = {
        "a": ["href", "title"],
        "code": ["class"],
    }

    return bleach.clean(
        content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True,
    )


def generate_request_id() -> str:
    """Generate a unique request ID for tracking.

    Returns:
        Request ID
    """
    return str(uuid.uuid4())
