"""Voting models for Werewolf game."""

from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class EliminatedPlayer:
    """Information about an eliminated player."""
    name: str
    role: str

@dataclass
class VotingResult:
    """Result of a voting phase."""
    votes: List[str]
    vote_counts: Dict[str, int]
    eliminated: Optional[EliminatedPlayer] = None
    error: Optional[str] = None
