"""Simplified database service for managing database connections and operations."""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import func
from contextlib import contextmanager

from ..models.database import Base, User, Game, Player, SystemEvent, UserEvent
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for managing database operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.database_url = self.settings.database_url or "postgresql://werewolf_user:werewolf_password@localhost:5432/werewolf_game"
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection and create tables."""
        try:
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=False  # Set to True for SQL debugging
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create tables if they don't exist
            Base.metadata.create_all(bind=self.engine, checkfirst=True)
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def init_db(self):
        """Public method to initialize database - called by FastAPI lifespan."""
        if not self.engine:
            self._initialize_database()
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check if database connection is healthy."""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")
    
    # User operations
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.email == email).first()
                if user:
                    session.expunge(user)
                return user
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    def create_user(self, email: str, name: str, picture: Optional[str] = None, 
                   provider: str = "google") -> Optional[User]:
        """Create a new user."""
        try:
            with self.get_session() as session:
                user = User(
                    email=email,
                    name=name,
                    picture=picture,
                    provider=provider
                )
                session.add(user)
                session.flush()
                session.expunge(user)
                return user
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def update_user_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp."""
        try:
            with self.get_session() as session:
                session.query(User).filter(User.id == user_id).update({
                    'last_login': datetime.now(timezone.utc)
                })
                return True
        except Exception as e:
            logger.error(f"Error updating last login for user {user_id}: {e}")
            return False
    
    def increment_user_games(self, user_id: str) -> bool:
        """Increment user's total games played and decrement free games remaining."""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    user.total_games_played += 1
                    if user.free_games_remaining > 0:
                        user.free_games_remaining -= 1
                    session.flush()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error incrementing games for user {user_id}: {e}")
            return False

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    session.expunge(user)
                return user
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None

    def decrement_free_games(self, user_id: str) -> bool:
        """Decrement user's free games remaining."""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if user and user.free_games_remaining > 0:
                    user.free_games_remaining -= 1
                    session.flush()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error decrementing free games for user {user_id}: {e}")
            return False

    def increment_free_games(self, user_id: str) -> bool:
        """Increment user's free games remaining (for refunds/errors)."""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    user.free_games_remaining += 1
                    session.flush()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error incrementing free games for user {user_id}: {e}")
            return False

    # Game operations
    def create_game(self, user_id: str, game_config: Dict[str, Any], 
                   game_state: Dict[str, Any], num_players: int,
                   current_phase: Optional[str] = None) -> Optional[Game]:
        """Create a new game."""
        try:
            with self.get_session() as session:
                game = Game(
                    user_id=user_id,
                    game_config=game_config,
                    game_state=game_state,
                    num_players=num_players,
                    current_phase=current_phase
                )
                session.add(game)
                session.flush()
                session.expunge(game)
                return game
        except Exception as e:
            logger.error(f"Error creating game: {e}")
            return None
    
    def get_game(self, game_id: str) -> Optional[Game]:
        """Get game by ID."""
        try:
            with self.get_session() as session:
                game = session.query(Game).filter(Game.id == game_id).first()
                if game:
                    session.expunge(game)
                return game
        except Exception as e:
            logger.error(f"Error getting game {game_id}: {e}")
            return None
    
    def update_game(self, game_id: str, **kwargs) -> bool:
        """Update game with given fields."""
        try:
            with self.get_session() as session:
                kwargs['updated_at'] = datetime.now(timezone.utc)
                session.query(Game).filter(Game.id == game_id).update(kwargs)
                return True
        except Exception as e:
            logger.error(f"Error updating game {game_id}: {e}")
            return False
    
    def get_user_games(self, user_id: str, status: Optional[str] = None) -> List[Game]:
        """Get all games for a user, optionally filtered by status."""
        try:
            with self.get_session() as session:
                query = session.query(Game).filter(Game.user_id == user_id)
                if status:
                    query = query.filter(Game.status == status)
                games = query.order_by(Game.created_at.desc()).all()
                for game in games:
                    session.expunge(game)
                return games
        except Exception as e:
            logger.error(f"Error getting games for user {user_id}: {e}")
            return []
    
    # Player operations
    def create_player(self, game_id: str, player_name: str, role: Optional[str] = None,
                     is_god: bool = False, ai_personality: Optional[Dict[str, Any]] = None,
                     strategy_pattern: Optional[Dict[str, Any]] = None) -> Optional[Player]:
        """Create a new player."""
        try:
            with self.get_session() as session:
                player = Player(
                    game_id=game_id,
                    player_name=player_name,
                    role=role,
                    is_god=is_god,
                    ai_personality=ai_personality,
                    strategy_pattern=strategy_pattern
                )
                session.add(player)
                session.flush()
                session.expunge(player)
                return player
        except Exception as e:
            logger.error(f"Error creating player: {e}")
            return None
    
    def get_game_players(self, game_id: str) -> List[Player]:
        """Get all players for a game."""
        try:
            with self.get_session() as session:
                players = session.query(Player).filter(Player.game_id == game_id).all()
                for player in players:
                    session.expunge(player)
                return players
        except Exception as e:
            logger.error(f"Error getting players for game {game_id}: {e}")
            return []
    
    def get_player(self, player_id: str) -> Optional[Player]:
        """Get player by ID."""
        try:
            with self.get_session() as session:
                player = session.query(Player).filter(Player.id == player_id).first()
                if player:
                    session.expunge(player)
                return player
        except Exception as e:
            logger.error(f"Error getting player {player_id}: {e}")
            return None
    
    def update_player(self, player_id: str, **kwargs) -> bool:
        """Update player with given fields."""
        try:
            with self.get_session() as session:
                session.query(Player).filter(Player.id == player_id).update(kwargs)
                return True
        except Exception as e:
            logger.error(f"Error updating player {player_id}: {e}")
            return False
    
    # System event operations
    def create_system_event(self, game_id: str, event_type: str, event_description: str,
                           phase: Optional[str] = None, day_number: Optional[int] = None,
                           event_metadata: Optional[Dict[str, Any]] = None) -> Optional[SystemEvent]:
        """Create a new system event."""
        try:
            with self.get_session() as session:
                event = SystemEvent(
                    game_id=game_id,
                    event_type=event_type,
                    event_description=event_description,
                    phase=phase,
                    day_number=day_number,
                    event_metadata=event_metadata
                )
                session.add(event)
                session.flush()
                session.expunge(event)
                return event
        except Exception as e:
            logger.error(f"Error creating system event: {e}")
            return None
    
    def get_game_system_events(self, game_id: str, event_type: Optional[str] = None,
                              limit: int = 100) -> List[SystemEvent]:
        """Get system events for a game."""
        try:
            with self.get_session() as session:
                query = session.query(SystemEvent).filter(SystemEvent.game_id == game_id)
                if event_type:
                    query = query.filter(SystemEvent.event_type == event_type)
                events = query.order_by(SystemEvent.event_time.asc()).limit(limit).all()
                for event in events:
                    session.expunge(event)
                return events
        except Exception as e:
            logger.error(f"Error getting system events for game {game_id}: {e}")
            return []
    
    # User event operations
    def create_user_event(self, player_id: str, event_type: str, modified_value: str,
                         original_value: Optional[str] = None, phase: Optional[str] = None,
                         day_number: Optional[int] = None, 
                         event_metadata: Optional[Dict[str, Any]] = None) -> Optional[UserEvent]:
        """Create a new user event."""
        try:
            with self.get_session() as session:
                event = UserEvent(
                    player_id=player_id,
                    event_type=event_type,
                    original_value=original_value,
                    modified_value=modified_value,
                    phase=phase,
                    day_number=day_number,
                    event_metadata=event_metadata
                )
                session.add(event)
                session.flush()
                session.expunge(event)
                return event
        except Exception as e:
            logger.error(f"Error creating user event: {e}")
            return None
    
    def get_player_user_events(self, player_id: str, event_type: Optional[str] = None,
                              limit: int = 100) -> List[UserEvent]:
        """Get user events for a player."""
        try:
            with self.get_session() as session:
                query = session.query(UserEvent).filter(UserEvent.player_id == player_id)
                if event_type:
                    query = query.filter(UserEvent.event_type == event_type)
                events = query.order_by(UserEvent.event_time.asc()).limit(limit).all()
                for event in events:
                    session.expunge(event)
                return events
        except Exception as e:
            logger.error(f"Error getting user events for player {player_id}: {e}")
            return []
    
    def get_game_user_events(self, game_id: str, event_type: Optional[str] = None,
                            limit: int = 100) -> List[UserEvent]:
        """Get all user events for a game."""
        try:
            with self.get_session() as session:
                query = session.query(UserEvent).join(Player).filter(Player.game_id == game_id)
                if event_type:
                    query = query.filter(UserEvent.event_type == event_type)
                events = query.order_by(UserEvent.event_time.asc()).limit(limit).all()
                for event in events:
                    session.expunge(event)
                return events
        except Exception as e:
            logger.error(f"Error getting user events for game {game_id}: {e}")
            return []
    
    # Game data retrieval for frontend
    def get_complete_game_data(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get complete game data including players, system events, and user events."""
        try:
            with self.get_session() as session:
                # Get game
                game = session.query(Game).filter(Game.id == game_id).first()
                if not game:
                    return None
                
                # Get players
                players = session.query(Player).filter(Player.game_id == game_id).all()
                
                # Get system events
                system_events = session.query(SystemEvent).filter(
                    SystemEvent.game_id == game_id
                ).order_by(SystemEvent.event_time.asc()).all()
                
                # Get user events for all players
                user_events = session.query(UserEvent).join(Player).filter(
                    Player.game_id == game_id
                ).order_by(UserEvent.event_time.asc()).all()
                
                # Detach all objects from session
                session.expunge(game)
                for player in players:
                    session.expunge(player)
                for event in system_events:
                    session.expunge(event)
                for event in user_events:
                    session.expunge(event)
                
                return {
                    "game": game.to_dict(),
                    "players": [player.to_dict() for player in players],
                    "system_events": [event.to_dict() for event in system_events],
                    "user_events": [event.to_dict() for event in user_events]
                }
        except Exception as e:
            logger.error(f"Error getting complete game data for {game_id}: {e}")
            return None


# Global database service instance
db_service = DatabaseService()
