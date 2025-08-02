"""Wolf agent - can kill at night, must lie during day."""

from dataclasses import dataclass
from langchain.prompts import PromptTemplate
from langchain.schema import AIMessage
from typing import List, TypedDict, Annotated
from .base_agent import AgentType, BaseAgent
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command, interrupt
from langchain_core.language_models import BaseChatModel

import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from src.promote.game_intro import game_intro as game_intro_data

class WolfAgent(BaseAgent):
    """Wolf agent - can kill at night, must lie during day."""
    
    def __init__(self, llm, player_id: int, name: str):
        """Initialize the wolf agent.
        
        Args:
            llm: Language model instance
            player_id: Unique identifier for this player
            name: Display name for this player
        """
        super().__init__(llm, player_id, name)
        self.teammates: List[int] = []
        
        # Wolf speaking prompt
        self.speak_prompt = PromptTemplate(
            input_variables=["game_state", "context", "memory", "teammates"],
            template="""You are a WOLF in a Werewolf game. Your goal is to eliminate all civilians while avoiding detection.

IMPORTANT WOLF STRATEGY:
- You MUST lie and appear to be a civilian
- Blend in with civilians by acting suspicious of others
- Protect your wolf teammates subtly (don't be obvious)
- Create doubt about other players
- Never reveal you are a wolf

Your teammates are: {teammates}

Current game state:
{game_state}

Current context:
{context}

Your memory:
{memory}

Respond with natural speech that makes you seem like a concerned civilian trying to find wolves. Keep your response under 100 words and sound natural.

Your response:"""
        )
        
        # Wolf voting prompt
        self.vote_prompt = PromptTemplate(
            input_variables=["game_state", "context", "memory", "eligible_players", "teammates"],
            template="""You are a WOLF voting to eliminate someone. 

Your wolf teammates: {teammates}

Current game state:
{game_state}

Context: {context}

Your memory: {memory}

Eligible players to vote for: {eligible_players}

Strategy:
- Vote for a CIVILIAN (not your wolf teammates)
- Try to vote for someone who seems suspicious to others
- Avoid voting for your teammates

Respond with just the player name you want to vote for. Choose from: {eligible_players}

Your vote (just the name):"""
        )
        
        # Night kill prompt
        self.kill_prompt = PromptTemplate(
            input_variables=["game_state", "context", "memory", "eligible_players", "teammates"],
            template="""You are a WOLF choosing who to kill at night.

Your wolf teammates: {teammates}

Current game state:
{game_state}

Context: {context}

Your memory: {memory}

Eligible players to kill: {eligible_players}

Strategy:
- Kill civilians who seem smart or influential
- Don't kill someone you've been defending (too obvious)
- Consider killing players who might expose you

Respond with just the player name you want to kill. Choose from: {eligible_players}

Your kill choice (name):"""
        )
        
    def set_teammates(self, teammates: List[int]) -> None:
        """Set wolf teammates.
        
        Args:
            teammates: List of player IDs who are also wolves
        """
        self.teammates = [t for t in teammates if t != self.player_id]
        
    def speak(self, game_state: str, context: str) -> str:
        """Generate wolf speech - must appear as civilian.
        
        Args:
            game_state: Current state of the game
            context: Additional context for the speech
            
        Returns:
            Speech text that appears civilian-like
        """
        memory_context = self.get_memory_context()
        teammates_str = ", ".join([f"Player_{t}" for t in self.teammates]) if self.teammates else "None"
        
        prompt = self.speak_prompt.format(
            game_state=game_state,
            context=context,
            memory=memory_context,
            teammates=teammates_str
        )
        
        response = self.llm.invoke(prompt)
        self.add_to_memory(f"I said: {response}")
        return response
        
    def vote(self, game_state: str, context: str, eligible_players: List[str]) -> str:
        """Vote for someone (avoid teammates).
        
        Args:
            game_state: Current state of the game
            context: Additional context for voting
            eligible_players: List of player IDs that can be voted for
            
        Returns:
            Player ID to vote for
        """
        # Filter out teammates from eligible players
        safe_targets = [p for p in eligible_players if p not in self.teammates]
        
        if not safe_targets:
            # If only teammates available, pick randomly
            return random.choice(eligible_players)
            
        memory_context = self.get_memory_context()
        teammates_str = ", ".join([f"Player_{t}" for t in self.teammates]) if self.teammates else "None"
        
        prompt = self.vote_prompt.format(
            game_state=game_state,
            context=context,
            memory=memory_context,
            eligible_players=safe_targets,
            teammates=teammates_str
        )
        
        response: AIMessage = self.llm.invoke(prompt)
        
        # Extract number from response
        try:
            vote_target = response.content.strip()
            if vote_target in safe_targets:
                self.add_to_memory(f"I voted for Player_{vote_target}")
                return vote_target
        except ValueError:
            pass
            
        # Fallback to random choice from safe targets
        choice = random.choice(safe_targets)
        self.add_to_memory(f"I voted for Player_{choice} (fallback)")
        return choice
        
    def choose_kill_target(self, game_state: str, context: str, eligible_players: List[str]) -> str:
        """Choose who to kill at night.
        
        Args:
            game_state: Current state of the game
            context: Additional context for the kill decision
            eligible_players: List of player IDs that can be killed
            
        Returns:
            Player ID to kill
        """
        # Filter out teammates
        targets = [p for p in eligible_players if p not in self.teammates]
        
        if not targets:
            return random.choice(eligible_players)
            
        memory_context = self.get_memory_context()
        teammates_str = ", ".join([f"Player_{t}" for t in self.teammates]) if self.teammates else "None"
        
        prompt = self.kill_prompt.format(
            game_state=game_state,
            context=context,
            memory=memory_context,
            eligible_players=targets,
            teammates=teammates_str
        )
        
        response: AIMessage = self.llm.invoke(prompt)
        
        # Extract number from response
        try:
            kill_target_name = response.content.strip()
            if kill_target_name in eligible_players:
                self.add_to_memory(f"We decided to kill Player_{kill_target_name}")
                return kill_target_name
        except ValueError:
            pass
            
        # Fallback to random choice
        choice = random.choice(targets)
        self.add_to_memory(f"We decided to kill Player_{choice} (fallback)")
        return choice.name


