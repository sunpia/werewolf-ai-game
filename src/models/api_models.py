"""Simplified API models for Werewolf game backend."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

# Request models
class GameCreateRequest(BaseModel):
    """Request model for creating a new game."""
    num_players: int
    api_key: Optional[str] = None
    model: Optional[str] = None

class PlayerAction(BaseModel):
    """Model for player actions."""
    player_name: str
    action_type: str  # 'speak', 'vote', 'night_kill'
    target: Optional[str] = None
    message: Optional[str] = None

class SystemEventRequest(BaseModel):
    """Request model for creating system events."""
    event_type: str  # day_transition, night_transition, game_start, game_end, voting_start, voting_end
    event_description: str
    phase: Optional[str] = None
    day_number: Optional[int] = None
    event_metadata: Optional[Dict[str, Any]] = None

class UserEventRequest(BaseModel):
    """Request model for creating user events."""
    event_type: str  # speech, strategy_change, vote, accusation, defense, night_action
    original_value: Optional[str] = None
    modified_value: str
    phase: Optional[str] = None
    day_number: Optional[int] = None
    event_metadata: Optional[Dict[str, Any]] = None

# Create models (for internal use)
class SystemEventCreate(BaseModel):
    """Model for creating system events."""
    game_id: str
    event_type: str  # day_transition, night_transition, game_start, game_end, voting_start, voting_end
    event_description: str
    phase: Optional[str] = None
    day_number: Optional[int] = None
    event_metadata: Optional[Dict[str, Any]] = None

class UserEventCreate(BaseModel):
    """Model for creating user events."""
    game_id: str
    player_id: str
    event_type: str  # speech, strategy_change, vote, accusation, defense, night_action
    original_value: Optional[str] = None
    modified_value: str
    phase: Optional[str] = None
    day_number: Optional[int] = None
    event_metadata: Optional[Dict[str, Any]] = None

# Response models
class GameResponse(BaseModel):
    """Response model for game operations."""
    game_id: str
    status: str
    message: str

class GameStateResponse(BaseModel):
    """Response model for game state."""
    game_id: str
    phase: str
    day_count: int
    alive_players: List[Dict[str, Any]]
    current_speaker: Optional[str]
    is_game_over: bool
    winner: Optional[str]

class PlayerResponse(BaseModel):
    """Response model for player information."""
    id: str
    game_id: str
    player_name: str
    role: Optional[str]
    is_alive: bool
    is_god: bool
    ai_personality: Optional[Dict[str, Any]]
    strategy_pattern: Optional[Dict[str, Any]]
    created_at: str

class SystemEventResponse(BaseModel):
    """Response model for system events."""
    id: str
    game_id: str
    event_type: str
    event_description: str
    event_time: str
    phase: Optional[str]
    day_number: Optional[int]
    event_metadata: Optional[Dict[str, Any]]

class UserEventResponse(BaseModel):
    """Response model for user events."""
    id: str
    player_id: str
    event_type: str
    original_value: Optional[str]
    modified_value: str
    event_time: str
    phase: Optional[str]
    day_number: Optional[int]
    event_metadata: Optional[Dict[str, Any]]

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

class CompleteGameDataResponse(BaseModel):
    """Response model for complete game data including all events."""
    game: Dict[str, Any]
    players: List[Dict[str, Any]]
    system_events: List[Dict[str, Any]]
    user_events: List[Dict[str, Any]]

class EventMessage(BaseModel):
    """Model for event messages."""
    event_type: str
    timestamp: str
    data: Dict[str, Any]
