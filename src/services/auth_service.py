"""Authentication service for user management and JWT tokens."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import logging

from jose import JWTError, jwt
from passlib.context import CryptContext
from google.oauth2 import id_token
from google.auth.transport import requests

from ..config.settings import get_settings
from ..models.auth_models import User, UserCreate, UserResponse, TokenData

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory user storage (replace with database in production)
users_db: Dict[str, User] = {}
user_emails: Dict[str, str] = {}  # email -> user_id mapping


class AuthService:
    """Authentication service for handling user authentication and JWT tokens."""
    
    def __init__(self):
        self.settings = get_settings()
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.settings.secret_key, algorithm=self.settings.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify a JWT token and return token data."""
        try:
            payload = jwt.decode(token, self.settings.secret_key, algorithms=[self.settings.algorithm])
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            if user_id is None:
                return None
            return TokenData(user_id=user_id, email=email)
        except JWTError:
            return None
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return users_db.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        user_id = user_emails.get(email)
        if user_id:
            return users_db.get(user_id)
        return None
    
    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        user = User(
            id=user_id,
            email=user_data.email,
            name=user_data.name,
            picture=user_data.picture,
            provider=user_data.provider,
            created_at=now,
            last_login=now
        )
        
        users_db[user_id] = user
        user_emails[user_data.email] = user_id
        
        logger.info(f"Created new user: {user_data.email}")
        return user
    
    def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp."""
        if user_id in users_db:
            users_db[user_id].last_login = datetime.now(timezone.utc)
    
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
            user_create = UserCreate(
                email=user_info['email'],
                name=user_info['name'],
                picture=user_info.get('picture'),
                provider='google'
            )
            user = self.create_user(user_create)
        else:
            # Update last login
            self.update_last_login(user.id)
        
        # Create access token
        access_token = self.create_access_token({
            "sub": user.id,
            "email": user.email,
            "name": user.name
        })
        
        return user, access_token
    
    def to_user_response(self, user: User) -> UserResponse:
        """Convert User to UserResponse."""
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            picture=user.picture,
            provider=user.provider
        )
