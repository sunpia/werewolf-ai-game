"""Authentication service for user management and JWT tokens."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import logging

from jose import JWTError, jwt
from passlib.context import CryptContext
from google.oauth2 import id_token
from google.auth.transport import requests

from src import auth

from ..config.settings import get_settings
from ..models.auth_models import UserResponse, TokenData
from ..models.database import User
from ..services.database_service import db_service

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service for handling user authentication and JWT tokens."""
    
    def __init__(self):
        self.settings = get_settings()
        self.db = db_service
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.settings.jwt_secret, algorithm=self.settings.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify a JWT token and return token data."""
        try:
            payload = jwt.decode(token, self.settings.jwt_secret, algorithms=[self.settings.algorithm])
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            if user_id is None:
                return None
            return TokenData(user_id=user_id, email=email)
        except JWTError:
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.db.get_user_by_id(user_id)
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID (alias for compatibility)."""
        return self.get_user_by_id(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.get_user_by_email(email)
    
    def create_user(self, email: str, name: str, picture: str = None, provider: str = "google") -> Optional[User]:
        """Create a new user."""
        return self.db.create_user(email, name, picture, provider)
    
    def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp."""
        self.db.update_user_last_login(user_id)
    
    def can_create_game(self, user_id: str) -> bool:
        """Check if user can create a new game (has free games remaining)."""
        user = self.db.get_user_by_id(user_id)
        if user:
            return user.free_games_remaining > 0
        return False
    
    def use_free_game(self, user_id: str) -> bool:
        """Use one of the user's free games."""
        return self.db.decrement_free_games(user_id)
    
    async def verify_google_token(self, credential: str) -> Optional[Dict[str, Any]]:
        """Verify Google ID token and return user info."""
        try:
            if not self.settings.google_client_id:
                logger.error("Google Client ID not configured")
                return None
            
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                credential, 
                requests.Request(), 
                self.settings.google_client_id
            )
            
            # Verify the issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                logger.error("Invalid token issuer")
                return None
            
            return {
                'email': idinfo['email'],
                'name': idinfo['name'],
                'picture': idinfo.get('picture'),
                'provider': 'google'
            }
        except Exception as e:
            logger.error(f"Error verifying Google token: {e}")
            return None
    
    async def authenticate_google_user(self, credential: str) -> Optional[tuple[User, str]]:
        """Authenticate user with Google OAuth and return user and access token."""
        user_info = await self.verify_google_token(credential)
        if not user_info:
            return None
        
        # Check if user exists
        user = self.get_user_by_email(user_info['email'])
        
        if not user:
            # Create new user
            user = self.create_user(
                email=user_info['email'],
                name=user_info['name'],
                picture=user_info.get('picture'),
                provider='google'
            )
            if not user:
                return None
        else:
            # Update last login
            self.update_last_login(str(user.id))
        
        # Capture user data to avoid detached instance issues
        user_id = str(user.id)
        user_email = user.email
        user_name = user.name
        
        # Create access token using captured data
        access_token = self.create_access_token({
            "sub": user_id,
            "email": user_email,
            "name": user_name
        })
        
        return user, access_token
        
        return user, access_token
    
    def to_user_response(self, user: User) -> UserResponse:
        """Convert User to UserResponse."""
        return UserResponse(
            id=str(user.id),  # Ensure string conversion
            email=user.email,
            name=user.name,
            picture=user.picture,
            provider=user.provider
        )