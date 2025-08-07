"""Main game orchestrator for the Werewolf game."""

import os
import time
from typing import List, Optional, Tuple, Callable
from enum import Enum

from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

from .game_state import GameState, GamePhase
from .player import Player, Role
from ..agents.god_advanced_agent import GodAdvancedAgent
from ..agents.advanced_agent import AdvancedAgent, AgentType
from ..models.game_actions import (
    AIAction, SpeechAction, NightKillAction, PhaseCompleteAction, 
    WolfCommunication, ActionType
)
from ..models.voting_models import VotingResult, EliminatedPlayer
from ..utils.output_handler import OutputHandler, OutputEventType, create_console_output_handler

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
    
    def __init__(self, num_players: int, api_key: str, model: str, output_handler: Optional[OutputHandler] = None):
        """Initialize the Werewolf game.
        
        Args:
            num_players: Number of players (6-15)
            api_key: OpenAI API key
            model: LLM model to use
            output_handler: Optional custom output handler for messages
        """
        self.game_state = GameState(num_players)
        self.llm = init_chat_model(openai_api_key=api_key, model=model, temperature=0.7, max_tokens=200)
        self.api_key = api_key
        self.model = model
        self.output_handler = output_handler or create_console_output_handler()
        
        self._initialize_agents()

    def _initialize_agents(self) -> None:
        """Initialize all agents based on player roles."""

        for _, player in self.game_state.players.items():
            if player.is_wolf():
                player.agent = AdvancedAgent(self.api_key, self.model, player.name, agent_type=AgentType.WOLF)
            elif player.is_civilian():
                player.agent = AdvancedAgent(self.api_key, self.model, player.name, agent_type=AgentType.VILLAGERS)
            elif player.is_god():
                player.agent = GodAdvancedAgent(self.api_key, self.model, player.name)

        self.output_handler.notify(
            "=== Game Initialized ===", 
            event_type=OutputEventType.SYSTEM
        )
        

    def _print_setup_info(self) -> None:
        """Print game setup information."""
        wolves = self.game_state.wolves
        civilians = self.game_state.civilians
        god = self.game_state.god_player
        
        wolves_str = f"Wolves: {', '.join([p.name for p in wolves])}"
        civilians_str = f"Civilians: {', '.join([p.name for p in civilians])}"
        god_str = f"God: {god.name}"
        total_str = f"Total Players: {len(self.game_state.players)}"
        
        self.output_handler.notify(wolves_str, event_type=OutputEventType.GAME_STATE)
        self.output_handler.notify(civilians_str, event_type=OutputEventType.GAME_STATE)
        self.output_handler.notify(god_str, event_type=OutputEventType.GAME_STATE)
        self.output_handler.notify(total_str, event_type=OutputEventType.GAME_STATE)

    def _notify(self, message, player: Optional[Player] = None, event_type: OutputEventType = OutputEventType.SYSTEM) -> None:
        """Print colored message based on player role."""
        self.output_handler.notify(message, player, event_type)

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
        day_header = f"=== DAY {self.game_state.day_count} ==="
        self.output_handler.notify(
            day_header, 
            event_type=OutputEventType.PHASE_TRANSITION,
            metadata={"day_count": self.game_state.day_count}
        )
        
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
        self._notify(announcement, self.game_state.god_player, OutputEventType.GAME_ANNOUNCEMENT)
        
        # Speaking phase - use backend integration method
        self._run_speaking_phase_with_ai()
        
        # Voting phase (if enabled)
        if self.game_state.voting_enabled:
            voting_result = self.run_voting_phase()
            if voting_result.eliminated:
                eliminated = voting_result.eliminated
                elimination_msg = f"{eliminated.name} ({eliminated.role}) was eliminated by vote"
                self.output_handler.notify(
                    elimination_msg, 
                    event_type=OutputEventType.ELIMINATION,
                    metadata={"eliminated_player": eliminated.name, "role": eliminated.role}
                )
            else:
                self.output_handler.notify(
                    "No one was eliminated (tie or no votes)", 
                    event_type=OutputEventType.VOTING
                )

    def _run_speaking_phase_with_ai(self) -> None:
        """Run the speaking phase using AI backend integration methods."""
        self.output_handler.notify(
            "--- Speaking Phase ---", 
            event_type=OutputEventType.PHASE_TRANSITION
        )

        speaking_rounds = 1  # Each player speaks once

        for round_num in range(speaking_rounds):
            round_msg = f"Speaking Round {round_num + 1}:"
            self.output_handler.notify(
                round_msg, 
                event_type=OutputEventType.PHASE_TRANSITION,
                metadata={"round_number": round_num + 1}
            )
            
            # Use the backend integration method to get AI responses
            while True:
                ai_action = self.get_next_ai_action()
                if not ai_action or isinstance(ai_action, PhaseCompleteAction):
                    break
                
                if isinstance(ai_action, SpeechAction):
                    player_name = ai_action.player
                    message = ai_action.message
                    role = ai_action.role
                    
                    # Find the player object for colored printing
                    speaker = None
                    for player in self.game_state.players.values():
                        if player.name == player_name:
                            speaker = player
                            break
                    
                    self._notify(message, speaker, OutputEventType.PLAYER_SPEECH)
                    time.sleep(5)  # Brief pause for readability

    def _run_speaking_phase(self) -> None:
        """Legacy speaking phase method - kept for compatibility."""
        self._run_speaking_phase_with_ai()

    def _run_voting_phase(self) -> None:
        """Legacy voting phase method - now uses backend integration method."""
        self.output_handler.notify(
            "--- Voting Phase ---", 
            event_type=OutputEventType.PHASE_TRANSITION
        )
        eligible_voters = [p for p in self.game_state.alive_players if not p.is_god()]
        voters_msg = f"Eligible voters: {', '.join([p.name for p in eligible_voters])}"
        self.output_handler.notify(
            voters_msg, 
            event_type=OutputEventType.VOTING,
            metadata={"eligible_voters": [p.name for p in eligible_voters]}
        )
        
        god = self.game_state.god_player
        god_agent: GodAdvancedAgent = god.agent
        
        # Use the backend integration method
        voting_result = self.run_voting_phase()
        
        # Display results
        if voting_result.eliminated:
            eliminated = voting_result.eliminated
            announcement = god_agent.announce_vote_results(
                voting_result.vote_counts, 
                eliminated.name
            )
            self._notify(announcement, god, OutputEventType.GAME_ANNOUNCEMENT)
        else:
            no_elimination_msg = "No one was eliminated (tie or no votes)"
            self._notify(no_elimination_msg, god, OutputEventType.VOTING)

    def run_night_phase(self) -> None:
        """Run the night phase."""
        night_header = f"=== NIGHT {self.game_state.day_count} ==="
        self.output_handler.notify(
            night_header, 
            event_type=OutputEventType.PHASE_TRANSITION,
            metadata={"day_count": self.game_state.day_count, "phase": "night"}
        )
        
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
        self._notify(announcement, god, OutputEventType.GAME_ANNOUNCEMENT)
        
        # Use backend integration method for night actions
        if alive_wolf_names:
            night_action = self.get_next_ai_action()
            if night_action and isinstance(night_action, NightKillAction):
                target = night_action.target
                wolf_communications = night_action.wolf_communications
                
                # Display wolf communications
                if wolf_communications:
                    self.output_handler.notify(
                        "--- Wolf Communication ---", 
                        event_type=OutputEventType.WOLF_COMMUNICATION
                    )
                    for comm in wolf_communications:
                        comm_msg = f"{comm.player} (to wolves): {comm.message}"
                        self.output_handler.notify(
                            comm_msg, 
                            event_type=OutputEventType.WOLF_COMMUNICATION,
                            metadata={"speaker": comm.player, "private": True}
                        )
                
                # Execute the kill
                success = self.execute_night_kill(target)
                if success:
                    kill_msg = "Wolves have chosen their victim..."
                    self.output_handler.notify(
                        kill_msg, 
                        event_type=OutputEventType.NIGHT_KILL,
                        metadata={"target": target}
                    )

        self.game_state.switch_to_day()

    def init_strategy(self) -> None:
        # Initialize agents with game state
        public_info = self.game_state.get_public_game_state()
        for player in self.game_state.players.values():
            if not player.is_god():
                player.agent.start(public_info)
            else:
                # Initialize god with special god-specific information
                god_info = f"You are the game moderator. {public_info}"
                player.agent.start(god_info)

    def run_game(self) -> None:
        """Run the complete game."""
        start_msg = "🎮 WEREWOLF GAME STARTING! 🎮"
        self.output_handler.notify(
            start_msg, 
            event_type=OutputEventType.GAME_ANNOUNCEMENT,
            metadata={"game_status": "starting"}
        )
        self.init_strategy()
        self._print_setup_info() 


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
        self.output_handler.notify(
            final_announcement, 
            event_type=OutputEventType.GAME_ANNOUNCEMENT,
            metadata={"game_status": "ended", "winner": winner}
        )
        
        # Print final roles
        final_reveal_msg = "=== Final Role Reveal ==="
        self.output_handler.notify(
            final_reveal_msg, 
            event_type=OutputEventType.GAME_STATE
        )
        
        for player in self.game_state.players.values():
            if not player.is_god():
                status = "Alive" if player.is_alive else "Dead"
                role_reveal = f"{player.name}: {player.role.value} ({status})"
                self.output_handler.notify(
                    role_reveal, 
                    player,
                    OutputEventType.GAME_STATE,
                    metadata={"final_reveal": True, "status": status}
                )

    # Backend integration methods
    def get_next_ai_action(self) -> Optional[AIAction]:
        """Get the next AI action for backend integration."""
        if self.game_state.current_phase == GamePhase.DAY:
            # Day phase: speaking
            current_speaker = self.game_state.get_next_speaker()
            if current_speaker and current_speaker.is_alive and not current_speaker.is_god():
                try:
                    # Get AI response using the existing logic
                    agent = current_speaker.agent
                    instruction = f"It's your turn to speak. Current game state: {self.game_state.get_public_game_state()}. Share your thoughts about the game so far."
                    speech_message = agent.step(instruction)
                    speech = speech_message.content if hasattr(speech_message, 'content') else str(speech_message)
                    
                    # Add to game history
                    speech_event = f"{current_speaker.name}: {speech}"
                    self.game_state.game_history.append(speech_event)
                    
                    # Distribute to other agents
                    self._distribute_event_to_agents(speech_event, current_speaker, EventType.PUBLIC, "day")
                    
                    return SpeechAction(
                        type="speech",
                        player=current_speaker.name,
                        message=speech,
                        role=current_speaker.role.value
                    )
                except Exception as e:
                    print(f"Error getting AI response: {e}")
                    return None
            else:
                # No more speakers, ready for voting or night transition
                return PhaseCompleteAction(type="phase_complete", current_phase="day")
                
        elif self.game_state.current_phase == GamePhase.NIGHT:
            # Night phase: wolf action
            alive_wolves = self.game_state.alive_wolves
            if alive_wolves and not hasattr(self, '_night_action_taken'):
                try:
                    # Wolf communication first
                    wolf_communications = []
                    if len(alive_wolves) > 1:
                        for wolf in alive_wolves:
                            instruction = "Night phase: Communicate with your fellow wolves about who to eliminate. Share your strategy."
                            wolf_message = wolf.agent.step(instruction)
                            wolf_speech = wolf_message.content if hasattr(wolf_message, 'content') else str(wolf_message)
                            wolf_communications.append(WolfCommunication(
                                player=wolf.name,
                                message=wolf_speech
                            ))
                    
                    # Choose target
                    eligible_targets = [x.name for x in self.game_state.alive_civilians]
                    if eligible_targets:
                        wolf_agent = alive_wolves[0].agent
                        instruction = f"Night phase: Choose a player to eliminate tonight. Available targets: {', '.join(eligible_targets)}. Make your final decision."
                        kill_message = wolf_agent.step(instruction)
                        kill_target_name = kill_message.content if hasattr(kill_message, 'content') else str(kill_message)
                        
                        # Extract target name
                        kill_target_name = kill_target_name.strip()
                        for target in eligible_targets:
                            if target.lower() in kill_target_name.lower():
                                kill_target_name = target
                                break
                        
                        if kill_target_name not in eligible_targets:
                            kill_target_name = eligible_targets[0]
                        
                        # Mark night action as taken
                        self._night_action_taken = True
                        
                        return NightKillAction(
                            type="night_kill",
                            target=kill_target_name,
                            wolf_communications=wolf_communications
                        )
                except Exception as e:
                    print(f"Error in wolf night action: {e}")
                    return None
            else:
                return PhaseCompleteAction(type="phase_complete", current_phase="night")
        
        return None
    
    def execute_night_kill(self, target_name: str) -> bool:
        """Execute a night kill and return success."""
        try:
            for player in self.game_state.players.values():
                if player.name == target_name:
                    player.is_alive = False
                    kill_msg = f"{target_name} was killed by wolves"
                    self.game_state.game_history.append(kill_msg)
                    
                    # Distribute to agents
                    self._distribute_event_to_agents(kill_msg, None, EventType.NIGHT_KILL, "night")
                    
                    return True
            return False
        except Exception as e:
            print(f"Error executing night kill: {e}")
            return False
    
    def transition_to_day(self) -> None:
        """Transition to day phase."""
        self.game_state.current_phase = GamePhase.DAY
        self.game_state.day_count += 1
        self.game_state.update_speaking_order()
        
        # Reset night action flag
        if hasattr(self, '_night_action_taken'):
            delattr(self, '_night_action_taken')
        
        # Distribute day transition event
        day_transition_event = f"Day {self.game_state.day_count} begins! Time for discussion."
        self._distribute_event_to_agents(day_transition_event, None, EventType.DAY_TRANSITION, "day")
    
    def transition_to_night(self) -> None:
        """Transition to night phase."""
        self.game_state.current_phase = GamePhase.NIGHT
        
        # Distribute night transition event
        night_transition_event = f"Night falls. Most players go to sleep, but wolves prowl..."
        self._distribute_event_to_agents(night_transition_event, None, EventType.DAY_TRANSITION, "night")
    
    def run_voting_phase(self) -> VotingResult:
        """Run voting phase and return results."""
        try:
            eligible_voters = [p for p in self.game_state.alive_players if not p.is_god()]
            eligible_targets_name = [p.name for p in eligible_voters]
            
            voting_process = []
            
            # Collect votes
            for voter in eligible_voters:
                agent = voter.agent
                instruction = f"Voting phase: You must vote to eliminate one player. Current voting status: {str(voting_process)}. Choose from: {', '.join(eligible_targets_name)}"
                vote_message = agent.step(instruction)
                vote_target = vote_message.content if hasattr(vote_message, 'content') else str(vote_message)
                
                # Extract target name
                vote_target = vote_target.strip()
                original_vote = vote_target
                for target in eligible_targets_name:
                    if target.lower() in vote_target.lower():
                        vote_target = target
                        break
                
                if vote_target not in eligible_targets_name:
                    vote_target = eligible_targets_name[0]
                
                self.game_state.vote_for_player(voter.name, vote_target)
                vote_msg = f"{voter.name} voted for {vote_target}"
                voting_process.append(vote_msg)
                self.game_state.add_to_history(vote_msg)
                self._distribute_event_to_agents(vote_msg, voter, EventType.PUBLIC, "voting")
            
            # Count votes and eliminate
            eliminated_id, vote_counts = self.game_state.get_vote_results()
            
            eliminated_player = None
            if eliminated_id:
                eliminated_player_obj = self.game_state.players[eliminated_id]
                self.game_state.kill_player(eliminated_id)
                
                elimination_msg = f"{eliminated_player_obj.name} ({eliminated_player_obj.role.value}) was eliminated by vote"
                self.game_state.add_to_history(elimination_msg)
                self._distribute_event_to_agents(elimination_msg, None, EventType.ELIMINATION, "voting")
                
                eliminated_player = EliminatedPlayer(
                    name=eliminated_player_obj.name,
                    role=eliminated_player_obj.role.value
                )
            
            self.game_state.reset_votes()
            
            return VotingResult(
                votes=voting_process,
                vote_counts=vote_counts,
                eliminated=eliminated_player
            )
            
        except Exception as e:
            error_msg = f"Error in voting phase: {e}"
            self.output_handler.notify(
                error_msg, 
                event_type=OutputEventType.ERROR,
                metadata={"error": str(e)}
            )
            return VotingResult(
                votes=[],
                vote_counts={},
                error=str(e)
            )


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
