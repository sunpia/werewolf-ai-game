import React, { useEffect, useState, useRef, useCallback } from 'react';
import axios from 'axios';
import { GameState, Player } from '../App';
import PlayerList from './PlayerList';
import ChatArea from './ChatArea';
import GameStatus from './GameStatus';
import UserProfile from './UserProfile';

interface GameRoomProps {
  gameId: string;
  gameState: GameState | null;
  onGameStateUpdate: (state: GameState) => void;
  onLeaveGame: () => void;
}

interface GameEvent {
  event_type: string;
  timestamp: string;
  data: any;
}

const GameRoom: React.FC<GameRoomProps> = ({
  gameId,
  gameState,
  onGameStateUpdate,
  onLeaveGame
}) => {
  const [players, setPlayers] = useState<Player[]>([]);
  const [messages, setMessages] = useState<any[]>([]);
  const [gameStarted, setGameStarted] = useState<boolean>(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const onGameStateUpdateRef = useRef(onGameStateUpdate);

  // Keep the ref updated with the latest onGameStateUpdate function
  useEffect(() => {
    onGameStateUpdateRef.current = onGameStateUpdate;
  }, [onGameStateUpdate]);

  const handleGameEvent = useCallback((event: GameEvent) => {
    switch (event.event_type) {
      case 'game_state_update':
        onGameStateUpdateRef.current({
          game_id: gameId,
          phase: event.data.phase,
          day_count: event.data.day_count,
          alive_players: event.data.alive_players,
          current_speaker: event.data.current_speaker,
          game_history: event.data.game_history,
          is_game_over: event.data.is_game_over,
          winner: event.data.winner
        });
        break;
      
      case 'player_action':
        if (event.data.action_type === 'speak' && event.data.message) {
          setMessages(prev => [...prev, {
            id: Date.now(),
            player: event.data.player,
            message: event.data.message,
            timestamp: event.timestamp,
            type: event.data.role === 'wolf' ? 'wolf' : event.data.role === 'god' ? 'god' : 'player'
          }]);
        } else if (event.data.action_type === 'vote') {
          setMessages(prev => [...prev, {
            id: Date.now(),
            message: event.data.message || `${event.data.player} voted`,
            timestamp: event.timestamp,
            type: 'system'
          }]);
        }
        break;
      
      case 'game_started':
        setGameStarted(true);
        setMessages(prev => [...prev, {
          id: Date.now(),
          message: 'Game has started!',
          timestamp: event.timestamp,
          type: 'system'
        }]);
        break;
      
      case 'phase_change':
        setMessages(prev => [...prev, {
          id: Date.now(),
          message: `Phase changed to ${event.data.new_phase}. Day ${event.data.day_count}`,
          timestamp: event.timestamp,
          type: 'system'
        }]);
        break;
      
      case 'speaker_turn':
        setMessages(prev => [...prev, {
          id: Date.now(),
          message: `It's ${event.data.speaker}'s turn to speak`,
          timestamp: event.timestamp,
          type: 'system'
        }]);
        break;
      
      default:
        // Handle other event types
        if (event.data.message) {
          setMessages(prev => [...prev, {
            id: Date.now(),
            message: event.data.message,
            timestamp: event.timestamp,
            type: 'system'
          }]);
        }
    }
  }, [gameId]);

  useEffect(() => {
    // Fetch initial players
    const fetchPlayersLocal = async () => {
      try {
        const response = await axios.get(`/api/v1/games/${gameId}/players`);
        setPlayers(response.data.players);
      } catch (error) {
        console.error('Failed to fetch players:', error);
      }
    };

    // Set up Server-Sent Events
    const setupEventStreamLocal = () => {
      const eventSource = new EventSource(`/api/v1/games/${gameId}/events`);
      eventSourceRef.current = eventSource;

      eventSource.onmessage = (event) => {
        try {
          const gameEvent: GameEvent = JSON.parse(event.data);
          handleGameEvent(gameEvent);
        } catch (error) {
          console.error('Failed to parse event:', error);
        }
      };

      eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
        // Attempt to reconnect after 5 seconds
        setTimeout(() => {
          if (eventSourceRef.current?.readyState === EventSource.CLOSED) {
            setupEventStreamLocal();
          }
        }, 5000);
      };
    };

    fetchPlayersLocal();
    setupEventStreamLocal();
    
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [gameId, handleGameEvent]); // Only depend on gameId and handleGameEvent

  const handleStartGame = async () => {
    try {
      await axios.post(`/api/v1/games/${gameId}/start`);
    } catch (error) {
      console.error('Failed to start game:', error);
    }
  };

  return (
    <div className="game-container">
      <div className="players-sidebar">
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ 
            margin: '0 0 16px 0', 
            fontSize: '1.3em', 
            fontWeight: '600',
            color: 'rgba(255, 255, 255, 0.9)'
          }}>
            🎯 Game: {gameId.slice(0, 8)}
          </h3>
          <button 
            onClick={onLeaveGame} 
            style={{ 
              marginBottom: '12px',
              width: '100%',
              padding: '12px 16px',
              background: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '8px',
              color: 'white',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              backdropFilter: 'blur(10px)'
            }}
            onMouseEnter={(e) => {
              const target = e.target as HTMLButtonElement;
              target.style.background = 'rgba(255, 255, 255, 0.2)';
              target.style.transform = 'translateY(-1px)';
            }}
            onMouseLeave={(e) => {
              const target = e.target as HTMLButtonElement;
              target.style.background = 'rgba(255, 255, 255, 0.1)';
              target.style.transform = 'translateY(0)';
            }}
          >
            ← Leave Game
          </button>
          {!gameStarted && (
            <button 
              onClick={handleStartGame}
              className="create-game-button"
              style={{ 
                padding: '12px 16px', 
                fontSize: '14px',
                width: '100%',
                background: 'linear-gradient(135deg, #4caf50, #45a049)',
                border: 'none',
                borderRadius: '8px',
                color: 'white',
                cursor: 'pointer',
                fontWeight: '600',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                boxShadow: '0 4px 16px rgba(76, 175, 80, 0.3)'
              }}
            >
              🚀 Start AI Battle
            </button>
          )}
        </div>
        
        <PlayerList players={players} />
      </div>
      
      <div className="main-game-area">
        <div className="game-header" style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '20px 24px',
          marginBottom: '24px',
          background: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(20px)',
          borderRadius: '16px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.1)'
        }}>
          <h1 style={{
            margin: 0,
            fontSize: '1.5em',
            fontWeight: '600',
            color: 'rgba(255, 255, 255, 0.95)'
          }}>
            Game Room
          </h1>
          <UserProfile />
        </div>
        
        <GameStatus gameState={gameState} />
        
        <ChatArea
          messages={messages}
          gameStarted={gameStarted}
        />
      </div>
    </div>
  );
};

export default GameRoom;
