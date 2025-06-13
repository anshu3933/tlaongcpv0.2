import pytest
from datetime import datetime, timedelta, timezone
from auth_service.src.repositories.user_repository import UserRepository
from auth_service.src.repositories.audit_repository import AuditRepository
from auth_service.src.models.user import User
from auth_service.src.models.user_session import UserSession
from auth_service.src.models.audit_log import AuditLog
from auth_service.src.security import hash_password

class TestUserRepository:
    @pytest.fixture
    async def user_repo(self, test_session):
        return UserRepository(test_session)

    async def test_create_user(self, user_repo):
        """Test user creation"""
        user_data = User(
            email="newuser@example.com",
            hashed_password=hash_password("password123"),
            full_name="New User",
            role="user",
            is_active=True
        )
        
        created_user = await user_repo.create(user_data)
        
        assert created_user.id is not None
        assert created_user.email == "newuser@example.com"
        assert created_user.full_name == "New User"
        assert created_user.is_active is True

    async def test_get_user_by_email(self, user_repo, test_user):
        """Test getting user by email"""
        user = await user_repo.get_by_email(test_user.email)
        
        assert user is not None
        assert user.email == test_user.email
        assert user.id == test_user.id

    async def test_get_user_by_id(self, user_repo, test_user):
        """Test getting user by ID"""
        user = await user_repo.get_by_id(test_user.id)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    async def test_get_nonexistent_user(self, user_repo):
        """Test getting non-existent user"""
        user = await user_repo.get_by_email("nonexistent@example.com")
        assert user is None
        
        user = await user_repo.get_by_id(99999)
        assert user is None

    async def test_update_user(self, user_repo, test_user):
        """Test user update"""
        test_user.full_name = "Updated Name"
        updated_user = await user_repo.update(test_user)
        
        assert updated_user.full_name == "Updated Name"

    async def test_create_session(self, user_repo, test_user):
        """Test session creation"""
        token_hash = "sample_token_hash"
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        
        await user_repo.create_session(test_user.id, token_hash, expires_at)
        
        # Verify session was created
        session = await user_repo.get_session_by_token_hash(token_hash)
        assert session is not None
        assert session.user_id == test_user.id
        assert session.token_hash == token_hash

    async def test_delete_expired_sessions(self, user_repo, test_user):
        """Test deleting expired sessions"""
        # Create expired session
        expired_token = "expired_token_hash"
        expired_time = datetime.now(timezone.utc) - timedelta(days=1)
        await user_repo.create_session(test_user.id, expired_token, expired_time)
        
        # Create valid session
        valid_token = "valid_token_hash"
        valid_time = datetime.now(timezone.utc) + timedelta(days=1)
        await user_repo.create_session(test_user.id, valid_token, valid_time)
        
        # Delete expired sessions
        deleted_count = await user_repo.delete_expired_sessions()
        
        assert deleted_count == 1
        
        # Verify expired session is gone but valid session remains
        expired_session = await user_repo.get_session_by_token_hash(expired_token)
        valid_session = await user_repo.get_session_by_token_hash(valid_token)
        
        assert expired_session is None
        assert valid_session is not None

    async def test_delete_user_sessions(self, user_repo, test_user):
        """Test deleting all user sessions"""
        # Create multiple sessions
        token1 = "token_hash_1"
        token2 = "token_hash_2"
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        
        await user_repo.create_session(test_user.id, token1, expires_at)
        await user_repo.create_session(test_user.id, token2, expires_at)
        
        # Delete all user sessions
        deleted_count = await user_repo.delete_user_sessions(test_user.id)
        
        assert deleted_count == 2
        
        # Verify sessions are gone
        session1 = await user_repo.get_session_by_token_hash(token1)
        session2 = await user_repo.get_session_by_token_hash(token2)
        
        assert session1 is None
        assert session2 is None

    async def test_update_last_login(self, user_repo, test_user):
        """Test updating last login timestamp"""
        original_last_login = test_user.last_login
        
        await user_repo.update_last_login(test_user.id)
        
        # Refresh user from database
        updated_user = await user_repo.get_by_id(test_user.id)
        
        assert updated_user.last_login is not None
        assert updated_user.last_login != original_last_login

class TestAuditRepository:
    @pytest.fixture
    async def audit_repo(self, test_session):
        return AuditRepository(test_session)

    async def test_log_action(self, audit_repo, test_user):
        """Test logging an action"""
        log_entry = await audit_repo.log_action(
            entity_type="user",
            entity_id=test_user.id,
            action="login",
            user_id=test_user.id,
            user_role=test_user.role,
            ip_address="192.168.1.1",
            details={"browser": "Chrome"}
        )
        
        assert log_entry.id is not None
        assert log_entry.entity_type == "user"
        assert log_entry.entity_id == test_user.id
        assert log_entry.action == "login"
        assert log_entry.user_id == test_user.id
        assert log_entry.user_role == test_user.role
        assert log_entry.ip_address == "192.168.1.1"
        assert log_entry.details == {"browser": "Chrome"}

    async def test_get_logs_by_entity(self, audit_repo, test_user):
        """Test getting logs by entity"""
        # Create multiple log entries
        await audit_repo.log_action(
            entity_type="user",
            entity_id=test_user.id,
            action="login",
            user_id=test_user.id,
            user_role=test_user.role,
            ip_address="192.168.1.1"
        )
        
        await audit_repo.log_action(
            entity_type="user",
            entity_id=test_user.id,
            action="logout",
            user_id=test_user.id,
            user_role=test_user.role,
            ip_address="192.168.1.1"
        )
        
        logs = await audit_repo.get_logs_by_entity("user", test_user.id)
        
        assert len(logs) == 2
        assert logs[0].action in ["login", "logout"]
        assert logs[1].action in ["login", "logout"]

    async def test_get_logs_by_user(self, audit_repo, test_user):
        """Test getting logs by user"""
        await audit_repo.log_action(
            entity_type="user",
            entity_id=test_user.id,
            action="profile_update",
            user_id=test_user.id,
            user_role=test_user.role,
            ip_address="192.168.1.1"
        )
        
        logs = await audit_repo.get_logs_by_user(test_user.id)
        
        assert len(logs) >= 1
        assert any(log.action == "profile_update" for log in logs)