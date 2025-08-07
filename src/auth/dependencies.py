"""Authentication middleware and dependencies."""

from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..services.auth_service import AuthService
from ..models.database import User

# Security scheme
security = HTTPBearer()
auth_service = AuthService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify the token
        token_data = auth_service.verify_token(credentials.credentials)
        if not token_data:
            raise credentials_exception
        
        # Get user from database
        user_id = token_data.user_id
        if not user_id:
            raise credentials_exception
        
        user = auth_service.get_user_by_id(user_id)
        if not user:
            raise credentials_exception
        
        return user
        
    except HTTPException:
        raise
    except Exception:
        raise credentials_exception


async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[User]:
    """Get current authenticated user if token is provided, otherwise return None."""
    if credentials is None:
        return None
    
    token_data = auth_service.verify_token(credentials.credentials)
    if token_data is None:
        return None
    
    user = auth_service.get_user(token_data.user_id)
    return user
