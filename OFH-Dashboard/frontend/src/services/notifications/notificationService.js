import { io } from 'socket.io-client'
import axios from 'axios'

class NotificationService {
  constructor() {
    this.socket = null
    this.listeners = new Map()
    this.isConnected = false
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 1000
    // For Socket.IO, use the Vite proxy path which handles WebSocket upgrades properly
    // The proxy is configured in vite.config.js to forward /socket.io to the backend
    // Use relative path to go through Vite dev server proxy, or absolute URL if VITE_API_URL is set
    this.baseURL = import.meta.env.VITE_API_URL || window.location.origin
  }

  connect() {
    // If already connected, return resolved promise
    if (this.isConnected && this.socket?.connected) {
      console.log('🔔 Notification service already connected, reusing existing connection')
      return Promise.resolve()
    }

    // If socket exists but not connected, disconnect first
    if (this.socket && !this.socket.connected) {
      console.log('🔔 Cleaning up previous socket connection')
      this.socket.disconnect()
      this.socket = null
    }

    // Connect to real WebSocket server through Vite proxy
    return new Promise((resolve, reject) => {
      try {
        // Use the baseURL (which goes through Vite proxy) for Socket.IO connection
        // The proxy will handle WebSocket upgrades properly
        this.socket = io(this.baseURL, {
          path: '/socket.io',  // Explicitly set Socket.IO path
          transports: ['polling', 'websocket'],  // Try polling first, then upgrade to websocket
          reconnection: true,
          reconnectionDelay: this.reconnectDelay,
          reconnectionAttempts: this.maxReconnectAttempts,
          timeout: 20000,  // 20 second timeout
          forceNew: false,  // Reuse connection if available
          autoConnect: true,
          withCredentials: true  // Include credentials for CORS
        })

        this.socket.on('connect', () => {
          console.log('🔔 Notification service connected')
          this.isConnected = true
          this.reconnectAttempts = 0
          resolve()
        })

        // Handle disconnection gracefully
        this.socket.on('disconnect', (reason) => {
          this.isConnected = false
          // Only log unexpected disconnections
          if (reason !== 'io server disconnect' && reason !== 'transport close') {
            if (import.meta.env.DEV) {
              console.log('🔔 Notification service disconnected:', reason)
            }
          }
        })

        this.socket.on('connect_error', (error) => {
          // Connection errors are normal during development (server restarts, etc.)
          // Only log unexpected errors, not connection resets
          if (import.meta.env.DEV && error.message && !error.message.includes('xhr poll error')) {
            // Suppress common connection reset errors
            const isConnectionReset = error.message.includes('ECONNRESET') || 
                                     error.message.includes('ECONNREFUSED') ||
                                     error.message.includes('connection closed')
            if (!isConnectionReset) {
              console.warn('🔔 Socket.IO connection error:', error.message || error)
            }
          }
          // Don't reject on initial connect - let it retry in background
          this.handleReconnect()
        })

        // Listen for notifications from backend
        this.socket.on('notification', (data) => {
          this.handleNotification(data)
        })

        this.socket.on('alert_escalation', (data) => {
          this.handleAlertEscalation(data)
        })

        this.socket.on('system_status', (data) => {
          this.handleSystemStatus(data)
        })

        this.socket.on('guardrail_event', (data) => {
          this.handleGuardrailEvent(data)
        })

        this.socket.on('operator_action', (data) => {
          this.handleOperatorAction(data)
        })

        this.socket.on('guardrail_control', (data) => {
          this.handleGuardrailControl(data)
        })

      } catch (error) {
        console.error('🔔 Failed to connect:', error)
        reject(error)
      }
    })
  }

  handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('🔔 Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    
    console.log(`🔔 Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`)
    
    setTimeout(() => {
      this.connect().catch(() => {
        // Reconnection failed, will try again
      })
    }, delay)
  }

  handleNotification(data) {
    console.log('🔔 Received notification:', data)
    this.notifyListeners('notification', data)
  }

  handleAlertEscalation(data) {
    console.log('🔔 Alert escalated:', data)
    this.notifyListeners('alert_escalation', data)
  }

  handleSystemStatus(data) {
    console.log('🔔 System status update:', data)
    this.notifyListeners('system_status', data)
  }

  handleGuardrailEvent(data) {
    console.log('🛡️ Guardrail event received:', data)
    this.notifyListeners('guardrail_event', data)
  }

  handleOperatorAction(data) {
    console.log('🕹️ Operator action received:', data)
    this.notifyListeners('operator_action', data)
  }

  handleGuardrailControl(data) {
    console.log('🎛️ Guardrail control feedback:', data)
    this.notifyListeners('guardrail_control', data)
  }

  notifyListeners(event, data) {
    const listeners = this.listeners.get(event) || []
    listeners.forEach(callback => {
      try {
        callback(data)
      } catch (error) {
        console.error('🔔 Error in notification listener:', error)
      }
    })
  }

  subscribe(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event).push(callback)

    // Return unsubscribe function
    return () => {
      const listeners = this.listeners.get(event) || []
      const index = listeners.indexOf(callback)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }

  unsubscribe(event, callback) {
    const listeners = this.listeners.get(event) || []
    const index = listeners.indexOf(callback)
    if (index > -1) {
      listeners.splice(index, 1)
    }
  }

  async sendNotification(notification) {
    try {
      const response = await axios.post('/api/notifications/test', notification)
      console.log('🔔 Notification sent:', response.data)
      return response.data
    } catch (error) {
      console.error('🔔 Failed to send notification:', error)
      throw error
    }
  }

  async requestNotificationHistory(limit = 50) {
    try {
      const response = await axios.get(`/api/notifications/history?limit=${limit}`)
      if (response.data.success) {
        console.log(`🔔 Loaded ${response.data.notifications?.length || 0} notifications`)
        return response.data.notifications || []
      }
      return []
    } catch (error) {
      console.error('🔔 Failed to get notification history:', error)
      return []
    }
  }

  async getNotificationPreferences() {
    try {
      const response = await axios.get('/api/notifications/preferences')
      console.log('🔔 Preferences loaded successfully:', response.data)
      return response.data
    } catch (error) {
      console.error('🔔 Failed to load preferences:', error)
      throw error
    }
  }

  async updateNotificationPreferences(preferences) {
    try {
      const response = await axios.put('/api/notifications/preferences', preferences)
      console.log('🔔 Preferences updated successfully:', response.data)
      return response.data
    } catch (error) {
      console.error('🔔 Failed to update preferences:', error)
      throw error
    }
  }

  disconnect() {
    console.log('🔔 Notification service disconnected')
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
    this.isConnected = false
    this.listeners.clear()
  }

  getConnectionStatus() {
    return {
      connected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts
    }
  }
}

// Create singleton instance
const notificationService = new NotificationService()

export default notificationService
