"""Core package for Werewolf game components."""

from .game import WerewolfGame
from .game_state import GameState, GamePhase
from .player import Player, Role

__all__ = ["WerewolfGame", "GameState", "GamePhase", "Player", "Role"]
