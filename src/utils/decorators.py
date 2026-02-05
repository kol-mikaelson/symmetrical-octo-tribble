"""Utility decorators for common functionality."""

import functools
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def audit_log(action: str) -> Callable:
    """Decorator to automatically log actions to audit log.

    Args:
        action: Action name to log

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function that logs the action."""
            # Execute the function
            result = await func(*args, **kwargs)

            # Log the action (implementation will be in audit_service)
            logger.info(f"Action logged: {action}")

            return result

        return wrapper

    return decorator
