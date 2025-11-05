import { useState, useEffect, useMemo } from 'react'
import axios from 'axios'
import MetricCard from '../components/MetricCard'
import MetricCardSkeleton from '../components/MetricCardSkeleton'
import GuardrailChart from '../components/GuardrailChart'
import ConversationList from '../components/ConversationList'
import ConversationListSkeleton from '../components/ConversationListSkeleton'
import ConversationStatus from '../components/ConversationStatus'
import ConversationStatusSkeleton from '../components/ConversationStatusSkeleton'
import Sidebar from '../components/Sidebar'
import TimeAgo from '../components/TimeAgo'
import notificationService from '../services/notificationService'
import './Dashboard.css'

function Dashboard() {
  const [metrics, setMetrics] = useState(null)
  const [error, setError] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [conversations, setConversations] = useState([])
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(new Date())
  const [realtimeActive, setRealtimeActive] = useState(false)
  const [previousMetrics, setPreviousMetrics] = useState(null)

  useEffect(() => {
    // 1. Create an AbortController
    const controller = new AbortController()
    const signal = controller.signal

    // 2. Pass the signal to your fetch functions
    fetchMetrics(signal)
    fetchAlerts(signal)
    fetchConversations(signal)
    
    // Connect to WebSocket (this is already async, which is good)
    notificationService.connect().then(() => {
      console.log('✅ Connected to notification service')
    }).catch(err => {
      console.error('❌ Failed to connect to notification service:', err)
    })
    
    // Subscribe to notifications (covers guardrail events)
    const unsubscribeNotification = notificationService.subscribe('notification', (data) => {
      console.log('🔔 Received notification:', data)
      // Refresh alerts when new event arrives (no signal needed for these - they're user-triggered)
      fetchAlerts()
      fetchConversations()
    })
    
    // Subscribe to alert escalations (for high/critical events)
    const unsubscribeEscalation = notificationService.subscribe('alert_escalation', (data) => {
      console.log('🚨 Alert escalated:', data)
      fetchAlerts()
      fetchConversations()
    })
    
    // Subscribe to system status updates
    const unsubscribeStatus = notificationService.subscribe('system_status', (data) => {
      console.log('📡 System status update:', data)
      setMetrics(data)
      setLastUpdated(new Date())
      setRealtimeActive(true)
    })
    
    // Fallback: Refresh metrics every 30 seconds if no real-time updates
    const interval = setInterval(() => {
      if (!notificationService.isConnected) {
        fetchMetrics()
        fetchAlerts()
        fetchConversations()
      }
    }, 30000)
    
    // 3. Return a cleanup function
    return () => {
      // This runs on unmount
      console.log('🧹 Cleaning up Dashboard: aborting requests...')
      controller.abort() // This cancels all 3 pending requests
      
      clearInterval(interval)
      unsubscribeNotification()
      unsubscribeEscalation()
      unsubscribeStatus()
    }
  }, [])

  const fetchMetrics = async (signal) => {
    try {
      // Pass the signal to axios
      const response = await axios.get('/api/metrics', { signal })
      const currentData = response.data
      
      // Store previous metrics for trend calculation
      if (metrics) {
        setPreviousMetrics(metrics)
      }
      
      setMetrics(currentData)
      setLastUpdated(new Date())
    } catch (err) {
      // Don't set an error if the request was intentionally aborted
      if (err.name !== 'CanceledError' && !axios.isCancel(err)) {
        console.error('Failed to load metrics:', err)
        setError('Failed to load metrics. Make sure the backend is running.')
      }
    }
  }

  // Calculate trend percentage between current and previous value
  // Returns undefined if no meaningful comparison can be made (to hide the trend indicator)
  const calculateTrend = (current, previous) => {
    // If no previous data, don't show trend
    if (previous === null || previous === undefined) return undefined
    // If previous was 0 and current is also 0, don't show trend
    if (previous === 0 && current === 0) return undefined
    // If values are the same, return 0 (no change)
    if (current === previous) return 0
    // If previous was 0 but current has value, can't calculate meaningful percentage
    if (previous === 0 && current > 0) return undefined
    // Calculate percentage change
    const change = ((current - previous) / previous) * 100
    return Math.round(change * 10) / 10 // Round to 1 decimal place
  }

  const fetchAlerts = async (signal) => {
    try {
      // Pass the signal to axios
      const response = await axios.get('/api/alerts', { signal })
      setAlerts(response.data.alerts || [])
    } catch (err) {
      // Don't log an error if aborted
      if (err.name !== 'CanceledError' && !axios.isCancel(err)) {
        console.error('Failed to load alerts:', err)
      }
    }
  }

  const fetchConversations = async (signal) => {
    try {
      // Pass the signal to axios
      const response = await axios.get('/api/conversations', { signal })
      setConversations(response.data.conversations || [])
      console.log('📞 Fetched conversations:', response.data.conversations?.length || 0)
    } catch (err) {
      // Don't log an error if aborted
      if (err.name !== 'CanceledError' && !axios.isCancel(err)) {
        console.error('Failed to load conversations:', err)
        // Fallback to empty array if API fails
        setConversations([])
      }
    }
  }

  // ✅ Memoize expensive calculations
  const activeConversations = useMemo(() => {
    return conversations.filter(c => c.status === 'IN_PROGRESS').length
  }, [conversations]) // Only re-runs when 'conversations' changes

  const criticalAlerts = useMemo(() => {
    return conversations.filter(c => c.situationLevel === 'high' || c.situationLevel === 'critical').length
  }, [conversations]) // Only re-runs when 'conversations' changes

  const totalConversations = useMemo(() => {
    return conversations.length
  }, [conversations]) // Only re-runs when 'conversations' changes

  // This error check is still good
  if (error && !metrics && conversations.length === 0) {
    return <div className="error">{error}</div>
  }

  return (
    <div className="dashboard">
      {/* Enhanced Professional Header with Integrated Critical Alert */}
      <div className={`dashboard-header ${alerts.filter(alert => alert.severity === 'critical' || alert.severity === 'CRITICAL').length > 0 ? 'has-critical-alerts' : ''}`}>
        <div className="header-left">
          <div className="header-title">
            <h1>Monitoraggio conversazioni</h1>
            <span className="header-subtitle">Sistema di monitoraggio real-time per conversazioni terapeutiche</span>
          </div>
          
          {/* Critical Alert Indicator */}
          {alerts.filter(alert => alert.severity === 'critical' || alert.severity === 'CRITICAL').length > 0 && (
            <div className="critical-alert-indicator">
              <span className="alert-icon">🚨</span>
              <span className="alert-text">
                {alerts.filter(alert => alert.severity === 'critical' || alert.severity === 'CRITICAL').length} Critical Alert(s) - 
                <button 
                  className="btn-view-critical-alerts"
                  onClick={() => setSidebarOpen(true)}
                >
                  View Now
                </button>
              </span>
            </div>
          )}
          
          <div className="system-status">
            <span className="status-indicator status-online"></span>
            <span className="status-text">System Online</span>
            <span className="status-divider">|</span>
            {/* Real-time indicator removed as requested */}
            <TimeAgo timestamp={lastUpdated} />
          </div>
        </div>
        
        <div className="header-right">
          {/* Alert button removed as requested */}
        </div>
      </div>
      
      {/* --- SKELETON LOGIC --- */}
      {/* Show a skeleton if data isn't ready yet */}
      {!metrics ? (
        <ConversationStatusSkeleton />
      ) : (
        <ConversationStatus conversations={conversations} />
      )}

      {/* Check for conversations OR !metrics as the trigger */}
      {!metrics && conversations.length === 0 ? (
        <ConversationListSkeleton />
      ) : (
        <ConversationList 
          conversations={conversations}
          onConversationsRefresh={fetchConversations}
        />
      )}

      {/* --- SKELETON LOGIC --- */}
      <div className="metrics-grid">
        {!metrics ? (
          <>
            <MetricCardSkeleton />
            <MetricCardSkeleton />
            <MetricCardSkeleton />
            <MetricCardSkeleton />
          </>
        ) : (
          <>
            <MetricCard 
              title="Conversazioni Attive"
              value={activeConversations}
              icon="💬"
              trend={previousMetrics ? calculateTrend(
                activeConversations,
                previousMetrics.conversation_metrics?.active_sessions || 0
              ) : undefined}
            />
            <MetricCard 
              title="Allarmi Critici"
              value={criticalAlerts}
              icon="🚨"
              trend={previousMetrics ? calculateTrend(
                criticalAlerts,
                previousMetrics.alert_metrics?.critical_alerts || 0
              ) : undefined}
              isAlert={true}
            />
            <MetricCard 
              title="Conversazioni Oggi"
              value={totalConversations}
              icon="📅"
              trend={previousMetrics ? calculateTrend(
                totalConversations,
                previousMetrics.conversation_metrics?.total_sessions || 0
              ) : undefined}
            />
            <MetricCard 
              title="Durata Media"
              value={metrics?.conversation_metrics?.average_session_duration 
                ? `${Math.round(metrics.conversation_metrics.average_session_duration)} min`
                : 'N/A'}
              icon="⏱️"
              trend={previousMetrics ? calculateTrend(
                metrics?.conversation_metrics?.average_session_duration || 0,
                previousMetrics.conversation_metrics?.average_session_duration || 0
              ) : undefined}
            />
          </>
        )}
      </div>

      {/* Sidebar */}
      <Sidebar 
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        alerts={alerts}
        onAlertsRefresh={fetchAlerts}
      />

    </div>
  )
}

export default Dashboard

