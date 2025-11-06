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

        this.socket.on('disconnect', () => {
          console.log('🔔 Notification service disconnected')
          this.isConnected = false
        })

        this.socket.on('connect_error', (error) => {
          // Only log errors in development, and make them less noisy
          if (import.meta.env.DEV) {
            console.warn('🔔 Socket.IO connection error (this is normal if backend is not running):', error.message || error)
          }
          // Don't reject on initial connect - let it retry in background
          this.handleReconnect()
          // Only reject if this was the initial connection attempt
          if (this.reconnectAttempts === 0) {
            // Don't reject - let it retry silently
          }
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
      // API doesn't have a specific endpoint for notification history yet
      // Return empty array until it's implemented
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
