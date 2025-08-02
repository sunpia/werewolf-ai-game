"""Main game orchestrator for the Werewolf game."""

import os
import time
import random
from typing import Dict, List, Optional, Tuple
from colorama import init, Fore, Back, Style

from langchain.chat_models import init_chat_model
from langchain.schema import AIMessage
from dotenv import load_dotenv

from .game_state import GameState, GamePhase
from .player import Player, Role
from ..agents.wolf_agent import WolfAgent
from ..agents.civilian_agent import CivilianAgent
from ..agents.god_agent import GodAgent
from src.agents import god_agent

# Initialize colorama for colored output
init(autoreset=True)

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
        
        self._initialize_agents()

    def _initialize_agents(self) -> None:
        """Initialize all agents based on player roles."""
        wolves: List[Player] = []

        for player_id, player in self.game_state.players.items():
            if player.is_wolf():
                player.agent = WolfAgent(self.llm, player_id, player.name)
                wolves.append(player)
            elif player.is_civilian():
                player.agent = CivilianAgent(self.llm, player_id, player.name)
            elif player.is_god():
                player.agent = GodAgent(self.llm, player_id, player.name)

        print(f"\n{Fore.CYAN}=== Game Initialized ==={Style.RESET_ALL}")
        self._print_setup_info()

    def _print_setup_info(self) -> None:
        """Print game setup information."""
        wolves = self.game_state.wolves
        civilians = self.game_state.civilians
        god = self.game_state.god_player
        
        print(f"{Fore.RED}Wolves: {', '.join([p.name for p in wolves])}")
        print(f"{Fore.GREEN}Civilians: {', '.join([p.name for p in civilians])}")
        print(f"{Fore.YELLOW}God: {god.name}")
        print(f"Total Players: {len(self.game_state.players)}")

    def _print_colored(self, message: AIMessage, player: Optional[Player] = None) -> None:
        """Print colored message based on player role."""
        content = message.content
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

    def run_day_phase(self) -> None:
        """Run the day phase."""
        print(f"\n{Back.YELLOW}{Fore.BLACK} === DAY {self.game_state.day_count} === {Style.RESET_ALL}")
        god_agent: GodAgent = self.game_state.god_player.agent

        
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
                
                # Get agent speech
                agent = speaker.agent
                game_context = self.game_state.game_history
                speech = agent.speak(self.game_state.get_public_game_state(), game_context)
                
                self._print_colored(speech, speaker)
                
                # Add to all agents' memory
                for player in self.game_state.players.values():
                    if player.name != speaker.name:
                        player.agent.add_to_memory(f"{speaker.name} said: {speech}")
                    else:
                        player.agent.add_to_memory(f"You said: {speech}")

                time.sleep(1)  # Brief pause for readability

    def _run_voting_phase(self) -> None:
        """Run the voting phase."""
        print(f"\n{Fore.CYAN}--- Voting Phase ---{Style.RESET_ALL}")
        # Exclude the god from voting
        eligible_voters = [p for p in self.game_state.alive_players if not p.is_god()]
        eligible_targets = eligible_voters.copy()
        eligible_targets_name = [p.name for p in eligible_targets]
        
        print(f"Eligible voters: {', '.join([f'{p.name}' for p in eligible_voters])}")
        voting_process = []
        god = self.game_state.god_player
        god_agent: GodAgent = god.agent
        
        # Collect votes
        for voter in eligible_voters:
            agent = voter.agent

            vote_target = agent.vote(self.game_state.get_public_game_state(), str(voting_process), eligible_targets_name)

            self.game_state.vote_for_player(voter.name, vote_target)
            print(f"{voter.name} votes for {vote_target}")
            
            # Add to memory
            vote_msg = f"{voter.name} voted for {vote_target}"
            voting_process.append(vote_msg)
            self.game_state.add_to_history(vote_msg)
            agent.add_to_memory(vote_msg)
                
        # Count votes and eliminate player
        eliminated_id, vote_counts = self.game_state.get_vote_results()
        
        if eliminated_id:
            eliminated_player = self.game_state.players[eliminated_id]
            self.game_state.kill_player(eliminated_id)
            
            announcement = god_agent.announce_vote_results(vote_counts, eliminated_player.name)
            self._print_colored(announcement, self.game_state.god_player)
            
            elimination_msg = f"{eliminated_player.name} ({eliminated_player.role.value}) was eliminated by vote"
            self.game_state.add_to_history(elimination_msg)
            for p in self.game_state.players.values():
                p.agent.add_to_memory(elimination_msg)
                
        else:
            no_elimination_msg = "No one was eliminated (tie or no votes)"
            self._print_colored(no_elimination_msg, self.game_state.god_player)
            self.game_state.add_to_history(no_elimination_msg)
            
        self.game_state.reset_votes()

    def run_night_phase(self) -> None:
        """Run the night phase."""
        print(f"\n{Back.BLUE}{Fore.WHITE} === NIGHT {self.game_state.day_count} === {Style.RESET_ALL}")
        god = self.game_state.god_player
        god_agent: GodAgent = god.agent
        
        self.game_state.switch_to_night()
        
        # God announces night start
        alive_wolf_names = list(map(lambda wolf: wolf.name, self.game_state.alive_wolves))
        announcement = god_agent.announce_night_start(
            self.game_state.get_public_game_state(),
            alive_wolf_names
        )
        self._print_colored(announcement, god)
        
        # Wolves choose target
        if alive_wolf_names:
            # Let first alive wolf choose (representing wolf consensus)
            wolf_agent: WolfAgent = self.game_state.alive_wolves[0].agent

            eligible_targets = list(map(lambda x: x.name, self.game_state.alive_civilians))

            if eligible_targets:
                game_context = self.game_state.game_history
                kill_target_name = wolf_agent.choose_kill_target(
                    self.game_state.get_public_game_state(),
                    game_context,
                    eligible_targets
                )
                
                # Kill the target
                target_player = self.game_state.players[kill_target_name]
                self.game_state.kill_player(kill_target_name)

                kill_msg = f"{target_player.name} was killed by wolves"
                self.game_state.add_to_history(kill_msg)
                
                print(f"{Fore.RED}Wolves have chosen their victim...{Style.RESET_ALL}")
                
                # Add to wolf agents' memory
                for a in self.game_state.alive_wolves:
                    a.agent.add_to_memory(kill_msg)

        self.game_state.switch_to_day()

    def check_game_over(self) -> Tuple[bool, str]:
        """Check if game is over."""
        return self.game_state.check_game_over()

    def run_game(self) -> None:
        """Run the complete game."""
        print(f"\n{Back.GREEN}{Fore.BLACK} 🎮 WEREWOLF GAME STARTING! 🎮 {Style.RESET_ALL}")

        god = self.game_state.god_player
        god_agent: GodAgent = god.agent
        
        game_over = False
        winner = ""
        
        while not game_over:
            # Run day phase
            self.run_day_phase()
            
            # Check game over after day
            game_over, winner = self.check_game_over()
            if game_over:
                break
                
            # Run night phase
            self.run_night_phase()
            
            # Check game over after night
            game_over, winner = self.check_game_over()
            
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
