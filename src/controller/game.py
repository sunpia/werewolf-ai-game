#!/usr/bin/env python3
"""
Werewolf AI Game Backend Service

FastAPI backend with Server-Sent Events (SSE) for real-time game updates.
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from src.core.game import WerewolfGame, EventType
from src.core.game_state import GameState, GamePhase
from src.core.player import Player, Role

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Werewolf AI Game Backend",
    description="Backend service for the Werewolf AI game with real-time updates",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global game instances storage
games: Dict[str, WerewolfGame] = {}
game_events: Dict[str, List[Dict]] = {}
active_connections: Dict[str, List[asyncio.Queue]] = {}

# Pydantic models
class GameCreateRequest(BaseModel):
    num_players: int
    api_key: Optional[str] = None
    model: Optional[str] = None

class GameResponse(BaseModel):
    game_id: str
    status: str
    message: str

class PlayerAction(BaseModel):
    player_name: str
    action_type: str  # 'speak', 'vote', 'night_kill'
    target: Optional[str] = None
    message: Optional[str] = None

class GameStateResponse(BaseModel):
    game_id: str
    phase: str
    day_count: int
    alive_players: List[Dict[str, Any]]
    current_speaker: Optional[str]
    game_history: List[str]
    is_game_over: bool
    winner: Optional[str]

class EventMessage(BaseModel):
    event_type: str
    timestamp: str
    data: Dict[str, Any]

# Helper functions
def get_game_or_404(game_id: str) -> WerewolfGame:
    """Get game instance or raise 404."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    return games[game_id]

async def broadcast_event(game_id: str, event: Dict[str, Any]):
    """Broadcast an event to all connected clients for a game."""
    if game_id not in active_connections:
        return
    
    event_msg = {
        "event_type": event.get("type", "unknown"),
        "timestamp": datetime.now().isoformat(),
        "data": event
    }
    
    # Store event in history
    if game_id not in game_events:
        game_events[game_id] = []
    game_events[game_id].append(event_msg)
    
    # Broadcast to all connected clients
    disconnected_queues = []
    for queue in active_connections[game_id]:
        try:
            await queue.put(event_msg)
        except Exception:
            disconnected_queues.append(queue)
    
    # Remove disconnected queues
    for queue in disconnected_queues:
        active_connections[game_id].remove(queue)

def player_to_dict(player: Player, include_role: bool = False) -> Dict[str, Any]:
    """Convert player object to dictionary."""
    result = {
        "id": player.id,
        "name": player.name,
        "is_alive": player.is_alive,
        "is_god": player.is_god()
    }
    if include_role:
        result["role"] = player.role.value
    return result

def get_game_state_dict(game: WerewolfGame, include_roles: bool = False) -> Dict[str, Any]:
    """Get current game state as dictionary."""
    # Check if game has methods for game over and winner
    is_game_over = False
    winner = None
    
    try:
        # Check win conditions
        alive_wolves = len(game.game_state.alive_wolves)
        alive_civilians = len(game.game_state.alive_civilians)
        
        if alive_wolves == 0:
            is_game_over = True
            winner = "villagers"
        elif alive_wolves >= alive_civilians:
            is_game_over = True
            winner = "wolves"
    except:
        pass
    
    current_speaker = None
    if hasattr(game.game_state, 'speaker_queue') and game.game_state.speaker_queue:
        # Don't remove the speaker, just peek
        current_speaker = game.game_state.speaker_queue[0].name if game.game_state.speaker_queue else None
    
    return {
        "phase": game.game_state.current_phase.value,
        "day_count": game.game_state.day_count,
        "alive_players": [player_to_dict(p, include_roles) for p in game.game_state.alive_players],
        "current_speaker": current_speaker,
        "game_history": game.game_state.game_history[-20:],  # Last 20 events
        "is_game_over": is_game_over,
        "winner": winner
    }

# API Endpoints

