"""Main application entry point."""

import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from src.api.game_routes import router as game_router, set_game_service as set_game_service_routes
from src.api.health_routes import router as health_router, set_game_service as set_health_service_routes
from src.config.settings import get_settings
from src.services.game_service import GameService


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    # Initialize FastAPI app
    app = FastAPI(
        title="Werewolf AI Game Backend",
        description="Backend service for the Werewolf AI game with real-time updates",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize services
    game_service = GameService()
    
    # Inject service into route modules
    set_game_service_routes(game_service)
    set_health_service_routes(game_service)
    
    # Include routers
    app.include_router(game_router)
    app.include_router(health_router)
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level
    )
