"""Audit logging service for tracking sensitive operations."""
import uuid
from datetime import datetime
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
import json

from src.models.audit_log import AuditLog
from src.models.user import User


class AuditService:
    """Audit logging service for tracking operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize audit service.

        Args:
            db: Database session
        """
        self.db = db

    async def log_action(
        self,
        user: Optional[User],
        action: str,
        resource: str,
        status: str = "success",
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log an action to the audit log.

        Args:
            user: User performing the action (None for anonymous)
            action: Action being performed
            resource: Resource being acted upon
            status: Status of the action (success, failure, denied)
            old_value: Old value (for updates)
            new_value: New value (for updates)
            ip_address: IP address of the request
            user_agent: User agent of the request

        Returns:
            Created audit log entry
        """
        # Convert values to JSON strings
        old_value_str = json.dumps(old_value) if old_value is not None else None
        new_value_str = json.dumps(new_value) if new_value is not None else None

        audit_log = AuditLog(
            user_id=user.id if user else None,
            action=action,
            resource=resource,
            old_value=old_value_str,
            new_value=new_value_str,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
        )

        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)

        return audit_log

    async def log_auth_event(
        self,
        action: str,
        email: str,
        status: str,
        ip_address: str,
        user_agent: str,
        user: Optional[User] = None,
    ) -> None:
        """Log an authentication event.

        Args:
            action: Authentication action (login, logout, register, etc.)
            email: User email
            status: Status of the action
            ip_address: IP address
            user_agent: User agent
            user: User object if available
        """
        await self.log_action(
            user=user,
            action=action,
            resource=f"auth:{email}",
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_permission_denial(
        self,
        user: User,
        action: str,
        resource: str,
        ip_address: str,
    ) -> None:
        """Log a permission denial.

        Args:
            user: User who was denied
            action: Action that was denied
            resource: Resource that was protected
            ip_address: IP address
        """
        await self.log_action(
            user=user,
            action=action,
            resource=resource,
            status="denied",
            ip_address=ip_address,
        )

    async def log_state_transition(
        self,
        user: User,
        resource: str,
        old_state: str,
        new_state: str,
        ip_address: str,
    ) -> None:
        """Log a state transition.

        Args:
            user: User performing the transition
            resource: Resource being transitioned
            old_state: Old state
            new_state: New state
            ip_address: IP address
        """
        await self.log_action(
            user=user,
            action="STATE_TRANSITION",
            resource=resource,
            status="success",
            old_value=old_state,
            new_value=new_state,
            ip_address=ip_address,
        )
