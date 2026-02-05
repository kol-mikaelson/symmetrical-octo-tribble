
import pytest
from src.utils.validators import validate_state_transition, validate_critical_issue_closure
from src.models.issue import IssueStatus
from src.app.exceptions import InvalidStateTransitionError

def test_validate_state_transition_valid():
    """Test valid state transitions."""
    # Open -> In Progress
    validate_state_transition(IssueStatus.OPEN, IssueStatus.IN_PROGRESS)
    # In Progress -> Resolved
    validate_state_transition(IssueStatus.IN_PROGRESS, IssueStatus.RESOLVED)
    # Same status
    validate_state_transition(IssueStatus.OPEN, IssueStatus.OPEN)

def test_validate_state_transition_invalid():
    """Test invalid state transitions."""
    # Open -> Closed (Valid based on code? let's check dict)
    # VALID_STATE_TRANSITIONS = {IssueStatus.OPEN: [IssueStatus.IN_PROGRESS, IssueStatus.CLOSED]...}
    # Open -> Reopened (Invalid)
    with pytest.raises(InvalidStateTransitionError):
        validate_state_transition(IssueStatus.OPEN, IssueStatus.REOPENED)

def test_validate_critical_issue_closure_valid():
    """Test valid closure of critical issue."""
    # Critical with comments
    validate_critical_issue_closure("critical", IssueStatus.CLOSED, comment_count=1)
    # Non-critical with no comments
    validate_critical_issue_closure("low", IssueStatus.CLOSED, comment_count=0)
    # Critical but not closing
    validate_critical_issue_closure("critical", IssueStatus.IN_PROGRESS, comment_count=0)

def test_validate_critical_issue_closure_invalid():
    """Test invalid closure of critical issue."""
    # Critical with no comments
    with pytest.raises(InvalidStateTransitionError):
        validate_critical_issue_closure("critical", IssueStatus.CLOSED, comment_count=0)
