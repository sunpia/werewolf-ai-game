"""User API routes - User-related information and operations."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List

from ..models.api_models import (
    GameLimitsResponse, GameHistoryResponse, UserGamesResponse,
    SystemEventCreate, SystemEventResponse
)
from ..models.database import User
from ..services.database_service import db_service
from ..auth.dependencies import get_current_user

import logging

v1_router = APIRouter(prefix="/api/v1", tags=["users"])
logger = logging.getLogger(__name__)


# ============================================================================
# USER GAME LIMITS AND INFORMATION
# ============================================================================

@v1_router.get("/user/games/limits", response_model=GameLimitsResponse)
async def get_game_limits(current_user: User = Depends(get_current_user)):
    """Get user's game limits and remaining free games."""
    try:
        user = db_service.get_user_by_id(str(current_user.id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return GameLimitsResponse(
            free_games_remaining=user.free_games_remaining,
            total_games_played=user.total_games_played,
            can_create_game=user.free_games_remaining > 0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting game limits: {str(e)}")


@v1_router.get("/user/games/history", response_model=UserGamesResponse)
async def get_user_games(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get user's game history."""
    try:
        games = db_service.get_user_games(str(current_user.id))
        
        game_responses = []
        for game in games[:limit]:  # Apply limit
            game_responses.append(GameHistoryResponse(
                id=str(game.id),
                user_id=str(game.user_id),
                status=game.status or "completed",
                num_players=game.num_players,
                current_phase=game.current_phase or "completed",
                created_at=game.created_at,
                updated_at=game.updated_at
            ))
        
        return UserGamesResponse(games=game_responses)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user games: {str(e)}")


# ============================================================================
# USER SYSTEM EVENTS
# ============================================================================

@v1_router.post("/user/system-events", response_model=Dict[str, Any])
async def create_system_event(
    event: SystemEventCreate,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new system event."""
    try:
        result = await db_service.create_system_event(event)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error creating system event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TEST ENDPOINTS
# ============================================================================

@v1_router.get("/test")
async def test_v1_endpoint():
    """Test endpoint to verify v1 router is working."""
    return {"message": "v1 user router is working"}


@v1_router.get("/user/profile")
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get user profile information."""
    try:
        user = db_service.get_user_by_id(str(current_user.id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "free_games_remaining": user.free_games_remaining,
            "total_games_played": user.total_games_played,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user profile: {str(e)}")


@v1_router.get("/user/stats")
async def get_user_stats(current_user: User = Depends(get_current_user)):
    """Get user statistics and achievements."""
    try:
        user = db_service.get_user_by_id(str(current_user.id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's games for statistics
        games = db_service.get_user_games(str(current_user.id))
        
        # Calculate statistics
        total_games = len(games)
        completed_games = len([g for g in games if g.status == "completed"])
        active_games = len([g for g in games if g.status == "active"])
        
        return {
            "user_id": str(user.id),
            "total_games_created": total_games,
            "completed_games": completed_games,
            "active_games": active_games,
            "free_games_remaining": user.free_games_remaining,
            "total_games_played": user.total_games_played,
            "member_since": user.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user stats: {str(e)}")
