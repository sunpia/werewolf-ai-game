import React, { useState } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { GameState } from '../App';

interface GameLobbyProps {
  onGameCreated: (gameId: string, gameState: GameState) => void;
}

interface GameLimits {
  free_games_remaining: number;
  total_games_played: number;
  can_create_game: boolean;
}

const GameLobby: React.FC<GameLobbyProps> = ({ onGameCreated }) => {
  const [numPlayers, setNumPlayers] = useState<number>(8);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [gameLimits, setGameLimits] = useState<GameLimits | null>(null);
  const { token } = useAuth();

  // Load game limits on component mount
  React.useEffect(() => {
    const loadGameLimits = async () => {
      try {
        const response = await axios.get('/api/games/limits', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setGameLimits(response.data);
      } catch (error) {
        console.error('Failed to load game limits:', error);
      }
    };

    if (token) {
      loadGameLimits();
    }
  }, [token]);

  const handleCreateGame = async () => {
    if (!token) {
      setError('Please sign in to create a game');
      return;
    }

    if (numPlayers < 6 || numPlayers > 15) {
      setError('Number of players must be between 6 and 15');
      return;
    }

    if (gameLimits && !gameLimits.can_create_game) {
      setError(`No free games remaining. You have played ${gameLimits.total_games_played} games.`);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/api/games', {
        num_players: numPlayers
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const gameId = response.data.game_id;

      // Get initial game state
      const stateResponse = await axios.get(`/api/games/${gameId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      onGameCreated(gameId, stateResponse.data);
      
      // Refresh game limits after creating a game
      const limitsResponse = await axios.get('/api/games/limits', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setGameLimits(limitsResponse.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create game');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="lobby-container">
      <div className="lobby-card">
        <h1 className="lobby-title">🐺 AI Werewolf Game</h1>
        <p style={{ fontSize: '1.2em', marginBottom: '2rem', opacity: '0.9', lineHeight: '1.6' }}>
          Watch sophisticated AI agents battle it out in the ultimate game of deception and strategy. 
          Experience the future of AI gaming where every move is calculated, every word is strategic.
        </p>
        
        {/* Game Limits Display */}
        {gameLimits && (
          <div className="game-limits" style={{ 
            background: 'rgba(255, 255, 255, 0.1)', 
            padding: '1rem', 
            borderRadius: '8px', 
            marginBottom: '2rem',
            border: gameLimits.can_create_game ? '1px solid rgba(0, 255, 0, 0.3)' : '1px solid rgba(255, 0, 0, 0.3)'
          }}>
            <h3 style={{ margin: '0 0 0.5rem 0', color: '#fff' }}>🎮 Game Status</h3>
            <p style={{ margin: 0, color: '#fff' }}>
              Free games remaining: <strong>{gameLimits.free_games_remaining}</strong><br/>
              Total games played: <strong>{gameLimits.total_games_played}</strong>
            </p>
            {!gameLimits.can_create_game && (
              <p style={{ margin: '0.5rem 0 0 0', color: '#ff6b6b', fontWeight: 'bold' }}>
                ⚠️ No free games remaining
              </p>
            )}
          </div>
        )}
        
        {error && <div className="error">{error}</div>}
        
        {!token && (
          <div className="auth-warning" style={{ 
            background: 'rgba(255, 165, 0, 0.2)', 
            padding: '1rem', 
            borderRadius: '8px', 
            marginBottom: '2rem',
            border: '1px solid rgba(255, 165, 0, 0.5)'
          }}>
            <p style={{ margin: 0, color: '#ffa500' }}>
              🔐 Please sign in to create and play games
            </p>
          </div>
        )}
        
        <div className="form-group">
          <label className="form-label">🎯 Select Game Size (6-15 players):</label>
          <input
            type="number"
            min="6"
            max="15"
            value={numPlayers}
            onChange={(e) => setNumPlayers(parseInt(e.target.value))}
            className="form-input"
            disabled={loading || !token}
            placeholder="Enter number of AI players"
          />
        </div>

        <button
          onClick={handleCreateGame}
          disabled={loading || !token || (gameLimits ? !gameLimits.can_create_game : false)}
          className="create-game-button"
        >
          {loading ? '🚀 Initializing AI Game...' : 
           !token ? '🔐 Sign In to Play' :
           (gameLimits && !gameLimits.can_create_game) ? '❌ No Free Games Left' :
           '⚡ Launch AI Battle Game'}
        </button>

        <div style={{ 
          marginTop: '3rem', 
          fontSize: '0.95em', 
          opacity: '0.85',
          background: 'rgba(255, 255, 255, 0.05)',
          padding: '2rem',
          borderRadius: '16px',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          <h3 style={{ 
            marginTop: 0, 
            marginBottom: '1rem', 
            color: 'rgba(255, 255, 255, 0.9)',
            fontSize: '1.1em',
            fontWeight: '600'
          }}>
            ⚔️ What You'll Experience:
          </h3>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
            gap: '1rem',
            textAlign: 'left'
          }}>
            <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.05)', borderRadius: '12px' }}>
              <strong>🤖 Advanced AI Agents</strong>
              <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.9em' }}>
                Watch AI werewolves craft deceptive strategies while AI villagers use logic to hunt them down
              </p>
            </div>
            <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.05)', borderRadius: '12px' }}>
              <strong>🧠 Real-time Strategy</strong>
              <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.9em' }}>
                Observe AI decision-making processes as they adapt, bluff, and counter each other's moves
              </p>
            </div>
            <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.05)', borderRadius: '12px' }}>
              <strong>👁️ Spectator Mode</strong>
              <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.9em' }}>
                Sit back and enjoy the psychological warfare unfold in this battle of artificial minds
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GameLobby;
