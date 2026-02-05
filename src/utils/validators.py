"""Custom validators for request validation."""
from typing import Optional
from src.models.issue import IssueStatus
from src.app.exceptions import InvalidStateTransitionError


# Valid state transitions for issues
VALID_STATE_TRANSITIONS = {
    IssueStatus.OPEN: [IssueStatus.IN_PROGRESS, IssueStatus.CLOSED],
    IssueStatus.IN_PROGRESS: [IssueStatus.RESOLVED, IssueStatus.OPEN],
    IssueStatus.RESOLVED: [IssueStatus.CLOSED, IssueStatus.REOPENED],
    IssueStatus.CLOSED: [IssueStatus.REOPENED],
    IssueStatus.REOPENED: [IssueStatus.IN_PROGRESS, IssueStatus.RESOLVED],
}


def validate_state_transition(
    current_status: IssueStatus,
    new_status: IssueStatus,
) -> None:
    """Validate issue state transition.

    Args:
        current_status: Current issue status
        new_status: New issue status

    Raises:
        InvalidStateTransitionError: If transition is not allowed
    """
    if current_status == new_status:
        return  # No transition

    valid_transitions = VALID_STATE_TRANSITIONS.get(current_status, [])
    if new_status not in valid_transitions:
        raise InvalidStateTransitionError(
            f"Cannot transition from {current_status.value} to {new_status.value}. "
            f"Valid transitions: {', '.join(s.value for s in valid_transitions)}"
        )


def validate_critical_issue_closure(
    priority: str,
    status: IssueStatus,
    comment_count: int,
) -> None:
    """Validate that critical issues have comments before closing.

    Args:
        priority: Issue priority
        status: New issue status
        comment_count: Number of comments on the issue

    Raises:
        InvalidStateTransitionError: If critical issue has no comments
    """
    if priority == "critical" and status == IssueStatus.CLOSED and comment_count == 0:
        raise InvalidStateTransitionError(
            "Critical issues cannot be closed without at least one comment"
        )
