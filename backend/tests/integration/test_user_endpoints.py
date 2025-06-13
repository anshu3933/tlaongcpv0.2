import pytest
from httpx import AsyncClient

class TestUserEndpoints:
    async def test_get_user_profile(self, client: AsyncClient, auth_headers, test_user):
        """Test getting user's own profile"""
        response = await client.get(f"/users/{test_user.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email

    async def test_get_other_user_profile_forbidden(self, client: AsyncClient, auth_headers, test_superuser):
        """Test getting another user's profile (should be forbidden for regular user)"""
        response = await client.get(f"/users/{test_superuser.id}", headers=auth_headers)
        
        assert response.status_code == 403

    async def test_get_user_profile_as_superuser(self, client: AsyncClient, admin_headers, test_user):
        """Test getting user profile as superuser"""
        response = await client.get(f"/users/{test_user.id}", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id

    async def test_get_all_users_as_superuser(self, client: AsyncClient, admin_headers):
        """Test getting all users as superuser"""
        response = await client.get("/users/", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # At least test_user and test_superuser

    async def test_get_all_users_as_regular_user(self, client: AsyncClient, auth_headers):
        """Test getting all users as regular user (should be forbidden)"""
        response = await client.get("/users/", headers=auth_headers)
        
        assert response.status_code == 403

    async def test_update_own_profile(self, client: AsyncClient, auth_headers, test_user):
        """Test updating own profile"""
        update_data = {
            "full_name": "Updated Test User",
            "role": "user"  # Should not be able to change role
        }
        
        response = await client.put(f"/users/{test_user.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Test User"

    async def test_update_other_user_profile_forbidden(self, client: AsyncClient, auth_headers, test_superuser):
        """Test updating another user's profile (should be forbidden)"""
        update_data = {"full_name": "Hacked Name"}
        
        response = await client.put(f"/users/{test_superuser.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 403

    async def test_change_own_password(self, client: AsyncClient, auth_headers, test_user):
        """Test changing own password"""
        password_data = {
            "current_password": "testpassword123",
            "new_password": "NewPassword123"
        }
        
        response = await client.post(f"/users/{test_user.id}/change-password", json=password_data, headers=auth_headers)
        
        assert response.status_code == 200
        assert "Password changed successfully" in response.json()["message"]

    async def test_change_password_wrong_current(self, client: AsyncClient, auth_headers, test_user):
        """Test changing password with wrong current password"""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "NewPassword123"
        }
        
        response = await client.post(f"/users/{test_user.id}/change-password", json=password_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]

    async def test_change_password_weak_new_password(self, client: AsyncClient, auth_headers, test_user):
        """Test changing password with weak new password"""
        password_data = {
            "current_password": "testpassword123",
            "new_password": "weak"
        }
        
        response = await client.post(f"/users/{test_user.id}/change-password", json=password_data, headers=auth_headers)
        
        assert response.status_code == 422  # Validation error

class TestSuperuserEndpoints:
    async def test_deactivate_user(self, client: AsyncClient, admin_headers, test_user):
        """Test deactivating a user as superuser"""
        response = await client.post(f"/users/{test_user.id}/deactivate", headers=admin_headers)
        
        assert response.status_code == 200
        assert "User deactivated successfully" in response.json()["message"]

    async def test_activate_user(self, client: AsyncClient, admin_headers, test_user):
        """Test activating a user as superuser"""
        # First deactivate
        await client.post(f"/users/{test_user.id}/deactivate", headers=admin_headers)
        
        # Then activate
        response = await client.post(f"/users/{test_user.id}/activate", headers=admin_headers)
        
        assert response.status_code == 200
        assert "User activated successfully" in response.json()["message"]

    async def test_deactivate_user_as_regular_user(self, client: AsyncClient, auth_headers, test_superuser):
        """Test deactivating a user as regular user (should be forbidden)"""
        response = await client.post(f"/users/{test_superuser.id}/deactivate", headers=auth_headers)
        
        assert response.status_code == 403

    async def test_get_users_by_role(self, client: AsyncClient, admin_headers):
        """Test getting users by role as superuser"""
        response = await client.get("/users/role/user", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_users_by_role_as_regular_user(self, client: AsyncClient, auth_headers):
        """Test getting users by role as regular user (should be forbidden)"""
        response = await client.get("/users/role/user", headers=auth_headers)
        
        assert response.status_code == 403

    async def test_get_user_audit_logs(self, client: AsyncClient, auth_headers, test_user):
        """Test getting own audit logs"""
        response = await client.get(f"/users/{test_user.id}/audit-logs", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_other_user_audit_logs_forbidden(self, client: AsyncClient, auth_headers, test_superuser):
        """Test getting another user's audit logs (should be forbidden)"""
        response = await client.get(f"/users/{test_superuser.id}/audit-logs", headers=auth_headers)
        
        assert response.status_code == 403

    async def test_get_user_audit_logs_as_superuser(self, client: AsyncClient, admin_headers, test_user):
        """Test getting user audit logs as superuser"""
        response = await client.get(f"/users/{test_user.id}/audit-logs", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

class TestEndpointValidation:
    async def test_invalid_user_id(self, client: AsyncClient, auth_headers):
        """Test accessing endpoint with invalid user ID"""
        response = await client.get("/users/99999", headers=auth_headers)
        
        assert response.status_code == 404

    async def test_update_user_invalid_email(self, client: AsyncClient, auth_headers, test_user):
        """Test updating user with invalid email format"""
        update_data = {"email": "invalid-email"}
        
        response = await client.put(f"/users/{test_user.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 422  # Validation error

    async def test_update_user_duplicate_email(self, client: AsyncClient, auth_headers, test_user, test_superuser):
        """Test updating user with email that already exists"""
        update_data = {"email": test_superuser.email}
        
        response = await client.put(f"/users/{test_user.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]