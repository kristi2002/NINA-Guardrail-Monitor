import { useState, useEffect } from 'react'
import axios from 'axios'
import MetricCard from '../components/MetricCard'
import GuardrailChart from '../components/GuardrailChart'
import ConversationList from '../components/ConversationList'
import ConversationStatus from '../components/ConversationStatus'
import Sidebar from '../components/Sidebar'
import notificationService from '../services/notificationService'
import './Dashboard.css'

function Dashboard() {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [conversations, setConversations] = useState([])
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(new Date())
  const [updateCounter, setUpdateCounter] = useState(0)
  const [realtimeActive, setRealtimeActive] = useState(false)

  useEffect(() => {
    fetchMetrics()
    fetchAlerts()
    fetchConversations()
    
    // Connect to WebSocket via notification service
    notificationService.connect().then(() => {
      console.log('✅ Connected to notification service')
    }).catch(err => {
      console.error('❌ Failed to connect to notification service:', err)
    })
    
    // Subscribe to notifications (covers guardrail events)
    const unsubscribeNotification = notificationService.subscribe('notification', (data) => {
      console.log('🔔 Received notification:', data)
      // Refresh alerts when new event arrives
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
    
    // Update timer display every second
    const timeInterval = setInterval(() => {
      setUpdateCounter(prev => prev + 1)
    }, 1000)
    
    return () => {
      clearInterval(interval)
      clearInterval(timeInterval)
      unsubscribeNotification()
      unsubscribeEscalation()
      unsubscribeStatus()
    }
  }, [])

  const fetchMetrics = async () => {
    try {
      const response = await axios.get('/api/metrics')
      setMetrics(response.data)
      setLastUpdated(new Date())
      setLoading(false)
    } catch (err) {
      setError('Failed to load metrics. Make sure the backend is running.')
      setLoading(false)
    }
  }

  const fetchAlerts = async () => {
    try {
      const response = await axios.get('/api/alerts')
      setAlerts(response.data.alerts || [])
    } catch (err) {
      console.error('Failed to load alerts:', err)
    }
  }

  const fetchConversations = async () => {
    try {
      const response = await axios.get('/api/conversations')
      setConversations(response.data.conversations || [])
      console.log('📞 Fetched conversations:', response.data.conversations?.length || 0)
    } catch (err) {
      console.error('Failed to load conversations:', err)
      // Fallback to empty array if API fails
      setConversations([])
    }
  }

  const getTimeSinceUpdate = () => {
    const seconds = Math.floor((new Date() - lastUpdated) / 1000)
    if (seconds < 60) return `${seconds}s ago`
    const minutes = Math.floor(seconds / 60)
    return `${minutes}m ago`
  }


  if (loading) {
    return <div className="loading">Loading dashboard...</div>
  }

  if (error) {
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
            <span className="last-updated">Updated {getTimeSinceUpdate()}</span>
          </div>
        </div>
        
        <div className="header-right">
          {/* Alert button removed as requested */}
        </div>
      </div>
      
      {/* Conversation Status Overview */}
      <ConversationStatus conversations={conversations} />

      {/* Conversation Monitoring Section */}
      <ConversationList 
        conversations={conversations}
        onConversationsRefresh={fetchConversations}
      />

      {/* Optional: Keep some metrics for system health */}
      <div className="metrics-grid">
        <MetricCard 
          title="Conversazioni Attive"
          value={conversations.filter(c => c.status === 'IN_PROGRESS').length}
          icon="💬"
          trend={0}
        />
        <MetricCard 
          title="Allarmi Critici"
          value={conversations.filter(c => c.situationLevel === 'high').length}
          icon="🚨"
          trend={0}
          isAlert={true}
        />
        <MetricCard 
          title="Conversazioni Oggi"
          value={conversations.length}
          icon="📅"
          trend={0}
        />
        <MetricCard 
          title="Sistema Online"
          value="100%"
          icon="✅"
          trend={0}
        />
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

