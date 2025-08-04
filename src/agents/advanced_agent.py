"""Wolf agent - can kill at night, must lie during day."""

from enum import Enum
from langchain.schema import AIMessage
from typing import List, TypedDict, Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END

from langgraph.types import Command, interrupt
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver

from src.promote.game_intro import game_intro as game_intro_data
from src.promote.agent_personality import personality_traits as personality_data 
import random


class AgentType(Enum):
    """Types of agents."""
    WOLF = "wolf"
    VILLAGERS = "villagers"
    GOD = "god"


class AgentState(TypedDict):
    """State of the agent for thinking."""
    messages: Annotated[list, add_messages]
    name: str
    agent_type: str
    strategy: str
    personality: str

    
class AdvancedAgent:
    """Advanced wolf agent with additional strategies."""
    
    def __init__(self, api_key:str, model: str, name: str, agent_type: AgentType = AgentType.WOLF):
        """Initialize the advanced wolf agent."""
        self.llm = init_chat_model(openai_api_key=api_key, model=model, temperature=0.7, max_tokens=500)
        self.name = name
        self.agent_type = agent_type
        self.config = {"configurable": {"thread_id": "1"}}
        self.personality = random.choice(personality_data)
        self.agent_state: AgentState = AgentState(agent_type=agent_type.value, name=name, messages=[], strategy="", personality=self.personality)
        self._build_graph()
        self.event_history = []
        
        # Additional prompts or strategies can be added here
        # For example, more complex voting logic or night kill strategies
    def _build_graph(self) -> None:
        """Build the state graph for the agent."""
        graph_builder = StateGraph(AgentState)

        # Define the initial state
        graph_builder.add_node("start", self._start)

        # Define the waiting state
        graph_builder.add_node("waiting", self._waiting)

        # Define the action state
        graph_builder.add_node("action", self._action)

        # Add edges between states
        graph_builder.add_edge(START, "start")

        graph_builder.add_edge("start", "waiting")
        graph_builder.add_edge("waiting", "action")
        graph_builder.add_edge("action", "waiting")
        graph_builder.add_edge("action", END)

        # Set entry point
        graph_builder.set_entry_point("start")


        self.graph = graph_builder.compile(checkpointer=InMemorySaver())
        self.graph.update_state(self.config, self.agent_state)

    def add_event(self, event: str) -> None:
        self.event_history.append(event)

    def _start(self, state: AgentState) -> None:
        """Initialize the agent's state at the start of the game."""
        message : AIMessage = self.llm.invoke(state['messages'])
        return {
            "messages": [message],
            "strategy": message.content.strip(),
        }

    def _waiting(self, state: AgentState) -> None:
        """Initialize the agent's state at the waiting state."""
        moderator_instruction = interrupt({})
        return {"messages": f"Events since your last speak: {moderator_instruction['events']}\n" + \
               f"Your strategy: {state['strategy']}\n" + \
               f"Your personality: {state['personality']} +\n" + \
               f"Your next action: {moderator_instruction['instruction']}"}

    def _action(self, game_state: AgentState) -> None:
        message = self.llm.invoke(game_state['messages'])
        return {"messages": [message]}

    def start(self, public_info: str) -> None:
        """Start the agent with the given public information."""
        def init_prompt() -> str:
            """Initialize the prompt for the agent.

            Returns:
                str: The initial prompt string.
            """
            # You can customize this as needed for your prompt format
            intro_str = str(game_intro_data)
            return (
                f"You will join a game named Werewolf, This is the meta info you should consider.\n"
                f"After reading these infomation, you should design a strategy to win the game, strategy should be short (less than 50 words) and focused. And your speak based on the strategy should also be more focuse without feeling like an AI talk. then you can convert yourself into waiting.\n"
                f"Your Agent Type: {self.agent_type}\n"
                f"Your Personality: {self.personality}\n"
                f"Your Name: {self.name}\n"
                f"Game Intro: {intro_str}\n"
                f"Current Game State: {public_info}\n"
            )
        promote = init_prompt()
        
        list(self.graph.stream({"messages": [{"role": "user", "content": promote}]}, self.config))

    def step(self, instruction: str) -> str:
        # Invoke the graph to get the next action

        promote_events = "\n".join([str(e) for e in self.event_history])
        command = Command(resume={"events": promote_events, "instruction": instruction})
        self.event_history.clear()  # Clear history after processing the step

        graph_events = self.graph.stream(command, self.config, stream_mode="values")
        for event in graph_events:
            pass
        return event["messages"][-1]
