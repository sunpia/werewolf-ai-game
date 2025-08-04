"""Database service for managing database connections and operations."""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import func
from contextlib import contextmanager

from ..models.database import Base, User, Game, GameHistory, Player
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
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def init_db(self):
        """Public method to initialize database - called by FastAPI lifespan."""
        if not self.engine:
            self._initialize_database()
        else:
            logger.info("Database already initialized")
    
    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")
        else:
            logger.info("No database connections to close")
    
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
        """Check database connectivity."""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    # User operations
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.email == email).first()
                if user:
                    # Expunge the object from session to avoid detached instance errors
                    session.expunge(user)
                return user
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    # Expunge the object from session to avoid detached instance errors
                    session.expunge(user)
                return user
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    def create_user(self, email: str, name: str, picture: str = None, provider: str = "google") -> Optional[User]:
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
                session.flush()  # Get the ID
                session.refresh(user)
                # Expunge to avoid detached instance errors
                session.expunge(user)
                return user
        except SQLAlchemyError as e:
            logger.error(f"Error creating user {email}: {e}")
            return None
    
    def update_user_login(self, user_id: str) -> bool:
        """Update user's last login timestamp."""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    user.last_login = datetime.now(timezone.utc)
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"Error updating user login {user_id}: {e}")
            return False
    
    def decrement_free_games(self, user_id: str) -> bool:
        """Decrement user's free games remaining."""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if user and user.free_games_remaining > 0:
                    user.free_games_remaining -= 1
                    user.total_games_played += 1
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"Error decrementing free games for user {user_id}: {e}")
            return False
    
    def increment_user_games(self, user_id: str, decrement: bool = True) -> bool:
        """Increment or restore user's free games.
        
        Args:
            user_id: The user ID
            decrement: If True, decrement free games (use one). If False, increment free games (restore one)
        """
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    if decrement:
                        # Use a free game (decrement)
                        if user.free_games_remaining > 0:
                            user.free_games_remaining -= 1
                            user.total_games_played += 1
                            return True
                        return False
                    else:
                        # Restore a free game (increment)
                        user.free_games_remaining += 1
                        if user.total_games_played > 0:
                            user.total_games_played -= 1
                        return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"Error updating user games for user {user_id}: {e}")
            return False
    
    # Game operations
    def create_game(self, user_id: str, game_config: Dict[str, Any], initial_state: Dict[str, Any]) -> Optional[Game]:
        """Create a new game."""
        try:
            with self.get_session() as session:
                game = Game(
                    user_id=user_id,
                    game_config=game_config,
                    game_state=initial_state,
                    num_players=game_config.get("num_players", 6),
                    current_phase=initial_state.get("phase", "lobby"),
                    current_day=initial_state.get("day_count", 1)
                )
                session.add(game)
                session.flush()
                session.refresh(game)
                # Expunge to avoid detached instance errors
                session.expunge(game)
                return game
        except SQLAlchemyError as e:
            logger.error(f"Error creating game for user {user_id}: {e}")
            return None
    
    def get_game_by_id(self, game_id: str) -> Optional[Game]:
        """Get game by ID."""
        try:
            with self.get_session() as session:
                game = session.query(Game).filter(Game.id == game_id).first()
                if game:
                    # Expunge to avoid detached instance errors
                    session.expunge(game)
                return game
        except SQLAlchemyError as e:
            logger.error(f"Error getting game {game_id}: {e}")
            return None
    
    def update_game_state(self, game_id: str, game_state: Dict[str, Any]) -> bool:
        """Update game state."""
        try:
            with self.get_session() as session:
                game = session.query(Game).filter(Game.id == game_id).first()
                if game:
                    game.game_state = game_state
                    game.current_phase = game_state.get("phase")
                    game.current_day = game_state.get("day_count")
                    game.is_game_over = game_state.get("is_game_over", False)
                    game.winner = game_state.get("winner")
                    
                    if game.is_game_over and game.status == "active":
                        game.status = "completed"
                        game.completed_at = datetime.now(timezone.utc)
                    
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"Error updating game state {game_id}: {e}")
            return False
    
    def get_user_games(self, user_id: str, limit: int = 50) -> List[Game]:
        """Get user's games."""
        try:
            with self.get_session() as session:
                games = session.query(Game).filter(Game.user_id == user_id).order_by(Game.created_at.desc()).limit(limit).all()
                # Expunge all games to avoid detached instance errors
                for game in games:
                    session.expunge(game)
                return games
        except SQLAlchemyError as e:
            logger.error(f"Error getting games for user {user_id}: {e}")
            return []
    
    # Game history operations
    def add_game_event(self, game_id: str, event_type: str, event_data: Dict[str, Any], phase: str = None, day_count: int = None) -> bool:
        """Add event to game history."""
        try:
            with self.get_session() as session:
                history = GameHistory(
                    game_id=game_id,
                    event_type=event_type,
                    event_data=event_data,
                    phase=phase,
                    day_count=day_count
                )
                session.add(history)
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error adding game event for game {game_id}: {e}")
            return False
    
    def get_game_history(self, game_id: str) -> List[GameHistory]:
        """Get game history."""
        try:
            with self.get_session() as session:
                history = session.query(GameHistory).filter(GameHistory.game_id == game_id).order_by(GameHistory.timestamp.asc()).all()
                # Expunge all history objects to avoid detached instance errors
                for hist in history:
                    session.expunge(hist)
                return history
        except SQLAlchemyError as e:
            logger.error(f"Error getting game history for game {game_id}: {e}")
            return []
    
    # Player operations
    def create_players(self, game_id: str, players_data: List[Dict[str, Any]]) -> bool:
        """Create players for a game."""
        try:
            with self.get_session() as session:
                players = []
                for player_data in players_data:
                    player = Player(
                        game_id=game_id,
                        player_name=player_data["name"],
                        role=player_data.get("role"),
                        is_alive=player_data.get("is_alive", True),
                        is_god=player_data.get("is_god", False),
                        ai_personality=player_data.get("ai_personality")
                    )
                    players.append(player)
                
                session.add_all(players)
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error creating players for game {game_id}: {e}")
            return False
    
    def get_game_players(self, game_id: str) -> List[Player]:
        """Get players for a game."""
        try:
            with self.get_session() as session:
                players = session.query(Player).filter(Player.game_id == game_id).all()
                # Expunge all player objects to avoid detached instance errors
                for player in players:
                    session.expunge(player)
                return players
        except SQLAlchemyError as e:
            logger.error(f"Error getting players for game {game_id}: {e}")
            return []


# Global database service instance
db_service = DatabaseService()
