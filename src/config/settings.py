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
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Game Configuration
    min_players: int = 6
    max_players: int = 15
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
