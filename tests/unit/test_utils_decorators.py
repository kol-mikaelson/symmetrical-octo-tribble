import pytest
from unittest.mock import patch
from src.utils.decorators import audit_log

@pytest.mark.asyncio
async def test_audit_log_decorator():
    """Test audit_log decorator."""
    action_name = "TEST_ACTION"
    
    # Create the decorated function
    @audit_log(action=action_name)
    async def sample_function(arg):
        return f"Result: {arg}"
    
    with patch("src.utils.decorators.logger") as mock_logger:
        result = await sample_function("test")
        
        assert result == "Result: test"
        mock_logger.info.assert_called_once()
        assert action_name in mock_logger.info.call_args[0][0]
