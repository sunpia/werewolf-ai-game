"""God Advanced Agent - AI-powered game moderator using AdvancedAgent framework."""

from typing import List, Dict
from .advanced_agent import AdvancedAgent, AgentType


class GodAdvancedAgent(AdvancedAgent):
    """God agent using AdvancedAgent framework for game moderation."""
    
    def __init__(self, api_key: str, model: str, name: str):
        """Initialize the god advanced agent."""
        super().__init__(api_key, model, name, agent_type=AgentType.GOD)
        
    def announce_day_start(self, day_count: int, game_state: str, recent_events: str) -> str:
        """Announce the start of a new day."""
        instruction = f"""You are the MODERATOR (God) of a Werewolf game. 

It's Day {day_count}.

Current game state:
{game_state}

Recent events:
{recent_events}

Make a brief announcement to start the day. Include:
- Day number
- Who died last night (if anyone)
- Current player count
- Whether voting is enabled today
- For day one voting is not enabled

Keep it concise and atmospheric. Example:
"Good morning! This is Day 2. Last night, Player_3 was found dead. 8 players remain alive. Today you may discuss and vote."

Provide only the announcement:"""
        
        response = self.step(instruction)
        return response.content if hasattr(response, 'content') else str(response)
    
    def announce_night_start(self, game_state: str, wolves: List[str]) -> str:
        """Announce the start of night phase."""
        instruction = f"""You are the MODERATOR (God) of a Werewolf game.

Current game state:
{game_state}

Alive wolves: {', '.join(wolves) if wolves else 'None'}

Announce the start of the night phase. Include:
- That night has fallen
- Players should go to sleep
- Wolves wake up to choose their victim (if any wolves alive)

Keep it brief and atmospheric. Example:
"Night falls over the village. All players close their eyes and go to sleep... Werewolves, wake up and choose your victim."

Provide only the announcement:"""
        
        response = self.step(instruction)
        return response.content if hasattr(response, 'content') else str(response)
    
    def announce_vote_results(self, vote_results: Dict[int, int], eliminated_player: str) -> str:
        """Announce voting results and elimination."""
        vote_summary = []
        for player_name, vote_count in vote_results.items():
            vote_summary.append(f"Player {player_name} received {vote_count} vote(s)")
        
        vote_text = ", ".join(vote_summary)
        
        instruction = f"""You are the MODERATOR (God) of a Werewolf game.

Voting results: {vote_text}

Eliminated player: {eliminated_player}

Announce the voting results and elimination. Include:
- Vote counts for each player
- Who was eliminated
- Brief dramatic flair

Keep it concise. Example:
"The votes are in! Player A received 3 votes, Player B received 1 vote, and Players C and D received none. Player A has been eliminated!"

Provide only the announcement:"""
        
        response = self.step(instruction)
        return response.content if hasattr(response, 'content') else str(response)
    
    def announce_game_over(self, winner: str, final_state: str) -> str:
        """Announce game over and winner."""
        instruction = f"""You are the MODERATOR (God) of a Werewolf game.

Winner: {winner}
Final game state: {final_state}

Announce the end of the game. Include:
- That the game is over
- Who won (Wolves or Civilians)
- Brief congratulations
- Thank players for playing

Keep it celebratory. Example:
"🎮 GAME OVER! 🎮\nWinner: Civilians\nFinal state: 3 alive players, all civilians\n\nCongratulations to the surviving villagers! Thank you for playing Werewolf!"

Provide only the announcement:"""
        
        response = self.step(instruction)
        return response.content if hasattr(response, 'content') else str(response)
    
    def speak(self, game_state: str, context: str) -> str:
        """Generate speech for god (shouldn't be called in normal gameplay)."""
        instruction = f"""You are the MODERATOR (God) of a Werewolf game.

Game state: {game_state}
Context: {context}

As the moderator, provide guidance or commentary if needed. Usually the god doesn't speak during normal gameplay phases.

Your response:"""
        
        response = self.step(instruction)
        return response.content if hasattr(response, 'content') else str(response)
