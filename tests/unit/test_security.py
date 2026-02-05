"""Unit tests for security utilities."""
import pytest
from datetime import datetime, timedelta

from src.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    sanitize_html,
    generate_token,
)


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword@123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPassword@123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPassword@123"
        wrong_password = "WrongPassword@123"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_hash_password_different_for_same_input(self):
        """Test that hashing same password twice gives different hashes."""
        password = "TestPassword@123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestTokenGeneration:
    """Test JWT token generation and verification."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_refresh_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_valid(self):
        """Test token verification with valid token."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(user_id)
        
        payload = verify_token(token)
        
        assert payload is not None
        assert payload.get("sub") == user_id
        assert "exp" in payload
    
    def test_verify_token_invalid(self):
        """Test token verification with invalid token."""
        invalid_token = "invalid.token.here"
        
        payload = verify_token(invalid_token)
        
        assert payload is None
    
    def test_token_expiration(self):
        """Test that token contains expiration."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(user_id)
        
        payload = verify_token(token)
        
        assert "exp" in payload
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        
        # Token should expire in the future
        assert exp_datetime > datetime.utcnow()


class TestHTMLSanitization:
    """Test HTML sanitization."""
    
    def test_sanitize_html_removes_script(self):
        """Test that script tags are removed."""
        dirty_html = '<p>Hello</p><script>alert("XSS")</script>'
        clean_html = sanitize_html(dirty_html)
        
        assert "<script>" not in clean_html
        assert "alert" not in clean_html
        assert "<p>Hello</p>" in clean_html or "Hello" in clean_html
    
    def test_sanitize_html_removes_onclick(self):
        """Test that onclick attributes are removed."""
        dirty_html = '<a href="#" onclick="alert(\'XSS\')">Click</a>'
        clean_html = sanitize_html(dirty_html)
        
        assert "onclick" not in clean_html
        assert "alert" not in clean_html
    
    def test_sanitize_html_allows_safe_tags(self):
        """Test that safe HTML tags are preserved."""
        safe_html = "<p>Hello <strong>World</strong></p>"
        clean_html = sanitize_html(safe_html)
        
        assert "Hello" in clean_html
        assert "World" in clean_html
    
    def test_sanitize_html_empty_string(self):
        """Test sanitization of empty string."""
        clean_html = sanitize_html("")
        
        assert clean_html == ""
    
    def test_sanitize_html_plain_text(self):
        """Test sanitization of plain text."""
        text = "Just plain text"
        clean_html = sanitize_html(text)
        
        assert clean_html == text


class TestTokenGenerator:
    """Test random token generation."""
    
    def test_generate_token_default_length(self):
        """Test token generation with default length."""
        token = generate_token()
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) == 64  # 32 bytes = 64 hex chars
    
    def test_generate_token_custom_length(self):
        """Test token generation with custom length."""
        length = 16
        token = generate_token(length)
        
        assert len(token) == length * 2  # bytes to hex doubles length
    
    def test_generate_token_uniqueness(self):
        """Test that generated tokens are unique."""
        token1 = generate_token()
        token2 = generate_token()
        
        assert token1 != token2
    
    def test_generate_token_hex_format(self):
        """Test that generated token is valid hex."""
        token = generate_token()
        
        # Should be valid hex string
        try:
            int(token, 16)
            is_hex = True
        except ValueError:
            is_hex = False
        
        assert is_hex is True
