"""Player and game enums for the Werewolf game."""

from enum import Enum
from typing import Optional

from src.agents.advanced_agent import AdvancedAgent

class Role(Enum):
    """Player roles in the Werewolf game."""
    WOLF = "wolf"
    CIVILIAN = "civilian"
    GOD = "god"

class GamePhase(Enum):
    """Game phases."""
    DAY = "day"
    NIGHT = "night"
    GAME_OVER = "game_over"

class Player:
    """Represents a player in the Werewolf game."""
    
    def __init__(self, player_id: int, name: str, role: Role):
        """Initialize a player.
        
        Args:
            player_id: Unique identifier for the player
            name: Display name for the player
            role: The player's role in the game
        """
        self.player_id = player_id
        self.name = name
        self.role = role
        self.is_alive = True
        self.votes_received = 0
        self.vote_target: Optional[str] = None
        self.agent: Optional[AdvancedAgent] = None  # Will be set to the agent instance later

    def is_wolf(self) -> bool:
        """Check if this player is a wolf."""
        return self.role == Role.WOLF
        
    def is_civilian(self) -> bool:
        """Check if this player is a civilian."""
        return self.role == Role.CIVILIAN
        
    def is_god(self) -> bool:
        """Check if this player is the god (moderator)."""
        return self.role == Role.GOD
    
    def kill(self) -> None:
        """Kill this player."""
        self.is_alive = False
        
    def reset_votes(self) -> None:
        """Reset votes for new voting round."""
        self.votes_received = 0
        self.vote_target = None
        
    def __str__(self) -> str:
        status = "Alive" if self.is_alive else "Dead"
        return f"Player {self.player_id} ({self.name}) - {self.role.value} - {status}"
        
    def __repr__(self) -> str:
        return self.__str__()
