import React, { useState } from 'react';
import GoogleSignIn from './GoogleSignIn';

interface LoginProps {
  onLoginSuccess: () => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [error, setError] = useState<string>('');

  const handleGoogleSuccess = () => {
    setError('');
    onLoginSuccess();
  };

  const handleGoogleError = (errorMessage: string) => {
    setError(errorMessage);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1 className="login-title">🐺 AI Werewolf Game</h1>
        <p className="login-subtitle">
          Sign in to access the ultimate AI gaming experience
        </p>
        
        {error && <div className="error-message">{error}</div>}
        
        <div className="login-content">
          <div className="auth-section">
            <h3>Sign in to Continue</h3>
            <p style={{ fontSize: '0.9em', opacity: '0.8', marginBottom: '1.5rem' }}>
              Choose your authentication method
            </p>
            <GoogleSignIn 
              onSuccess={handleGoogleSuccess}
              onError={handleGoogleError}
            />
          </div>
          
          <div className="login-features">
            <h3 style={{ marginBottom: '1rem', color: 'rgba(255, 255, 255, 0.9)' }}>
              🎮 What awaits you:
            </h3>
            <div className="feature-grid">
              <div className="feature-item">
                <span className="feature-icon">🤖</span>
                <div>
                  <strong>Advanced AI Agents</strong>
                  <p>Watch sophisticated AI strategies unfold</p>
                </div>
              </div>
              <div className="feature-item">
                <span className="feature-icon">🧠</span>
                <div>
                  <strong>Real-time Gameplay</strong>
                  <p>Experience dynamic AI decision-making</p>
                </div>
              </div>
              <div className="feature-item">
                <span className="feature-icon">👁️</span>
                <div>
                  <strong>Spectator Mode</strong>
                  <p>Enjoy the AI battle from front row seats</p>
                </div>
              </div>
              <div className="feature-item">
                <span className="feature-icon">⚡</span>
                <div>
                  <strong>Instant Access</strong>
                  <p>Jump right into the action</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
