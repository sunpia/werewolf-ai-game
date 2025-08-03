import React from 'react';
import { GameState } from '../App';

interface GameStatusProps {
  gameState: GameState | null;
}

const GameStatus: React.FC<GameStatusProps> = ({ gameState }) => {
  if (!gameState) {
    return (
      <div className="game-status">
        <h2>Game Status</h2>
        <p>Loading game state...</p>
      </div>
    );
  }

  const getPhaseColor = (phase: string) => {
    return phase.toLowerCase() === 'day' ? 'day' : 'night';
  };

  const aliveWolves = gameState.alive_players.filter(p => p.role === 'wolf').length;
  const aliveCivilians = gameState.alive_players.filter(p => p.role === 'civilian').length;

  return (
    <div className="game-status">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ margin: 0, fontSize: '1.8em', fontWeight: '700', color: 'rgba(255, 255, 255, 0.95)' }}>
          🎮 Game Status
        </h2>
        <span className={`game-phase ${getPhaseColor(gameState.phase)}`}>
          {gameState.phase} {gameState.day_count}
        </span>
      </div>
      
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', 
        gap: '16px',
        marginBottom: '20px'
      }}>
        <div style={{
          background: 'rgba(255, 255, 255, 0.1)',
          padding: '16px',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '1.5em', marginBottom: '8px' }}>
            {gameState.phase === 'DAY' ? '☀️' : '🌙'}
          </div>
          <strong style={{ color: 'rgba(255, 255, 255, 0.9)' }}>Current Phase</strong>
          <br />
          <span style={{ fontSize: '0.9em', opacity: '0.8' }}>
            {gameState.phase === 'DAY' ? 'Day Phase' : 'Night Phase'}
          </span>
        </div>
        
        <div style={{
          background: 'rgba(255, 255, 255, 0.1)',
          padding: '16px',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '1.5em', marginBottom: '8px' }}>📅</div>
          <strong style={{ color: 'rgba(255, 255, 255, 0.9)' }}>Day Count</strong>
          <br />
          <span style={{ fontSize: '0.9em', opacity: '0.8' }}>
            Day {gameState.day_count}
          </span>
        </div>
        
        <div style={{
          background: 'rgba(255, 255, 255, 0.1)',
          padding: '16px',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '1.5em', marginBottom: '8px' }}>👥</div>
          <strong style={{ color: 'rgba(255, 255, 255, 0.9)' }}>Alive Players</strong>
          <br />
          <span style={{ fontSize: '0.9em', opacity: '0.8' }}>
            {gameState.alive_players.length} total
          </span>
        </div>
        
        {gameState.current_speaker && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.1)',
            padding: '16px',
            borderRadius: '12px',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '1.5em', marginBottom: '8px' }}>🎤</div>
            <strong style={{ color: 'rgba(255, 255, 255, 0.9)' }}>Current Speaker</strong>
            <br />
            <span style={{ fontSize: '0.9em', opacity: '0.8' }}>
              {gameState.current_speaker}
            </span>
          </div>
        )}
      </div>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
        gap: '16px',
        marginTop: '20px'
      }}>
        <div style={{ 
          background: 'linear-gradient(135deg, rgba(244, 67, 54, 0.2), rgba(244, 67, 54, 0.1))',
          padding: '20px', 
          borderRadius: '12px', 
          textAlign: 'center',
          border: '1px solid rgba(244, 67, 54, 0.3)',
          backdropFilter: 'blur(10px)'
        }}>
          <div style={{ fontSize: '2em', marginBottom: '8px' }}>🐺</div>
          <strong style={{ fontSize: '1.1em' }}>Wolves</strong>
          <br />
          <span style={{ fontSize: '1.2em', fontWeight: '600' }}>
            {aliveWolves} alive
          </span>
        </div>
        
        <div style={{ 
          background: 'linear-gradient(135deg, rgba(76, 175, 80, 0.2), rgba(76, 175, 80, 0.1))',
          padding: '20px', 
          borderRadius: '12px', 
          textAlign: 'center',
          border: '1px solid rgba(76, 175, 80, 0.3)',
          backdropFilter: 'blur(10px)'
        }}>
          <div style={{ fontSize: '2em', marginBottom: '8px' }}>👤</div>
          <strong style={{ fontSize: '1.1em' }}>Civilians</strong>
          <br />
          <span style={{ fontSize: '1.2em', fontWeight: '600' }}>
            {aliveCivilians} alive
          </span>
        </div>
      </div>
      
      {gameState.is_game_over && (
        <div style={{ 
          marginTop: '24px', 
          padding: '24px', 
          background: gameState.winner === 'wolves' 
            ? 'linear-gradient(135deg, rgba(244, 67, 54, 0.3), rgba(244, 67, 54, 0.2))'
            : 'linear-gradient(135deg, rgba(76, 175, 80, 0.3), rgba(76, 175, 80, 0.2))',
          borderRadius: '16px',
          border: `1px solid ${gameState.winner === 'wolves' ? 'rgba(244, 67, 54, 0.4)' : 'rgba(76, 175, 80, 0.4)'}`,
          textAlign: 'center',
          fontSize: '1.3em',
          fontWeight: '700',
          backdropFilter: 'blur(20px)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)'
        }}>
          🎉 Game Over! {gameState.winner === 'wolves' ? 'Wolves' : 'Villagers'} Win! 🎉
        </div>
      )}
    </div>
  );
};

export default GameStatus;
