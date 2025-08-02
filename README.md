# 🐺 Werewolf AI Agent Game v2.0

A sophisticated multi-agent implementation of the classic Werewolf/Mafia game featuring advanced AI agents with multi-step reasoning capabilities and internet research integration.

## ✨ Features

### 🎮 Core Game Features
- **Complete Werewolf/Mafia Game**: Full implementation with day/night cycles, voting, and win conditions
- **6-15 Players**: Supports standard game sizes with balanced role distribution
- **Role-Based Agents**: Wolves, Civilians, and God (moderator) with distinct behaviors
- **Colored Terminal Output**: Beautiful, easy-to-follow game progression

### 🧠 Advanced AI Features
- **Multi-Step Reasoning**: Agents analyze, plan, validate, and execute decisions
- **Internet Research**: Real-time web search for strategic insights
- **Strategic Memory**: Agents remember and learn from game events
- **Confidence Scoring**: Quantified decision-making quality
- **Adaptive Behavior**: Different strategies based on game state

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### 2. Setup

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-3.5-turbo-instruct
```

### 3. Run the Game

```bash
python main.py
```

## 🎯 Game Rules

### Roles
- **Wolves** (20% of players, minimum 1): Can kill one player per night, must lie during day
- **Civilians** (remaining players): Must identify and eliminate all wolves
- **God** (1 player): Game moderator, manages phases and announcements

### Gameplay
1. **Day Phase**: Players discuss and vote to eliminate suspected wolves
2. **Night Phase**: Wolves secretly choose a victim
3. **Victory Conditions**:
   - **Civilians win**: All wolves eliminated
   - **Wolves win**: Wolves equal or outnumber civilians
```
OPENAI_API_KEY=your_api_key_here
```

3. Run the game:
```bash
python main.py
```

## Files Structure

- `main.py` - Game entry point
- `game.py` - Main game logic and orchestration
- `agents/` - Agent implementations
  - `wolf_agent.py` - Wolf player agent
  - `god_agent.py` - Game moderator agent
  - `civilian_agent.py` - Civilian player agent
- `utils/` - Utility functions
  - `game_state.py` - Game state management
  - `player.py` - Player class definition
