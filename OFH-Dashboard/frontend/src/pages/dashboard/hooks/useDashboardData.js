/**
 * Dashboard Data Hook
 * Manages all data fetching and real-time subscriptions for Dashboard
 */
import { useState, useEffect } from 'react'
import axios from 'axios'
import { notificationService } from '../../../services/notifications'

export function useDashboardData() {
  const [metrics, setMetrics] = useState(null)
  const [error, setError] = useState(null)
  const [conversations, setConversations] = useState([])
  const [lastUpdated, setLastUpdated] = useState(new Date())
  const [realtimeActive, setRealtimeActive] = useState(false)
  const [previousMetrics, setPreviousMetrics] = useState(null)

  const fetchMetrics = async (signal) => {
    try {
      const response = await axios.get('/api/metrics', { signal })
      const currentData = response.data
      
      if (metrics) {
        setPreviousMetrics(metrics)
      }
      
      setMetrics(currentData)
      setLastUpdated(new Date())
    } catch (err) {
      if (err.name !== 'CanceledError' && !axios.isCancel(err)) {
        console.error('Failed to load metrics:', err)
        setError('Failed to load metrics. Make sure the backend is running.')
      }
    }
  }

  const fetchConversations = async (signal) => {
    try {
      const response = await axios.get('/api/conversations', { signal })
      setConversations(response.data.conversations || [])
      console.log('📞 Fetched conversations:', response.data.conversations?.length || 0)
    } catch (err) {
      if (err.name !== 'CanceledError' && !axios.isCancel(err)) {
        console.error('Failed to load conversations:', err)
        setConversations([])
      }
    }
  }

  useEffect(() => {
    const controller = new AbortController()
    const signal = controller.signal
    let isMounted = true

    fetchMetrics(signal)
    fetchConversations(signal)
    
    // Connect to WebSocket (only if not already connected)
    // The notificationService will handle duplicate connection attempts
    notificationService.connect().then(() => {
      if (isMounted) {
        console.log('✅ Connected to notification service')
      }
    }).catch(err => {
      if (isMounted) {
        console.error('❌ Failed to connect to notification service:', err)
      }
    })
    
    // Subscribe to notifications
    const unsubscribeNotification = notificationService.subscribe('notification', (data) => {
      if (isMounted) {
        console.log('🔔 Received notification:', data)
        fetchMetrics()
        fetchConversations()
      }
    })
    
    // Subscribe to alert escalations
    const unsubscribeEscalation = notificationService.subscribe('alert_escalation', (data) => {
      if (isMounted) {
        console.log('🚨 Alert escalated:', data)
        fetchMetrics()
        fetchConversations()
      }
    })
    
    // Subscribe to system status updates
    const unsubscribeStatus = notificationService.subscribe('system_status', (data) => {
      if (isMounted) {
        console.log('📡 System status update:', data)
        setMetrics(data)
        setLastUpdated(new Date())
        setRealtimeActive(true)
      }
    })

    const unsubscribeGuardrail = notificationService.subscribe('guardrail_event', (data) => {
      if (isMounted) {
        console.log('🛡️ Guardrail event push:', data)
        fetchMetrics()
        fetchConversations()
      }
    })

    const unsubscribeOperator = notificationService.subscribe('operator_action', (data) => {
      if (isMounted) {
        console.log('🕹️ Operator action push:', data)
        fetchMetrics()
        fetchConversations()
      }
    })
    
    // Fallback: Refresh metrics every 30 seconds if no real-time updates
    const interval = setInterval(() => {
      if (isMounted && !notificationService.isConnected) {
        fetchMetrics()
        fetchConversations()
      }
    }, 30000)
    
    return () => {
      isMounted = false
      console.log('🧹 Cleaning up Dashboard: aborting requests...')
      controller.abort()
      clearInterval(interval)
      unsubscribeNotification()
      unsubscribeEscalation()
      unsubscribeStatus()
      unsubscribeGuardrail()
      unsubscribeOperator()
      // Note: We don't disconnect the notification service here because it's a singleton
      // that might be used by other components. It will be cleaned up when the app unmounts.
    }
  }, [])

  return {
    metrics,
    error,
    conversations,
    lastUpdated,
    realtimeActive,
    previousMetrics,
    fetchMetrics,
    fetchConversations
  }
}

