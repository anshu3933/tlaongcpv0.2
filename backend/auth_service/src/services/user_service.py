from typing import List, Optional
from fastapi import HTTPException, status
from ..repositories.user_repository import UserRepository
from ..repositories.audit_repository import AuditRepository
from ..models.user import User
from ..schemas import UserCreate, UserUpdate, PasswordChange
from ..security import hash_password, verify_password

class UserService:
    def __init__(self, user_repo: UserRepository, audit_repo: AuditRepository):
        self.user_repo = user_repo
        self.audit_repo = audit_repo

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return await self.user_repo.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return await self.user_repo.get_by_email(email)

    async def get_all_users(self, current_user: User) -> List[User]:
        """Get all users (superuser only)"""
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return await self.user_repo.list_all()

    async def update_user(
        self, 
        user_id: int, 
        user_update: UserUpdate, 
        current_user: User,
        ip_address: str
    ) -> User:
        """Update user information"""
        # Check permissions
        if user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check email uniqueness if email is being updated
        if user_update.email and user_update.email != user.email:
            existing_user = await self.user_repo.get_by_email(user_update.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

        # Update fields
        update_data = user_update.dict(exclude_unset=True)
        changes = {}
        
        for field, value in update_data.items():
            if hasattr(user, field) and getattr(user, field) != value:
                changes[field] = {
                    "old": getattr(user, field),
                    "new": value
                }
                setattr(user, field, value)

        if changes:
            updated_user = await self.user_repo.update(user)
            
            # Log the update
            await self.audit_repo.log_action(
                entity_type="user",
                entity_id=user_id,
                action="update",
                user_id=current_user.id,
                user_role=current_user.role,
                ip_address=ip_address,
                details={"changes": changes}
            )
            
            return updated_user
        
        return user

    async def change_password(
        self, 
        user_id: int, 
        password_change: PasswordChange, 
        current_user: User,
        ip_address: str
    ) -> bool:
        """Change user password"""
        # Check permissions
        if user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify current password (unless superuser changing another user's password)
        if user_id == current_user.id:
            if not verify_password(password_change.current_password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )

        # Update password
        user.hashed_password = hash_password(password_change.new_password)
        await self.user_repo.update(user)

        # Invalidate all user sessions to force re-login
        await self.user_repo.delete_user_sessions(user_id)

        # Log password change
        await self.audit_repo.log_action(
            entity_type="user",
            entity_id=user_id,
            action="password_change",
            user_id=current_user.id,
            user_role=current_user.role,
            ip_address=ip_address,
            details={"changed_by": current_user.id if current_user.id != user_id else "self"}
        )

        return True

    async def deactivate_user(
        self, 
        user_id: int, 
        current_user: User,
        ip_address: str
    ) -> bool:
        """Deactivate user account"""
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )

        user.is_active = False
        await self.user_repo.update(user)

        # Invalidate all user sessions
        await self.user_repo.delete_user_sessions(user_id)

        # Log deactivation
        await self.audit_repo.log_action(
            entity_type="user",
            entity_id=user_id,
            action="deactivate",
            user_id=current_user.id,
            user_role=current_user.role,
            ip_address=ip_address,
            details={"deactivated_by": current_user.id}
        )

        return True

    async def activate_user(
        self, 
        user_id: int, 
        current_user: User,
        ip_address: str
    ) -> bool:
        """Activate user account"""
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user.is_active = True
        await self.user_repo.update(user)

        # Log activation
        await self.audit_repo.log_action(
            entity_type="user",
            entity_id=user_id,
            action="activate",
            user_id=current_user.id,
            user_role=current_user.role,
            ip_address=ip_address,
            details={"activated_by": current_user.id}
        )

        return True

    async def get_users_by_role(self, role: str, current_user: User) -> List[dict]:
        """Get all users with specific role"""
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return await self.user_repo.get_users_by_role(role)