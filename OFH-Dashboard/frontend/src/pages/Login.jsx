import { useState, useEffect } from 'react';
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
      setError(`Account temporarily locked. Try again in ${lockoutCountdown} seconds.`);
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
      setError('Please enter both username and password');
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
          setError(`Too many failed attempts. Account locked for 5 minutes. Try again at ${lockoutTime.toLocaleTimeString()}.`);
        } else if (newFailedAttempts >= 3) {
          // Warning after 3 failed attempts
          setError(`${result.error || 'Login failed'}. Warning: ${4 - newFailedAttempts} attempts remaining before account lockout.`);
        } else {
          setError(result.error || 'Login failed');
        }
      }
    } catch (err) {
      // Increment failed attempts for network errors too
      const newFailedAttempts = failedAttempts + 1;
      setFailedAttempts(newFailedAttempts);
      setError('An unexpected error occurred. Please try again.');
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
        <p>Initializing...</p>
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
            <h1>NINA Guardrail Monitor</h1>
            <p className="login-subtitle">Healthcare AI Security Dashboard</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="username"
              value={credentials.username}
              onChange={handleInputChange}
              placeholder="Enter your username"
              disabled={isLoading}
              autoComplete="username"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="password-input">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={credentials.password}
                onChange={handleInputChange}
                placeholder="Enter your password"
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
                Failed attempts: {failedAttempts}/5
                {failedAttempts >= 3 && (
                  <span className="lockout-warning">
                    {' '}• Account will be locked after {5 - failedAttempts} more failed attempts
                  </span>
                )}
              </span>
            </div>
          )}

          {lockoutUntil && new Date() < lockoutUntil && (
            <div className="lockout-status">
              <span className="lockout-icon">🔒</span>
              <span className="lockout-text">
                Account Locked • Unlocks in {Math.floor(lockoutCountdown / 60)}:{(lockoutCountdown % 60).toString().padStart(2, '0')}
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
                Authenticating...
              </>
            ) : (
              <>
                🔐 Sign In
              </>
            )}
          </button>
        </form>


        <div className="login-footer">
          <div className="security-notice">
            <span className="security-icon">🔒</span>
            <div className="security-text">
              <strong>Secure Healthcare System</strong>
              <br />
              HIPAA compliant • End-to-end encryption • Audit logging
            </div>
          </div>
        </div>
      </div>

      <div className="login-features">
        <div className="feature">
          <span className="feature-icon">🛡️</span>
          <div className="feature-text">
            <strong>Secure Authentication</strong>
            <p>JWT authentication with secure session management</p>
          </div>
        </div>
        <div className="feature">
          <span className="feature-icon">📊</span>
          <div className="feature-text">
            <strong>Real-time Monitoring</strong>
            <p>Live guardrail violation tracking and alerts</p>
          </div>
        </div>
        <div className="feature">
          <span className="feature-icon">🏥</span>
          <div className="feature-text">
            <strong>Healthcare Ready</strong>
            <p>HIPAA compliance and audit trail support</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;
