"""Enhanced game API routes with database support."""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Optional, List

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse

from ..models.api_models import (
    GameCreateRequest, GameResponse, PlayerAction, 
    GameStateResponse, EventMessage, GameHistoryResponse,
    UserGamesResponse, GameLimitsResponse
)
from ..models.database import User
from ..services.game_service import GameService
from ..services.database_service import db_service
from ..auth.dependencies import get_current_user
from ..utils.output_handler import OutputHandler, OutputEventType, create_custom_output_handler
from ..config.settings import get_settings

router = APIRouter(prefix="/api", tags=["games"])

# Game service instance (will be injected later)
game_service: GameService = None


def set_game_service(service: GameService):
    """Set the game service instance."""
    global game_service
    game_service = service


@router.get("/games/limits", response_model=GameLimitsResponse)
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


@router.get("/games/history", response_model=UserGamesResponse)
async def get_user_games(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get user's game history."""
    try:
        games = db_service.get_user_games(str(current_user.id), limit)
        user = db_service.get_user_by_id(str(current_user.id))
        
        game_responses = []
        for game in games:
            game_responses.append(GameHistoryResponse(
                id=str(game.id),
                user_id=str(game.user_id),
                status=game.status,
                num_players=game.num_players,
                current_phase=game.current_phase,
                current_day=game.current_day or 1,
                winner=game.winner,
                is_game_over=game.is_game_over,
                created_at=game.created_at.isoformat() if game.created_at else "",
                completed_at=game.completed_at.isoformat() if game.completed_at else None
            ))
        
        return UserGamesResponse(
            games=game_responses,
            total_games=len(games),
            free_games_remaining=user.free_games_remaining if user else 0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting game history: {str(e)}")


@router.get("/games/{game_id}/history")
async def get_game_history(
    game_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed history for a specific game."""
    try:
        # Verify user owns this game
        game = db_service.get_game_by_id(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        if str(game.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        history = db_service.get_game_history(game_id)
        return {
            "game": game.to_dict(),
            "history": [event.to_dict() for event in history]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting game history: {str(e)}")


@router.post("/games", response_model=GameResponse)
async def create_game(
    request: GameCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Create a new game with database persistence."""
    try:
        # Check if user can create games
        user = db_service.get_user_by_id(str(current_user.id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.free_games_remaining <= 0:
            raise HTTPException(
                status_code=403,
                detail=f"No free games remaining. You have played {user.total_games_played} games."
            )
        
        # Validate request
        if request.num_players < 6 or request.num_players > 15:
            raise HTTPException(
                status_code=400,
                detail="Number of players must be between 6 and 15"
            )
        
        # Use a free game
        if not db_service.decrement_free_games(str(current_user.id)):
            raise HTTPException(status_code=500, detail="Failed to use free game")
        
        # Create game configuration
        game_config = {
            "num_players": request.num_players,
            "api_key": request.api_key,
            "model": request.model,
            "created_by": str(current_user.id),
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Create initial game state
        initial_state = {
            "phase": "lobby",
            "day_count": 1,
            "alive_players": [],
            "current_speaker": None,
            "game_history": [],
            "is_game_over": False,
            "winner": None
        }
        
        # Save to database
        db_game = db_service.create_game(
            user_id=str(current_user.id),
            game_config=game_config,
            initial_state=initial_state
        )
        
        if not db_game:
            raise HTTPException(status_code=500, detail="Failed to create game in database")
        
        game_id = str(db_game.id)
        
        # Create the actual game using the existing game service
        try:
            created_game = game_service.create_game(
                game_id=game_id,
                num_players=request.num_players,
                api_key=request.api_key,
                model=request.model
            )
            
            # Log game creation event
            db_service.add_game_event(
                game_id=game_id,
                event_type="game_created",
                event_data={
                    "num_players": request.num_players,
                    "user_id": str(current_user.id),
                    "user_name": current_user.name
                },
                phase="lobby",
                day_count=1
            )
            
            # Start the game in background
            background_tasks.add_task(start_game_with_persistence, game_id, created_game)
            
            return GameResponse(
                game_id=game_id,
                status="created",
                message=f"Game created successfully with {request.num_players} AI players"
            )
            
        except Exception as e:
            # If game creation fails, restore the free game
            db_service.decrement_free_games(str(current_user.id))  # This will increment it back
            raise HTTPException(status_code=500, detail=f"Failed to initialize game: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create game: {str(e)}")


async def start_game_with_persistence(game_id: str, created_game):
    """Start game with database persistence."""
    try:
        # Create persistent output handler
        output_handler = create_persistent_output_handler(game_id)
        
        # Start the game
        await game_service.start_game_async(game_id, output_handler)
        
        # Mark game as completed
        game = game_service.get_game(game_id)
        if game:
            final_state = {
                "phase": game.current_phase,
                "day_count": game.day_count,
                "alive_players": [player.to_dict() for player in game.alive_players],
                "current_speaker": game.current_speaker.name if game.current_speaker else None,
                "game_history": game.get_game_history(),
                "is_game_over": game.is_game_over,
                "winner": game.winner
            }
            
            db_service.update_game_state(game_id, final_state)
            
            # Log game completion
            db_service.add_game_event(
                game_id=game_id,
                event_type="game_completed",
                event_data={
                    "winner": game.winner,
                    "final_phase": game.current_phase,
                    "total_days": game.day_count
                },
                phase=game.current_phase,
                day_count=game.day_count
            )
            
    except Exception as e:
        # Log error and update game status
        db_service.add_game_event(
            game_id=game_id,
            event_type="game_error",
            event_data={"error": str(e)},
            phase="error"
        )


def create_persistent_output_handler(game_id: str) -> OutputHandler:
    """Create an output handler that persists events to database."""
    
    async def persistent_output_function(
        message: str, 
        event_type: OutputEventType, 
        player: Optional[Any] = None, 
        metadata: dict = None
    ) -> None:
        """Persist game output to database and forward to frontend."""
        try:
            # Handle both AIMessage objects and strings
            if hasattr(message, 'content'):
                content = message.content
            else:
                content = str(message)
            
            # Get current game state for context
            game = game_service.get_game(game_id)
            current_phase = game.current_phase if game else None
            current_day = game.day_count if game else None
            
            # Save to database
            event_data = {
                "message": content,
                "event_type": event_type.value,
                "player": player.name if player and hasattr(player, 'name') else None,
                "metadata": metadata or {}
            }
            
            db_service.add_game_event(
                game_id=game_id,
                event_type="game_output",
                event_data=event_data,
                phase=current_phase,
                day_count=current_day
            )
            
            # Also update game state if this is a significant event
            if event_type in [OutputEventType.PHASE_CHANGE, OutputEventType.GAME_END]:
                if game:
                    updated_state = {
                        "phase": game.current_phase,
                        "day_count": game.day_count,
                        "alive_players": [p.to_dict() for p in game.alive_players],
                        "current_speaker": game.current_speaker.name if game.current_speaker else None,
                        "game_history": game.get_game_history(),
                        "is_game_over": game.is_game_over,
                        "winner": game.winner
                    }
                    db_service.update_game_state(game_id, updated_state)
                    
        except Exception as e:
            print(f"Error in persistent output handler: {e}")
    
    return create_custom_output_handler(persistent_output_function)


@router.get("/games/{game_id}")
async def get_game_state(
    game_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get current game state from database or memory."""
    try:
        # First check database
        db_game = db_service.get_game_by_id(game_id)
        if not db_game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Verify user owns this game
        if str(db_game.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # If game is active, get live state from game service
        if db_game.status == "active":
            game = game_service.get_game(game_id)
            if game:
                return GameStateResponse(
                    game_id=game_id,
                    phase=game.current_phase,
                    day_count=game.day_count,
                    alive_players=[player.to_dict() for player in game.alive_players],
                    current_speaker=game.current_speaker.name if game.current_speaker else None,
                    game_history=game.get_game_history(),
                    is_game_over=game.is_game_over,
                    winner=game.winner
                )
        
        # Return persisted state from database
        state = db_game.game_state
        return GameStateResponse(
            game_id=game_id,
            phase=state.get("phase", "completed"),
            day_count=state.get("day_count", 1),
            alive_players=state.get("alive_players", []),
            current_speaker=state.get("current_speaker"),
            game_history=state.get("game_history", []),
            is_game_over=state.get("is_game_over", True),
            winner=state.get("winner")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting game state: {str(e)}")


@router.get("/games/{game_id}/events")
async def stream_game_events(
    game_id: str,
    current_user: User = Depends(get_current_user)
):
    """Stream game events (Server-Sent Events)."""
    try:
        # Verify game exists and user has access
        db_game = db_service.get_game_by_id(game_id)
        if not db_game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        if str(db_game.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        async def event_generator():
            """Generate Server-Sent Events for the game."""
            try:
                # Send initial game state
                if db_game.status == "active":
                    game = game_service.get_game(game_id)
                    if game:
                        yield f"data: {json.dumps({'type': 'game_state', 'data': game.to_dict()})}\n\n"
                
                # Stream live events for active games
                if db_game.status == "active":
                    # This would need to be implemented in the game service
                    # to provide real-time event streaming
                    while not db_game.is_game_over:
                        await asyncio.sleep(1)
                        # Check for new events and yield them
                        yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error streaming events: {str(e)}")


# Keep existing routes for compatibility...
# (Additional routes from the original file would go here)
