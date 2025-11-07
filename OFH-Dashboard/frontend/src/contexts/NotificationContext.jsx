import { createContext, useContext, useReducer, useEffect } from 'react'
import { notificationService } from '../services/notifications'
import { messagingService, escalationService } from '../services/api'
import { useAuth } from './AuthContext'

const NotificationContext = createContext()

// Notification reducer
const notificationReducer = (state, action) => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload }
    
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false }
    
    case 'CLEAR_ERROR':
      return { ...state, error: null }
    
    case 'SET_CONNECTION_STATUS':
      return { ...state, connectionStatus: action.payload }
    
    case 'ADD_NOTIFICATION':
      // Ensure the notification has required fields
      const newNotification = {
        ...action.payload,
        id: action.payload.id || `notif_${Date.now()}_${Math.random()}`,
        title: action.payload.title || action.payload.message || 'Notification',
        message: action.payload.message || action.payload.title || 'New notification',
        priority: action.payload.priority || action.payload.severity || 'info',
        timestamp: action.payload.timestamp || new Date().toISOString(),
        read: action.payload.read || false
      }
      return {
        ...state,
        notifications: [newNotification, ...state.notifications].slice(0, 100), // Keep last 100
        unreadCount: state.unreadCount + 1
      }
    
    case 'MARK_AS_READ':
      return {
        ...state,
        notifications: state.notifications.map(n => 
          n.id === action.payload ? { ...n, read: true } : n
        ),
        unreadCount: Math.max(0, state.unreadCount - 1)
      }
    
    case 'MARK_ALL_AS_READ':
      return {
        ...state,
        notifications: state.notifications.map(n => ({ ...n, read: true })),
        unreadCount: 0
      }
    
    case 'SET_NOTIFICATIONS':
      return {
        ...state,
        notifications: action.payload,
        unreadCount: action.payload.filter(n => !n.read).length
      }
    
    case 'SET_PREFERENCES':
      return { ...state, preferences: action.payload }
    
    case 'SET_ESCALATION_WORKFLOWS':
      return { ...state, escalationWorkflows: action.payload }
    
    case 'ADD_ESCALATION':
      return {
        ...state,
        escalations: [action.payload, ...state.escalations].slice(0, 50) // Keep last 50
      }
    
    case 'UPDATE_ESCALATION':
      return {
        ...state,
        escalations: state.escalations.map(e => 
          e.id === action.payload.id ? { ...e, ...action.payload } : e
        )
      }
    
    case 'SET_STATS':
      return { ...state, stats: action.payload }
    
    default:
      return state
  }
}

// Initial state
const initialState = {
  loading: false,
  error: null,
  connectionStatus: { connected: false, reconnectAttempts: 0 },
  notifications: [],
  unreadCount: 0,
  preferences: {
    email: { enabled: true, critical: true, warning: true, info: false },
    sms: { enabled: false, critical: true, warning: false, info: false },
    push: { enabled: true, critical: true, warning: true, info: true },
    webhook: { enabled: false, url: '', critical: true, warning: false, info: false },
    escalation: { enabled: true, autoEscalate: true, escalationDelay: 15, maxEscalations: 3 },
    quietHours: { enabled: false, start: '22:00', end: '08:00', timezone: 'UTC' }
  },
  escalationWorkflows: [],
  escalations: [],
  stats: {
    totalNotifications: 0,
    deliveryRate: 0,
    escalationRate: 0,
    responseTime: 0
  }
}

