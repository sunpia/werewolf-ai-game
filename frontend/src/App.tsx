import React, { useState } from 'react';
import './index.css';
import GameLobby from './components/GameLobby';
import GameRoom from './components/GameRoom';

export interface Player {
  id: number;
  name: string;
  is_alive: boolean;
  is_god: boolean;
  role?: string;
}

export interface GameState {
  game_id: string;
  phase: string;
  day_count: number;
  alive_players: Player[];
  current_speaker: string | null;
  game_history: string[];
  is_game_over: boolean;
  winner: string | null;
}

const App: React.FC = () => {
  const [gameId, setGameId] = useState<string | null>(null);
  const [gameState, setGameState] = useState<GameState | null>(null);

  const handleGameCreated = (id: string, state: GameState) => {
    setGameId(id);
    setGameState(state);
  };

  const handleGameStateUpdate = (state: GameState) => {
    setGameState(state);
  };

  const handleLeaveGame = () => {
    setGameId(null);
    setGameState(null);
  };

  return (
    <div className="App">
      {!gameId ? (
        <GameLobby onGameCreated={handleGameCreated} />
      ) : (
        <GameRoom
          gameId={gameId}
          gameState={gameState}
          onGameStateUpdate={handleGameStateUpdate}
          onLeaveGame={handleLeaveGame}
        />
      )}
    </div>
  );
};

export default App;
