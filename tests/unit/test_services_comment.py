import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock
from src.services.comment_service import CommentService
from src.schemas.comment import CommentCreate, CommentUpdate
from src.models.comment import Comment
from src.models.issue import Issue
from src.models.user import User

@pytest.fixture
def comment_service(mock_db_session):
    return CommentService(mock_db_session)

@pytest.mark.asyncio
async def test_create_comment(comment_service, mock_db_session):
    """Test creating a comment."""
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = Issue(id=uuid.uuid4())
    
    user = User(id=uuid.uuid4(), username="commenter")
    issue_id = uuid.uuid4()
    comment_data = CommentCreate(content="This is a comment", issue_id=issue_id)
    
    comment = await comment_service.create_comment(issue_id, comment_data, user)
    
    assert comment.content == "This is a comment"
    assert comment.issue_id == issue_id
    assert comment.author_id == user.id
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_update_comment(comment_service, mock_db_session):
    """Test updating a comment."""
    comment_id = uuid.uuid4()
    mock_comment = Comment(id=comment_id, content="Old content", author_id=uuid.uuid4())
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_comment
    
    update_data = CommentUpdate(content="New content")
    result = await comment_service.update_comment(comment_id, update_data)
    
    assert result.content == "New content"
    mock_db_session.commit.assert_called_once()
