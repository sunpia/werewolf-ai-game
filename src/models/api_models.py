"""API models for Werewolf game backend."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel

class GameCreateRequest(BaseModel):
    """Request model for creating a new game."""
    num_players: int
    api_key: Optional[str] = None
    model: Optional[str] = None

class GameResponse(BaseModel):
    """Response model for game operations."""
    game_id: str
    status: str
    message: str

class PlayerAction(BaseModel):
    """Model for player actions."""
    player_name: str
    action_type: str  # 'speak', 'vote', 'night_kill'
    target: Optional[str] = None
    message: Optional[str] = None

class GameStateResponse(BaseModel):
    """Response model for game state."""
    game_id: str
    phase: str
    day_count: int
    alive_players: List[Dict[str, Any]]
    current_speaker: Optional[str]
    game_history: List[str]
    is_game_over: bool
    winner: Optional[str]

class EventMessage(BaseModel):
    """Model for event messages."""
    event_type: str
    timestamp: str
    data: Dict[str, Any]
