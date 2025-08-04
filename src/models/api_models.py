"""API models for Werewolf game backend."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

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

class GameHistoryResponse(BaseModel):
    """Response model for game history."""
    id: str
    user_id: str
    status: str
    num_players: int
    current_phase: Optional[str]
    current_day: int
    winner: Optional[str]
    is_game_over: bool
    created_at: str
    completed_at: Optional[str]

class UserGamesResponse(BaseModel):
    """Response model for user's games."""
    games: List[GameHistoryResponse]
    total_games: int
    free_games_remaining: int

class GameLimitsResponse(BaseModel):
    """Response model for user's game limits."""
    free_games_remaining: int
    total_games_played: int
    can_create_game: bool
    winner: Optional[str]
    is_game_over: bool
    created_at: str
    completed_at: Optional[str]

class UserGamesResponse(BaseModel):
    """Response model for user's games."""
    games: List[GameHistoryResponse]
    total_games: int
    free_games_remaining: int

class GameLimitsResponse(BaseModel):
    """Response model for user's game limits."""
    free_games_remaining: int
    total_games_played: int
    can_create_game: bool
