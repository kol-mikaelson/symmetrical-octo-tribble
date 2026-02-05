"""Unit tests for validators."""
import pytest

from src.utils.validators import (
    validate_password_strength,
    validate_email_format,
    validate_username,
)


class TestPasswordValidation:
    """Test password strength validation."""
    
    def test_valid_password(self):
        """Test validation of strong password."""
        password = "StrongPass@123"
        is_valid, message = validate_password_strength(password)
        
        assert is_valid is True
        assert message == "Password is strong"
    
    def test_password_too_short(self):
        """Test password that is too short."""
        password = "Short1!"
        is_valid, message = validate_password_strength(password)
        
        assert is_valid is False
        assert "at least 8 characters" in message
    
    def test_password_no_uppercase(self):
        """Test password without uppercase letter."""
        password = "lowercase123!"
        is_valid, message = validate_password_strength(password)
        
        assert is_valid is False
        assert "uppercase" in message.lower()
    
    def test_password_no_lowercase(self):
        """Test password without lowercase letter."""
        password = "UPPERCASE123!"
        is_valid, message = validate_password_strength(password)
        
        assert is_valid is False
        assert "lowercase" in message.lower()
    
    def test_password_no_digit(self):
        """Test password without digit."""
        password = "NoDigits!@#"
        is_valid, message = validate_password_strength(password)
        
        assert is_valid is False
        assert "digit" in message.lower()
    
    def test_password_no_special_char(self):
        """Test password without special character."""
        password = "NoSpecial123"
        is_valid, message = validate_password_strength(password)
        
        assert is_valid is False
        assert "special character" in message.lower()


class TestEmailValidation:
    """Test email format validation."""
    
    def test_valid_email(self):
        """Test validation of valid email."""
        email = "user@example.com"
        is_valid, message = validate_email_format(email)
        
        assert is_valid is True
    
    def test_valid_email_with_subdomain(self):
        """Test validation of email with subdomain."""
        email = "user@mail.example.com"
        is_valid, message = validate_email_format(email)
        
        assert is_valid is True
    
    def test_invalid_email_no_at(self):
        """Test email without @ symbol."""
        email = "userexample.com"
        is_valid, message = validate_email_format(email)
        
        assert is_valid is False
    
    def test_invalid_email_no_domain(self):
        """Test email without domain."""
        email = "user@"
        is_valid, message = validate_email_format(email)
        
        assert is_valid is False
    
    def test_invalid_email_no_username(self):
        """Test email without username."""
        email = "@example.com"
        is_valid, message = validate_email_format(email)
        
        assert is_valid is False
    
    def test_invalid_email_spaces(self):
        """Test email with spaces."""
        email = "user name@example.com"
        is_valid, message = validate_email_format(email)
        
        assert is_valid is False


class TestUsernameValidation:
    """Test username validation."""
    
    def test_valid_username(self):
        """Test validation of valid username."""
        username = "john_doe123"
        is_valid, message = validate_username(username)
        
        assert is_valid is True
    
    def test_valid_username_short(self):
        """Test validation of minimum length username."""
        username = "abc"
        is_valid, message = validate_username(username)
        
        assert is_valid is True
    
    def test_username_too_short(self):
        """Test username that is too short."""
        username = "ab"
        is_valid, message = validate_username(username)
        
        assert is_valid is False
        assert "at least 3 characters" in message
    
    def test_username_too_long(self):
        """Test username that is too long."""
        username = "a" * 51
        is_valid, message = validate_username(username)
        
        assert is_valid is False
        assert "maximum 50 characters" in message
    
    def test_username_with_spaces(self):
        """Test username with spaces."""
        username = "john doe"
        is_valid, message = validate_username(username)
        
        assert is_valid is False
        assert "alphanumeric" in message.lower() or "underscore" in message.lower()
    
    def test_username_with_special_chars(self):
        """Test username with special characters."""
        username = "john@doe"
        is_valid, message = validate_username(username)
        
        assert is_valid is False
    
    def test_username_starts_with_number(self):
        """Test username starting with number."""
        username = "123john"
        is_valid, message = validate_username(username)
        
        # This should be valid
        assert is_valid is True
