"""Authentication API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends

from ..models.auth_models import GoogleOAuthRequest, AuthResponse, UserResponse
from ..services.auth_service import AuthService
from ..auth.dependencies import get_current_user, get_current_user_optional
from ..models.auth_models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Auth service instance
auth_service = AuthService()


@router.post("/google", response_model=AuthResponse)
async def google_oauth(request: GoogleOAuthRequest):
    """Authenticate user with Google OAuth."""
    try:
        result = await auth_service.authenticate_google_user(request.credential)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google credentials"
            )
        
        user, access_token = result
        user_response = auth_service.to_user_response(user)
        
        return AuthResponse(
            success=True,
            message="Authentication successful",
            user=user_response,
            access_token=access_token,
            token_type="bearer"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return auth_service.to_user_response(current_user)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout current user (client-side token removal)."""
    return {"success": True, "message": "Logged out successfully"}


@router.get("/status")
async def auth_status(current_user: Optional[User] = Depends(get_current_user_optional)):
    """Check authentication status."""
    if current_user:
        return {
            "authenticated": True,
            "user": auth_service.to_user_response(current_user)
        }
    else:
        return {"authenticated": False}
