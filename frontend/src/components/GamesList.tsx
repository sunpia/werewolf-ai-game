import React, { useState, useEffect, useCallback } from 'react';
import GameViewer from './GameViewer';

interface Game {
  id: string;
  user_id: string;
  status: string;
  num_players: number;
  current_phase?: string;
  current_day: number;
  winner?: string;
  is_game_over: boolean;
  created_at: string;
  completed_at?: string;
}

interface GamesListProps {
  onBack?: () => void;
}

const GamesList: React.FC<GamesListProps> = ({ onBack }) => {
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedGameId, setSelectedGameId] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'active' | 'completed'>('all');

  const fetchGames = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/user/games/history', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch games');
      }

      const data = await response.json();
      setGames(data.games || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGames();
  }, [fetchGames]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return '#28a745';
      case 'completed': return '#007bff';
      case 'abandoned': return '#6c757d';
      default: return '#6c757d';
    }
  };

  const filteredGames = games.filter(game => {
    if (filter === 'all') return true;
    if (filter === 'active') return game.status === 'active';
    if (filter === 'completed') return game.status === 'completed';
    return true;
  });

  if (selectedGameId) {
    return (
      <GameViewer 
        gameId={selectedGameId} 
        onBack={() => setSelectedGameId(null)} 
      />
    );
  }

  if (loading) {
    return (
      <div className="games-list loading">
        <p>Loading your games...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="games-list error">
        <p>Error: {error}</p>
        <button onClick={fetchGames}>Retry</button>
      </div>
    );
  }

  return (
    <div className="games-list">
      <div className="games-header">
        {onBack && (
          <button onClick={onBack} className="back-button">
            ← Back
          </button>
        )}
        <h1>Your Games</h1>
      </div>

      <div className="games-controls">
        <div className="filter-buttons">
          <button 
            className={filter === 'all' ? 'active' : ''}
            onClick={() => setFilter('all')}
          >
            All Games ({games.length})
          </button>
          <button 
            className={filter === 'active' ? 'active' : ''}
            onClick={() => setFilter('active')}
          >
            Active ({games.filter(g => g.status === 'active').length})
          </button>
          <button 
            className={filter === 'completed' ? 'active' : ''}
            onClick={() => setFilter('completed')}
          >
            Completed ({games.filter(g => g.status === 'completed').length})
          </button>
        </div>
        <button onClick={fetchGames} className="refresh-button">
          Refresh
        </button>
      </div>

      {filteredGames.length === 0 ? (
        <div className="empty-state">
          <p>No games found for the selected filter.</p>
          {filter !== 'all' && (
            <button onClick={() => setFilter('all')}>
              Show All Games
            </button>
          )}
        </div>
      ) : (
        <div className="games-grid">
          {filteredGames.map(game => (
            <div key={game.id} className="game-card">
              <div className="game-header">
                <div className="game-status">
                  <span 
                    className="status-dot" 
                    style={{ backgroundColor: getStatusColor(game.status) }}
                  ></span>
                  <span className="status-text">{game.status}</span>
                </div>
                <span className="game-date">{formatDate(game.created_at)}</span>
              </div>

              <div className="game-details">
                <div className="game-meta">
                  <div className="meta-item">
                    <strong>Players:</strong> {game.num_players}
                  </div>
                  <div className="meta-item">
                    <strong>Day:</strong> {game.current_day}
                  </div>
                  {game.current_phase && (
                    <div className="meta-item">
                      <strong>Phase:</strong> {game.current_phase}
                    </div>
                  )}
                </div>

                {game.winner && (
                  <div className="game-winner">
                    🏆 Winner: {game.winner}
                  </div>
                )}

                {game.completed_at && (
                  <div className="game-completed">
                    Completed: {formatDateTime(game.completed_at)}
                  </div>
                )}
              </div>

              <div className="game-actions">
                <button 
                  onClick={() => setSelectedGameId(game.id)}
                  className="view-button primary"
                >
                  View Details
                </button>
                {game.status === 'active' && (
                  <button className="resume-button">
                    Resume Game
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default GamesList;
