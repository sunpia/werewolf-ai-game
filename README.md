# 🐺 Werewolf AI Agent Game v2.0

A sophisticated multi-agent implementation of the classic Werewolf/Mafia game featuring advanced AI agents with realistic personalities, strategic thinking, and immersive roleplay elements.

## ✨ Features

### 🎮 Core Game Features
- **Complete Werewolf/Mafia Game**: Full implementation with day/night cycles, voting, and win conditions
- **6-15 Players**: Supports standard game sizes with balanced role distribution (20% wolves, minimum 1)
- **Role-Based Agents**: Wolves, Civilians, and God (moderator) with distinct behaviors and personalities
- **Dynamic Terminal Output**: Real-time game progression with clear phase transitions and voting results
- **Realistic Player Names**: Randomly generated diverse character names for immersive gameplay

### 🧠 Advanced AI Features
- **Personality-Driven Agents**: Each AI has unique speaking patterns and decision-making styles
- **Strategic Wolf Coordination**: Wolves communicate privately to plan eliminations and avoid detection
- **Multi-Phase Gameplay**: Speaking phases, voting phases, and night elimination rounds
- **Behavioral Analysis**: Agents analyze voting patterns, speech patterns, and behavioral changes
- **Adaptive Strategies**: Different approaches based on game state, role, and social dynamics

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/sunpia/werewolf-ai-game.git
cd werewolf-ai-game

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4-turbo
```

### 3. Run the Game

```bash
python main.py
```

The game will prompt you to:
1. Enter the number of players (6-15)
2. Watch as AI agents are assigned random names and roles
3. Observe the strategic gameplay unfold automatically

## 🎭 Sample Gameplay Experience

When you run the game, you'll see:

```
🐺 Welcome to Werewolf AI Agent Game! 🐺

Enter number of players (6-15): 12

=== Game Initialized ===
Wolves: Molly Eaton, Virginia Perry
Civilians: Stephanie Miller, James Baker, Brandon Shaw MD, Stacy Galvan, 
          Mr. Kyle Travis, Edward Flowers, Julie Dunn, John Horton, David Phillips
God: Alexis Lee
Total Players: 12

🎮 WEREWOLF GAME STARTING! 🎮
```

### What You'll Experience:
- **Rich Character Interactions**: Each AI agent has distinct speaking patterns and strategies
- **Strategic Wolf Coordination**: Private wolf discussions during night phases
- **Dynamic Social Deduction**: Agents analyze behavior, voting patterns, and speech
- **Realistic Game Progression**: From cautious early game to intense late-game accusations
- **Authentic Werewolf Drama**: Suspicion, betrayal, and strategic eliminations

## 🎮 Example Game Scenarios

### Early Game Dynamics
```
👤 Stephanie Miller: "I'm curious about everyone's initial thoughts—does anyone 
have any gut feelings, or notice anything odd yet?"

👤 Edward Flowers: "Are you all serious right now? 'Let's wait and listen'—
that's how the wolves win! I want names and reasons, not wishy-washy nonsense."

🐺 Virginia Perry: "Sometimes the wolves don't hide in silence—they hide by 
pretending to be the loudest 'villager' in the room."
```

### Strategic Wolf Coordination
```
🐺 Molly Eaton (to wolves): "Consider eliminating someone who seems level-headed 
and trusted—David Phillips stands out as wise and reasonable. Taking him out 
might make the village more divided and easier to manipulate."

🐺 Virginia Perry (to wolves): "I agree—eliminating David Phillips is the best 
play. He's calm, rational, and already encouraging people to be thoughtful."
```

### Voting Drama
```
⭐ Alexis Lee: Votes are in! Brandon Shaw MD: 8 votes. Edward Flowers: 2 votes. 
Brandon Shaw MD has been eliminated—justice or mistake? We'll see.

⭐ Alexis Lee: Day 3. Last night, Stephanie Miller was killed. 8 players left. 
Voting is enabled—get to it.
```

## 🏆 Game Balance & Strategy

### Wolf Advantages
- **Information Asymmetry**: Wolves know each other's identities
- **Coordinated Strategy**: Private communication for optimal target selection
- **Deception Skills**: Ability to blend in and misdirect suspicion

### Civilian Challenges
- **Limited Information**: Must deduce wolf identities through behavior
- **Social Pressure**: Balancing caution with need for decisive action
- **Trust Building**: Forming alliances without knowing true loyalties

### Winning Strategies Observed
- **Wolves**: Eliminate key unifying voices, exploit village infighting
- **Civilians**: Pattern analysis, consistent behavioral observation, coordinated voting

## 🎯 Future Enhancements

- **Enhanced Personality System**: More diverse agent archetypes
- **Advanced Strategy Engine**: Machine learning-based gameplay optimization
- **Interactive Mode**: Human player integration with AI agents
- **Game Analytics**: Post-game analysis and strategy insights
- **Multiple Game Variants**: Different rule sets and special roles

---

*Ready to witness AI social deduction at its finest? Clone the repo and watch the drama unfold!* 🎭
- **Authentic Werewolf Drama**: Suspicion, betrayal, and strategic eliminations

## 🎯 Game Rules & Mechanics

### Roles
- **Wolves** (20% of players, minimum 1): Can eliminate one player per night, must deceive during day phases
- **Civilians** (remaining players): Must identify and vote out all wolves to win
- **God** (1 moderator): Manages game phases, announces deaths, and oversees voting

### Gameplay Flow
1. **Day Phase**: 
   - All players participate in speaking rounds
   - Open discussion about suspicions and observations
   - Voting phase to eliminate suspected wolves
   - Real-time vote tallying and elimination announcements

2. **Night Phase**: 
   - Wolves privately coordinate to choose their next victim
   - Strategic elimination targeting key village members
   - Moderator announces the elimination at dawn

3. **Victory Conditions**:
   - **Civilians win**: All wolves eliminated through voting
   - **Wolves win**: Wolves equal or outnumber remaining civilians

### Game Features Demonstrated
- **Dynamic Player Personalities**: From cautious and analytical to aggressive and confrontational
- **Strategic Wolf Play**: Coordinated elimination of key village voices and unity builders
- **Realistic Social Deduction**: Suspicion patterns, voting analysis, and behavioral observation
- **Escalating Tension**: Increasing pressure as player count decreases
- **Authentic Werewolf Experience**: Classic game mechanics with AI-driven social dynamics


📖 **[View Complete Game Demo](DEMO.md)** - See a full 12-player game from start to finish with detailed AI interactions and strategic gameplay.