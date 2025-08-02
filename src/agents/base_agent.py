"""Base agent class for all Werewolf game agents."""

from langchain.llms.base import LLM
from typing import List
from enum import Enum, auto

class AgentType(Enum):
    GOLD = auto()
    WOLF = auto()
    CIVILIAN = auto()

class BaseAgent:
    """Base class for all game agents."""
    
    def __init__(self, llm: LLM, player_id: int, name: str):
        """Initialize the base agent.
        
        Args:
            llm: Language model instance
            player_id: Unique identifier for this player
            name: Display name for this player
        """
        self.llm = llm
        self.player_id = player_id
        self.name = name
        self.memory: List[str] = []
        
    def add_to_memory(self, message: str) -> None:
        """Add a message to the agent's memory.
        
        Args:
            message: Message to remember
        """
        self.memory.append(message)
        # Keep only last 20 messages to avoid token limit
        if len(self.memory) > 20:
            self.memory = self.memory[-20:]
            
    def get_memory_context(self) -> str:
        """Get formatted memory context.
        
        Returns:
            Formatted string of recent memories
        """
        if not self.memory:
            return "No previous events to remember."
        return "Previous events:\n" + "\n".join(self.memory[-10:])  # Last 10 events
        
    def speak(self, game_state: str, context: str) -> str:
        """Generate speech for day phase.
        
        Args:
            game_state: Current state of the game
            context: Additional context for the speech
            
        Returns:
            Speech text
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement speak method")
        
    def vote(self, game_state: str, context: str, eligible_players: List[str]) -> str:
        """Choose who to vote for.
        
        Args:
            game_state: Current state of the game
            context: Additional context for voting
            eligible_players: List of player IDs that can be voted for
            
        Returns:
            Player ID to vote for
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement vote method")
