import pytest
from datetime import datetime, timedelta, timezone
from auth_service.src.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    create_token_hash
)

class TestPasswordHashing:
    def test_hash_password(self):
        """Test password hashing"""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False

class TestTokens:
    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": 1, "email": "test@example.com"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test refresh token creation"""
        data = {"sub": 1, "email": "test@example.com"}
        token = create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_access_token_valid(self):
        """Test access token verification with valid token"""
        data = {"sub": 1, "email": "test@example.com"}
        token = create_access_token(data)
        
        token_data = verify_token(token, "access")
        
        assert token_data is not None
        assert token_data.user_id == 1
        assert token_data.email == "test@example.com"

    def test_verify_refresh_token_valid(self):
        """Test refresh token verification with valid token"""
        data = {"sub": 1, "email": "test@example.com"}
        token = create_refresh_token(data)
        
        token_data = verify_token(token, "refresh")
        
        assert token_data is not None
        assert token_data.user_id == 1
        assert token_data.email == "test@example.com"

    def test_verify_token_invalid(self):
        """Test token verification with invalid token"""
        token_data = verify_token("invalid.token.here", "access")
        assert token_data is None

    def test_verify_token_wrong_type(self):
        """Test token verification with wrong token type"""
        data = {"sub": 1, "email": "test@example.com"}
        access_token = create_access_token(data)
        
        # Try to verify access token as refresh token
        token_data = verify_token(access_token, "refresh")
        assert token_data is None

    def test_create_token_hash(self):
        """Test token hash creation"""
        token = "sample.token.here"
        hash1 = create_token_hash(token)
        hash2 = create_token_hash(token)
        
        assert hash1 == hash2  # Same token should produce same hash
        assert len(hash1) == 64  # SHA256 produces 64 character hex string

    def test_token_expiration(self):
        """Test that expired tokens are rejected"""
        data = {"sub": 1, "email": "test@example.com"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta)
        
        # Token should be invalid due to expiration
        token_data = verify_token(token, "access")
        assert token_data is None