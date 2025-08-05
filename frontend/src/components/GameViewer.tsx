import React, { useState, useEffect, useCallback } from 'react';
import './GameViewer.css';

interface SystemEvent {
  id: string;
  game_id: string;
  event_type: string;
  event_description: string;
  event_time: string;
  phase?: string;
  day_number?: number;
  event_metadata?: any;
}

interface UserEvent {
  id: string;
  player_id: string;
  event_type: string;
  original_value?: string;
  modified_value: string;
  event_time: string;
  phase?: string;
  day_number?: number;
  event_metadata?: any;
}

interface Player {
  id: string;
  game_id: string;
  player_name: string;
  role?: string;
  is_alive: boolean;
  is_god: boolean;
  ai_personality?: any;
  strategy_pattern?: any;
  created_at: string;
}

interface Game {
  id: string;
  user_id: string;
  game_config: any;
  game_state: any;
  status: string;
  num_players: number;
  current_phase?: string;
  current_day: number;
  winner?: string;
  is_game_over: boolean;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

interface CompleteGameData {
  game: Game;
  players: Player[];
  system_events: SystemEvent[];
  user_events: UserEvent[];
}

interface GameViewerProps {
  gameId: string;
  onBack: () => void;
}

const GameViewer: React.FC<GameViewerProps> = ({ gameId, onBack }) => {
  const [gameData, setGameData] = useState<CompleteGameData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'events' | 'players'>('overview');

  const fetchCompleteGameData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/tracking/games/${gameId}/complete`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch game data');
      }

      const data = await response.json();
      setGameData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  }, [gameId]);

  useEffect(() => {
    fetchCompleteGameData();
  }, [fetchCompleteGameData]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatEventType = (eventType: string) => {
    return eventType.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  if (loading) {
    return (
      <div className="game-viewer loading">
        <p>Loading game data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="game-viewer error">
        <p>Error: {error}</p>
        <button onClick={onBack}>Back to Games</button>
      </div>
    );
  }

  if (!gameData) {
    return (
      <div className="game-viewer">
        <p>No game data found</p>
        <button onClick={onBack}>Back to Games</button>
      </div>
    );
  }

  const { game, players, system_events, user_events } = gameData;

  // Combine and sort all events by time
  const allEvents = [
    ...system_events.map(e => ({ ...e, source: 'system' as const })),
    ...user_events.map(e => ({ ...e, source: 'user' as const }))
  ].sort((a, b) => new Date(a.event_time).getTime() - new Date(b.event_time).getTime());

  const getPlayerName = (playerId: string) => {
    const player = players.find(p => p.id === playerId);
    return player?.player_name || 'Unknown Player';
  };

  return (
    <div className="game-viewer">
      <div className="game-viewer-header">
        <button onClick={onBack} className="back-button">← Back to Games</button>
        <h1>Game Details</h1>
      </div>

      <div className="game-info">
        <h2>{game.status === 'completed' ? 'Completed Game' : 'Game in Progress'}</h2>
        <div className="game-meta">
          <p><strong>Created:</strong> {formatDate(game.created_at)}</p>
          <p><strong>Players:</strong> {game.num_players}</p>
          <p><strong>Current Phase:</strong> {game.current_phase || 'N/A'}</p>
          <p><strong>Day:</strong> {game.current_day}</p>
          {game.winner && <p><strong>Winner:</strong> {game.winner}</p>}
          {game.completed_at && <p><strong>Completed:</strong> {formatDate(game.completed_at)}</p>}
        </div>
      </div>

      <div className="tabs">
        <button 
          className={selectedTab === 'overview' ? 'active' : ''}
          onClick={() => setSelectedTab('overview')}
        >
          Overview
        </button>
        <button 
          className={selectedTab === 'players' ? 'active' : ''}
          onClick={() => setSelectedTab('players')}
        >
          Players ({players.length})
        </button>
        <button 
          className={selectedTab === 'events' ? 'active' : ''}
          onClick={() => setSelectedTab('events')}
        >
          Events ({allEvents.length})
        </button>
      </div>

      <div className="tab-content">
        {selectedTab === 'overview' && (
          <div className="overview-tab">
            <div className="overview-stats">
              <div className="stat-card">
                <h3>System Events</h3>
                <p className="stat-number">{system_events.length}</p>
              </div>
              <div className="stat-card">
                <h3>User Actions</h3>
                <p className="stat-number">{user_events.length}</p>
              </div>
              <div className="stat-card">
                <h3>Alive Players</h3>
                <p className="stat-number">{players.filter(p => p.is_alive).length}</p>
              </div>
            </div>
            
            <div className="recent-events">
              <h3>Recent Events</h3>
              <div className="event-list">
                {allEvents.slice(-10).map((event, index) => (
                  <div key={`${event.source}-${event.id}`} className={`event-item ${event.source}`}>
                    <div className="event-header">
                      <span className="event-type">{formatEventType(event.event_type)}</span>
                      <span className="event-time">{formatDate(event.event_time)}</span>
                    </div>
                    <div className="event-content">
                      {event.source === 'system' ? (
                        <p>{(event as SystemEvent).event_description}</p>
                      ) : (
                        <div>
                          <p><strong>{getPlayerName((event as UserEvent).player_id)}:</strong></p>
                          <p>{(event as UserEvent).modified_value}</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'players' && (
          <div className="players-tab">
            <div className="players-grid">
              {players.map(player => (
                <div key={player.id} className={`player-card ${!player.is_alive ? 'dead' : ''}`}>
                  <div className="player-header">
                    <h3>{player.player_name}</h3>
                    <span className={`status ${player.is_alive ? 'alive' : 'dead'}`}>
                      {player.is_alive ? 'Alive' : 'Dead'}
                    </span>
                  </div>
                  <div className="player-details">
                    {player.role && <p><strong>Role:</strong> {player.role}</p>}
                    {player.is_god && <p><strong>Type:</strong> God Player</p>}
                    <p><strong>Joined:</strong> {formatDate(player.created_at)}</p>
                  </div>
                  <div className="player-events">
                    <h4>Actions ({user_events.filter(e => e.player_id === player.id).length})</h4>
                    <div className="event-types">
                      {Array.from(new Set(user_events.filter(e => e.player_id === player.id).map(e => e.event_type))).map(type => (
                        <span key={type} className="event-type-tag">{formatEventType(type)}</span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'events' && (
          <div className="events-tab">
            <div className="events-timeline">
              {allEvents.map((event, index) => (
                <div key={`${event.source}-${event.id}`} className={`timeline-event ${event.source}`}>
                  <div className="timeline-marker"></div>
                  <div className="timeline-content">
                    <div className="event-header">
                      <span className="event-type">{formatEventType(event.event_type)}</span>
                      <span className="event-time">{formatDate(event.event_time)}</span>
                      {event.phase && <span className="event-phase">{event.phase}</span>}
                      {event.day_number && <span className="event-day">Day {event.day_number}</span>}
                    </div>
                    <div className="event-content">
                      {event.source === 'system' ? (
                        <p>{(event as SystemEvent).event_description}</p>
                      ) : (
                        <div>
                          <p><strong>{getPlayerName((event as UserEvent).player_id)}:</strong></p>
                          <p>{(event as UserEvent).modified_value}</p>
                          {(event as UserEvent).original_value && (
                            <p className="original-value">
                              <em>Previous: {(event as UserEvent).original_value}</em>
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GameViewer;
