import axios from 'axios';

class AuthService {
  constructor() {
    this.token = localStorage.getItem('nina_token');
    this.user = JSON.parse(localStorage.getItem('nina_user') || 'null');
    this.setupAxiosInterceptors();
  }

  setupAxiosInterceptors() {
    // Request interceptor to add token to headers
    axios.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('nina_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle token expiration
    axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Don't redirect if already on login page or if it's a logout request
          const isLoginPage = window.location.pathname === '/login';
          const isLogoutRequest = error.config?.url?.includes('/logout');
          
          if (!isLoginPage && !isLogoutRequest) {
            // Only clear auth data and redirect if we're not already logging out
            const token = localStorage.getItem('nina_token');
            if (token) {
              this.logout();
              // Use setTimeout to avoid WSGI write() errors during redirect
              setTimeout(() => {
                window.location.href = '/login';
              }, 100);
            }
          }
        }
        return Promise.reject(error);
      }
    );
  }

  async login(username, password) {
    try {
      console.log('🔐 AuthService: Attempting login for username:', username);
      console.log('🔐 AuthService: Making request to /api/auth/login');
      
      const response = await axios.post('/api/auth/login', {
        username,
        password
      });

      console.log('🔐 AuthService: Response received:', response.status, response.data);

      if (response.data.token) {
        // Store token and user data
        localStorage.setItem('nina_token', response.data.token);
        localStorage.setItem('nina_user', JSON.stringify(response.data.user));
        
        this.token = response.data.token;
        this.user = response.data.user;

        console.log('✅ AuthService: Login successful for user:', response.data.user.username);
        
        return {
          success: true,
          user: response.data.user,
          expiresIn: response.data.expires_in
        };
      } else {
        console.error('❌ AuthService: No token in response');
        return {
          success: false,
          error: 'No authentication token received'
        };
      }
    } catch (error) {
      console.error('❌ AuthService: Login error:', error);
      console.error('❌ AuthService: Error response:', error.response?.data);
      console.error('❌ AuthService: Error status:', error.response?.status);
      
      // Extract error message from backend response
      // Backend returns: { success: false, error: 'error_type', message: 'Detailed message' }
      const errorMessage = error.response?.data?.message || 
                          error.response?.data?.error || 
                          error.message || 
                          'Login failed';
      
      return {
        success: false,
        error: errorMessage,
        errorType: error.response?.data?.error // Include error type if available
      };
    }
  }

  async validateToken() {
    try {
      if (!this.token) return false;

      const response = await axios.get('/api/auth/validate');
      
      if (response.data.valid) {
        this.user = response.data.user;
        localStorage.setItem('nina_user', JSON.stringify(response.data.user));
        return true;
      } else {
        this.logout();
        return false;
      }
    } catch (error) {
      console.error('Token validation failed:', error);
      this.logout();
      return false;
    }
  }

  logout() {
    console.log('🔐 Logging out...');
    
    // Clear stored data
    localStorage.removeItem('nina_token');
    localStorage.removeItem('nina_user');
    
    this.token = null;
    this.user = null;
    
    console.log('✅ Logout completed');
  }

  isAuthenticated() {
    return !!this.token && !!this.user;
  }

  getCurrentUser() {
    return this.user;
  }


  getTokenExpiry() {
    if (!this.token) return null;
    
    try {
      const payload = JSON.parse(atob(this.token.split('.')[1]));
      return new Date(payload.exp * 1000);
    } catch {
      return null;
    }
  }

  isTokenExpiringSoon(minutesThreshold = 10) {
    const expiry = this.getTokenExpiry();
    if (!expiry) return false;
    
    const now = new Date();
    const timeUntilExpiry = expiry.getTime() - now.getTime();
    const thresholdMs = minutesThreshold * 60 * 1000;
    
    return timeUntilExpiry < thresholdMs;
  }

  async refreshTokenIfNeeded() {
    if (this.isTokenExpiringSoon()) {
      console.log('⚠️ Token expiring soon, validating...');
      return await this.validateToken();
    }
    return true;
  }

  // Security monitoring
  logSecurityEvent(eventType, details = {}) {
    console.log(`🔒 Security Event: ${eventType}`, details);
    // In production, you might want to send this to a security monitoring endpoint
  }
}

// Create singleton instance
const authService = new AuthService();

export default authService;
