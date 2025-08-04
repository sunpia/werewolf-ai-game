import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

const UserProfile: React.FC = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const [showMenu, setShowMenu] = useState(false);

  if (!isAuthenticated || !user) {
    return null;
  }

  const handleLogout = () => {
    logout();
    setShowMenu(false);
  };

  return (
    <div className="user-profile">
      <div 
        className="user-avatar"
        onClick={() => setShowMenu(!showMenu)}
      >
        {user.picture ? (
          <img 
            src={user.picture} 
            alt={user.name}
            className="avatar-image"
          />
        ) : (
          <div className="avatar-placeholder">
            {user.name.charAt(0).toUpperCase()}
          </div>
        )}
        <span className="user-name">{user.name}</span>
        <span className="dropdown-arrow">▼</span>
      </div>
      
      {showMenu && (
        <div className="user-menu">
          <div className="user-info">
            <div className="user-details">
              <strong>{user.name}</strong>
              <div className="user-email">{user.email}</div>
              <div className="user-provider">via {user.provider}</div>
            </div>
          </div>
          <div className="menu-divider"></div>
          <button 
            className="logout-button"
            onClick={handleLogout}
          >
            🚪 Sign Out
          </button>
        </div>
      )}
    </div>
  );
};

export default UserProfile;
