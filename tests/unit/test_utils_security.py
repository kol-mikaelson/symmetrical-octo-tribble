import pytest
from src.utils.security import hash_password, verify_password, sanitize_html
from unittest.mock import patch, MagicMock

def test_password_hashing():
    """Test password hashing and verification."""
    password = "secret_password"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_sanitize_html():
    """Test HTML sanitization."""
    # Script tags should be removed
    dirty = '<script>alert("xss")</script><p>Safe content</p>'
    clean = sanitize_html(dirty)
    assert "<script>" not in clean
    assert "Safe content" in clean
    
    # Allowed tags should pass
    safe = '<p><strong>Bold</strong></p>'
    result = sanitize_html(safe)
    assert "<strong>" in result
    
    # Attributes whitelist
    link = '<a href="http://example.com" onclick="steal()">Link</a>'
    result = sanitize_html(link)
    assert 'href="http://example.com"' in result
    assert 'onclick' not in result
