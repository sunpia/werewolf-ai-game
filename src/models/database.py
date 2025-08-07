"""Database models for the Werewolf AI Game."""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """User model for authentication and game tracking."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    picture = Column(Text)
    provider = Column(String(50), nullable=False, default="google")
    free_games_remaining = Column(Integer, nullable=False, default=3)
    total_games_played = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    games = relationship("Game", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "email": self.email,
            "name": self.name,
            "picture": self.picture,
            "provider": self.provider,
            "free_games_remaining": self.free_games_remaining,
            "total_games_played": self.total_games_played,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }


class Game(Base):
    """Game model for storing game state and configuration."""
    __tablename__ = "games"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    game_config = Column(JSONB, nullable=False)
    game_state = Column(JSONB, nullable=False)
    status = Column(String(50), nullable=False, default="active", index=True)  # active, completed, abandoned
    num_players = Column(Integer, nullable=False)
    current_phase = Column(String(50))
    current_day = Column(Integer, default=1)
    winner = Column(String(100))
    is_game_over = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="games")
    players = relationship("Player", back_populates="game", cascade="all, delete-orphan")
    system_events = relationship("SystemEvent", back_populates="game", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Game(id={self.id}, user_id={self.user_id}, status='{self.status}')>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "game_config": self.game_config,
            "game_state": self.game_state,
            "status": self.status,
            "num_players": self.num_players,
            "current_phase": self.current_phase,
            "current_day": self.current_day,
            "winner": self.winner,
            "is_game_over": self.is_game_over,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class SystemEvent(Base):
    """System event model for tracking game transitions and system actions."""
    __tablename__ = "system_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # day_transition, night_transition, game_start, game_end, voting_start, voting_end
    event_description = Column(Text, nullable=False)  # What happened
    event_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    phase = Column(String(50))  # day, night, voting, lobby
    day_number = Column(Integer)
    event_metadata = Column(JSONB, nullable=True)  # Additional event data

    # Relationships
    game = relationship("Game", back_populates="system_events")

    def __repr__(self):
        return f"<SystemEvent(id={self.id}, game_id={self.game_id}, event_type='{self.event_type}')>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "game_id": str(self.game_id),
            "event_type": self.event_type,
            "event_description": self.event_description,
            "event_time": self.event_time.isoformat() if self.event_time else None,
            "phase": self.phase,
            "day_number": self.day_number,
            "event_metadata": self.event_metadata
        }


class Player(Base):
    """Player model for storing game participants."""
    __tablename__ = "players"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    player_name = Column(String(255), nullable=False)
    role = Column(String(50))
    is_alive = Column(Boolean, default=True)
    is_god = Column(Boolean, default=False)
    ai_personality = Column(JSONB)
    strategy_pattern = Column(JSONB)  # Current strategy patterns
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    game = relationship("Game", back_populates="players")
    user_events = relationship("UserEvent", back_populates="player", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Player(id={self.id}, game_id={self.game_id}, name='{self.player_name}')>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "game_id": str(self.game_id),
            "player_name": self.player_name,
            "role": self.role,
            "is_alive": self.is_alive,
            "is_god": self.is_god,
            "ai_personality": self.ai_personality,
            "strategy_pattern": self.strategy_pattern,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class UserEvent(Base):
    """User event model for tracking user state changes and actions."""
    __tablename__ = "user_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # speech, strategy_change, vote, accusation, defense, night_action
    original_value = Column(Text, nullable=True)  # Previous state/value
    modified_value = Column(Text, nullable=False)  # New state/value (what user said or new strategy)
    event_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    phase = Column(String(50))  # day, night, voting
    day_number = Column(Integer)
    event_metadata = Column(JSONB, nullable=True)  # Additional context data

    # Relationships
    player = relationship("Player", back_populates="user_events")

    def __repr__(self):
        return f"<UserEvent(id={self.id}, player_id={self.player_id}, event_type='{self.event_type}')>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "player_id": str(self.player_id),
            "event_type": self.event_type,
            "original_value": self.original_value,
            "modified_value": self.modified_value,
            "event_time": self.event_time.isoformat() if self.event_time else None,
            "phase": self.phase,
            "day_number": self.day_number,
            "event_metadata": self.event_metadata
        }