@app.post("/api/games", response_model=GameResponse)
async def create_game(request: GameCreateRequest):
    """Create a new werewolf game."""
    if not (6 <= request.num_players <= 15):
        raise HTTPException(status_code=400, detail="Number of players must be between 6 and 15")
    
    # Use provided API key or default from environment
    api_key = request.api_key or os.getenv("OPENAI_API_KEY")
    model = request.model or os.getenv("OPENAI_MODEL", "gemini-2.5-flash-lite")
    
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    try:
        game_id = str(uuid.uuid4())
        game = WerewolfGame(request.num_players, api_key, model)
        games[game_id] = game
        active_connections[game_id] = []
        game_events[game_id] = []
        
        # Broadcast game creation event
        await broadcast_event(game_id, {
            "type": "game_created",
            "game_id": game_id,
            "num_players": request.num_players,
            "players": [player_to_dict(p) for p in game.game_state.players.values()]
        })
        
        return GameResponse(
            game_id=game_id,
            status="created",
            message=f"Game created with {request.num_players} players"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create game: {str(e)}")

@app.get("/api/games/{game_id}", response_model=GameStateResponse)
async def get_game_state(game_id: str):
    """Get current game state."""
    game = get_game_or_404(game_id)
    state_dict = get_game_state_dict(game)
    
    return GameStateResponse(
        game_id=game_id,
        **state_dict
    )

@app.post("/api/games/{game_id}/start")
async def start_game(game_id: str):
    """Start the game."""
    game = get_game_or_404(game_id)
    
    try:
        # Start the game in background
        asyncio.create_task(run_game_loop(game_id, game))
        
        await broadcast_event(game_id, {
            "type": "game_started",
            "game_id": game_id,
            "phase": game.game_state.current_phase.value,
            "day_count": game.game_state.day_count
        })
        
        return {"status": "started", "message": "Game has been started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start game: {str(e)}")

@app.post("/api/games/{game_id}/action")
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
        await broadcast_event(game_id, {
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

@app.get("/api/games/{game_id}/events")
async def stream_events(game_id: str):
    """Stream game events using Server-Sent Events."""
    game = get_game_or_404(game_id)
    
    async def event_stream():
        # Create a queue for this connection
        queue = asyncio.Queue()
        
        # Add queue to active connections
        if game_id not in active_connections:
            active_connections[game_id] = []
        active_connections[game_id].append(queue)
        
        try:
            # Send recent events first
            if game_id in game_events:
                for event in game_events[game_id][-10:]:  # Last 10 events
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
            if game_id in active_connections and queue in active_connections[game_id]:
                active_connections[game_id].remove(queue)
    
    return StreamingResponse(
        event_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@app.get("/api/games/{game_id}/players")
async def get_players(game_id: str):
    """Get all players in the game."""
    game = get_game_or_404(game_id)
    
    return {
        "players": [player_to_dict(p, include_role=True) for p in game.game_state.players.values()]
    }

@app.delete("/api/games/{game_id}")
async def delete_game(game_id: str):
    """Delete a game."""
    if game_id in games:
        del games[game_id]
    if game_id in game_events:
        del game_events[game_id]
    if game_id in active_connections:
        del active_connections[game_id]
    
    return {"status": "deleted", "message": "Game deleted successfully"}

# Background game loop
async def run_game_loop(game_id: str, game: WerewolfGame):
    """Run the game loop in the background with AI agents."""
    try:
        while True:
            await asyncio.sleep(3)  # Small delay between actions
            
            # Check win conditions
            alive_wolves = len(game.game_state.alive_wolves)
            alive_civilians = len(game.game_state.alive_civilians)
            
            if alive_wolves == 0:
                await broadcast_event(game_id, {
                    "type": "game_over",
                    "winner": "villagers",
                    "message": "All wolves have been eliminated! Villagers win!"
                })
                break
            elif alive_wolves >= alive_civilians:
                await broadcast_event(game_id, {
                    "type": "game_over",
                    "winner": "wolves", 
                    "message": "Wolves equal or outnumber villagers! Wolves win!"
                })
                break
            
            # Broadcast current state
            await broadcast_event(game_id, {
                "type": "game_state_update",
                **get_game_state_dict(game)
            })
            
            # Run actual game logic based on phase
            if game.game_state.current_phase == GamePhase.DAY:
                # Day phase: Let AI agents speak and discuss
                current_speaker = game.game_state.get_next_speaker()
                if current_speaker and current_speaker.agent:
                    try:
                        # Get AI response
                        ai_response = await asyncio.get_event_loop().run_in_executor(
                            None, 
                            lambda: current_speaker.agent.get_response(
                                game.game_state.get_public_game_state()
                            )
                        )
                        
                        # Add to game history
                        message = f"{current_speaker.name}: {ai_response.content if hasattr(ai_response, 'content') else str(ai_response)}"
                        game.game_state.game_history.append(message)
                        
                        # Broadcast the AI's message
                        await broadcast_event(game_id, {
                            "type": "player_action",
                            "player": current_speaker.name,
                            "action_type": "speak",
                            "message": ai_response.content if hasattr(ai_response, 'content') else str(ai_response),
                            "result": {"spoke": True}
                        })
                        
                    except Exception as e:
                        print(f"Error getting AI response: {e}")
                        # Continue with next speaker
                        pass
                else:
                    # No more speakers, transition to night
                    game.game_state.current_phase = GamePhase.NIGHT
                    await broadcast_event(game_id, {
                        "type": "phase_change",
                        "new_phase": "night",
                        "day_count": game.game_state.day_count,
                        "message": f"Day {game.game_state.day_count} discussion ended. Night phase begins."
                    })
                    
            else:  # Night phase
                # Let wolves decide on target
                alive_wolves = game.game_state.alive_wolves
                if alive_wolves and not game.game_state.night_kill_target:
                    try:
                        # Get the first alive wolf to make decision
                        wolf = alive_wolves[0]
                        if wolf.agent:
                            # Get wolf's target choice
                            wolf_response = await asyncio.get_event_loop().run_in_executor(
                                None,
                                lambda: wolf.agent.get_response(
                                    f"Night phase. Choose your target from alive civilians: {[p.name for p in game.game_state.alive_civilians]}"
                                )
                            )
                            
                            # Parse target from response (simplified)
                            response_text = wolf_response.content if hasattr(wolf_response, 'content') else str(wolf_response)
                            
                            # Find mentioned civilian name in response
                            for civilian in game.game_state.alive_civilians:
                                if civilian.name.lower() in response_text.lower():
                                    game.game_state.night_kill_target = civilian.name
                                    
                                    await broadcast_event(game_id, {
                                        "type": "night_action",
                                        "message": f"Wolves have chosen their target..."
                                    })
                                    break
                    except Exception as e:
                        print(f"Error in wolf night action: {e}")
                
                # After some time, execute night kill and move to day
                await asyncio.sleep(5)  # Night duration
                
                # Process night kill
                if game.game_state.night_kill_target:
                    target_name = game.game_state.night_kill_target
                    for player in game.game_state.players.values():
                        if player.name == target_name:
                            player.is_alive = False
                            game.game_state.game_history.append(f"{target_name} was killed during the night!")
                            break
                    game.game_state.night_kill_target = None
                    
                    await broadcast_event(game_id, {
                        "type": "night_kill",
                        "target": target_name,
                        "message": f"{target_name} was found dead at dawn!"
                    })
                
                # Move to next day
                game.game_state.current_phase = GamePhase.DAY
                game.game_state.day_count += 1
                game.game_state.update_speaking_order()
                
                await broadcast_event(game_id, {
                    "type": "phase_change",
                    "new_phase": "day",
                    "day_count": game.game_state.day_count,
                    "message": f"Day {game.game_state.day_count} begins! Time for discussion."
                })
                    
    except Exception as e:
        await broadcast_event(game_id, {
            "type": "error",
            "message": f"Game loop error: {str(e)}"
        })

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "active_games": len(games)}

if __name__ == "__main__":
    uvicorn.run(
        "game_backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
