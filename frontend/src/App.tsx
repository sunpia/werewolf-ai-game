import React, { useState } from 'react';
import './index.css';
import GameLobby from './components/GameLobby';
import GameRoom from './components/GameRoom';
import Login from './components/Login';
import UserProfile from './components/UserProfile';
import { AuthProvider, useAuth } from './contexts/AuthContext';

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

const AppContent: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();
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

  const handleLoginSuccess = () => {
    // Login successful, component will re-render with isAuthenticated = true
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="App">
      <header className="app-header">
        <UserProfile />
      </header>
      
      <main className="app-main">
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
      </main>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
