import React, { useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

declare global {
  interface Window {
    google: any;
    handleCredentialResponse?: (response: any) => void;
  }
}

interface GoogleSignInProps {
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

const GoogleSignIn: React.FC<GoogleSignInProps> = ({ onSuccess, onError }) => {
  const { login } = useAuth();

  const handleCredentialResponse = useCallback(async (response: any) => {
    try {
      const success = await login(response.credential);
      if (success) {
        onSuccess?.();
      } else {
        onError?.('Login failed. Please try again.');
      }
    } catch (error) {
      console.error('Login error:', error);
      onError?.('An error occurred during login.');
    }
  }, [login, onSuccess, onError]);

  useEffect(() => {
    // Load Google Sign-In script
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);

    script.onload = () => {
      if (window.google) {
        window.google.accounts.id.initialize({
          client_id: process.env.REACT_APP_GOOGLE_CLIENT_ID || 'your-google-client-id',
          callback: handleCredentialResponse,
        });

        window.google.accounts.id.renderButton(
          document.getElementById('google-signin-button'),
          {
            size: 'large',
            type: 'icon',
            shape: 'circle',
            logo_alignment: 'center',
            width: 60,
          }
        );
      }
    };

    return () => {
      document.head.removeChild(script);
    };
  }, [handleCredentialResponse]);

  // Make the handler available globally for Google's callback
  useEffect(() => {
    window.handleCredentialResponse = handleCredentialResponse;
    return () => {
      delete window.handleCredentialResponse;
    };
  }, [handleCredentialResponse]);

  return (
    <div className="google-signin-container">
      <div id="google-signin-button"></div>
    </div>
  );
};

export default GoogleSignIn;
