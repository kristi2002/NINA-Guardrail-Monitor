import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { Navigate, useNavigate } from 'react-router-dom';
import './Login.css';

function Login() {
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [failedAttempts, setFailedAttempts] = useState(0);
  const [lockoutUntil, setLockoutUntil] = useState(null);
  const [lockoutCountdown, setLockoutCountdown] = useState(0);
  
  const { login, isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();

  // Countdown timer for lockout
  useEffect(() => {
    let interval;
    if (lockoutUntil && new Date() < lockoutUntil) {
      interval = setInterval(() => {
        const now = new Date();
        if (now >= lockoutUntil) {
          setLockoutCountdown(0);
          setLockoutUntil(null);
          setFailedAttempts(0);
        } else {
          setLockoutCountdown(Math.ceil((lockoutUntil - now) / 1000));
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [lockoutUntil]);


  // Redirect if already authenticated
  if (isAuthenticated && !loading) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Check if account is locked out
    if (lockoutUntil && new Date() < lockoutUntil) {
      const secondsRemaining = Math.ceil((lockoutUntil - new Date()) / 1000);
      setError(t('login.errorLocked', { seconds: secondsRemaining }));
      return;
    }

    // Reset lockout if time has passed
    if (lockoutUntil && new Date() >= lockoutUntil) {
      setLockoutUntil(null);
      setFailedAttempts(0);
    }

    setError('');
    setIsLoading(true);

    // Basic validation
    if (!credentials.username || !credentials.password) {
      setError(t('login.errorRequiredFields'));
      setIsLoading(false);
      return;
    }

    try {
      const result = await login(credentials.username, credentials.password);
      
      if (result.success) {
        // Reset failed attempts on successful login
        setFailedAttempts(0);
        setLockoutUntil(null);
        // Success - AuthContext will handle the redirect via App.jsx
        navigate('/', { replace: true });
      } else {
        // Increment failed attempts
        const newFailedAttempts = failedAttempts + 1;
        setFailedAttempts(newFailedAttempts);
        
        // Security measures based on failed attempts
        if (newFailedAttempts >= 5) {
          // Lock account for 5 minutes after 5 failed attempts
          const lockoutTime = new Date(Date.now() + 5 * 60 * 1000);
          setLockoutUntil(lockoutTime);
          setError(t('login.errorLockedUntil', { time: lockoutTime.toLocaleTimeString() }));
        } else if (newFailedAttempts >= 3) {
          // Warning after 3 failed attempts
          setError(
            t('login.errorWarning', {
              message: result.error || t('login.errorDefault'),
              remaining: 4 - newFailedAttempts
            })
          );
        } else {
          setError(
            t('login.errorFailed', {
              message: result.error || t('login.errorDefault')
            })
          );
        }
      }
    } catch (err) {
      // Increment failed attempts for network errors too
      const newFailedAttempts = failedAttempts + 1;
      setFailedAttempts(newFailedAttempts);
      setError(t('login.errorUnexpected'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setCredentials(prev => ({
      ...prev,
      [name]: value
    }));
    // Error is cleared in handleSubmit, so it won't vanish immediately
  };


  if (loading) {
    return (
      <div className="login-loading">
        <div className="loading-spinner"></div>
        <p>{t('login.initializing')}</p>
      </div>
    );
  }

  return (
    <div className="login-container">
      <div className="login-background">
        <div className="security-pattern"></div>
      </div>
      
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo">
            <img src="/favicon.svg" alt="NINA Logo" className="logo-icon" />
            <h1>{t('app.title')}</h1>
            <p className="login-subtitle">{t('login.subtitle')}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">{t('login.usernameLabel')}</label>
            <input
              type="text"
              id="username"
              name="username"
              value={credentials.username}
              onChange={handleInputChange}
              placeholder={t('login.usernamePlaceholder')}
              disabled={isLoading}
              autoComplete="username"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">{t('login.passwordLabel')}</label>
            <div className="password-input">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={credentials.password}
                onChange={handleInputChange}
                placeholder={t('login.passwordPlaceholder')}
                disabled={isLoading}
                autoComplete="current-password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                disabled={isLoading}
              >
                {showPassword ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
          </div>

          {error && (
            <div className={`error-message ${failedAttempts >= 3 ? 'security-warning' : ''}`}>
              <span className="error-icon">
                {failedAttempts >= 5 ? '🔒' : failedAttempts >= 3 ? '⚠️' : '⚠️'}
              </span>
              {error}
            </div>
          )}

          {failedAttempts > 0 && failedAttempts < 5 && (
            <div className="attempts-warning">
              <span className="warning-icon">🛡️</span>
              <span className="warning-text">
                {t('login.attemptsStatus', { count: failedAttempts })}
                {failedAttempts >= 3 && (
                  <span className="lockout-warning">
                    {' '}• {t('login.lockoutWarning', { remaining: 5 - failedAttempts })}
                  </span>
                )}
              </span>
            </div>
          )}

          {lockoutUntil && new Date() < lockoutUntil && (
            <div className="lockout-status">
              <span className="lockout-icon">🔒</span>
              <span className="lockout-text">
                {t('login.lockoutStatus', {
                  minutes: Math.floor(lockoutCountdown / 60),
                  seconds: (lockoutCountdown % 60).toString().padStart(2, '0')
                })}
              </span>
            </div>
          )}

          <button
            type="submit"
            className="login-button"
            disabled={isLoading || (lockoutUntil && new Date() < lockoutUntil)}
          >
            {isLoading ? (
              <>
                <span className="loading-spinner small"></span>
                {t('login.buttonAuthenticating')}
              </>
            ) : (
              <>
                🔐 {t('login.buttonSignIn')}
              </>
            )}
          </button>
        </form>


        <div className="login-footer">
          <div className="security-notice">
            <span className="security-icon">🔒</span>
            <div className="security-text">
              <strong>{t('login.securityHeading')}</strong>
              <br />
              {t('login.securityDetails')}
            </div>
          </div>
        </div>
      </div>

      <div className="login-features">
        <div className="feature">
          <span className="feature-icon">🛡️</span>
          <div className="feature-text">
            <strong>{t('login.featureAuthenticationTitle')}</strong>
            <p>{t('login.featureAuthenticationDescription')}</p>
          </div>
        </div>
        <div className="feature">
          <span className="feature-icon">📊</span>
          <div className="feature-text">
            <strong>{t('login.featureMonitoringTitle')}</strong>
            <p>{t('login.featureMonitoringDescription')}</p>
          </div>
        </div>
        <div className="feature">
          <span className="feature-icon">🏥</span>
          <div className="feature-text">
            <strong>{t('login.featureHealthcareTitle')}</strong>
            <p>{t('login.featureHealthcareDescription')}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;
