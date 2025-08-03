"""API routes for the werewolf game."""

from .game_routes import router as game_router
from .health_routes import router as health_router

__all__ = ["game_router", "health_router"]
