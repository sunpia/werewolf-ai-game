"""Main game orchestrator for the Werewolf game."""

import os
import time
import random
from typing import Dict, List, Optional, Tuple
from enum import Enum
from colorama import init, Fore, Back, Style

from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

from .game_state import GameState, GamePhase
from .player import Player, Role
from ..agents.god_advanced_agent import GodAdvancedAgent
from ..agents.advanced_agent import AdvancedAgent, AgentType

# Initialize colorama for colored output
init(autoreset=True)

class EventType(Enum):
    """Types of events that can occur in the game."""
    PUBLIC = "public"                   # Events visible to all living players
    WOLF_PRIVATE = "wolf_private"       # Events only wolves can see
    ELIMINATION = "elimination"         # Player elimination events
    GAME_STATE = "game_state"          # General game state changes
    NIGHT_KILL = "night_kill"          # Night kill results
    DAY_TRANSITION = "day_transition"   # Day/night phase transitions
    DAY_NUMBER_CHANGE = "day_number_change"  # Day counter changes

class WerewolfGame:
    """Main game orchestrator for the Werewolf game."""
    
    def __init__(self, num_players: int, api_key: str, model: str):
        """Initialize the Werewolf game.
        
        Args:
            num_players: Number of players (6-15)
            api_key: OpenAI API key
            model: LLM model to use
        """
        self.game_state = GameState(num_players)
        self.llm = init_chat_model(openai_api_key=api_key, model=model, temperature=0.7, max_tokens=200)
        self.api_key = api_key
        self.model = model
        
        self._initialize_agents()

    def _initialize_agents(self) -> None:
        """Initialize all agents based on player roles."""

        for player_id, player in self.game_state.players.items():
            if player.is_wolf():
                player.agent = AdvancedAgent(self.api_key, self.model, player.name, agent_type=AgentType.WOLF)
            elif player.is_civilian():
                player.agent = AdvancedAgent(self.api_key, self.model, player.name, agent_type=AgentType.VILLAGERS)
            elif player.is_god():
                player.agent = GodAdvancedAgent(self.api_key, self.model, player.name)

        print(f"\n{Fore.CYAN}=== Game Initialized ==={Style.RESET_ALL}")
        self._print_setup_info()
        
        # Initialize agents with game state
        public_info = self.game_state.get_public_game_state()
        for player in self.game_state.players.values():
            if not player.is_god():
                player.agent.start(public_info)
            else:
                # Initialize god with special god-specific information
                god_info = f"You are the game moderator. {public_info}"
                player.agent.start(god_info)

    def _print_setup_info(self) -> None:
        """Print game setup information."""
        wolves = self.game_state.wolves
        civilians = self.game_state.civilians
        god = self.game_state.god_player
        
        print(f"{Fore.RED}Wolves: {', '.join([p.name for p in wolves])}")
        print(f"{Fore.GREEN}Civilians: {', '.join([p.name for p in civilians])}")
        print(f"{Fore.YELLOW}God: {god.name}")
        print(f"Total Players: {len(self.game_state.players)}")

    def _print_colored(self, message, player: Optional[Player] = None) -> None:
        """Print colored message based on player role."""
        # Handle both AIMessage objects and strings
        if hasattr(message, 'content'):
            content = message.content
        else:
            content = str(message)
            
        if player is None:
            print(f"{Fore.YELLOW}{content}{Style.RESET_ALL}")
        elif player.is_wolf():
            print(f"{Fore.RED}🐺 {player.name}: {content}{Style.RESET_ALL}")
        elif player.is_civilian():
            print(f"{Fore.GREEN}👤 {player.name}: {content}{Style.RESET_ALL}")
        elif player.is_god():
            print(f"{Fore.YELLOW}⭐ {player.name}: {content}{Style.RESET_ALL}")
        else:
            print(f"{content}")

    def _distribute_event_to_agents(self, event: str, speaker: Optional[Player] = None, 
                                   event_type: EventType = EventType.PUBLIC, context: str = "day") -> None:
        """Distribute events to agents based on game context and visibility rules.
        
        Args:
            event: The event message to distribute
            speaker: The player who triggered the event (if any)
            event_type: Type of event using EventType enum
            context: Game context - "day", "night", "voting"
        """
        for player in self.game_state.players.values():
            should_receive_event = False
            modified_event = event
            
            # God player doesn't participate in agent events (they have their own logic)
            if player.is_god():
                continue
                
            # Determine if player should receive this event based on context and type
            if event_type == EventType.PUBLIC:
                # Public events visible to all living players
                should_receive_event = player.is_alive
                
            elif event_type == EventType.WOLF_PRIVATE:
                # Wolf private communication - only wolves can see
                should_receive_event = player.is_alive and player.is_wolf()
                
            elif event_type in [EventType.ELIMINATION, EventType.GAME_STATE, 
                               EventType.DAY_TRANSITION, EventType.DAY_NUMBER_CHANGE]:
                # Game state changes visible to all players (alive and dead for meta info)
                should_receive_event = True
                
            elif event_type == EventType.NIGHT_KILL:
                # Night kill results visible to all in the morning
                should_receive_event = True
                
            # Modify event based on perspective
            if should_receive_event and speaker:
                if player.name == speaker.name:
                    # First person perspective for the speaker
                    if "said:" in event:
                        modified_event = event.replace(f"{speaker.name} said:", "You said:")
                    elif "voted for" in event:
                        modified_event = event.replace(f"{speaker.name} voted for", "You voted for")
                    else:
                        modified_event = event.replace(speaker.name, "You", 1)
                        
            # Add event to agent if they should receive it
            if should_receive_event:
                player.agent.add_event(modified_event)

    def run_day_phase(self) -> None:
        """Run the day phase."""
        print(f"\n{Back.YELLOW}{Fore.BLACK} === DAY {self.game_state.day_count} === {Style.RESET_ALL}")
        god_agent: GodAdvancedAgent = self.game_state.god_player.agent

        # Distribute day number change event
        day_number_event = f"Day {self.game_state.day_count} has arrived."
        self._distribute_event_to_agents(day_number_event, None, EventType.DAY_NUMBER_CHANGE, "day")
        
        # Distribute day transition event (only if not the first day)
        if self.game_state.day_count > 1:
            day_transition_event = f"Night has ended. Day phase begins. All players wake up."
            self._distribute_event_to_agents(day_transition_event, None, EventType.DAY_TRANSITION, "day")
        # Distribute day start event to all agents
        day_start_event = f"Day {self.game_state.day_count} begins. Current alive players: {', '.join([p.name for p in self.game_state.alive_players if not p.is_god()])}"
        self._distribute_event_to_agents(day_start_event, None, EventType.GAME_STATE, "day")
        
        # God announces day start
        recent_events = "\n".join(self.game_state.game_history[-3:]) if self.game_state.game_history else "Game start"
        announcement = god_agent.announce_day_start(
            self.game_state.day_count,
            self.game_state.get_public_game_state(),
            recent_events
        )
        self._print_colored(announcement, self.game_state.god_player)
        
        # Speaking phase
        self._run_speaking_phase()
        
        # Voting phase (if enabled)
        if self.game_state.voting_enabled:
            self._run_voting_phase()

    def _run_speaking_phase(self) -> None:
        """Run the speaking phase where players discuss."""
        print(f"\n{Fore.CYAN}--- Speaking Phase ---{Style.RESET_ALL}")

        speaking_rounds = 1  # Each player speaks once

        for round_num in range(speaking_rounds):
            print(f"\n{Fore.MAGENTA}Speaking Round {round_num + 1}:{Style.RESET_ALL}")
            
            for _ in range(len(self.game_state.speaker_queue)):
                speaker = self.game_state.get_next_speaker()
                if speaker is None:
                    break
                    
                if not speaker.is_alive:
                    continue
                    
                print(f"\n{Fore.CYAN}{speaker.name}'s turn to speak...{Style.RESET_ALL}")
                
                # Get agent speech using AdvancedAgent interface
                agent = speaker.agent
                if speaker.is_god():
                    # God agents work differently
                    game_context = self.game_state.game_history
                    speech = agent.speak(self.game_state.get_public_game_state(), game_context)
                else:
                    # Use AdvancedAgent step method
                    instruction = f"It's your turn to speak. Current game state: {self.game_state.get_public_game_state()}. Share your thoughts about the game so far."
                    speech_message = agent.step(instruction)
                    speech = speech_message.content if hasattr(speech_message, 'content') else str(speech_message)
                
                self._print_colored(speech, speaker)
                
                # Distribute speech event to appropriate agents
                speech_event = f"{speaker.name} said: {speech}"
                self._distribute_event_to_agents(speech_event, speaker, EventType.PUBLIC, "day")

                time.sleep(5)  # Brief pause for readability

    def _run_voting_phase(self) -> None:
        """Run the voting phase."""
        print(f"\n{Fore.CYAN}--- Voting Phase ---")
        # Exclude the god from voting
        eligible_voters = [p for p in self.game_state.alive_players if not p.is_god()]
        eligible_targets_name = [p.name for p in eligible_voters]
        
        print(f"Eligible voters: {', '.join([f'{p.name}' for p in eligible_voters])}{Style.RESET_ALL}")
        voting_process = []
        god = self.game_state.god_player
        god_agent: GodAdvancedAgent = god.agent
        
        # Collect votes
        for voter in eligible_voters:
            agent = voter.agent
            
            # Use AdvancedAgent step method for voting
            instruction = f"Voting phase: You must vote to eliminate one player, the decision should help you to win game. Current voting status: {str(voting_process)}. Chose the name and please only return the name from following list {', '.join(eligible_targets_name)}"
            vote_message = agent.step(instruction)
            vote_target = vote_message.content if hasattr(vote_message, 'content') else str(vote_message)
            
            # Extract just the player name from the response if needed
            vote_target = vote_target.strip()
            # Simple validation - if the response contains a valid target name, use it
            for target in eligible_targets_name:
                if target in vote_target:
                    vote_target = target
                    break

            self.game_state.vote_for_player(voter.name, vote_target)
            print(f"{voter.name} votes for {vote_target}")
            
            # Distribute voting event to all agents
            vote_msg = f"{voter.name} voted for {vote_target}"
            voting_process.append(vote_msg)
            self._distribute_event_to_agents(vote_msg, voter, EventType.PUBLIC, "voting")
                
        # Count votes and eliminate player
        eliminated_id, vote_counts = self.game_state.get_vote_results()
        
        if eliminated_id:
            eliminated_player = self.game_state.players[eliminated_id]
            self.game_state.kill_player(eliminated_id)
            
            announcement = god_agent.announce_vote_results(vote_counts, eliminated_player.name)
            self._print_colored(announcement, self.game_state.god_player)
            
            elimination_msg = f"{eliminated_player.name} ({eliminated_player.role.value}) was eliminated by vote"
            self.game_state.add_to_history(elimination_msg)
            self._distribute_event_to_agents(elimination_msg, None, EventType.ELIMINATION, "voting")
                
        else:
            no_elimination_msg = "No one was eliminated (tie or no votes)"
            self._print_colored(no_elimination_msg, self.game_state.god_player)
            self.game_state.add_to_history(no_elimination_msg)
            
        self.game_state.reset_votes()

    def run_night_phase(self) -> None:
        """Run the night phase."""
        print(f"\n{Back.BLUE}{Fore.WHITE} === NIGHT {self.game_state.day_count} === {Style.RESET_ALL}")
        god = self.game_state.god_player
        god_agent: GodAdvancedAgent = god.agent
        
        self.game_state.switch_to_night()
        
        # Distribute night transition event
        night_transition_event = f"Day has ended. Night phase begins. Most players fall asleep."
        self._distribute_event_to_agents(night_transition_event, None, EventType.DAY_TRANSITION, "night")
        
        # Distribute night start event to all agents
        night_start_event = f"Night {self.game_state.day_count} begins. All players go to sleep except wolves."
        self._distribute_event_to_agents(night_start_event, None, EventType.GAME_STATE, "night")
        
        # God announces night start
        alive_wolf_names = [wolf.name for wolf in self.game_state.alive_wolves]
        announcement = god_agent.announce_night_start(
            self.game_state.get_public_game_state(),
            alive_wolf_names
        )
        self._print_colored(announcement, god)
        
        # Wolves choose target
        if alive_wolf_names:
            # Wolf communication phase (only wolves can see this)
            if len(self.game_state.alive_wolves) > 1:
                print(f"{Fore.RED}--- Wolf Communication ---{Style.RESET_ALL}")
                for wolf in self.game_state.alive_wolves:
                    instruction = "Night phase: Communicate with your fellow wolves about who to eliminate. Share your strategy."
                    wolf_message = wolf.agent.step(instruction)
                    wolf_speech = wolf_message.content if hasattr(wolf_message, 'content') else str(wolf_message)
                    
                    print(f"{Fore.RED}🐺 {wolf.name} (to wolves): {wolf_speech}{Style.RESET_ALL}")
                    
                    # Only wolves can hear wolf communication
                    wolf_comm_event = f"{wolf.name} said to wolves: {wolf_speech}"
                    self._distribute_event_to_agents(wolf_comm_event, wolf, EventType.WOLF_PRIVATE, "night")
            
            # Let first alive wolf choose (representing wolf consensus)
            wolf_agent: AdvancedAgent = self.game_state.alive_wolves[0].agent

            eligible_targets = [x.name for x in self.game_state.alive_civilians]

            if eligible_targets:
                instruction = f"Night phase: Choose a player to eliminate tonight. Available targets: {', '.join(eligible_targets)}. Make your final decision."
                kill_message = wolf_agent.step(instruction)
                kill_target_name = kill_message.content if hasattr(kill_message, 'content') else str(kill_message)
                
                # Extract just the player name from the response if needed
                kill_target_name = kill_target_name.strip()
                # Simple validation - if the response contains a valid target name, use it
                for target in eligible_targets:
                    if target in kill_target_name:
                        kill_target_name = target
                        break
                
                # Kill the target
                target_player = self.game_state.players[kill_target_name]
                self.game_state.kill_player(kill_target_name)

                kill_msg = f"{target_player.name} was killed by wolves"
                self.game_state.add_to_history(kill_msg)
                
                print(f"{Fore.RED}Wolves have chosen their victim...{Style.RESET_ALL}")
                
                # Distribute night kill result (all agents will learn about this in the morning)
                self._distribute_event_to_agents(kill_msg, None, EventType.NIGHT_KILL, "night")

        self.game_state.switch_to_day()

    def run_game(self) -> None:
        """Run the complete game."""
        print(f"\n{Back.GREEN}{Fore.BLACK} 🎮 WEREWOLF GAME STARTING! 🎮 {Style.RESET_ALL}")

        god = self.game_state.god_player
        god_agent: GodAdvancedAgent = god.agent
        
        game_over = False
        winner = ""
        
        while not game_over:
            # Run day phase
            self.run_day_phase()
            
            # Check game over after day
            game_over, winner = self.game_state.check_game_over()
            if game_over:
                break
                
            # Run night phase
            self.run_night_phase()
            
            # Check game over after night
            game_over, winner = self.game_state.check_game_over()
            
        # Game over
        final_announcement = god_agent.announce_game_over(
            winner,
            self.game_state.get_public_game_state()
        )
        print(f"\n{Back.GREEN}{Fore.BLACK}{final_announcement}{Style.RESET_ALL}")
        
        # Print final roles
        print(f"\n{Fore.CYAN}=== Final Role Reveal ==={Style.RESET_ALL}")
        for player in self.game_state.players.values():
            if not player.is_god():
                status = "Alive" if player.is_alive else "Dead"
                color = Fore.RED if player.is_wolf() else Fore.GREEN
                print(f"{color}{player.name}: {player.role.value} ({status}){Style.RESET_ALL}")


def main() -> None:
    """Main entry point."""
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    llm_model = os.getenv("OPENAI_MODEL", "gemini-2.5-flash-lite")
    if not api_key:
        print("❌ Please set OPENAI_API_KEY in your .env file")
        return
        
    print("🐺 Welcome to Werewolf AI Agent Game! 🐺")
    
    # Get number of players
    while True:
        try:
            num_players = int(input("\nEnter number of players (6-15): "))
            if 6 <= num_players <= 15:
                break
            else:
                print("Please enter a number between 6 and 15")
        except ValueError:
            print("Please enter a valid number")
            
    # Create and run game
    game = WerewolfGame(num_players, api_key, llm_model)
    game.run_game()


if __name__ == "__main__":
    main()
