"""Authentication middleware and dependencies."""

from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..services.auth_service import AuthService
from ..models.auth_models import User

# Security scheme
security = HTTPBearer()

# Global auth service instance
auth_service = AuthService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = auth_service.verify_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception
    
    user = auth_service.get_user(token_data.user_id)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[User]:
    """Get current authenticated user if token is provided, otherwise return None."""
    if credentials is None:
        return None
    
    token_data = auth_service.verify_token(credentials.credentials)
    if token_data is None:
        return None
    
    user = auth_service.get_user(token_data.user_id)
    return user
