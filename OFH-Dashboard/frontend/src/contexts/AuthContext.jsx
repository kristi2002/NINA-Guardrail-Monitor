import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService } from '../services/api';

const AuthContext = createContext();

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      if (authService.isAuthenticated()) {
        // Validate existing token
        const isValid = await authService.validateToken();
        if (isValid) {
          setUser(authService.getCurrentUser());
          setIsAuthenticated(true);
        }
      }
    } catch (error) {
      console.error('Auth initialization failed:', error);
      authService.logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    console.log('🔐 AuthContext: Login called with username:', username);
    setLoading(true);
    try {
      const result = await authService.login(username, password);
      console.log('🔐 AuthContext: AuthService returned:', result);
      
      // Defensive check: verify result exists and has success property
      if (result && result.success && result.user) {
        console.log('✅ AuthContext: Setting user and authenticated state');
        setUser(result.user);
        setIsAuthenticated(true);
        authService.logSecurityEvent('frontend_login_success', {
          username: result.user.username || username
        });
      } else {
        // Login failed - result.success is false or result.user is missing
        const errorMessage = result?.error || 'Login failed';
        console.error('❌ AuthContext: Login failed:', errorMessage);
        // Don't set user or authenticated state on failure
      }
      
      setLoading(false);
      return result || { success: false, error: 'No response from authentication service' };
    } catch (error) {
      console.error('❌ AuthContext: Login exception:', error);
      setLoading(false);
      authService.logSecurityEvent('frontend_login_error', { error: error.message });
      return { success: false, error: error.message || 'An unexpected error occurred' };
    }
  };

  const logout = useCallback(() => {
    authService.logSecurityEvent('frontend_logout', {
      username: user?.username
    });
    
    authService.logout();
    setUser(null);
    setIsAuthenticated(false);
  }, [user]);

  const refreshAuth = async () => {
    const isValid = await authService.validateToken();
    if (isValid) {
      setUser(authService.getCurrentUser());
      setIsAuthenticated(true);
    } else {
      setUser(null);
      setIsAuthenticated(false);
    }
    return isValid;
  };

  // Auto-refresh token if needed
  useEffect(() => {
    if (isAuthenticated) {
      const interval = setInterval(async () => {
        try {
          await authService.refreshTokenIfNeeded();
        } catch (error) {
          console.error('Token refresh failed:', error);
          logout();
        }
      }, 5 * 60 * 1000); // Check every 5 minutes

      return () => clearInterval(interval);
    }
  }, [isAuthenticated, logout]);

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    logout,
    refreshAuth,
    
    // Token management
    getTokenExpiry: () => authService.getTokenExpiry(),
    isTokenExpiringSoon: (minutes) => authService.isTokenExpiringSoon(minutes)
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
