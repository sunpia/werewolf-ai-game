"""Civilian agent - tries to identify wolves through discussion."""

from langchain.prompts import PromptTemplate
from langchain.schema import AIMessage
from typing import List
from .base_agent import BaseAgent
import random

class CivilianAgent(BaseAgent):
    """Civilian agent - tries to identify wolves through discussion."""
    
    def __init__(self, llm, player_id: int, name: str):
        """Initialize the civilian agent.
        
        Args:
            llm: Language model instance
            player_id: Unique identifier for this player
            name: Display name for this player
        """
        super().__init__(llm, player_id, name)
        
        # Civilian speaking prompt
        self.speak_prompt = PromptTemplate(
            input_variables=["game_state", "context", "memory"],
            template="""You are a CIVILIAN in a Werewolf game. Your goal is to identify and eliminate all wolves.

CIVILIAN STRATEGY:
- Analyze other players' behavior for suspicious patterns
- Share your observations and suspicions
- Ask probing questions to expose wolves
- Work with other civilians to find the truth
- Pay attention to who defends whom
- Look for contradictions in stories

Current game state:
{game_state}

Current context:
{context}

Your memory:
{memory}

As a civilian, speak naturally about your observations and suspicions. Try to contribute useful information to help identify wolves. Keep your response under 100 words.

Your response:"""
        )
        
        # Civilian voting prompt
        self.vote_prompt = PromptTemplate(
            input_variables=["game_state", "context", "memory", "eligible_players"],
            template="""You are a CIVILIAN voting to eliminate someone you suspect is a wolf.

Current game state:
{game_state}

Context: {context}

Your memory: {memory}

Eligible players to vote for: {eligible_players}

Based on your observations and the discussions, who do you think is most likely to be a wolf?

Consider:
- Who has been acting suspiciously?
- Who has been defending others without good reason?
- Who has been trying to deflect suspicion?
- Who's stories don't add up?

Respond with just the player name you want to vote for. Choose from: {eligible_players}

Your vote (just the name):"""
        )
        
    def speak(self, game_state: str, context: str) -> str:
        """Generate civilian speech - tries to find wolves.
        
        Args:
            game_state: Current state of the game
            context: Additional context for the speech
            
        Returns:
            Speech text focused on wolf detection
        """
        memory_context = self.get_memory_context()
        
        prompt = self.speak_prompt.format(
            game_state=game_state,
            context=context,
            memory=memory_context
        )
        
        response = self.llm.invoke(prompt)
        self.add_to_memory(f"I said: {response}")
        return response

    def vote(self, game_state: str, context: str, eligible_players: List[str]) -> str:
        """Vote for suspected wolf.
        
        Args:
            game_state: Current state of the game
            context: Additional context for voting
            eligible_players: List of player IDs that can be voted for
            
        Returns:
            Player ID to vote for
        """
        memory_context = self.get_memory_context()
        
        prompt = self.vote_prompt.format(
            game_state=game_state,
            context=context,
            memory=memory_context,
            eligible_players=eligible_players
        )
        
        response: AIMessage = self.llm.invoke(prompt)
        
        # Extract number from response
        try:
            vote_target = response.content.strip()
            if vote_target in eligible_players:
                self.add_to_memory(f"I voted for Player_{vote_target}")
                return vote_target
        except ValueError:
            pass
            
        # Fallback to random choice
        choice = random.choice(eligible_players)
        self.add_to_memory(f"I voted for Player_{choice} (fallback)")
        return choice
