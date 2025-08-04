"""Game service for managing werewolf games."""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from ..core.game import WerewolfGame, EventType
from ..core.game_state import GameState, GamePhase
from ..core.player import Player, Role
from ..models.game_actions import AIAction, SpeechAction, NightKillAction, PhaseCompleteAction
from ..models.voting_models import VotingResult
from ..models.api_models import GameCreateRequest, GameResponse
from ..utils.output_handler import OutputHandler, OutputEventType, create_custom_output_handler


class GameService:
    """Service for managing werewolf games."""
    
    def __init__(self):
        """Initialize the game service."""
        self.games: Dict[str, WerewolfGame] = {}
        self.game_events: Dict[str, List[Dict]] = {}
        self.active_connections: Dict[str, List[asyncio.Queue]] = {}
    
    async def create_game(self, request: GameCreateRequest, output_handler: OutputHandler, game_id: str = None) -> str:
        """Create a new werewolf game."""
        if game_id is None:
            game_id = str(uuid.uuid4())
        
        # Create game with custom output handler
        game = WerewolfGame(request.num_players, request.api_key, request.model, output_handler)
        self.games[game_id] = game
        self.active_connections[game_id] = []
        self.game_events[game_id] = []
        
        return game_id
    
    def get_game(self, game_id: str) -> Optional[WerewolfGame]:
        """Get a game by ID."""
        return self.games.get(game_id)
    
    def delete_game(self, game_id: str) -> bool:
        """Delete a game and clean up resources."""
        removed = False
        if game_id in self.games:
            del self.games[game_id]
            removed = True
        if game_id in self.game_events:
            del self.game_events[game_id]
        if game_id in self.active_connections:
            del self.active_connections[game_id]
        return removed
    
    def add_connection(self, game_id: str, queue: asyncio.Queue):
        """Add a new connection for a game."""
        if game_id not in self.active_connections:
            self.active_connections[game_id] = []
        self.active_connections[game_id].append(queue)
    
    def remove_connection(self, game_id: str, queue: asyncio.Queue):
        """Remove a connection for a game."""
        if game_id in self.active_connections and queue in self.active_connections[game_id]:
            self.active_connections[game_id].remove(queue)
    
    async def broadcast_event(self, game_id: str, event: Dict[str, Any]):
        """Broadcast an event to all connected clients for a game."""
        if game_id not in self.active_connections:
            return
        
        event_msg = {
            "event_type": event.get("type", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "data": event
        }
        
        # Store event in history
        if game_id not in self.game_events:
            self.game_events[game_id] = []
        self.game_events[game_id].append(event_msg)
        
        # Broadcast to all connected clients
        disconnected_queues = []
        for queue in self.active_connections[game_id]:
            try:
                await queue.put(event_msg)
            except Exception:
                disconnected_queues.append(queue)
        
        # Remove disconnected queues
        for queue in disconnected_queues:
            self.active_connections[game_id].remove(queue)
    
    def get_recent_events(self, game_id: str, count: int = 10) -> List[Dict]:
        """Get recent events for a game."""
        if game_id not in self.game_events:
            return []
        return self.game_events[game_id][-count:]
    
    def player_to_dict(self, player: Player, include_role: bool = True) -> Dict[str, Any]:
        """Convert player object to dictionary."""
        return {
            "id": player.id,
            "name": player.name,
            "is_alive": player.is_alive,
            "is_god": player.is_god(),
            "role": player.role.value  # Always include role for spectator mode
        }
    
    def get_game_state_dict(self, game: WerewolfGame, include_roles: bool = False) -> Dict[str, Any]:
        """Get current game state as dictionary."""
        # Check win conditions
        is_game_over = False
        winner = None
        
        try:
            alive_wolves = len(game.game_state.alive_wolves)
            alive_civilians = len(game.game_state.alive_civilians)
            
            if alive_wolves == 0:
                is_game_over = True
                winner = "villagers"
            elif alive_wolves >= alive_civilians:
                is_game_over = True
                winner = "wolves"
        except:
            pass
        
        current_speaker = None
        if hasattr(game.game_state, 'speaker_queue') and game.game_state.speaker_queue:
            current_speaker = game.game_state.speaker_queue[0].name if game.game_state.speaker_queue else None
        
        return {
            "phase": game.game_state.current_phase.value,
            "day_count": game.game_state.day_count,
            "alive_players": [self.player_to_dict(p) for p in game.game_state.alive_players],
            "current_speaker": current_speaker,
            "game_history": game.game_state.game_history[-20:],  # Last 20 events
            "is_game_over": is_game_over,
            "winner": winner
        }
    
    async def run_game_loop(self, game_id: str):
        """Run the game loop in the background with actual AI agents."""
        game = self.get_game(game_id)
        if not game:
            return
        
        try:
            speaking_round = 0
            max_speaking_rounds = 2  # Allow multiple rounds of speaking
            
            while True:
                await asyncio.sleep(2)  # Small delay to prevent tight loop
                
                # Check win conditions
                alive_wolves = len(game.game_state.alive_wolves)
                alive_civilians = len(game.game_state.alive_civilians)
                
                if alive_wolves == 0:
                    await self.broadcast_event(game_id, {
                        "type": "game_over",
                        "winner": "villagers",
                        "message": "All wolves have been eliminated! Villagers win!"
                    })
                    break
                elif alive_wolves >= alive_civilians:
                    await self.broadcast_event(game_id, {
                        "type": "game_over",
                        "winner": "wolves", 
                        "message": "Wolves equal or outnumber villagers! Wolves win!"
                    })
                    break
                
                # Broadcast current state
                await self.broadcast_event(game_id, {
                    "type": "game_state_update",
                    **self.get_game_state_dict(game)
                })
                
                # Handle AI actions based on current phase
                if game.game_state.current_phase == GamePhase.DAY:
                    # Get next AI action
                    ai_action = await asyncio.get_event_loop().run_in_executor(
                        None, game.get_next_ai_action
                    )
                    
                    if ai_action:
                        if isinstance(ai_action, SpeechAction):
                            # Broadcast AI speech
                            await self.broadcast_event(game_id, {
                                "type": "player_action",
                                "player": ai_action.player,
                                "action_type": "speak",
                                "message": ai_action.message,
                                "role": ai_action.role,
                                "result": {"spoke": True}
                            })
                            
                            speaking_round += 1
                            
                        elif isinstance(ai_action, PhaseCompleteAction):
                            # Check if we should do voting or go to night
                            if speaking_round >= max_speaking_rounds:
                                # Run voting phase
                                voting_result = await asyncio.get_event_loop().run_in_executor(
                                    None, game.run_voting_phase
                                )
                                
                                # Broadcast voting results
                                for vote in voting_result.votes:
                                    await self.broadcast_event(game_id, {
                                        "type": "player_action",
                                        "action_type": "vote",
                                        "message": vote,
                                        "result": {"voted": True}
                                    })
                                    await asyncio.sleep(1)  # Delay between votes
                                
                                if voting_result.eliminated:
                                    await self.broadcast_event(game_id, {
                                        "type": "elimination",
                                        "eliminated": {
                                            "name": voting_result.eliminated.name,
                                            "role": voting_result.eliminated.role
                                        },
                                        "message": f"{voting_result.eliminated.name} was eliminated by vote!"
                                    })
                                
                                # Transition to night
                                game.transition_to_night()
                                speaking_round = 0
                                
                                await self.broadcast_event(game_id, {
                                    "type": "phase_change",
                                    "new_phase": "night",
                                    "day_count": game.game_state.day_count,
                                    "message": f"Day {game.game_state.day_count} ends. Night falls..."
                                })
                            else:
                                # Continue speaking phase
                                game.game_state.update_speaking_order()
                                
                else:  # Night phase
                    # Get wolf action
                    ai_action = await asyncio.get_event_loop().run_in_executor(
                        None, game.get_next_ai_action
                    )
                    
                    if ai_action:
                        if isinstance(ai_action, NightKillAction):
                            # Show wolf communications first
                            for comm in ai_action.wolf_communications:
                                await self.broadcast_event(game_id, {
                                    "type": "wolf_communication",
                                    "player": comm.player,
                                    "message": comm.message,
                                    "private": True
                                })
                                await asyncio.sleep(2)
                            
                            # Execute the kill
                            success = await asyncio.get_event_loop().run_in_executor(
                                None, game.execute_night_kill, ai_action.target
                            )
                            
                            if success:
                                await self.broadcast_event(game_id, {
                                    "type": "night_kill",
                                    "target": ai_action.target,
                                    "message": f"{ai_action.target} was killed during the night!"
                                })
                            
                            # Transition to day
                            await asyncio.sleep(3)  # Night duration
                            game.transition_to_day()
                            
                            await self.broadcast_event(game_id, {
                                "type": "phase_change",
                                "new_phase": "day",
                                "day_count": game.game_state.day_count,
                                "message": f"Day {game.game_state.day_count} begins! The town awakens to find what happened during the night."
                            })
                            
                        elif isinstance(ai_action, PhaseCompleteAction):
                            # No wolves alive, transition to day
                            game.transition_to_day()
                            
                            await self.broadcast_event(game_id, {
                                "type": "phase_change",
                                "new_phase": "day",
                                "day_count": game.game_state.day_count,
                                "message": f"Day {game.game_state.day_count} begins peacefully."
                            })
                            
        except Exception as e:
            await self.broadcast_event(game_id, {
                "type": "error",
                "message": f"Game loop error: {str(e)}"
            })
    
    def get_active_games_count(self) -> int:
        """Get the number of active games."""
        return len(self.games)
