import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../contexts/AuthContext';
import './UserProfile.css';

function UserProfile({ isDropdownOpen, onClose }) {
  const { user, logout, getTokenExpiry, isTokenExpiringSoon } = useAuth();
  const [timeUntilExpiry, setTimeUntilExpiry] = useState('');
  const { t } = useTranslation();

  useEffect(() => {
    const updateTokenTimer = () => {
      const expiry = getTokenExpiry();
      if (expiry) {
        const now = new Date();
        const diff = expiry.getTime() - now.getTime();
        
        if (diff > 0) {
          const hours = Math.floor(diff / (1000 * 60 * 60));
          const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
          setTimeUntilExpiry(`${hours}h ${minutes}m`);
        } else {
          setTimeUntilExpiry('expired');
        }
      }
    };

    updateTokenTimer();
    const interval = setInterval(updateTokenTimer, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [getTokenExpiry]);

  // Add click-outside-to-close functionality
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isDropdownOpen) {
        // Check if click is outside the dropdown and not on the user info button
        const dropdown = document.querySelector('.user-profile-dropdown');
        const userInfo = document.querySelector('.user-info-compact');
        
        if (dropdown && 
            !dropdown.contains(event.target) && 
            !userInfo?.contains(event.target)) {
          onClose();
        }
      }
    };

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen, onClose]);

  const handleLogout = () => {
    logout();
    onClose();
  };

  const getUserIcon = () => {
    return '👤';
  };

  if (!isDropdownOpen) return null;

  return (
    <>
      <div className="user-profile-dropdown" onClick={(e) => e.stopPropagation()}>
        <div className="user-profile-header">
          <div className="user-avatar">
            {getUserIcon()}
          </div>
          <div className="user-info">
            <div className="user-name">{user.username}</div>
            <div className="user-email">{user.email}</div>
          </div>
        </div>

        <div className="session-info">
          <div className="session-item">
            <span className="session-label">{t('user.tokenExpiresIn')}</span>
            <span className={`session-value ${isTokenExpiringSoon() ? 'expiring' : ''}`}>
              {timeUntilExpiry === 'expired' ? t('user.sessionExpired') : timeUntilExpiry}
            </span>
          </div>
          
          {isTokenExpiringSoon() && (
            <div className="expiry-warning">
              <span className="warning-icon">⚠️</span>
              {t('user.sessionExpiring')}
            </div>
          )}
        </div>

        <div className="user-profile-actions">
          <button 
            className="profile-action-btn logout"
            onClick={handleLogout}
          >
            <span className="action-icon">🚪</span>
            {t('user.signOut')}
          </button>
        </div>

        <div className="profile-footer">
          <div className="security-status">
            <span className="status-icon">🛡️</span>
            <span className="status-text">{t('user.secureSessionActive')}</span>
          </div>
        </div>
      </div>
    </>
  );
}

// Compact user info for the navbar
export function UserInfo({ onClick }) {
  const { user, isTokenExpiringSoon } = useAuth();
  const { t } = useTranslation();

  if (!user) return null;

  const getUserIcon = () => {
    return '👤';
  };

  return (
    <div className="user-info-compact" onClick={onClick}>
      <div className="user-avatar-compact">
        {getUserIcon()}
      </div>
      <div className="user-details-compact">
        <div className="user-name-compact">{user.username}</div>
        <div className={`user-status-compact ${isTokenExpiringSoon() ? 'expiring' : ''}`}>
          {t('user.role')}
          {isTokenExpiringSoon() && <span className="expiry-indicator">⚠️</span>}
        </div>
      </div>
      <div className="dropdown-arrow">▼</div>
    </div>
  );
}

export default UserProfile;
