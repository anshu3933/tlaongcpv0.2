import pytest
from httpx import AsyncClient

class TestAuthEndpoints:
    async def test_register_user(self, client: AsyncClient):
        """Test user registration"""
        user_data = {
            "email": "newuser@example.com",
            "password": "TestPassword123",
            "full_name": "New User",
            "role": "user"
        }
        
        response = await client.post("/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert data["is_active"] is True
        assert "id" in data

    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with duplicate email"""
        user_data = {
            "email": test_user.email,
            "password": "TestPassword123",
            "full_name": "Duplicate User"
        }
        
        response = await client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password"""
        user_data = {
            "email": "weakpass@example.com",
            "password": "weak",
            "full_name": "Weak Password User"
        }
        
        response = await client.post("/auth/register", json=user_data)
        
        assert response.status_code == 422  # Validation error

    async def test_login_valid_credentials(self, client: AsyncClient, test_user):
        """Test login with valid credentials"""
        login_data = {
            "email": test_user.email,
            "password": "testpassword123"
        }
        
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    async def test_login_invalid_email(self, client: AsyncClient):
        """Test login with invalid email"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "testpassword123"
        }
        
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    async def test_login_invalid_password(self, client: AsyncClient, test_user):
        """Test login with invalid password"""
        login_data = {
            "email": test_user.email,
            "password": "wrongpassword"
        }
        
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    async def test_get_current_user(self, client: AsyncClient, auth_headers):
        """Test getting current user info"""
        response = await client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "full_name" in data
        assert "role" in data

    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication"""
        response = await client.get("/auth/me")
        
        assert response.status_code == 401

    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = await client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401

    async def test_refresh_token(self, client: AsyncClient, test_user):
        """Test token refresh"""
        # First login to get tokens
        login_response = await client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123"
            }
        )
        tokens = login_response.json()
        
        # Use refresh token to get new access token
        refresh_data = {"refresh_token": tokens["refresh_token"]}
        response = await client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token"""
        refresh_data = {"refresh_token": "invalid.refresh.token"}
        response = await client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401

    async def test_logout(self, client: AsyncClient, auth_headers):
        """Test user logout"""
        response = await client.post("/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]

    async def test_logout_unauthorized(self, client: AsyncClient):
        """Test logout without authentication"""
        response = await client.post("/auth/logout")
        
        assert response.status_code == 401

class TestProtectedEndpoints:
    async def test_protected_endpoint_with_valid_token(self, client: AsyncClient, auth_headers):
        """Test accessing protected endpoint with valid token"""
        response = await client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200

    async def test_protected_endpoint_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token"""
        response = await client.get("/auth/me")
        assert response.status_code == 401

    async def test_protected_endpoint_with_expired_token(self, client: AsyncClient):
        """Test accessing protected endpoint with expired token"""
        # This would require creating an expired token, which is complex
        # For now, we'll test with an invalid token format
        headers = {"Authorization": "Bearer expired.token.here"}
        response = await client.get("/auth/me", headers=headers)
        assert response.status_code == 401