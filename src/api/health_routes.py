"""Health check API routes."""

from fastapi import APIRouter

from ..services.game_service import GameService

router = APIRouter(prefix="/api", tags=["health"])

# Game service instance (will be injected later)
game_service: GameService = None


def set_game_service(service: GameService):
    """Set the game service instance."""
    global game_service
    game_service = service


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    active_games = game_service.get_active_games_count() if game_service else 0
    return {"status": "healthy", "active_games": active_games}
