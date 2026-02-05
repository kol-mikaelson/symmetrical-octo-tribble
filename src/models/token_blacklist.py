"""Token blacklist model for JWT invalidation."""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from src.database.database import Base


class TokenBlacklist(Base):
    """Token blacklist model for JWT invalidation on logout."""

    __tablename__ = "token_blacklist"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)

    # Token Information
    jti: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)  # JWT ID
    token_type: Mapped[str] = mapped_column(String(20), nullable=False)  # access or refresh

    # Expiry
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Timestamp
    blacklisted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        """String representation of TokenBlacklist."""
        return f"<TokenBlacklist(jti={self.jti}, type={self.token_type})>"