export const NotificationProvider = ({ children }) => {
  const [state, dispatch] = useReducer(notificationReducer, initialState)
  const { isAuthenticated } = useAuth()

  // Initialize notification service with delay to avoid blocking app startup
  useEffect(() => {
    // Only initialize if user is authenticated
    if (!isAuthenticated) {
      return
    }

    // Define cleanup functions at the top level
    let unsubscribeNotification = null
    let unsubscribeEscalation = null
    let unsubscribeSystemStatus = null

    const initializeService = async () => {
      // Add a small delay to let the app load first
      await new Promise(resolve => setTimeout(resolve, 100))
      
      try {
        dispatch({ type: 'SET_LOADING', payload: true })
        
        // Try to connect, but don't fail the app if it doesn't work
        try {
          await notificationService.connect()
          dispatch({ type: 'SET_CONNECTION_STATUS', payload: notificationService.getConnectionStatus() })
          
          // Subscribe to notification events and assign cleanup functions
          unsubscribeNotification = notificationService.subscribe('notification', (data) => {
            dispatch({ type: 'ADD_NOTIFICATION', payload: data })
          })
          
          unsubscribeEscalation = notificationService.subscribe('alert_escalation', (data) => {
            dispatch({ type: 'ADD_ESCALATION', payload: data })
          })
          
          unsubscribeSystemStatus = notificationService.subscribe('system_status', (data) => {
            dispatch({ type: 'SET_CONNECTION_STATUS', payload: data })
          })
        } catch (connectionError) {
          console.warn('Notification service connection failed, continuing without real-time notifications:', connectionError)
          dispatch({ type: 'SET_CONNECTION_STATUS', payload: { connected: false, reconnectAttempts: 0 } })
        }

        // Load initial data (these can work without WebSocket)
        try {
          await loadNotificationHistory()
        } catch (error) {
          console.warn('Failed to load notification history:', error)
        }
        
        try {
          await loadEscalationWorkflows()
        } catch (error) {
          console.warn('Failed to load escalation workflows:', error)
        }
        
        try {
          await loadStats()
        } catch (error) {
          console.warn('Failed to load stats:', error)
        }

        dispatch({ type: 'SET_LOADING', payload: false })
      } catch (error) {
        console.error('Failed to initialize notification service:', error)
        dispatch({ type: 'SET_ERROR', payload: 'Failed to connect to notification service' })
        dispatch({ type: 'SET_LOADING', payload: false })
      }
    }

    initializeService()

    // Return cleanup function synchronously
    return () => {
      if (unsubscribeNotification) unsubscribeNotification()
      if (unsubscribeEscalation) unsubscribeEscalation()
      if (unsubscribeSystemStatus) unsubscribeSystemStatus()
      notificationService.disconnect()
    }
  }, [isAuthenticated])

  // Load notification history
  const loadNotificationHistory = async () => {
    if (!isAuthenticated) {
      return
    }
    
    try {
      const notifications = await notificationService.requestNotificationHistory(50)
      dispatch({ type: 'SET_NOTIFICATIONS', payload: notifications })
    } catch (error) {
      console.error('Failed to load notification history:', error)
      // Set empty notifications if service fails
      dispatch({ type: 'SET_NOTIFICATIONS', payload: [] })
    }
  }

  // Load escalation workflows
  const loadEscalationWorkflows = async () => {
    if (!isAuthenticated) {
      return
    }
    
    try {
      const result = await escalationService.getEscalationWorkflows()
      if (result.success) {
        dispatch({ type: 'SET_ESCALATION_WORKFLOWS', payload: result.workflows })
      }
    } catch (error) {
      console.error('Failed to load escalation workflows:', error)
      // Set empty workflows if service fails
      dispatch({ type: 'SET_ESCALATION_WORKFLOWS', payload: [] })
    }
  }

  // Load statistics
  const loadStats = async () => {
    if (!isAuthenticated) {
      return
    }
    
    try {
      const [notificationStats, escalationStats] = await Promise.all([
        messagingService.getNotificationStats('24h'),
        escalationService.getEscalationStats('24h')
      ])
      
      dispatch({
        type: 'SET_STATS',
        payload: {
          totalNotifications: notificationStats.totalNotifications || 0,
          deliveryRate: notificationStats.deliveryRate || 0,
          escalationRate: escalationStats.escalationRate || 0,
          responseTime: escalationStats.avgResponseTime || 0
        }
      })
    } catch (error) {
      console.error('Failed to load stats:', error)
      // Set default stats if service fails
      dispatch({
        type: 'SET_STATS',
        payload: {
          totalNotifications: 0,
          deliveryRate: 0,
          escalationRate: 0,
          responseTime: 0
        }
      })
    }
  }

  // Send notification
  const sendNotification = async (notification) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true })
      const result = await notificationService.sendNotification(notification)
      dispatch({ type: 'SET_LOADING', payload: false })
      return result
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message })
      throw error
    }
  }

  // Update preferences
  const updatePreferences = async (preferences) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true })
      await notificationService.updateNotificationPreferences(preferences)
      dispatch({ type: 'SET_PREFERENCES', payload: preferences })
      dispatch({ type: 'SET_LOADING', payload: false })
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message })
      throw error
    }
  }

  // Mark notification as read
  const markAsRead = (notificationId) => {
    dispatch({ type: 'MARK_AS_READ', payload: notificationId })
  }

  // Mark all notifications as read
  const markAllAsRead = () => {
    dispatch({ type: 'MARK_ALL_AS_READ' })
  }

  // Trigger escalation
  const triggerEscalation = async (alertId, workflowId, options = {}) => {
    try {
      const result = await escalationService.triggerEscalation(alertId, workflowId, options)
      if (result.success) {
        dispatch({ type: 'ADD_ESCALATION', payload: result.escalation })
      }
      return result
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message })
      throw error
    }
  }

  // Test notification
  const testNotification = async (notification) => {
    try {
      const result = await messagingService.testNotification(notification)
      return result
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message })
      throw error
    }
  }

  // Clear error
  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' })
  }

  // Refresh data
  const refresh = async () => {
    await Promise.all([
      loadNotificationHistory(),
      loadEscalationWorkflows(),
      loadStats()
    ])
  }

  const value = {
    ...state,
    sendNotification,
    updatePreferences,
    markAsRead,
    markAllAsRead,
    triggerEscalation,
    testNotification,
    clearError,
    refresh
  }

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  )
}

export const useNotifications = () => {
  const context = useContext(NotificationContext)
  if (!context) {
    console.warn('useNotifications called outside NotificationProvider, returning default values')
    return {
      loading: false,
      error: null,
      connectionStatus: { connected: false, reconnectAttempts: 0 },
      notifications: [],
      unreadCount: 0,
      preferences: {
        email: { enabled: true, critical: true, warning: true, info: false },
        sms: { enabled: false, critical: true, warning: false, info: false },
        push: { enabled: true, critical: true, warning: true, info: true },
        webhook: { enabled: false, url: '', critical: true, warning: false, info: false },
        escalation: { enabled: true, autoEscalate: true, escalationDelay: 15, maxEscalations: 3 },
        quietHours: { enabled: false, start: '22:00', end: '08:00', timezone: 'UTC' }
      },
      escalationWorkflows: [],
      escalations: [],
      stats: {
        totalNotifications: 0,
        deliveryRate: 0,
        escalationRate: 0,
        responseTime: 0
      },
      sendNotification: () => Promise.resolve({ success: true }),
      updatePreferences: () => Promise.resolve(),
      markAsRead: () => {},
      markAllAsRead: () => {},
      triggerEscalation: () => Promise.resolve({ success: true }),
      testNotification: () => Promise.resolve({ success: true }),
      clearError: () => {},
      refresh: () => Promise.resolve()
    }
  }
  return context
}

export default NotificationContext
