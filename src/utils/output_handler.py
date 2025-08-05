"""Output handler for Werewolf game messages and events."""

from typing import Optional, Callable, Any
from enum import Enum
from colorama import init, Fore, Back, Style

# Initialize colorama for colored output
init(autoreset=True)

class OutputEventType(Enum):
    """Types of output events that can occur in the game."""
    GAME_ANNOUNCEMENT = "game_announcement"      # God/moderator announcements
    PLAYER_SPEECH = "player_speech"              # Player speaking
    WOLF_COMMUNICATION = "wolf_communication"    # Wolf private communication
    VOTING = "voting"                            # Voting actions
    ELIMINATION = "elimination"                  # Player elimination
    NIGHT_KILL = "night_kill"                   # Night kill results
    PHASE_TRANSITION = "phase_transition"       # Day/night transitions
    GAME_STATE = "game_state"                   # Game state updates
    ERROR = "error"                             # Error messages
    SYSTEM = "system"                           # System messages

class OutputHandler:
    """Handles game output with pluggable output functions."""
    
    def __init__(self, output_function: Optional[Callable] = None):
        """Initialize with optional custom output function.
        
        Args:
            output_function: Custom function to handle output. Should accept:
                - message: str - The message to output
                - event_type: OutputEventType - Type of event
                - player: Optional[Player] - Player object if applicable
                - metadata: Optional[dict] - Additional event metadata
        """
        self.output_function = output_function or self._default_console_output
    
    def notify(self, message: str, player: Optional[Any] = None, 
                     event_type: OutputEventType = OutputEventType.SYSTEM,
                     metadata: Optional[dict] = None) -> None:
        """Print colored message with event information.
        
        Args:
            message: The message to output
            player: Player object (if applicable)
            event_type: Type of event
            metadata: Additional metadata about the event
        """
        self.output_function(message, event_type, player, metadata or {})
    
    def _default_console_output(self, message: str, event_type: OutputEventType, 
                               player: Optional[Any] = None, metadata: dict = None) -> None:
        """Default console output with colored formatting."""
        # Handle both AIMessage objects and strings
        if hasattr(message, 'content'):
            content = message.content
        else:
            content = str(message)
        
        # Color based on player role or event type
        if player is None:
            if event_type == OutputEventType.GAME_ANNOUNCEMENT:
                print(f"{Fore.YELLOW}⭐ {content}{Style.RESET_ALL}")
            elif event_type == OutputEventType.PHASE_TRANSITION:
                print(f"{Back.CYAN}{Fore.BLACK} {content} {Style.RESET_ALL}")
            elif event_type == OutputEventType.ERROR:
                print(f"{Fore.RED}❌ {content}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}{content}{Style.RESET_ALL}")
        elif hasattr(player, 'is_wolf') and player.is_wolf():
            if event_type == OutputEventType.WOLF_COMMUNICATION:
                print(f"{Fore.RED}🐺 {player.name} (to wolves): {content}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}🐺 {player.name}: {content}{Style.RESET_ALL}")
        elif hasattr(player, 'is_civilian') and player.is_civilian():
            print(f"{Fore.GREEN}👤 {player.name}: {content}{Style.RESET_ALL}")
        elif hasattr(player, 'is_god') and player.is_god():
            print(f"{Fore.YELLOW}⭐ {player.name}: {content}{Style.RESET_ALL}")
        else:
            print(f"{content}")

# Convenience function for backward compatibility
def create_console_output_handler() -> OutputHandler:
    """Create an output handler that prints to console."""
    return OutputHandler()

def create_custom_output_handler(output_function: Callable) -> OutputHandler:
    """Create an output handler with custom output function."""
    return OutputHandler(output_function)
