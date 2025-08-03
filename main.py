#!/usr/bin/env python3
"""
Werewolf AI Agent Game - Main Entry Point

A sophisticated multi-agent implementation of the classic Werewolf/Mafia game
with advanced AI agents capable of strategic reasoning and internet research.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from src.core.game import main

if __name__ == "__main__":
    main()
