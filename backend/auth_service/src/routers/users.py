from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from ..schemas import UserResponse, UserUpdate, PasswordChange, AuditLogResponse
from ..services.user_service import UserService
from ..dependencies import (
    get_user_repository, 
    get_audit_repository, 
    get_current_user, 
    get_current_superuser
)
from ..models.user import User

router = APIRouter(prefix="/users", tags=["users"])

async def get_user_service(
    user_repo=Depends(get_user_repository),
    audit_repo=Depends(get_audit_repository)
) -> UserService:
    return UserService(user_repo, audit_repo)

def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service)
):
    """Get all users (superuser only)"""
    users = await user_service.get_all_users(current_user)
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get user by ID"""
    # Users can only view their own profile unless they are superuser
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update user information"""
    ip_address = get_client_ip(request)
    updated_user = await user_service.update_user(user_id, user_update, current_user, ip_address)
    return updated_user

@router.post("/{user_id}/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    user_id: int,
    password_change: PasswordChange,
    request: Request,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Change user password"""
    ip_address = get_client_ip(request)
    success = await user_service.change_password(user_id, password_change, current_user, ip_address)
    if success:
        return {"message": "Password changed successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password change failed"
        )

@router.post("/{user_id}/deactivate", status_code=status.HTTP_200_OK)
async def deactivate_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service)
):
    """Deactivate user account (superuser only)"""
    ip_address = get_client_ip(request)
    success = await user_service.deactivate_user(user_id, current_user, ip_address)
    if success:
        return {"message": "User deactivated successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User deactivation failed"
        )

@router.post("/{user_id}/activate", status_code=status.HTTP_200_OK)
async def activate_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service)
):
    """Activate user account (superuser only)"""
    ip_address = get_client_ip(request)
    success = await user_service.activate_user(user_id, current_user, ip_address)
    if success:
        return {"message": "User activated successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User activation failed"
        )

@router.get("/role/{role}", response_model=List[dict])
async def get_users_by_role(
    role: str,
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends(get_user_service)
):
    """Get all users with specific role (superuser only)"""
    users = await user_service.get_users_by_role(role, current_user)
    return users

@router.get("/{user_id}/audit-logs", response_model=List[AuditLogResponse])
async def get_user_audit_logs(
    user_id: int,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    audit_repo=Depends(get_audit_repository)
):
    """Get audit logs for a user"""
    # Users can only view their own audit logs unless they are superuser
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    logs = await audit_repo.get_logs_by_user(user_id, limit)
    return logs