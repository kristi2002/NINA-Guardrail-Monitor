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
    this.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:5000'
  }

  connect() {
    // Connect to real WebSocket server
    return new Promise((resolve, reject) => {
      try {
        this.socket = io(this.baseURL, {
          transports: ['websocket', 'polling'],
          reconnection: true,
          reconnectionDelay: this.reconnectDelay,
          reconnectionAttempts: this.maxReconnectAttempts
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
          console.error('🔔 Connection error:', error)
          this.handleReconnect()
          reject(error)
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
