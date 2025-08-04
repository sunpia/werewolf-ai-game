"""Application settings and configuration."""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gemini-2.5-flash-lite"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    log_level: str = "info"
    
    # CORS Configuration
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Game Configuration
    min_players: int = 6
    max_players: int = 15
    
    # Authentication Configuration
    jwt_secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30 * 24 * 60  # 30 days
    
    # Database Configuration
    database_url: Optional[str] = None
    postgres_db: Optional[str] = None
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    
    # Google OAuth Configuration
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    
    # React App Google Client ID (for frontend)
    react_app_google_client_id: Optional[str] = None
    
    # GitHub OAuth Configuration (optional)
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    
    @property
    def jwt_secret(self) -> str:
        """Get JWT secret key."""
        return self.jwt_secret_key
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
