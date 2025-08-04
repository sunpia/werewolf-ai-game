import React, { useRef, useEffect } from 'react';

interface Message {
  id: number;
  player?: string;
  message: string;
  timestamp: string;
  type: 'player' | 'system' | 'wolf' | 'god';
}

interface ChatAreaProps {
  messages: Message[];
  gameStarted: boolean;
}

const ChatArea: React.FC<ChatAreaProps> = ({
  messages,
  gameStarted
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const getMessageClass = (message: Message) => {
    return `message ${message.type}`;
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getMessagePrefix = (message: Message) => {
    if (message.type === 'system') return '🎮 System';
    if (message.type === 'god') return '⭐ AI God';
    if (message.type === 'wolf') return '🐺 AI Wolf';
    return '👤 AI Player';
  };

  return (
    <div className="chat-area">
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div style={{ textAlign: 'center', opacity: '0.6', fontStyle: 'italic' }}>
            {gameStarted ? 'AI agents are thinking... Messages will appear here.' : 'Waiting for game to start...'}
          </div>
        ) : (
          messages.map(message => (
            <div key={message.id} className={getMessageClass(message)}>
              <div style={{ fontSize: '0.8em', opacity: '0.7', marginBottom: '5px' }}>
                {getMessagePrefix(message)} {message.player && `${message.player}`} • {formatTimestamp(message.timestamp)}
              </div>
              <div style={{ wordWrap: 'break-word' }}>
                {message.message}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatArea;
