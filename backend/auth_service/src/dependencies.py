from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from .database import get_async_session
from .repositories.user_repository import UserRepository
from .repositories.audit_repository import AuditRepository
from .security import verify_token
from .schemas import TokenData
from .models.user import User

security = HTTPBearer()

async def get_user_repository(session: AsyncSession = Depends(get_async_session)) -> UserRepository:
    """Get user repository instance"""
    return UserRepository(session)

async def get_audit_repository(session: AsyncSession = Depends(get_async_session)) -> AuditRepository:
    """Get audit repository instance"""
    return AuditRepository(session)

async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception
    
    return token_data

async def get_current_user(
    token_data: TokenData = Depends(get_current_user_token),
    user_repo: UserRepository = Depends(get_user_repository)
) -> User:
    """Get current user from database"""
    user = await user_repo.get_by_id(token_data.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    user_repo: UserRepository = Depends(get_user_repository)
) -> Optional[User]:
    """Get current user if token is provided, otherwise None"""
    if credentials is None:
        return None
    
    token_data = verify_token(credentials.credentials)
    if token_data is None:
        return None
    
    user = await user_repo.get_by_id(token_data.user_id)
    if user is None or not user.is_active:
        return None
    
    return user