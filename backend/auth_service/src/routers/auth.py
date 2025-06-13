from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from ..schemas import UserCreate, UserLogin, UserResponse, Token, RefreshToken
from ..services.auth_service import AuthService
from ..dependencies import get_user_repository, get_audit_repository, get_current_user
from ..models.user import User

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

async def get_auth_service(
    user_repo=Depends(get_user_repository),
    audit_repo=Depends(get_audit_repository)
) -> AuthService:
    return AuthService(user_repo, audit_repo)

def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user"""
    ip_address = get_client_ip(request)
    user = await auth_service.register_user(user_data, ip_address)
    return user

@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user and return access/refresh tokens"""
    ip_address = get_client_ip(request)
    user, token = await auth_service.authenticate_user(login_data, ip_address)
    return token

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshToken,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token using refresh token"""
    ip_address = get_client_ip(request)
    token = await auth_service.refresh_access_token(refresh_data.refresh_token, ip_address)
    return token

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout user by invalidating all sessions"""
    ip_address = get_client_ip(request)
    success = await auth_service.logout_user(current_user.id, ip_address)
    if success:
        return {"message": "Successfully logged out"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Logout failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@router.post("/cleanup-sessions", status_code=status.HTTP_200_OK)
async def cleanup_expired_sessions(
    auth_service: AuthService = Depends(get_auth_service)
):
    """Clean up expired sessions (internal use)"""
    deleted_count = await auth_service.cleanup_expired_sessions()
    return {"message": f"Cleaned up {deleted_count} expired sessions"}