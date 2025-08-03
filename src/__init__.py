"""
Werewolf AI Agent Game

A sophisticated multi-agent implementation of the classic Werewolf/Mafia game
using advanced AI agents with multi-step reasoning capabilities.
"""

__version__ = "2.0.0"
__author__ = "Werewolf AI Team"

from .core.game import WerewolfGame
from .core.game_state import GameState
from .core.player import Player, Role

__all__ = ["WerewolfGame", "GameState", "Player", "Role"]
