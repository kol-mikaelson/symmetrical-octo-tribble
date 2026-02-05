import pytest
from src.utils.validators import validate_state_transition, validate_critical_issue_closure
from src.app.exceptions import InvalidStateTransitionError
from src.models.issue import IssueStatus
from unittest.mock import MagicMock

def test_validate_state_transition_valid():
    """Test valid state transitions."""
    # Open -> In Progress
    validate_state_transition(IssueStatus.OPEN, IssueStatus.IN_PROGRESS)
    # In Progress -> Resolved
    validate_state_transition(IssueStatus.IN_PROGRESS, IssueStatus.RESOLVED)
    # No change
    validate_state_transition(IssueStatus.OPEN, IssueStatus.OPEN)

def test_validate_state_transition_invalid():
    """Test invalid state transitions."""
    # Open -> Resolved (direct skip not allowed)
    with pytest.raises(InvalidStateTransitionError):
        validate_state_transition(IssueStatus.OPEN, IssueStatus.RESOLVED)
    
    # Closed -> Open (must reopen first)
    with pytest.raises(InvalidStateTransitionError) as exc:
        validate_state_transition(IssueStatus.CLOSED, IssueStatus.OPEN)
    assert "Cannot transition from closed to open" in str(exc.value)

def test_validate_critical_issue_closure():
    """Test critical issue closure validation."""
    # Critical issue with comments -> OK
    validate_critical_issue_closure("critical", IssueStatus.CLOSED, 1)
    
    # Critical issue without comments -> Error
    with pytest.raises(InvalidStateTransitionError):
        validate_critical_issue_closure("critical", IssueStatus.CLOSED, 0)
        
    # Non-critical issue without comments -> OK
    validate_critical_issue_closure("high", IssueStatus.CLOSED, 0)
