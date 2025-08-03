import React from 'react';
import { Player } from '../App';

interface PlayerListProps {
  players: Player[];
}

const PlayerList: React.FC<PlayerListProps> = ({
  players
}) => {
  const getPlayerCardClass = (player: Player) => {
    let className = 'player-card';
    
    if (player.is_alive) {
      className += ' alive';
    } else {
      className += ' dead';
    }
    
    if (player.role === 'wolf') {
      className += ' wolf';
    } else if (player.is_god) {
      className += ' god';
    }
    
    return className;
  };

  const getPlayerStatusIcon = (player: Player) => {
    if (player.is_god) return '⭐';
    if (player.role === 'wolf') return '🐺';
    return '👤';
  };

  return (
    <div>
      <h3>Players ({players.length})</h3>
      
      <div style={{ marginBottom: '20px', textAlign: 'center', fontSize: '0.9em', opacity: '0.8' }}>
        👁️ <strong>Spectator Mode</strong> 👁️
        <br />
        Watch the AI agents play!
      </div>

      <div style={{ marginBottom: '20px' }}>
        {players.map(player => (
          <div key={player.id} className={getPlayerCardClass(player)}>
            <div className="player-name">
              {getPlayerStatusIcon(player)} {player.name}
            </div>
            <div className="player-status">
              {player.is_god ? 'Moderator (AI)' : 
               player.role ? `${player.role.toUpperCase()} (AI)` : 'AI Player'}
              {' • '}
              {player.is_alive ? 'Alive' : 'Dead'}
            </div>
          </div>
        ))}
      </div>
      
      <div style={{ fontSize: '0.8em', opacity: '0.7' }}>
        <p><strong>Legend:</strong></p>
        <p>⭐ AI Moderator/God</p>
        <p>🐺 AI Werewolf</p>
        <p>👤 AI Villager/Civilian</p>
        <p style={{ marginTop: '10px', fontStyle: 'italic' }}>
          All players are controlled by AI agents. You can see everyone's roles in spectator mode!
        </p>
      </div>
    </div>
  );
};

export default PlayerList;
