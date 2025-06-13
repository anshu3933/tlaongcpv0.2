from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from fastapi import HTTPException, status
from ..repositories.user_repository import UserRepository
from ..repositories.audit_repository import AuditRepository
from ..models.user import User
from ..schemas import UserCreate, UserLogin, Token
from ..security import (
    hash_password, 
    verify_password, 
    create_access_token, 
    create_refresh_token,
    create_token_hash,
    verify_token
)
from ..config import get_settings

settings = get_settings()

class AuthService:
    def __init__(self, user_repo: UserRepository, audit_repo: AuditRepository):
        self.user_repo = user_repo
        self.audit_repo = audit_repo

    async def register_user(self, user_data: UserCreate, ip_address: str) -> User:
        """Register a new user"""
        # Check if user already exists
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create user
        hashed_password = hash_password(user_data.password)
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=user_data.role or "user",
            is_active=True,
            is_superuser=False
        )
        
        created_user = await self.user_repo.create(user)
        
        # Log registration
        await self.audit_repo.log_action(
            entity_type="user",
            entity_id=created_user.id,
            action="register",
            user_id=created_user.id,
            user_role=created_user.role,
            ip_address=ip_address,
            details={"email": created_user.email}
        )
        
        return created_user

    async def authenticate_user(self, login_data: UserLogin, ip_address: str) -> Tuple[User, Token]:
        """Authenticate user and return tokens"""
        # Get user by email
        user = await self.user_repo.get_by_email(login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Check password
        if not verify_password(login_data.password, user.hashed_password):
            # Log failed login attempt
            await self.audit_repo.log_action(
                entity_type="user",
                entity_id=user.id,
                action="login_failed",
                user_id=user.id,
                user_role=user.role,
                ip_address=ip_address,
                details={"reason": "invalid_password"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )

        # Create tokens
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role}
        )
        refresh_token = create_refresh_token(
            data={"sub": user.id, "email": user.email}
        )

        # Store refresh token hash in database
        token_hash = create_token_hash(refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        await self.user_repo.create_session(user.id, token_hash, expires_at)

        # Update last login
        await self.user_repo.update_last_login(user.id)

        # Log successful login
        await self.audit_repo.log_action(
            entity_type="user",
            entity_id=user.id,
            action="login",
            user_id=user.id,
            user_role=user.role,
            ip_address=ip_address,
            details={"email": user.email}
        )

        token = Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )

        return user, token

    async def refresh_access_token(self, refresh_token: str, ip_address: str) -> Token:
        """Refresh access token using refresh token"""
        # Verify refresh token
        token_data = verify_token(refresh_token, "refresh")
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Check if refresh token exists in database
        token_hash = create_token_hash(refresh_token)
        session = await self.user_repo.get_session_by_token_hash(token_hash)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found"
            )

        # Check if session is expired
        if session.expires_at < datetime.now(timezone.utc):
            # Clean up expired session
            await self.user_repo.delete_expired_sessions()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )

        # Get user
        user = await self.user_repo.get_by_id(token_data.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Create new access token
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role}
        )

        # Log token refresh
        await self.audit_repo.log_action(
            entity_type="user",
            entity_id=user.id,
            action="token_refresh",
            user_id=user.id,
            user_role=user.role,
            ip_address=ip_address,
            details={"email": user.email}
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )

    async def logout_user(self, user_id: int, ip_address: str) -> bool:
        """Logout user by invalidating all sessions"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False

        # Delete all user sessions
        deleted_count = await self.user_repo.delete_user_sessions(user_id)

        # Log logout
        await self.audit_repo.log_action(
            entity_type="user",
            entity_id=user_id,
            action="logout",
            user_id=user_id,
            user_role=user.role,
            ip_address=ip_address,
            details={"sessions_invalidated": deleted_count}
        )

        return True

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        return await self.user_repo.delete_expired_sessions()