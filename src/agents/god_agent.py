"""God agent - game moderator, manages phases and orchestrates gameplay."""

from langchain.prompts import PromptTemplate
from typing import List, Dict

from .base_agent import BaseAgent

class GodAgent(BaseAgent):
    """God agent - game moderator, manages phases and orchestrates gameplay."""
    
    def __init__(self, llm, player_id: int, name: str):
        """Initialize the god agent.
        
        Args:
            llm: Language model instance
            player_id: Unique identifier for this player
            name: Display name for this player
        """
        super().__init__(llm, player_id, name)
        
        # Day announcement prompt
        self.day_announcement_prompt = PromptTemplate(
            input_variables=["day_count", "game_state", "recent_events"],
            template="""You are the MODERATOR (God) of a Werewolf game. 

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
- For day one the voting is not enabled

Keep it concise and atmospheric. Example:
"Good morning! This is Day 2. Last night, Player_3 was found dead. 8 players remain alive. Today you may discuss and vote."

Your announcement:"""
        )
        
        # Night announcement prompt
        self.night_announcement_prompt = PromptTemplate(
            input_variables=["game_state", "wolves"],
            template="""You are the MODERATOR (God) of a Werewolf game.

Night has fallen.

Current game state:
{game_state}

The wolves are: {wolves}

Make a brief night announcement. Keep it atmospheric and simple.

Example: "Night falls. Everyone goes to sleep. Wolves, you may now choose your victim."

Your announcement:"""
        )
        
        # Vote summary prompt
        self.vote_summary_prompt = PromptTemplate(
            input_variables=["vote_results", "eliminated_player"],
            template="""You are the MODERATOR announcing voting results.

Vote results: {vote_results}

Player eliminated: {eliminated_player}

Announce the voting results dramatically but concisely.

Example: "The votes have been counted. Player_5 received 3 votes, Player_2 received 2 votes. Player_5 has been eliminated!"

Your announcement:"""
        )
        
    def announce_day_start(self, day_count: int, game_state: str, recent_events: str) -> str:
        """Announce the start of a new day.
        
        Args:
            day_count: Current day number
            game_state: Current state of the game
            recent_events: Recent events to mention
            
        Returns:
            Day start announcement
        """
        prompt = self.day_announcement_prompt.format(
            day_count=day_count,
            game_state=game_state,
            recent_events=recent_events
        )
        
        response = self.llm.invoke(prompt)
        self.add_to_memory(f"Day {day_count} announcement: {response}")
        return response
        
    def announce_night_start(self, game_state: str, wolves: List[str]) -> str:
        """Announce the start of night phase.
        
        Args:
            game_state: Current state of the game
            wolves: List of wolf players
            
        Returns:
            Night start announcement
        """
        prompt = self.night_announcement_prompt.format(
            game_state=game_state,
            wolves=wolves
        )
        
        response = self.llm.invoke(prompt)
        self.add_to_memory(f"Night announcement: {response}")
        return response
        
    def announce_vote_results(self, vote_results: Dict[int, int], eliminated_player: str) -> str:
        """Announce voting results.
        
        Args:
            vote_results: Dictionary of player_id -> vote_count
            eliminated_player: Name of eliminated player
            
        Returns:
            Vote results announcement
        """
        vote_summary = ", ".join([f"Player_{pid}: {votes} votes" for pid, votes in vote_results.items()])
        
        prompt = self.vote_summary_prompt.format(
            vote_results=vote_summary,
            eliminated_player=eliminated_player
        )
        
        response = self.llm.invoke(prompt)
        self.add_to_memory(f"Vote results: {response}")
        return response
        
    def get_speaking_instruction(self, current_speaker: str, phase: str) -> str:
        """Get instruction for current speaker.
        
        Args:
            current_speaker: Name of the current speaker
            phase: Current game phase
            
        Returns:
            Speaking instruction
        """
        if phase == "day":
            return f"{current_speaker}, it's your turn to speak. Share your thoughts and suspicions."
        else:
            return f"{current_speaker}, please make your choice."
            
    def announce_game_over(self, winner: str, final_state: str) -> str:
        """Announce game over.
        
        Args:
            winner: The winning team
            final_state: Final game state
            
        Returns:
            Game over announcement
        """
        announcement = f"\n🎮 GAME OVER! 🎮\n"
        announcement += f"Winner: {winner}\n"
        announcement += f"Final state: {final_state}\n"
        announcement += f"Thank you for playing Werewolf!"
        
        self.add_to_memory(f"Game over: {winner} wins")
        return announcement
        
    def speak(self, game_state: str, context: str) -> str:
        """God doesn't speak during regular phases.
        
        Args:
            game_state: Current state of the game
            context: Additional context
            
        Returns:
            Empty string since god doesn't participate in regular discussion
        """
        return ""
        
    def vote(self, game_state: str, context: str, eligible_players: List[int]) -> int:
        """God doesn't vote.
        
        Args:
            game_state: Current state of the game
            context: Additional context
            eligible_players: List of eligible players
            
        Returns:
            -1 since god doesn't vote
        """
        return -1
