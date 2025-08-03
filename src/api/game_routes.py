"""Game API routes."""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from ..models.api_models import (
    GameCreateRequest, GameResponse, PlayerAction, 
    GameStateResponse, EventMessage
)
from ..services.game_service import GameService
from ..utils.output_handler import OutputHandler, OutputEventType, create_custom_output_handler
from ..config.settings import get_settings

router = APIRouter(prefix="/api", tags=["games"])

# Game service instance (will be injected later)
game_service: GameService = None


def set_game_service(service: GameService):
    """Set the game service instance."""
    global game_service
    game_service = service


def create_backend_output_handler(game_id: str) -> OutputHandler:
    """Create an output handler that forwards messages to frontend via SSE."""
    
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
        await game_service.broadcast_event(game_id, event_data)
    
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


def get_game_or_404(game_id: str):
    """Get game instance or raise 404."""
    game = game_service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.post("/games", response_model=GameResponse)
async def create_game(request: GameCreateRequest):
    """Create a new werewolf game."""
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
    
    try:
        # Create request with validated values
        validated_request = GameCreateRequest(
            num_players=request.num_players,
            api_key=api_key,
            model=model
        )
        
        # Create custom output handler for this game
        output_handler = create_backend_output_handler("")  # Will be updated with actual game_id
        
        # Create game
        game_id = await game_service.create_game(validated_request, output_handler)
        
        # Update output handler with actual game_id
        output_handler = create_backend_output_handler(game_id)
        game = game_service.get_game(game_id)
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create game: {str(e)}")


@router.get("/games/{game_id}", response_model=GameStateResponse)
async def get_game_state(game_id: str):
    """Get current game state."""
    game = get_game_or_404(game_id)
    state_dict = game_service.get_game_state_dict(game)
    
    return GameStateResponse(
        game_id=game_id,
        **state_dict
    )


@router.post("/games/{game_id}/start")
async def start_game(game_id: str):
    """Start the game."""
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


@router.post("/games/{game_id}/action")
async def player_action(game_id: str, action: PlayerAction):
    """Handle player action (speak, vote, etc.)."""
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


@router.get("/games/{game_id}/events")
async def stream_events(game_id: str):
    """Stream game events using Server-Sent Events."""
    
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


@router.get("/games/{game_id}/players")
async def get_players(game_id: str):
    """Get all players in the game."""
    game = get_game_or_404(game_id)
    
    return {
        "players": [game_service.player_to_dict(p) for p in game.game_state.players.values()]
    }


@router.delete("/games/{game_id}")
async def delete_game(game_id: str):
    """Delete a game."""
    success = game_service.delete_game(game_id)
    
    if success:
        return {"status": "deleted", "message": "Game deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Game not found")
