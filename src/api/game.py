"""Consolidated game API routes - All game-related endpoints in one file."""

import asyncio
import json
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from ..models.api_models import GameCreateRequest, GameResponse, GameStateResponse, PlayerAction
from ..models.database import User
from ..services.database_service import db_service
from ..services.game_service import GameService
from ..auth.dependencies import get_current_user
from ..config.settings import get_settings
from ..utils.output_handler import OutputHandler, OutputEventType, create_custom_output_handler

# Game service instance (will be injected later)
game_service: GameService = None

# Main router that combines all game routes
router = APIRouter()


# ============================================================================
# GAME UTILITIES
# ============================================================================

def set_game_service(service: GameService):
    """Set the game service instance."""
    global game_service
    game_service = service


def get_game_service() -> GameService:
    """Get the game service instance."""
    if game_service is None:
        raise HTTPException(status_code=500, detail="Game service not initialized")
    return game_service


def get_game_or_404(game_id: str):
    """Get game instance or raise 404."""
    service = get_game_service()
    game = service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


def create_backend_output_handler(game_id: str) -> OutputHandler:
    """Create an output handler that forwards messages to frontend via SSE."""
    service = get_game_service()
    
    async def backend_output_function(message: str, event_type: OutputEventType, 
                                    player: Optional[Any] = None, metadata: dict = None) -> None:
        """Forward game output to frontend via SSE."""
        # Handle both AIMessage objects and strings
        if hasattr(message, 'content'):
            content = message.content
        else:
            content = str(message)
        
        # Prepare event data
        event_data = {
            "type": "game_output",
            "output_type": event_type.value,
            "message": content,
            "metadata": metadata or {}
        }
        
        # Add player information if available
        if player:
            event_data["player"] = {
                "name": getattr(player, 'name', 'Unknown'),
                "role": getattr(player, 'role', {}).value if hasattr(getattr(player, 'role', None), 'value') else 'Unknown',
                "is_wolf": getattr(player, 'is_wolf', lambda: False)(),
                "is_civilian": getattr(player, 'is_civilian', lambda: False)(),
                "is_god": getattr(player, 'is_god', lambda: False)()
            }
        
        # Map event types to specific frontend event types
        frontend_event_type = "game_output"
        if event_type == OutputEventType.PLAYER_SPEECH:
            frontend_event_type = "player_action"
            event_data.update({
                "action_type": "speak",
                "player": getattr(player, 'name', 'Unknown') if player else None,
                "role": getattr(player, 'role', {}).value if player and hasattr(getattr(player, 'role', None), 'value') else None
            })
        elif event_type == OutputEventType.WOLF_COMMUNICATION:
            frontend_event_type = "wolf_communication"
        elif event_type == OutputEventType.PHASE_TRANSITION:
            frontend_event_type = "phase_transition"
        elif event_type == OutputEventType.ELIMINATION:
            frontend_event_type = "elimination"
        elif event_type == OutputEventType.NIGHT_KILL:
            frontend_event_type = "night_kill"
        elif event_type == OutputEventType.VOTING:
            frontend_event_type = "voting"
        elif event_type == OutputEventType.GAME_ANNOUNCEMENT:
            frontend_event_type = "game_announcement"
        
        event_data["frontend_type"] = frontend_event_type
        
        # Broadcast to frontend
        await service.broadcast_event(game_id, event_data)
    
    # Create a wrapper that handles the async nature
    def sync_output_function(message: str, event_type: OutputEventType, 
                           player: Optional[Any] = None, metadata: dict = None) -> None:
        """Synchronous wrapper for the async output function."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, schedule the coroutine
                asyncio.create_task(backend_output_function(message, event_type, player, metadata))
            else:
                # If not in async context, run it
                loop.run_until_complete(backend_output_function(message, event_type, player, metadata))
        except Exception as e:
            # Fallback to console output if broadcast fails
            print(f"[Game {game_id}] {message}")
    
    return create_custom_output_handler(sync_output_function)


# ============================================================================
# GAME MANAGEMENT ROUTES
# ============================================================================

@router.post("/api/v1/games", response_model=GameResponse, tags=["game"])
async def create_game(
    request: GameCreateRequest, 
    current_user: User = Depends(get_current_user)
):
    """Create a new werewolf game with authentication and database persistence."""
    try:
        game_service = get_game_service()
        
        # Check if user can create games
        user = db_service.get_user_by_id(str(current_user.id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.free_games_remaining <= 0:
            raise HTTPException(
                status_code=403,
                detail=f"No free games remaining. You have played {user.total_games_played} games."
            )
        
        settings = get_settings()
        
        if not (settings.min_players <= request.num_players <= settings.max_players):
            raise HTTPException(
                status_code=400, 
                detail=f"Number of players must be between {settings.min_players} and {settings.max_players}"
            )
        
        # Use provided API key or default from environment
        api_key = request.api_key or settings.openai_api_key
        model = request.model or settings.openai_model
        
        if not api_key:
            raise HTTPException(status_code=400, detail="API key is required")
        
        # Use a free game
        if not db_service.decrement_free_games(str(current_user.id)):
            raise HTTPException(status_code=500, detail="Failed to use free game")
        
        # Create game configuration
        game_config = {
            "num_players": request.num_players,
            "api_key": api_key,
            "model": model,
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
            game_state=initial_state,
            num_players=request.num_players
        )
        
        if not db_game:
            # Restore free game count on database failure
            db_service.increment_free_games(str(current_user.id))
            raise HTTPException(status_code=500, detail="Failed to create game in database")
        
        game_id = str(db_game.id)
        
        # Create validated request with database game ID
        validated_request = GameCreateRequest(
            num_players=request.num_players,
            api_key=api_key,
            model=model
        )
        
        # Create custom output handler for this game
        output_handler = create_backend_output_handler(game_id)
        
        # Create game in the game service
        try:
            created_game_id = await game_service.create_game(validated_request, output_handler, game_id)
            
            # Log game creation event
            db_service.create_system_event(
                game_id=game_id,
                event_type="game_created",
                event_description=f"Game created with {request.num_players} players by {current_user.name}",
                phase="lobby",
                day_number=1,
                event_metadata={
                    "num_players": request.num_players,
                    "user_id": str(current_user.id),
                    "user_name": current_user.name
                }
            )
            
            # Update output handler with actual game_id
            output_handler = create_backend_output_handler(game_id)
            game = game_service.get_game(game_id)
            if game:
                game.output_handler = output_handler
                
                # Broadcast game creation event
                await game_service.broadcast_event(game_id, {
                    "type": "game_created",
                    "game_id": game_id,
                    "num_players": request.num_players,
                    "players": [game_service.player_to_dict(p) for p in game.game_state.players.values()]
                })
            
            return GameResponse(
                game_id=game_id,
                status="created",
                message=f"Game created with {request.num_players} players"
            )
            
        except Exception as game_error:
            # If game service creation fails, restore the free game
            db_service.increment_free_games(str(current_user.id))
            raise HTTPException(status_code=500, detail=f"Failed to initialize game: {str(game_error)}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create game: {str(e)}")


@router.delete("/api/v1/games/{game_id}", tags=["game"])
async def delete_game(game_id: str):
    """Delete a game."""
    game_service = get_game_service()
    success = game_service.delete_game(game_id)
    
    if success:
        return {"status": "deleted", "message": "Game deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Game not found")


# ============================================================================
# GAME STATE ROUTES
# ============================================================================

@router.get("/api/v1/games/{game_id}", response_model=GameStateResponse, tags=["game"])
async def get_game_state(
    game_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get current game state with authentication."""
    try:
        game_service = get_game_service()
        
        # First check database for game ownership
        db_game = db_service.get_game(game_id)
        if not db_game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Verify user owns this game
        if str(db_game.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # If game is active, get live state from game service
        if db_game.status == "active":
            game = game_service.get_game(game_id)
            if game:
                state_dict = game_service.get_game_state_dict(game)
                return GameStateResponse(game_id=game_id, **state_dict)
        
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


@router.get("/api/v1/games/{game_id}/players", tags=["game"])
async def get_players(game_id: str):
    """Get all players in the game."""
    game_service = get_game_service()
    game = get_game_or_404(game_id)
    
    return {
        "players": [game_service.player_to_dict(p) for p in game.game_state.players.values()]
    }


# ============================================================================
# GAME ACTION ROUTES
# ============================================================================

@router.post("/api/v1/games/{game_id}/start", tags=["game"])
async def start_game(game_id: str):
    """Start the game."""
    game_service = get_game_service()
    game = get_game_or_404(game_id)
    
    try:
        # Start the game in background
        asyncio.create_task(game_service.run_game_loop(game_id))
        
        await game_service.broadcast_event(game_id, {
            "type": "game_started",
            "game_id": game_id,
            "phase": game.game_state.current_phase.value,
            "day_count": game.game_state.day_count
        })
        
        return {"status": "started", "message": "Game has been started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start game: {str(e)}")


@router.post("/api/v1/games/{game_id}/action", tags=["game"])
async def player_action(game_id: str, action: PlayerAction):
    """Handle player action (speak, vote, etc.)."""
    game_service = get_game_service()
    game = get_game_or_404(game_id)
    
    try:
        # Find the player
        player = None
        for p in game.game_state.players.values():
            if p.name == action.player_name:
                player = p
                break
        
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Process the action based on type
        result = None
        if action.action_type == "speak":
            if action.message:
                # Add message to game history
                game.game_state.game_history.append(f"{player.name}: {action.message}")
                result = {"spoke": True, "message": action.message}
        elif action.action_type == "vote":
            if action.target:
                # Handle voting logic
                result = {"voted": True, "target": action.target}
        elif action.action_type == "night_kill" and player.is_wolf():
            if action.target:
                # Handle night kill
                game.game_state.night_kill_target = action.target
                result = {"night_kill_set": True, "target": action.target}
        
        # Broadcast the action
        await game_service.broadcast_event(game_id, {
            "type": "player_action",
            "player": action.player_name,
            "action_type": action.action_type,
            "target": action.target,
            "message": action.message,
            "result": result
        })
        
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process action: {str(e)}")


# ============================================================================
# GAME EVENTS ROUTES
# ============================================================================

@router.get("/api/v1/games/{game_id}/events", tags=["game"])
async def stream_events(game_id: str):
    """Stream game events using Server-Sent Events."""
    game_service = get_game_service()
    
    async def event_stream():
        # Create a queue for this connection
        queue = asyncio.Queue()
        
        # Add queue to active connections
        game_service.add_connection(game_id, queue)
        
        try:
            # Send recent events first
            recent_events = game_service.get_recent_events(game_id, 10)
            for event in recent_events:
                yield f"data: {json.dumps(event)}\n\n"
            
            # Stream new events
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(event)}\n\n"       
                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield f"data: {json.dumps({'event_type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            # Remove queue from active connections
            game_service.remove_connection(game_id, queue)
    
    return StreamingResponse(
        event_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no"
        }
    )


# Export the service setter function for app.py
__all__ = ["router", "set_game_service"]
