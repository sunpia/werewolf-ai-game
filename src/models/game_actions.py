"""Game action models for Werewolf game."""

from dataclasses import dataclass
from typing import List, Optional, Union
from enum import Enum

class ActionType(Enum):
    """Types of AI actions."""
    SPEECH = "speech"
    NIGHT_KILL = "night_kill"
    PHASE_COMPLETE = "phase_complete"

@dataclass
class WolfCommunication:
    """Wolf communication during night phase."""
    player: str
    message: str

@dataclass
class SpeechAction:
    """Player speech action."""
    type: str = "speech"
    player: str = ""
    message: str = ""
    role: str = ""

@dataclass
class NightKillAction:
    """Night kill action by wolves."""
    type: str = "night_kill"
    target: str = ""
    wolf_communications: List[WolfCommunication] = None
    
    def __post_init__(self):
        if self.wolf_communications is None:
            self.wolf_communications = []

@dataclass
class PhaseCompleteAction:
    """Phase completion action."""
    type: str = "phase_complete"
    current_phase: str = ""

# Union type for all possible AI actions
AIAction = Union[SpeechAction, NightKillAction, PhaseCompleteAction]
