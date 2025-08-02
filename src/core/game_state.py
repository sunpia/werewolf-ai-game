"""Game state management for the Werewolf game."""

from typing import Dict, List, Optional, Tuple
import random
from .player import Player, Role, GamePhase
from faker import Faker

class GameState:
    """Manages the state of a Werewolf game."""
    
    def __init__(self, num_players: int):
        """Initialize game state.
        
        Args:
            num_players: Number of players in the game (6-15)
            
        Raises:
            ValueError: If num_players is not between 6 and 15
        """
        if num_players < 3 or num_players > 15:
            raise ValueError("Number of players must be between 6 and 15")
            
        self.num_players = num_players
        self.players: Dict[str, Player] = {}
        self.current_phase = GamePhase.DAY
        self.day_count = 1
        self.speaker_queue: List[Player] = []
        self.game_history: List[str] = []
        self.night_kill_target: Optional[str] = None
        self.voting_enabled = False
        self._god_player: Optional[Player] = None
        self._wolves: List[Player] = []
        self._civilians: List[Player] = []
        self._speaker_idx: int = 0
        self._initialize_players()
        
    def _initialize_players(self) -> None:
        """Initialize players with roles according to game rules."""
        faker = Faker()
        # Calculate roles
        num_wolves = max(1, int(self.num_players * 0.2))  # 20% wolves, minimum 1
        num_gods = 1  # Always 1 god
        num_civilians = self.num_players - num_wolves - num_gods
        
        # Create role list
        roles = [Role.WOLF] * num_wolves + [Role.GOD] * num_gods + [Role.CIVILIAN] * num_civilians
        random.shuffle(roles)
        
        # Assign roles to players
        for i in range(self.num_players):

            player_name = faker.name()
            self.players[player_name] = Player(i, player_name, roles[i])
            if roles[i] == Role.GOD:
                self._god_player = self.players[player_name]
            elif roles[i] == Role.WOLF:
                self._wolves.append(self.players[player_name])
            else:
                self._civilians.append(self.players[player_name])

        # Set initial speaking order (alive players only)
        self.update_speaking_order()
        
    def update_speaking_order(self) -> None:
        """Update speaking order with alive players only."""
        alive_players = [player for player in self.players.values() 
                        if player.is_alive and not player.is_god()]
        self.speaker_queue = alive_players
        
    @property
    def alive_players(self) -> List[Player]:
        """Get all alive players."""
        return [player for player in self.players.values() if player.is_alive]

    @property
    def alive_wolves(self) -> List[Player]:
        """Get all alive wolves."""
        return [player for player in self.players.values() if player.is_alive and player.is_wolf()]

    @property
    def alive_civilians(self) -> List[Player]:
        """Get all alive civilians."""
        return [player for player in self.players.values() if player.is_alive and player.is_civilian()]
                
    @property
    def god_player(self) -> Player:
        """Get the god player (cached)."""
        return self._god_player       
    
    @property
    def wolves(self) -> List[Player]:
        """Get all wolf players."""
        return self._wolves

    @property
    def civilians(self) -> List[Player]:
        """Get all civilian players."""
        return self._civilians

    def get_next_speaker(self) -> Optional[Player]:
        """Get the next player who should speak."""
        if len(self.speaker_queue) == 0:
            return None

        return self.speaker_queue.pop(0)  # Get and remove the first speaker
            
            
    def reset_speaker_order(self) -> None:
        """Reset speaker order for new day."""
        self.update_speaking_order()
        
    def switch_to_night(self) -> None:
        """Switch game phase to night."""
        self.current_phase = GamePhase.NIGHT
        
    def switch_to_day(self) -> None:
        """Switch game phase to day."""
        self.current_phase = GamePhase.DAY
        self.day_count += 1
        self.reset_speaker_order()
        self.voting_enabled = self.day_count > 1  # Voting starts from day 2
        
    def kill_player(self, player_id: str) -> None:
        """Kill a player."""
        if player_id in self.players:
            self.players[player_id].kill()
            self.update_speaking_order()
            
    def vote_for_player(self, voter_id: str, target_id: str) -> None:
        """Record a vote."""
        if voter_id in self.players and target_id in self.players:
            if self.players[voter_id].is_alive and self.players[target_id].is_alive:
                # Reset previous vote if any
                if self.players[voter_id].vote_target:
                    self.players[self.players[voter_id].vote_target].votes_received -= 1
                    
                # Record new vote
                self.players[voter_id].vote_target = target_id
                self.players[target_id].votes_received += 1
                
    def get_vote_results(self) -> Tuple[Optional[int], Dict[int, int]]:
        """Get voting results.
        
        Returns:
            Tuple of (player_with_most_votes, vote_counts)
        """
        vote_counts = {}
        for player in self.alive_players:
            if not player.is_god():
                vote_counts[player.name] = player.votes_received
                
        if not vote_counts:
            return None, vote_counts
            
        max_votes = max(vote_counts.values())
        if max_votes == 0:
            return None, vote_counts
            
        # Find players with max votes
        max_vote_players = [pname for pname, votes in vote_counts.items() if votes == max_votes]

        # If tie, randomly select one
        if len(max_vote_players) > 1:
            return random.choice(max_vote_players), vote_counts
        else:
            return max_vote_players[0], vote_counts
            
    def reset_votes(self) -> None:
        """Reset all votes."""
        for player in self.players.values():
            player.reset_votes()
            
    def check_game_over(self) -> Tuple[bool, str]:
        """Check if game is over.
        
        Returns:
            Tuple of (is_over, winner)
        """
        alive_wolves = self.alive_wolves
        alive_civilians = self.alive_civilians
        
        if not alive_wolves:
            return True, "Civilians"
        elif not alive_civilians:
            return True, "Wolves"
        elif len(alive_wolves) >= len(alive_civilians):
            return True, "Wolves"  # Wolves win when they equal or outnumber civilians
        else:
            return False, ""
            
    def add_to_history(self, message: str) -> None:
        """Add message to game history."""
        self.game_history.append(f"Day {self.day_count} ({self.current_phase.value}): {message}")
        
    def get_public_game_state(self) -> str:
        """Get public game state information."""
        alive_players = self.alive_players
        alive_names = len([p.name for p in alive_players if not p.is_god()])
        dead_players = [p for p in self.players.values() if not p.is_alive]
        
        state = f"=== Game State ===\n"
        state += f"Day: {self.day_count}, Phase: {self.current_phase.value}\n"
        state += f"Alive Players: {alive_names}\n"
        
        if dead_players:
            state += f"Dead Players: {', '.join([p.name for p in dead_players])}\n"
            
        if self.current_phase == GamePhase.DAY and self.voting_enabled:
            state += "Voting is enabled\n"
            
        return state
