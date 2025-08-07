"""Health check API routes."""

from fastapi import APIRouter

from .game import get_game_service

router = APIRouter(tags=["health"])


@router.get("/")
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        game_service = get_game_service()
        active_games = game_service.get_active_games_count()
    except:
        active_games = 0
    
    return {"status": "healthy", "active_games": active_games}
